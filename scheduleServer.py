from flask_login import UserMixin, current_user, LoginManager, login_required, login_user, logout_user
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask.wrappers import Response
from scheduler import scheduling
from ra_sched import RA
import scheduler3_0
import copy as cp
import datetime
import psycopg2
import calendar
import json
import os

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]
Bootstrap(app)
# Setup for flask_dance with oauth
app.secret_key = os.environ["SECRET_KEY"]
gBlueprint = make_google_blueprint(
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    scope=["profile", "email"],
    redirect_to="index"
)
app.register_blueprint(gBlueprint, url_prefix="/login")

conn = psycopg2.connect(os.environ["DATABASE_URL"])
baseOpts = {
    "HOST_URL": os.environ["HOST_URL"]
}

ALLOWED_EXTENSIONS = {'txt','csv'}
UPLOAD_FOLDER = "./static"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)                                                            # SQLAlchemy is used for OAuth
login_manager = LoginManager()                                                  # The login manager for the application
login_manager.init_app(app)
# The following classes are for SQLAlchemy to understand how the database is set up for OAuth
class User(UserMixin,db.Model):                                                 # Contains information about the user
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True)
    ra_id = db.Column(db.Integer, unique=True)

class OAuth(OAuthConsumerMixin,db.Model):                                       # Contains information about OAuth tokens
    provider_user_id = db.Column(db.String(256), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))                     # This links the tokens to the user
    user = db.relationship(User)

# The following creates the backend for flask_dance which associates users to OAuth tokens
#   user_required is set to False because of issues when users would first arrive to the
#   application before being authorized by Google and flask_dance would not be able to look
#   them up since they were not already authorized. By setting it to False, the app does not
#   require a user to already exist in our database to continue.
gBlueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user, user_required=False)

# Format date and time information for calendar
ct = datetime.datetime.now()
fDict = {"text_month":calendar.month_name[(ct.month+1)%12], "num_month":(ct.month+1)%12, "year":(ct.year if ct.month <= 12 else ct.year+1)}
cDict = {"text_month":calendar.month_name[ct.month], "num_month":ct.month, "year":ct.year}
cc = calendar.Calendar(6) #format calendar so Sunday starts the week

#     -- OAuth Decorators --

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

@oauth_authorized.connect_via(gBlueprint)
def googleLoggedIn(blueprint,token):
    print('googleLoggedIn')
    if not token:                                                               # If we don't have a token
        return False

    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:                                                             # If the response is bad
        print("NOT OK")
        return False
    google_info = resp.json()

    username = google_info["email"]
    gID = str(google_info["id"])

    query = OAuth.query.filter_by(provider=blueprint.name,                      # Query to find OAuth token in database
                                  provider_user_id=gID)
    try:
        oauth = query.one()                                                     # Execute the query
    except NoResultFound:                                                       # If there are no results
        print("NO OAUTH")
        oauth = OAuth(provider=blueprint.name,                                  # Create a new entry in our database
                      provider_user_id=gID,
                      token=token)

    if oauth.user:                                                              # If we have a user
        print("LOGGING OAUTH")
        login_user(oauth.user)                                                  # Log them in
    else:
        print("CREATE NEW USER")
        cur = conn.cursor()
        cur.execute("SELECT id FROM ra WHERE email = '{}'".format(username))    # Get the ra with the matching email so that we can link RAs to their emails
        raId = cur.fetchone()
        cur.close()

        user = User(username=username,ra_id=raId)                               # Create a new user in the database
        oauth.user = user                                                       # Associate it with the OAuth token
        db.session.add_all([user,oauth])
        db.session.commit()                                                     # Commit changes
        login_user(user)                                                        # Login user

    return False                                                                # Function should return False so that flask_dance won't try to store the token itself

#     -- Helper Functions --

def getAuth():
    uEmail = current_user.username                                              # The email returned from Google
    cur = conn.cursor()
    cur.execute("""
            SELECT ra.id, username, first_name, last_name, hall_id, auth_level, res_hall.name
            FROM "user" JOIN ra ON ("user".ra_id = ra.id)
                        JOIN res_hall ON (ra.hall_id = res_hall.id)
            WHERE username = '{}';""".format(uEmail))
    res = cur.fetchone()                                                        # Get user info from the database

    if res == None:                                                             # If user does not exist, go to error url
        cur.close()
        return redirect(url_for(".err",msg="No user found with email: {}".format(uEmail)))

    cur.close()
    return {"uEmail":uEmail,"ra_id":res[0],"name":res[2]+" "+res[3],
            "hall_id":res[4],"auth_level":res[5],"hall_name":res[6]}

def stdRet(status, msg):
    # Helper function to create a standard return object to help simplify code
    #  going back to the client when no additional data is to be sent.
    return {"status":status,"msg":msg}

def fileAllowed(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validateUpload(partList):

    pl = []
    for i in partList:
        i.replace("%","")
        i.replace(";","")
        i.replace("\\","")

        pl.append(i)

    valid = True
    reasons = []

    if len(partList) != 6:
        valid = False
        reasons.append("Expected 5 Parameters, Received: {}".format(len(partList)))
        print(partList)

    else:
        fName, lName, email, start, color, role = pl

        # Check Email Address
        if "@" not in email and "." not in email:
            valid = False
            reasons.append(fName+" "+lName+" - Invalid Email Address: "+email)
            print(email)

        # Check Start Date
        splitDate = start.split("/")
        if len(splitDate) != 3 or "-" in start or int(splitDate[0]) > 12 or \
            int(splitDate[1]) > 31 or int(splitDate[2]) < 1:
            valid = False
            reasons.append(fName+" "+lName+" - Invalid Start Date: "+start)
            print(start)

        # Check Color
        if len(color) != 7:
            valid = False
            reasons.append(fName+" "+lName+" - Invalid Color Format: {} Must be in 6-digit, hex format preceeded by a '#'".format(color))
            print(color)

    return pl, valid, reasons

def getSchoolYear(month, year):
    # Figure out what school year we are looking for

    if int(month) >= 8:
        # If the current month is August or later
        #  then the current year is the startYear
        startYear = int(year)
        endYear = int(year) + 1

    else:
        # If the current month is earlier than August
        #  then the current year is the endYear
        startYear = int(year) - 1
        endYear = int(year)

    # TODO: Currently, a school year is considered from August to August.
    #        Perhaps this should be configurable by the AHD/HDs?

    start = str(startYear) + '-08-01'
    end = str(endYear) + '-07-31'

    return start, end

def getCurSchoolYear():
    # Figure out what school year we are looking for
    month = datetime.date.today().month
    year = datetime.date.today().year

    return getSchoolYear(month, year)

#     -- Views --

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('.login'))

@app.route("/")
def login():
    return redirect(url_for("google.login"))

@app.route("/home")
@login_required
def index():
    userDict = getAuth()                                                        # Get the user's info from our database
    if type(userDict) != dict:
        return userDict
    return render_template("index.html",auth_level=userDict["auth_level"], \
                            curView=1, opts=baseOpts, hall_name=userDict["hall_name"])

@app.route("/conflicts")
def conflicts():
    userDict = getAuth()                                                        # Get the user's info from our database

    return render_template("conflicts.html",  auth_level=userDict["auth_level"], \
                            curView=2, opts=baseOpts, hall_name=userDict["hall_name"])

@app.route("/editSched")
@login_required
def editSched():
    userDict = getAuth()                                                        # Get the user's info from our database

    start, end = getCurSchoolYear()
    ptDict = getRAStats(userDict["hall_id"], start, end)

    #print(ptDict)

    cur = conn.cursor()
    cur.execute("SELECT id, first_name, last_name, color FROM ra WHERE hall_id = {} ORDER BY first_name ASC;".format(userDict["hall_id"]))

    # Sort alphabetically by last name of RA
    #ptDictSort = lambda kv: kv[1]["name"].split(" ")[1]

    return render_template("editSched.html", raList=cur.fetchall(), auth_level=userDict["auth_level"], \
                            ptDict=sorted(ptDict.items(), key=lambda x: x[1]["name"].split(" ")[1] ), \
                            curView=3, opts=baseOpts, hall_name=userDict["hall_name"])

@app.route("/staff")
@login_required
def manStaff():
    userDict = getAuth()                                                        # Get the user's info from our database

    start, end = getCurSchoolYear()

    cur = conn.cursor()
    cur.execute("SELECT ra.id, first_name, last_name, email, date_started, res_hall.name, color, auth_level \
                 FROM ra JOIN res_hall ON (ra.hall_id = res_hall.id) \
                 WHERE hall_id = {} ORDER BY ra.id ASC;".format(userDict["hall_id"]))

    ptStats = getRAStats(userDict["hall_id"], start, end)

    return render_template("staff.html",raList=cur.fetchall(),auth_level=userDict["auth_level"], \
                            opts=baseOpts,curView=3, hall_name=userDict["hall_name"], pts=ptStats)

#     -- API --

@app.route("/api/enterConflicts/", methods=['POST'])
@login_required
def processConflicts():
    userDict = getAuth()                                                        # Get the user's info from our database

    ra_id = userDict["ra_id"]
    hallId = userDict["hall_id"]

    #print(request.json)
    data = request.json

    insert_cur = conn.cursor()

    dateList = ()
    for d in data:                                                              # Append all dates to dateList (or in this case dateTUPLE)
        s = "TO_DATE('"+d+"','YYYY-MM-DD')"                                     # Create TO_DATE string from all date information
        dateList += (s,)                                                        # Add string to dateList

    bigDateStr = "("                                                            # Begin assembling the psql array string
    for i in dateList:
        bigDateStr+= i+", "
    bigDateStr = bigDateStr[:-2]+")"                                            # Get rid of the extra ", " at the end and cap it with a ")"

    exStr = """SELECT day.id FROM day
               WHERE day.date IN {};
                """.format(bigDateStr)                                          # Format the query string

    insert_cur.execute(exStr)                                                   # Execute the query
    dIds = insert_cur.fetchall()                                                # Get results

    for d in dIds:                                                              # For each date
        try:                                                                    # Try to insert it into the database
            insert_cur.execute("INSERT INTO conflicts (ra_id, day_id) VALUES ({},{});"\
                                .format(ra_id,d[0]))                            # Each entry is a tuple that must be indexed into to get the value. ie d[0]
            conn.commit()                                                       # Commit the change in case the try runs into an error
        except psycopg2.IntegrityError:                                         # If the conflict entry already exists
            print("error")
            conn.rollback()                                                     # Rollback last commit so that Internal Error doesn't occur
            insert_cur = conn.cursor()                                          # Create a new cursor

    insert_cur.close()
    return redirect(url_for(".index"))                                          # Send the user back to the main page (Not utilized by client currently)

@app.route("/api/getStaffInfo", methods=["GET"])
@login_required
def getStaffStats():
    userDict = getAuth()

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify("NOT AUTHORIZED")

    cur = conn.cursor()

    cur.execute("""SELECT ra.id, first_name, last_name, email, date_started, res_hall.name, color, auth_level
                 FROM ra JOIN res_hall ON (ra.hall_id = res_hall.id)
                 WHERE hall_id = {} ORDER BY ra.id DESC;""".format(userDict["hall_id"]))

    start, end = getCurSchoolYear()
    pts = getRAStats(userDict["hall_id"], start, end)

    ret = {"raList":cur.fetchall(), "pts":pts}

    return jsonify(ret)

@app.route("/api/getStats", methods=["GET"])
@login_required
def getRAStats(hallId=None,startDateStr=None,endDateStr=None):
    # API Hook that will get the RA stats for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  The server will then query the database for the appropriate statistics
    #  and send back a json object.

    fromServer = True
    if hallId is None and startDateStr is None and endDateStr is None:          # Effectively: If API was called from the client and not from the server
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False
        startDateStr = request.args.get("start")
        endDateStr = request.args.get("end")

    res = {}

    cur = conn.cursor()

    cur.execute("""SELECT ra.id, ra.first_name, ra.last_name, COALESCE(ptQuery.pts,0)
                   FROM (SELECT ra.id AS rid, SUM(duties.point_val) AS pts
                         FROM duties JOIN day ON (day.id=duties.day_id)
                                     JOIN ra ON (ra.id=duties.ra_id)
                         WHERE duties.hall_id = {}
                         AND duties.sched_id IN
                         (
                            SELECT DISTINCT ON (schedule.month_id) schedule.id
                            FROM schedule
                            WHERE schedule.hall_id = {}
                            AND schedule.month_id IN
                            (
                                SELECT month.id
                                FROM month
                                WHERE month.year >= TO_DATE('{}', 'YYYY-MM-DD')
                                AND month.year <= TO_DATE('{}', 'YYYY-MM-DD')
                            )
                            ORDER BY schedule.month_id, schedule.created DESC, schedule.id DESC
                        )
                        GROUP BY rid) AS ptQuery
                   RIGHT JOIN ra ON (ptQuery.rid = ra.id)
                   WHERE ra.hall_id = {};""".format(hallId, hallId, startDateStr, endDateStr, hallId))

    raList = cur.fetchall()

    for ra in raList:
        res[ra[0]] = { "name": ra[1] + " " + ra[2], "pts": ra[3] }

    cur.close()
    if fromServer:
        # If this function call is from the server, simply return the results
        return res
    else:
        # Otherwise, if this function call is from the client, return the
        #  results as a JSON response object.
        return jsonify(res)

@app.route("/api/getSchedule", methods=["GET"])
@login_required
def getSchedule2(monthNum=None,year=None,hallId=None,allColors=None):
    # API Hook that will get the requested schedule for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  The server will then query the database for the appropriate schedule
    #  and send back a jsonified version of the schedule. If no month and
    #  subsequently no schedule is found in the database, the server will
    #  return an empty list

    fromServer = True
    if monthNum is None and year is None and hallId is None and allColors is None:                    # Effectively: If API was called from the client and not from the server
        monthNum = int(request.args.get("monthNum"))
        year = int(request.args.get("year"))
        start = request.args.get("start").split("T")[0]                         # No need for the timezone in our current application
        end = request.args.get("end").split("T")[0]                             # No need for the timezone in our current application
        showAllColors = bool(request.args.get("allColors"))                     # Should all colors be displayed or only the current user's colors

        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False
    res = []

    cur = conn.cursor()

    cur.execute("""
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD')
        FROM duties JOIN day ON (day.id=duties.day_id)
                    JOIN RA ON (ra.id=duties.ra_id)
        WHERE duties.hall_id = {}
        AND duties.sched_id IN
                (
                SELECT DISTINCT ON (schedule.month_id) schedule.id
                FROM schedule
                WHERE schedule.hall_id = {}
                AND schedule.month_id IN
                    (
                        SELECT month.id
                        FROM month
                        WHERE month.year >= TO_DATE('{}','YYYY-MM')
                        AND month.year <= TO_DATE('{}','YYYY-MM')
                    )
                ORDER BY schedule.month_id, schedule.created DESC, schedule.id DESC
                )
        AND day.date >= TO_DATE('{}','YYYY-MM-DD')
        AND day.date <= TO_DATE('{}','YYYY-MM-DD')
        ORDER BY day.date ASC;
    """.format(hallId, hallId, start[:-3], end[:-3], start, end))

    rawRes = cur.fetchall()
    #print(rawRes)

    for row in rawRes:
        # If the ra is the same as the user, then display their color
        #  Otherwise, display a generic color.
        #print(userDict["ra_id"] == row[3])
        if not(showAllColors):
            # If the desired behavior is to not show all of the unique RA colors
            #  then check to see if the current user is the ra on the duty being
            #  added. If it is the ra, show their unique color, if not, show the
            #  same color.
            if userDict["ra_id"] == row[3]:
                c = row[2]
            else:
                c = "#2C3E50"

        # If the desired behavior is to show all of the unique RA colors, then
        #  simply set their color.
        else:
            c = row[2]

        res.append({
            "id": row[3],
            "title": row[0] + " " + row[1],
            "start": row[4],
            "color": c
        })

    if fromServer:
        return res
    else:
        return jsonify(res)

@app.route("/api/getMonth", methods=["GET"])
def getMonth(monthNum=None,year=None):
    # API Hook that will get the requested month format.
    # This function generates a blank calendar to return to the client for
    #  the given year and monthNum (1-12)

    if monthNum == None and year == None:                                       # Effectively: If API was called from the client and not from the server
        monthNum = int(request.args.get("monthNum"))
        year = int(request.args.get("year"))

    res = {}
    dateList = []
    for week in cc.monthdayscalendar(year,monthNum):
        weeklst = []
        for day in week:
            weeklst.append({"date":day,"ras":[]})

        dateList.append(weeklst)

    res["dates"] = dateList
    res["month"] = calendar.month_name[monthNum]

    return jsonify(res)

@app.route("/api/runScheduler", methods=["POST"])
def runScheduler3(hallId=None, monthNum=None, year=None):
    # TODO: Add ability to query double dates from arg values

    # API Hook that will run the scheduler for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  Additionally, the dates that should no have duties are also sent via
    #  request.args and can either be a string of comma separated integers
    #  ("1,2,3,4") or an empty string ("").
    #print("SCHEDULER")
    userDict = getAuth()                                                        # Get the user's info from our database
    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify("NOT AUTHORIZED")

    #print(request.json)

    fromServer = True
    if monthNum == None and year == None and hallId == None:                    # Effectively: If API was called from the client and not from the server
        month = int(request.json["monthNum"])
        year = int(request.json["year"])
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False
    res = {}

    try:
        if request.json["noDuty"] != "":
            noDutyList = [int(d) for d in request.json["noDuty"].split(",")]

        else:
            noDutyList = []

        if request.json["eligibleRAs"] != "":
            eligibleRAs = [int(i) for i in request.json["eligibleRAs"]]
            eligibleRAStr = "AND ra.id IN ({});".format(str(eligibleRAs)[1:-1])

        else:
            eligibleRAStr = ";"

    except:                                                                     # If error, send back an error message
        return jsonify("ERROR")

    hallId = userDict["hall_id"]
    cur = conn.cursor()

    cur.execute("SELECT id, year FROM month WHERE num = {} AND EXTRACT(YEAR FROM year) = {}".format(month,year))
    monthId, date = cur.fetchone()                                              # Get the month_id from the database
    #print(monthId)

    if monthId == None:                                                         # If the database does not have the correct month
        return jsonify("ERROR")                                                 # Send back an error message

    # Select all RAs in a particular hall whose auth_level is below 3 (HD)
    #  as well as all of their respective conflicts for a given month
    queryStr = """
        SELECT first_name, last_name, id, hall_id, date_started,
               COALESCE(cons.array_agg, ARRAY[]::date[])
        FROM ra LEFT OUTER JOIN (
            SELECT ra_id, ARRAY_AGG(days.date)
            FROM conflicts JOIN (
                SELECT id, date
                FROM day
                WHERE month_id = {}
                ) AS days
            ON (conflicts.day_id = days.id)
            GROUP BY ra_id
            ) AS cons
        ON (ra.id = cons.ra_id)
        WHERE ra.hall_id = {}
        AND ra.auth_level < 3 {}
    """.format(monthId, hallId, eligibleRAStr)

    #print(queryStr)

    cur.execute(queryStr)       # Query the database for the appropriate RAs and their respective information
    partialRAList = cur.fetchall()

    start, end = getSchoolYear(date.month, date.year)

    ptsDict = getRAStats(userDict["hall_id"], start, end)

    ra_list = [RA(res[0],res[1],res[2],res[3],res[4],res[5],ptsDict[res[2]]["pts"]) for res in partialRAList]

    # Set the Last Duty Assigned Tolerance based on floor dividing the number of
    #  RAs by 2 then adding 1. For example, with a staff of 15, the LDA Tolerance
    #  would be 8 days.
    ldat = (len(ra_list) // 2) + 1

    # Attempt to run the scheduler using deep copies of the raList and noDutyList.
    #  This is so that if the scheduler does not resolve on the first run, we
    #  can modify the parameters and try again with a fresh copy of the raList
    #  and noDutyList.
    copy_raList = cp.deepcopy(ra_list)
    copy_noDutyList = cp.copy(noDutyList)

    completed = False
    successful = True
    while not completed:
        # Create the Schedule
        sched = scheduler3_0.schedule(copy_raList,year,month,noDutyDates=copy_noDutyList,ldaTolerance=ldat)

        if len(sched) == 0:
            # If we were unable to schedule with the previous parameters,

            if ldat > 1:
                # And the LDATolerance is greater than 1
                #  then decrement the LDATolerance by 1 and try again

                #print("DECREASE LDAT: ", ldat)
                ldat -= 1
                copy_raList = cp.deepcopy(ra_list)
                copy_noDutyList = cp.copy(noDutyList)

            else:
                # The LDATolerance is not greater than 1 and we were unable to schedule
                completed = True
                successful = False

        else:
            # We were able to create a schedule
            completed = True

    #print(sched)

    if not successful:
        return jsonify({"status":0,"msg":"UNABLE TO GENERATE SCHEDULE"})

    # Add the schedule to the database and get its ID
    cur.execute("INSERT INTO schedule (hall_id, month_id, created) VALUES ({},{},NOW()) RETURNING id;".format(hallId, monthId))
    schedId = cur.fetchone()[0]
    conn.commit()
    #print(schedId)

    # Get the id of the schedule that was just created
    #cur.execute("SELECT id FROM schedule WHERE hall_id = {} AND month_id = {} ORDER BY created DESC, id DESC;".format(hallId, monthId))
    #schedId = cur.fetchone()[0]

    # Map the day id to the date
    days = {}
    cur.execute("SELECT EXTRACT(DAY FROM date), id FROM day WHERE month_id = {};".format(monthId))
    for res in cur.fetchall():
        days[res[0]] = res[1]

    # Iterate through the schedule
    dutyDayStr = ""
    noDutyDayStr = ""
    for d in sched:
        # If there are RAs assigned to this day
        if d.numberOnDuty() > 0:
            for r in d:
                dutyDayStr += "({},{},{},{},{}),".format(hallId, r.getId(), days[d.getDate()], schedId, d.getPoints())

        else:
            noDutyDayStr += "({},{},{},{}),".format(hallId, days[d.getDate()], schedId, d.getPoints())

    # Attempt to save the schedule to the DB
    try:
        # Add all of the duties that were scheduled for the month
        if dutyDayStr != "":
            cur.execute("""
                    INSERT INTO duties (hall_id, ra_id, day_id, sched_id, point_val) VALUES {};
                    """.format(dutyDayStr[:-1]))

        # Add all of the blank duty values for days that were not scheduled
        if noDutyDayStr != "":
            cur.execute("""
                    INSERT INTO duties (hall_id, day_id, sched_id, point_val) VALUES {};
                    """.format(noDutyDayStr[:-1]))

    except psycopg2.IntegrityError:
        #print("ROLLBACK")
        conn.rollback()

    conn.commit()

    cur.close()

    if fromServer:
        return stdRet(1,"successful")
    else:
        return jsonify(stdRet(1,"successful"))

# @app.route("/api/getEditInfo", methods=["GET"])
# @login_required
# def getEditInfo(hallId=None, monthNum=None, year=None):
#     # API Hook that will get a the list of RAs along with their conflicts for a.
#     #  given month. The month will be given via request.args as 'monthNum' and
#     #  'year'. The server will then query the database for the conflicts and
#     #  and return them along with a list of the RAs
#
#     userDict = getAuth()                                                        # Get the user's info from our database
#     if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
#         return jsonify("NOT AUTHORIZED")
#
#     fromServer = True
#     if monthNum == None and year == None and hallId == None:                    # Effectively: If API was called from the client and not from the server
#         monthNum = int(request.args.get("monthNum")) + 1
#         year = int(request.args.get("year"))
#         userDict = getAuth()                                                    # Get the user's info from our database
#         hallId = userDict["hall_id"]
#         fromServer = False
#     res = []
#     cur = conn.cursor()
#
#     #print(monthNum,year)
#
#     cur.execute("SELECT id FROM month WHERE num = {} AND year = TO_DATE('{}','YYYY')".format(monthNum,year))
#     monthId = cur.fetchone()[0]
#
#     cur.execute("SELECT id, first_name, last_name, points FROM ra WHERE hall_id = {};".format(hallId))
#     ra_list = cur.fetchall()
#
#     for raRes in ra_list:
#         raDict = {"id":raRes[0],"name":raRes[1]+" "+raRes[2][0]+".","points":raRes[3]}
#         cur.execute("""SELECT day.date
#                        FROM conflicts JOIN day ON (conflicts.day_id = day.id)
#                                       JOIN month ON (day.month_id = month.id)
#                        WHERE day.month_id = {} AND conflicts.ra_id = {};""".format(monthId,raRes[0]))
#
#         conList = cur.fetchall()
#         c = []
#         for con in conList:
#             c.append(con[0])
#
#         raDict["conflicts"] = c                                                 # Add conflicts to the RA Dict
#         res.append(raDict)                                                      # Append RA Dict to results list
#
#     if fromServer:
#         return res
#     else:
#         return jsonify(res)

@app.route("/api/changeStaffInfo", methods=["POST"])
@login_required
def changeStaffInfo():
    userDict = getAuth()                                                        # Get the user's info from our database

    hallId = userDict["hall_id"]

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify(stdRet(0,"NOT AUTHORIZED"))

    data = request.json

    cur = conn.cursor()
    cur.execute("""UPDATE ra
                   SET first_name = '{}', last_name = '{}',
                       date_started = TO_DATE('{}', 'YYYY-MM-DD'),
                       color = '{}', email = '{}', auth_level = {}
                   WHERE id = {};
                """.format(data["fName"],data["lName"], \
                        data["startDate"],data["color"], \
                        data["email"],data["authLevel"], \
                        data["raID"]))

    conn.commit()
    cur.close()
    return jsonify(stdRet(1,"successful"))

@app.route("/api/removeStaffer", methods=["POST"])
@login_required
def removeStaffer():
    userDict = getAuth()

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify("NOT AUTHORIZED")

    raID = request.json

    checkCur = conn.cursor()
    checkCur.execute("SELECT hall_id FROM ra WHERE id = {};".format(raID))

    if userDict["hall_id"] != checkCur.fetchone()[0]:
        return jsonify("NOT AUTHORIZED")

    checkCur.close()

    cur = conn.cursor()

    cur.execute("UPDATE ra SET hall_id = 0 WHERE id = {};".format(raID))
    conn.commit()
    cur.close()

    return jsonify(raID)

@app.route("/api/addStaffer", methods=["POST"])
@login_required
def addStaffer():
    userDict = getAuth()

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify("NOT AUTHORIZED")

    data = request.json

    checkCur = conn.cursor()
    checkCur.execute("SELECT * FROM ra WHERE email = '{}';".format(data["email"]))
    checkRes = checkCur.fetchone()

    if checkRes is not None:
        cur = conn.cursor()
        cur.execute("UPDATE ra SET hall_id = {} WHERE email = '{}';".format(userDict["hall_id"], data["email"]))
        conn.commit()

        cur.execute("SELECT * FROM ra WHERE email = '{}';".format(data["email"]))
        ret = cur.fetchone()
        cur.close()
        return jsonify(ret)

    cur = conn.cursor()

    cur.execute("""
    INSERT INTO ra (first_name,last_name,hall_id,date_started,color,email,auth_level)
    VALUES ('{}','{}',{},NOW(),'{}','{}','{}')
    RETURNING id;
    """.format(data["fName"],data["lName"],userDict["hall_id"],data["color"], \
                data["email"],data["authLevel"]))

    conn.commit()
    newId = cur.fetchone()[0]

    cur.execute("""SELECT ra.id, first_name, last_name, email, date_started, res_hall.name, color, auth_level
     FROM ra JOIN res_hall ON (ra.hall_id = res_hall.id)
     WHERE ra.id = {};""".format(newId))
    raData = cur.fetchone()
    cur.close()

    return jsonify(raData)

@app.route("/api/changeRAonDuty", methods=["POST"])
@login_required
def changeRAforDutyDay():
    userDict = getAuth()

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify({"status":-1,"msg":"NOT AUTHORIZED"})

    data = request.json
    #print("New RA id:", data["newId"])
    #print("Old RA Name:", data["oldName"])
    #print("HallID: ", userDict["hall_id"])
    # Expected as x/x/xxxx
    #print("DateStr: ", data["dateStr"])

    fName, lName = data["oldName"].split()

    cur = conn.cursor()

    # Find New RA
    cur.execute("SELECT id, first_name, last_name, color FROM ra WHERE id = {} AND hall_id = {};".format(data["newId"],userDict["hall_id"]))
    raParams = cur.fetchone()

    # Find Old RA
    cur.execute("SELECT id FROM ra WHERE first_name LIKE '{}' AND last_name LIKE '{}' AND hall_id = {}".format(fName, lName, userDict["hall_id"]))
    oldRA = cur.fetchone()

    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE('{}', 'MM/DD/YYYY');".format(data["dateStr"]))
    dayID, monthId = cur.fetchone()

    cur.execute("SELECT id FROM schedule WHERE hall_id = {} AND month_id = {} ORDER BY created DESC, id DESC;".format(userDict["hall_id"],monthId))
    schedId = cur.fetchone()


    if raParams is not None and dayID is not None and schedId is not None and oldRA is not None:
        cur.execute("""UPDATE duties
                       SET ra_id = {}
                       WHERE hall_id = {}
                       AND day_id = {}
                       AND sched_id = {}
                       AND ra_id = {}
                       """.format(raParams[0],userDict["hall_id"],dayID,schedId[0],oldRA[0]))

        conn.commit()

        cur.close()

        ret = stdRet(1,"successful")
        # ret["pointDict"] = getRAStats(userDict["hall_id"], start, end)

        return jsonify(ret)

    else:
        # Something is not in the DB

        cur.close()

        return jsonify(stdRet(0,"Unable to find parameters in DB"))


@app.route("/api/addNewDuty", methods=["POST"])
@login_required
def addNewDuty():
    userDict = getAuth()

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify("NOT AUTHORIZED")

    data = request.json

    #print("New RA id:", data["id"])
    #print("HallID: ", userDict["hall_id"])
    # Expected as x-x-xxxx
    #print("DateStr: ", data["dateStr"])

    cur = conn.cursor()

    cur.execute("SELECT id FROM ra WHERE id = {} AND hall_id = {};".format(data["id"],userDict["hall_id"]))
    raId = cur.fetchone()

    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE('{}', 'YYYY-MM-DD');".format(data["dateStr"]))
    dayID, monthId = cur.fetchone()

    cur.execute("SELECT id FROM schedule WHERE hall_id = {} AND month_id = {} ORDER BY created DESC, id DESC;".format(userDict["hall_id"],monthId))
    schedId = cur.fetchone()

    if raId is not None and dayID is not None and schedId is not None:
        cur.execute("""INSERT INTO duties (hall_id, ra_id, day_id, sched_id, point_val)
                        VALUES ({}, {}, {}, {}, {});""".format(userDict["hall_id"], raId[0], dayID, schedId[0], data["pts"]))

        conn.commit()

        cur.close()

        return jsonify(stdRet(1,"successful"))

    else:
        # Something is not in the DB

        cur.close()

        return jsonify(stdRet(-1,"Unable to find parameters in DB"))

@app.route("/api/deleteDuty", methods=["POST"])
@login_required
def daleteDuty():
    userDict = getAuth()

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify("NOT AUTHORIZED")

    data = request.json

    #print("Deleted Duty RA Name:", data["raName"])
    #print("HallID: ", userDict["hall_id"])
    # Expected as x-x-xxxx
    #print("DateStr: ", data["dateStr"])

    fName, lName = data["raName"].split()

    cur = conn.cursor()

    cur.execute("SELECT id FROM ra WHERE first_name LIKE '{}' AND last_name LIKE '{}' AND hall_id = {};".format(fName,lName,userDict["hall_id"]))
    raId = cur.fetchone()

    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE('{}', 'MM/DD/YYYY');".format(data["dateStr"]))
    dayID, monthId = cur.fetchone()

    cur.execute("SELECT id FROM schedule WHERE hall_id = {} AND month_id = {} ORDER BY created DESC, id DESC;".format(userDict["hall_id"],monthId))
    schedId = cur.fetchone()

    if raId is not None and dayID is not None and schedId is not None:
        cur.execute("""DELETE FROM duties
                        WHERE ra_id = {}
                        AND hall_id = {}
                        AND day_id = {}
                        AND sched_id = {}""".format(raId[0], userDict["hall_id"], dayID, schedId[0]))

        conn.commit()

        cur.close()

        return jsonify({"status":1})

    else:

        cur.close()

        return jsonify({"status":0,"error":"Unable to find parameters in DB"})

@app.route("/api/importStaff", methods=["POST"])
@login_required
def importStaff():
    userDict = getAuth()

    if userDict["auth_level"] < 3:                                              # If the user is not at least an AHD
        return jsonify("NOT AUTHORIZED")

    print(request.files)
    if 'file' not in request.files:
            return jsonify(stdRet(0,"No File Part"))

    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename

    if file.filename == '':
        return jsonify(stdRet(0,"No File Selected"))

    if file and fileAllowed(file.filename):
        dataStr = file.read().decode("utf-8")

        # Iterate through the rows of the dataStr
        #  The expected format for the csv contains
        #  a header row and is as follows:
        #  First Name, Last Name, Email, Date Started (MM/DD/YYYY), Color, Role

        #  Example:
        #  FName, LName-Hyphen, example@email.com, 05/28/2020, #OD1E76, RA
        print(dataStr)
        cur = conn.cursor()
        for row in dataStr.split("\n")[1:]:
            if row != "":
                pl = [ part.strip() for part in row.split(",") ]
                print(pl)

                # Do some validation checking

                pl, valid, reasons = validateUpload(pl)

                if not valid:
                    ret = stdRet("0","Invalid Formatting")
                    ret["except"] = reasons
                    return jsonify(ret)

                if pl[-1] == "HD" and userDict["auth_level"] >= 3:
                    auth = 3
                elif pl[-1] == "AHD":
                    auth = 2
                else:
                    auth = 1

                print(auth)

                try:
                    cur.execute("""
                        INSERT INTO ra (first_name,last_name,hall_id,date_started,color,email,auth_level)
                        VALUES ('{}','{}',{},TO_DATE('{}','MM/DD/YYYY'),'{}','{}',{});
                        """.format(pl[0],pl[1],userDict["hall_id"],pl[3],pl[4],pl[2],auth))

                    conn.commit()

                except psycopg2.IntegrityError:                                         # If the conflict entry already exists
                    print("Duplicate RA: ", pl)
                    conn.rollback()                                                     # Rollback last commit so that Internal Error doesn't occur
                    cur.close()
                    cur = conn.cursor()

        cur.close()

        return redirect(url_for(".manStaff"))

    else:
        return redirect(url_for(".err",msg="Unable to Import Staff"))

@app.route("/api/getConflicts", methods=["GET"])
@login_required
def getConflicts(monthNum=None,raID=None,year=None,hallId=None):
    # API Hook that will get the requested conflicts for a given user and month.
    #  The month will be given via request.args as 'monthNum' and 'year'.

    fromServer = True
    if monthNum is None and year is None and hallId is None and raID is None:                    # Effectively: If API was called from the client and not from the server
        monthNum = int(request.args.get("monthNum"))
        year = int(request.args.get("year"))

        userDict = getAuth()                                                    # Get the user's info from our database
        hallID = userDict["hall_id"]
        raID = userDict["ra_id"]
        fromServer = False


    print(monthNum, year, hallID, raID)

    cur = conn.cursor()

    cur.execute("SELECT id FROM month WHERE num = {} AND EXTRACT(YEAR FROM year) = {}".format(monthNum, year))
    monthID = cur.fetchone()

    if monthID is None:
        return jsonify(stdRet(-1,"No month found with Num = {}".format(monthNum)))

    else:
        monthID = monthID[0]

    cur.execute("""SELECT TO_CHAR(day.date, 'YYYY-MM-DD')
                   FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                   WHERE conflicts.ra_id = {}
                   AND day.month_id = {}""".format(raID, monthID, hallID))

    ret = [ d[0] for d in cur.fetchall() ]

    return jsonify({"conflicts":ret})


#     -- Error Handling --

@app.route("/error/<string:msg>")
def err(msg):
    return render_template("error.html", errorMsg=msg)

if __name__ == "__main__":
    local = os.environ["USE_ADHOC"]
    if local:
        app.run(ssl_context="adhoc", debug=True)
    else:
        app.run()
