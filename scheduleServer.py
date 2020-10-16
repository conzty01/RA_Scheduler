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
import scheduler4_0
import copy as cp
import datetime
import psycopg2
import calendar
import logging
import json
import os

logLevel = os.environ["LOG_LEVEL"].upper()

if logLevel == "DEBUG":
    logLevel = logging.DEBUG
elif logLevel == "INFO":
    logLevel = logging.INFO
elif logLevel == "WARNING":
    logLevel = logging.WARNING
elif logLevel == "ERROR":
    logLevel = logging.ERROR
elif logLevel == "CRITICAL":
    logLevel = logging.CRITICAL
else:
    logLevel = logging.WARNING

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
    logging.info('googleLoggedIn')
    if not token:                                                               # If we don't have a token
        return False

    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:                                                             # If the response is bad
        logging.info("NOT OK")
        return False
    google_info = resp.json()

    username = google_info["email"]
    gID = str(google_info["id"])

    query = OAuth.query.filter_by(provider=blueprint.name,                      # Query to find OAuth token in database
                                  provider_user_id=gID)
    try:
        oauth = query.one()                                                     # Execute the query
    except NoResultFound:                                                       # If there are no results
        logging.info("NO OAUTH")
        oauth = OAuth(provider=blueprint.name,                                  # Create a new entry in our database
                      provider_user_id=gID,
                      token=token)

    if oauth.user:                                                              # If we have a user
        logging.info("LOGGING OAUTH")
        login_user(oauth.user)                                                  # Log them in
    else:
        logging.info("CREATE NEW USER")
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
    logging.debug("Start getAuth")
    uEmail = current_user.username                                              # The email returned from Google
    cur = conn.cursor()
    cur.execute("""
            SELECT ra.id, username, first_name, last_name, hall_id, auth_level, res_hall.name
            FROM "user" JOIN ra ON ("user".ra_id = ra.id)
                        JOIN res_hall ON (ra.hall_id = res_hall.id)
            WHERE username = '{}';""".format(uEmail))
    res = cur.fetchone()                                                        # Get user info from the database

    if res == None:                                                             # If user does not exist, go to error url
        logging.warning("No user found with email: {}".format(uEmail))

        cur.close()
        return redirect(url_for(".err",msg="No user found with email: {}".format(uEmail)))

    cur.close()
    return {"uEmail":uEmail,"ra_id":res[0],"name":res[2]+" "+res[3],
            "hall_id":res[4],"auth_level":res[5],"hall_name":res[6]}

def stdRet(status, msg):
    # Helper function to create a standard return object to help simplify code
    #  going back to the client when no additional data is to be sent.
    logging.debug("Generate Standard Return")
    return {"status":status,"msg":msg}

def fileAllowed(filename):
    logging.debug("Checking if file is allowed")
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validateUpload(partList):
    logging.debug("Validating Upload")
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
        logging.debug("PartList: "+str(partList))

    else:
        fName, lName, email, start, color, role = pl

        # Check Email Address
        if "@" not in email and "." not in email:
            valid = False
            reasons.append(fName+" "+lName+" - Invalid Email Address: "+email)
            logging.debug("RA Email: "+email)

        # Check Start Date
        splitDate = start.split("/")
        if len(splitDate) != 3 or "-" in start or int(splitDate[0]) > 12 or \
            int(splitDate[1]) > 31 or int(splitDate[2]) < 1:
            valid = False
            reasons.append(fName+" "+lName+" - Invalid Start Date: "+start)
            logging.debug("RA Start Date: "+start)

        # Check Color
        if len(color) != 7:
            valid = False
            reasons.append(fName+" "+lName+" - Invalid Color Format: {} Must be in 6-digit, hex format preceeded by a '#'".format(color))
            logging.debug("RA Color: "+color)

    return pl, valid, reasons

def getSchoolYear(month, year):
    # Figure out what school year we are looking for
    logging.debug("Calculate School Year: {} {}".format(month, year))

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

    logging.debug("Start: "+ start)
    logging.debug("End: "+ end)

    return start, end

def getCurSchoolYear():
    # Figure out what school year we are looking for
    logging.debug("Calculate Current School Year")
    month = datetime.date.today().month
    year = datetime.date.today().year

    return getSchoolYear(month, year)

#     -- Views --

@app.route("/logout")
@login_required
def logout():
    logging.info("Logout User")
    logout_user()
    return redirect(url_for('.login'))

@app.route("/")
def login():
    logging.info("Redirect to Google Login")
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

    if userDict["auth_level"] < 2:
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    start, end = getCurSchoolYear()
    ptDict = getRAStats(userDict["hall_id"], start, end)

    logging.debug("Point Dict: {}".format(ptDict))

    cur = conn.cursor()
    cur.execute("SELECT id, first_name, last_name, color FROM ra WHERE hall_id = {} ORDER BY first_name ASC;".format(userDict["hall_id"]))

    # Sort alphabetically by last name of RA
    #ptDictSort = lambda kv: kv[1]["name"].split(" ")[1]

    return render_template("editSched.html", raList=cur.fetchall(), auth_level=userDict["auth_level"], \
                            ptDict=sorted(ptDict.items(), key=lambda x: x[1]["name"].split(" ")[1] ), \
                            curView=3, opts=baseOpts, hall_name=userDict["hall_name"])

@app.route("/editCons")
@login_required
def editCons():
    userDict = getAuth()

    if userDict["auth_level"] < 2:
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    cur = conn.cursor()
    cur.execute("SELECT id, first_name, last_name, color FROM ra WHERE hall_id = {} ORDER BY first_name ASC;".format(userDict["hall_id"]))

    return render_template("editCons.html", raList=cur.fetchall(), auth_level=userDict["auth_level"], \
                            curView=3, opts=baseOpts, hall_name=userDict["hall_name"])

@app.route("/staff")
@login_required
def manStaff():
    userDict = getAuth()                                                        # Get the user's info from our database

    if userDict["auth_level"] < 2:
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    start, end = getCurSchoolYear()

    cur = conn.cursor()
    cur.execute("SELECT ra.id, first_name, last_name, email, date_started, res_hall.name, color, auth_level \
                 FROM ra JOIN res_hall ON (ra.hall_id = res_hall.id) \
                 WHERE hall_id = {} ORDER BY ra.id ASC;".format(userDict["hall_id"]))

    ptStats = getRAStats(userDict["hall_id"], start, end)

    return render_template("staff.html",raList=cur.fetchall(),auth_level=userDict["auth_level"], \
                            opts=baseOpts,curView=3, hall_name=userDict["hall_name"], pts=ptStats)

@app.route("/editBreaks", methods=['GET'])
@login_required
def editBreaks():
    userDict = getAuth()

    if userDict["auth_level"] < 2:
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonfiy(stdRet(-1,"NOT AUTHORIZED"))

    start, end = getCurSchoolYear()
    logging.debug(start)
    logging.debug(end)

    bkDict = getRABreakStats(userDict["hall_id"], start, end)

    logging.debug(bkDict)

    cur = conn.cursor()
    cur.execute("SELECT id, first_name, last_name, color FROM ra WHERE hall_id = {} ORDER BY first_name ASC;".format(userDict["hall_id"]))

    return render_template("editBreaks.html", raList=cur.fetchall(), auth_level=userDict["auth_level"], \
                            bkDict=sorted(bkDict.items(), key=lambda x: x[1]["name"].split(" ")[1] ), \
                            curView=3, opts=baseOpts, hall_name=userDict["hall_name"])

#     -- API --

@app.route("/api/enterConflicts/", methods=['POST'])
@login_required
def processConflicts():
    logging.debug("Process Conflicts")
    userDict = getAuth()                                                        # Get the user's info from our database

    ra_id = userDict["ra_id"]
    hallId = userDict["hall_id"]

    logging.debug(request.json)
    monthNum = request.json["monthNum"]
    year = request.json["year"]
    conflicts = request.json["conflicts"]

    cur = conn.cursor()

    cur.execute("""SELECT TO_CHAR(day.date, 'YYYY-MM-DD')
                   FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                                  JOIN ra ON (ra.id = conflicts.ra_id)
                                  JOIN month ON (month.id = day.month_id)
                   WHERE num = {}
                   AND EXTRACT(YEAR from year) = {}
                   AND hall_id = {}
                   AND ra.id = {};""".format(monthNum,year, \
                                             userDict["hall_id"],userDict["ra_id"]))

    prevConflicts = cur.fetchall()
    prevSet = set([ i[0] for i in prevConflicts ])

    newSet = set(conflicts)

    # Get a set of dates that were previously entered but are not in the latest
    #  These items should be removed from the DB
    deleteSet = prevSet.difference(newSet)

    # Get a set of dates that have been submitted that were not previously
    #  These items shoudl be inserted into the DB
    addSet = newSet.difference(prevSet)

    cur = conn.cursor()
    logging.debug("DataConflicts: {}".format(conflicts))
    logging.debug("PrevSet: {}".format(prevSet))
    logging.debug("NewSet: {}".format(newSet))
    logging.debug("DeleteSet: {}, {}".format(deleteSet, str(deleteSet)[1:-1]))
    logging.debug("AddSet: {}, {}".format(addSet, str(addSet)[1:-1]))

    if len(deleteSet) > 0:

        cur.execute("""DELETE FROM conflicts
                       WHERE conflicts.day_id IN (
                            SELECT conflicts.day_id
                            FROM conflicts
                                JOIN day ON (conflicts.day_id = day.id)
                            WHERE TO_CHAR(day.date, 'YYYY-MM-DD') IN ({})
                            AND conflicts.ra_id = {}
                        );""".format(str(deleteSet)[1:-1],userDict["ra_id"]))

    if len(addSet) > 0:

        cur.execute("""INSERT INTO conflicts (ra_id, day_id)
                        SELECT {}, day.id FROM day
                        WHERE TO_CHAR(day.date, 'YYYY-MM-DD') IN ({})
                        """.format(userDict["ra_id"], str(addSet)[1:-1]))

    conn.commit()
    cur.close()
    return jsonify(stdRet(1,"successful"))                                          # Send the user back to the main page (Not utilized by client currently)

@app.route("/api/getStaffInfo", methods=["GET"])
@login_required
def getStaffStats():
    userDict = getAuth()

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

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
def getRAStats(hallId=None, startDateStr=None, endDateStr=None, maxBreakDay=None):
    # API Hook that will get the RA stats for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  The server will then query the database for the appropriate statistics
    #  and send back a json object.

    fromServer = True
    if hallId is None and startDateStr is None \
        and endDateStr is None and maxBreakDay is None:                         # Effectively: If API was called from the client and not from the server

        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False
        startDateStr = request.args.get("start")
        endDateStr = request.args.get("end")

    logging.debug("Get RA Stats - FromServer: {}".format(fromServer))

    res = {}

    cur = conn.cursor()

    breakDutyStart = startDateStr

    if maxBreakDay is None:
        # If maxBreakDay is None, then we should calculate the TOTAL number of points
        #  that each RA has for the course of the period specified (including
        #  all break duties).

        breakDutyEnd = endDateStr

    else:
        # If maxBreakDay is NOT None, then we should calculate the number of REGULAR
        #  duty points plus the number of BREAK duty points for the specified month.

        breakDutyEnd = maxBreakDay

    logging.debug("breakDutyStart: {}".format(breakDutyStart))
    logging.debug("breakDutyEnd: {}".format(breakDutyEnd))


    cur.execute("""SELECT ra.id, ra.first_name, ra.last_name, COALESCE(ptQuery.pts,0)
               FROM
               (
                   SELECT combined_res.rid AS rid, CAST(SUM(combined_res.pts) AS INTEGER) AS pts
                   FROM
                   (
                      SELECT ra.id AS rid, SUM(duties.point_val) AS pts
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
                      GROUP BY rid

                      UNION

                      SELECT ra.id AS rid, SUM(break_duties.point_val) AS pts
                      FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                                        JOIN ra ON (ra.id=break_duties.ra_id)
                      WHERE break_duties.hall_id = {}
                      AND day.date BETWEEN TO_DATE('{}', 'YYYY-MM-DD')
                                       AND TO_DATE('{}', 'YYYY-MM-DD')
                      GROUP BY rid
                   ) AS combined_res
                   GROUP BY combined_res.rid
               ) ptQuery
               RIGHT JOIN ra ON (ptQuery.rid = ra.id)
               WHERE ra.hall_id = {};""".format(hallId, hallId, startDateStr, \
                                                endDateStr, hallId, breakDutyStart, \
                                                breakDutyEnd, hallId))

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

        showAllColors = request.args.get("allColors") == "true"                 # Should all colors be displayed or only the current user's colors

        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False

    logging.debug("Get Schedule - From Server: {}".format(fromServer))
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
    logging.debug("RawRes: {}".format(rawRes))

    for row in rawRes:
        # If the ra is the same as the user, then display their color
        #  Otherwise, display a generic color.
        #logging.debug("Ra is same as user? {}".format(userDict["ra_id"] == row[3]))
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
            "color": c,
            "extendedProps": {"dutyType":"std"}
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

    logging.debug("Get Month - MonthNum: {}, Year: {}".format(monthNum, year))

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

    # API Hook that will run the scheduler for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  Additionally, the dates that should no have duties are also sent via
    #  request.args and can either be a string of comma separated integers
    #  ("1,2,3,4") or an empty string ("").

    # -- Check authorization --
    userDict = getAuth()                                                        # Get the user's info from our database
    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    logging.debug("Request.json: {}".format(request.json))

    # -- Begin parsing provided parameters --
    fromServer = True
    if monthNum == None and year == None and hallId == None:                    # Effectively: If API was called from the client and not from the server
        monthNum = int(request.json["monthNum"])
        year = int(request.json["year"])
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False

    logging.debug("Run Scheduler - From Server: {}".format(fromServer))
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
        return jsonify(stdRet(-1,"Error parsing No Duty Days and Eligible RAs"))

    hallId = userDict["hall_id"]
    cur = conn.cursor()

    # -- Find the month in the Database
    cur.execute("SELECT id, year FROM month WHERE num = {} AND EXTRACT(YEAR FROM year) = {}".format(monthNum,year))
    monthId, date = cur.fetchone()                                              # Get the month_id from the database
    logging.debug("MonthId: {}".format(monthId))

    if monthId == None:                                                         # If the database does not have the correct month
        logging.warning("Unable to find month {}/{} in DB".format(monthNum,year))
        return jsonify(stdRet(-1,"Unable to find month {}/{} in DB".format(monthNum,year)))


    # -- Get all eligible RAs and their conflicts --

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

    logging.debug(queryStr)

    cur.execute(queryStr)       # Query the database for the appropriate RAs and their respective information
    partialRAList = cur.fetchall()


    # -- Get the start and end date for the school year --

    start, end = getSchoolYear(date.month, date.year)

    # -- Get the number of points that the RAs have --

    # Calculate maxBreakDay
    dateNum = calendar.monthrange(date.year, date.month)[1]
    mBD = "{:04d}-{:02d}-{:02d}".format(date.year, date.month, dateNum)

    ptsDict = getRAStats(userDict["hall_id"], start, end, maxBreakDay=mBD)

    logging.debug("ptsDict: {}".format(ptsDict))

    # -- Assemble the RA List --

    ra_list = [RA(res[0],res[1],res[2],res[3],res[4],res[5],ptsDict[res[2]]["pts"]) for res in partialRAList]

    # logging.debug("RA_LIST_______________________")
    # for ra in ra_list:
    #     logging.debug("Name: {}".format(ra.getName()))
    #     logging.debug("ID: {}".format(ra.getId()))
    #     logging.debug("Hall: {}".format(ra.getHallId()))
    #     logging.debug("Started: {}".format(ra.getStartDate()))
    #     logging.debug("Hash: {}".format(hash(ra)))
    #
    # input()

    # Set the Last Duty Assigned Tolerance based on floor dividing the number of
    #  RAs by 2 then adding 1. For example, with a staff of 15, the LDA Tolerance
    #  would be 8 days.
    ldat = (len(ra_list) // 2) + 1

    # Get the last ldaTolerance number of days worth of duties from the previous month

    # If the current monthNum is 1
    if monthNum == 1:
        # Then the previous month is 12 of the previous year
        startMonthStr = '{}-12'.format(year - 1)

    else:
        startMonthStr = '{}-{}'.format(year, "{0:02d}".format(monthNum - 1))

    endMonthStr = '{}-{}'.format(year, "{0:02d}".format(monthNum))

    logging.debug("StartMonthStr: {}".format(startMonthStr))
    logging.debug("EndMonthStr: {}".format(endMonthStr))
    logging.debug("Hall Id: {}".format(userDict["hall_id"]))
    logging.debug("Year: {}".format(year))
    logging.debug('MonthNum: {0:02d}'.format(monthNum))
    logging.debug("LDAT: {}".format(ldat))

    cur.execute("""SELECT ra.first_name, ra.last_name, ra.id, ra.hall_id,
                          ra.date_started, day.date - TO_DATE('{}-{}-01','YYYY-MM-DD')
                  FROM duties JOIN day ON (day.id=duties.day_id)
                              JOIN ra ON (ra.id=duties.ra_id)
                  WHERE duties.hall_id = {}
                  AND duties.sched_id IN (
                        SELECT DISTINCT ON (schedule.month_id) schedule.id
                        FROM schedule
                        WHERE schedule.hall_id = {}
                        AND schedule.month_id IN (
                            SELECT month.id
                            FROM month
                            WHERE month.year >= TO_DATE('{}','YYYY-MM')
                            AND month.year <= TO_DATE('{}','YYYY-MM')
                        )
                        ORDER BY schedule.month_id, schedule.created DESC, schedule.id DESC
                  )
                  AND day.date >= TO_DATE('{}-{}-01','YYYY-MM-DD') - {}
                  AND day.date <= TO_DATE('{}-{}-01','YYYY-MM-DD') - 1
                  ORDER BY day.date ASC;
    """.format(year,'{0:02d}'.format(monthNum), userDict["hall_id"], userDict["hall_id"], \
               startMonthStr, endMonthStr, year, '{0:02d}'.format(monthNum), \
               ldat, year, '{0:02d}'.format(monthNum)))

    prevDuties = cur.fetchall()
    # Create shell RA objects that will hash to the appropriate value
    prevRADuties = [ ( RA(d[0],d[1],d[2],d[3],d[4]), d[5] ) for d in prevDuties ]

    logging.debug("PREVIOUS DUTIES: {}".format(prevRADuties))

    # -- Query DB for list of break duties for the month. --
    #     In version 4.0 of the scheduler, break duties essentially are treated
    #     like noDutyDates and are skipped in the scheduling process. As a result,
    #     only the date is needed.
    cur.execute("""
        SELECT TO_CHAR(day.date, 'DD')
        FROM break_duties JOIN day ON (break_duties.day_id = day.id)
        WHERE break_duties.month_id = {}
        AND break_duties.hall_id = {}
    """.format(monthId, userDict["hall_id"]))

    breakDuties = [ int(row[0]) for row in cur.fetchall() ]
    logging.debug("Break Duties: {}".format(breakDuties))


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
        sched = scheduler4_0.schedule(copy_raList, year, monthNum,\
                noDutyDates=copy_noDutyList, ldaTolerance=ldat, \
                prevDuties=prevRADuties, breakDuties=breakDuties)

        if len(sched) == 0:
            # If we were unable to schedule with the previous parameters,

            if ldat > 1:
                # And the LDATolerance is greater than 1
                #  then decrement the LDATolerance by 1 and try again

                logging.info("DECREASE LDAT: ", ldat)
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

    logging.debug("Schedule: {}".format(sched))

    if not successful:
        logging.info("Unable to Generate Schedule for Hall: {} MonthNum: {} Year: {}".format(userDict["hall_id"], monthNum, year))
        return jsonify(stdRet(0,"UNABLE TO GENERATE SCHEDULE"))

    # Add the schedule to the database and get its ID
    cur.execute("INSERT INTO schedule (hall_id, month_id, created) VALUES ({},{},NOW()) RETURNING id;".format(hallId, monthId))
    schedId = cur.fetchone()[0]
    conn.commit()
    logging.debug("Schedule ID: {}".format(schedId))

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
        logging.debug("ROLLBACK")
        conn.rollback()

    conn.commit()

    cur.close()

    logging.info("Successfully Generated Schedule: {}".format(schedId))

    if fromServer:
        return stdRet(1,"successful")
    else:
        return jsonify(stdRet(1,"successful"))

@app.route("/api/changeStaffInfo", methods=["POST"])
@login_required
def changeStaffInfo():
    userDict = getAuth()                                                        # Get the user's info from our database

    hallId = userDict["hall_id"]

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

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
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

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
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

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
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    data = request.json
    logging.debug("New RA id: {}".format(data["newId"]))
    logging.debug("Old RA Name: {}".format(data["oldName"]))
    logging.debug("HallID: {}".format(userDict["hall_id"]))
    # Expected as x/x/xxxx
    logging.debug("DateStr: {}".format(data["dateStr"]))

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
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    data = request.json

    logging.debug("New RA id: {}".format(data["id"]))
    logging.debug("HallID: {}".format(userDict["hall_id"]))
    # Expected as x-x-xxxx
    logging.debug("DateStr: {}".format(data["dateStr"]))

    cur = conn.cursor()

    cur.execute("SELECT id FROM ra WHERE id = {} AND hall_id = {};".format(data["id"],userDict["hall_id"]))
    raId = cur.fetchone()

    if raId is None:
        ret = stdRet(-1,"Unable to find RA {} in database".format(data["id"]))


    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE('{}', 'YYYY-MM-DD');".format(data["dateStr"]))
    dayID, monthId = cur.fetchone()

    if dayID is None:
        cur.close()
        logging.warning("Unable to find day {} in database".format(data["dateStr"]))
        return stdRet(-1,"Unable to find day {} in database".format(data["dateStr"]))

    if monthId is None:
        cur.close()
        logging.warning("Unable to find month for {} in database".format(data["dateStr"]))
        return stdRet(-1,"Unable to find month for {} in database".format(data["dateStr"]))


    cur.execute("SELECT id FROM schedule WHERE hall_id = {} AND month_id = {} ORDER BY created DESC, id DESC;".format(userDict["hall_id"],monthId))
    schedId = cur.fetchone()

    cur.execute("""INSERT INTO duties (hall_id, ra_id, day_id, sched_id, point_val)
                    VALUES ({}, {}, {}, {}, {});""".format(userDict["hall_id"], raId[0], dayID, schedId[0], data["pts"]))

    conn.commit()

    cur.close()

    logging.debug("Successfully added new duty")
    return jsonify(stdRet(1,"successful"))

@app.route("/api/deleteDuty", methods=["POST"])
@login_required
def daleteDuty():
    userDict = getAuth()

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    data = request.json

    logging.debug("Deleted Duty RA Name: {}".format(data["raName"]))
    logging.debug("HallID: {}".format(userDict["hall_id"]))
    # Expected as x-x-xxxx
    logging.debug("DateStr: {}".format(data["dateStr"]))

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

        logging.info("Successfully deleted duty")
        return jsonify(stdRet(1,"successful"))

    else:

        cur.close()

        logging.info("Unable to locate duty to delete")
        return jsonify({"status":0,"error":"Unable to find parameters in DB"})

@app.route("/api/importStaff", methods=["POST"])
@login_required
def importStaff():
    userDict = getAuth()

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    logging.info("Import File: {}".format(request.files))
    if 'file' not in request.files:
        logging.info("No file part found")
        return jsonify(stdRet(0,"No File Part"))

    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename

    if file.filename == '':
        logging.info("No File Selected")
        return jsonify(stdRet(0,"No File Selected"))

    if file and fileAllowed(file.filename):
        dataStr = file.read().decode("utf-8")

        # Iterate through the rows of the dataStr
        #  The expected format for the csv contains
        #  a header row and is as follows:
        #  First Name, Last Name, Email, Date Started (MM/DD/YYYY), Color, Role

        #  Example:
        #  FName, LName-Hyphen, example@email.com, 05/28/2020, #OD1E76, RA
        logging.debug(dataStr)
        cur = conn.cursor()
        for row in dataStr.split("\n")[1:]:
            if row != "":
                pl = [ part.strip() for part in row.split(",") ]
                logging.debug("PL: {}".format(pl))

                # Do some validation checking

                pl, valid, reasons = validateUpload(pl)

                if not valid:
                    ret = stdRet("0","Invalid Formatting")
                    ret["except"] = reasons
                    logging.info("Invalid Formatting")
                    return jsonify(ret)

                if pl[-1] == "HD" and userDict["auth_level"] >= 3:
                    auth = 3
                elif pl[-1] == "AHD":
                    auth = 2
                else:
                    auth = 1

                logging.debug(auth)

                try:
                    cur.execute("""
                        INSERT INTO ra (first_name,last_name,hall_id,date_started,color,email,auth_level)
                        VALUES ('{}','{}',{},TO_DATE('{}','MM/DD/YYYY'),'{}','{}',{});
                        """.format(pl[0],pl[1],userDict["hall_id"],pl[3],pl[4],pl[2],auth))

                    conn.commit()

                except psycopg2.IntegrityError:                                         # If the conflict entry already exists
                    logging.debug("Duplicate RA: {}, rolling back DB changes".format(pl))
                    conn.rollback()                                                     # Rollback last commit so that Internal Error doesn't occur
                    cur.close()
                    cur = conn.cursor()

        cur.close()

        return redirect(url_for(".manStaff"))

    else:
        logging.info("Unable to Import Staff")
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

    logging.debug("Get Conflicts - From Server: {}".format(fromServer))

    logging.debug("MonthNum: {}, Year: {}, HallID: {}, raID: {}".format(monthNum, year, hallID, raID))

    cur = conn.cursor()

    cur.execute("SELECT id FROM month WHERE num = {} AND EXTRACT(YEAR FROM year) = {}".format(monthNum, year))
    monthID = cur.fetchone()

    if monthID is None:
        logging.warning("No month found with Num = {}".format(monthNum))
        return jsonify(stdRet(-1,"No month found with Num = {}".format(monthNum)))

    else:
        monthID = monthID[0]

    cur.execute("""SELECT TO_CHAR(day.date, 'YYYY-MM-DD')
                   FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                   WHERE conflicts.ra_id = {}
                   AND day.month_id = {}""".format(raID, monthID, hallID))

    ret = [ d[0] for d in cur.fetchall() ]

    if fromServer:
        return ret
    else:
        return jsonify({"conflicts":ret})

@app.route("/api/getRAConflicts", methods=["GET"])
@login_required
def getRAConflicts():
    userDict = getAuth()

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    hallId = userDict["hall_id"]
    raId = request.args.get("raID")
    monthNum = request.args.get("monthNum")
    year = request.args.get("year")

    logging.debug("HallId: {}".format(hallId))
    logging.debug("RaId: {}".format(raId))
    logging.debug("MonthNum: {}".format(monthNum))
    logging.debug("Year: {}".format(year))
    logging.debug("RaId == -1? {}".format(int(raId) != -1))

    if int(raId) != -1:
        addStr = "AND conflicts.ra_id = {};".format(raId)
    else:
        addStr = ""

    logging.debug(addStr)

    cur = conn.cursor()

    cur.execute("SELECT id FROM month WHERE num = {} AND EXTRACT(YEAR FROM year) = {}".format(monthNum, year))
    monthID = cur.fetchone()

    if monthID is None:
        logging.info("No month found with Num = {}".format(monthNum))
        return jsonify(stdRet(-1,"No month found with Num = {}".format(monthNum)))

    else:
        monthID = monthID[0]

    cur.execute("""SELECT conflicts.id, ra.first_name, ra.last_name, TO_CHAR(day.date, 'YYYY-MM-DD'), ra.color
                   FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                                  JOIN ra ON (ra.id = conflicts.ra_id)
                   WHERE day.month_id = {}
                   AND ra.hall_id = {}
                   {};""".format(monthID, hallId, addStr))

    conDates = cur.fetchall()
    logging.debug("ConDates: {}".format(conDates))

    res = []

    for d in conDates:
        res.append({
            "id": d[0],
            "title": d[1] + " " + d[2],
            "start": d[3],
            "color": d[4]
        })

    return jsonify(res)

@app.route("/api/getStaffConflicts", methods=["GET"])
@login_required
def getRACons(hallId=None,startDateStr=None,endDateStr=None):
    # API Hook that will get the conflicts for a given month and hall.
    #  The month will be given via request.args as 'start' and 'end'.
    #  The server will then query the database for the appropriate conflicts.

    fromServer = True
    if hallId is None and startDateStr is None and endDateStr is None:
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        startDateStr = request.args.get("start").split("T")[0]                  # No need for the timezone in our current application
        endDateStr = request.args.get("end").split("T")[0]                      # No need for the timezone in our current application

        fromServer = False

    logging.debug("Get Staff Conflicts - From Server: {}".format(fromServer))

    res = []

    cur = conn.cursor()

    cur.execute("""
        SELECT ra.id, ra.first_name, ra.last_name, ra.color, TO_CHAR(day.date, 'YYYY-MM-DD')
        FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                       JOIN ra ON (conflicts.ra_id = ra.id)
        WHERE day.date >= TO_DATE('{}', 'YYYY-MM-DD')
        AND day.date <= TO_DATE('{}', 'YYYY-MM-DD')
        AND ra.hall_ID = {};
    """.format(startDateStr, endDateStr, hallId))

    rawRes = cur.fetchall()

    for row in rawRes:
        res.append({
            "id": row[0],
            "title": row[1] + " " + row[2],
            "start": row[4],
            "color": row[3]
        })

    if fromServer:
        return rawRes
    else:
        return jsonify(res)

@app.route("/api/getConflictNums", methods=["GET"])
@login_required
def getNumberConflicts(hallId=None,monthNum=None,year=None):

    fromServer = True
    if hallId is None and monthNum is None and year is None:
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        monthNum = request.args.get("monthNum")
        year = request.args.get("year")

        fromServer = False

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    cur = conn.cursor()

    cur.execute("""
        SELECT ra.id, COUNT(cons.id)
        FROM ra LEFT JOIN (
            SELECT conflicts.id, ra_id
            FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                           JOIN month ON (month.id = day.month_id)
            WHERE month.num = {}
            AND EXTRACT(YEAR FROM month.year) = {}
        ) AS cons ON (cons.ra_id = ra.id)
        WHERE ra.hall_id = {}
        GROUP BY ra.id;
    """.format(monthNum, year, hallId))

    res = {}
    for row in cur.fetchall():
        res[row[0]] = row[1]

    if fromServer:
        return res
    else:
        return jsonify(res)

@app.route("/api/getRABreakStats", methods=["GET"])
@login_required
def getRABreakStats(hallId=None,startDateStr=None,endDateStr=None):
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

    logging.debug("Get RA Break Duty Stats - FromServer: {}".format(fromServer))

    res = {}

    cur = conn.cursor()

    cur.execute("""SELECT ra.id, ra.first_name, ra.last_name, COALESCE(numQuery.count, 0)
                   FROM (SELECT ra.id AS rid, COUNT(break_duties.id) AS count
                         FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                                           JOIN ra ON (ra.id=break_duties.ra_id)
                         WHERE break_duties.hall_id = {}
                         AND day.date BETWEEN TO_DATE('{}', 'YYYY-MM-DD')
                                          AND TO_DATE('{}', 'YYYY-MM-DD')
                        GROUP BY rid) AS numQuery
                   RIGHT JOIN ra ON (numQuery.rid = ra.id)
                   WHERE ra.hall_id = {};""".format(hallId, startDateStr, \
                        endDateStr, hallId))

    raList = cur.fetchall()

    for ra in raList:
        res[ra[0]] = { "name": ra[1] + " " + ra[2], "count": ra[3] }

    cur.close()
    if fromServer:
        # If this function call is from the server, simply return the results
        return res
    else:
        # Otherwise, if this function call is from the client, return the
        #  results as a JSON response object.
        return jsonify(res)

@app.route("/api/getBreakDuties", methods=["GET"])
@login_required
def getBreakDuties(hallId=None,monthNum=None,year=None):
    userDict = getAuth()

    fromServer = True
    if monthNum is None and year is None and hallId is None:                    # Effectively: If API was called from the client and not from the server
        monthNum = int(request.args.get("monthNum"))
        year = int(request.args.get("year"))
        start = request.args.get("start").split("T")[0]                         # No need for the timezone in our current application
        end = request.args.get("end").split("T")[0]                             # No need for the timezone in our current application

        showAllColors = request.args.get("allColors") == "true"                 # Should all colors be displayed or only the current user's colors

        userDict = getAuth()                                                    # Get the user's info from our database
        hallID = userDict["hall_id"]
        fromServer = False

    cur = conn.cursor()

    cur.execute("""
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD')
        FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                          JOIN month ON (month.id=break_duties.month_id)
                          JOIN ra ON (ra.id=break_duties.ra_id)
        WHERE break_duties.hall_id = {}
        AND month.year >= TO_DATE('{}','YYYY-MM')
        AND month.year <= TO_DATE('{}','YYYY-MM')
    """.format(hallID,start,end))

    res = []

    for row in cur.fetchall():

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
            "color": c,
            "extendedProps": {"dutyType":"brk"}
        })

    if fromServer:
        return res
    else:
        return jsonify(res)

@app.route("/api/addBreakDuty", methods=["POST"])
def addBreakDuty():
    userDict = getAuth()

    data = request.json

    selID = data["id"]
    hallId = userDict["hall_id"]
    ptVal = data["pts"]
    dateStr = data["dateStr"]

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    cur = conn.cursor()

    # Validate that the RA desired exists and belongs to the same hall
    cur.execute("SELECT id FROM ra WHERE id = {} AND hall_id = {};".format(selID, hallId))
    raId = cur.fetchone()

    if raId is None:
        cur.close()
        logging.warning("Unable to find RA {} in hall {}".format(selID,hallId))
        ret = stdRet(-1,"Unable to find RA {} in hall {}".format(selID,hallId))

    else:
        # Extract the id from the tuple
        raId = raId[0]

    # Get the month and day IDs necessary to associate a record in break_duties
    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE('{}', 'YYYY-MM-DD');".format(dateStr))
    dayID, monthId = cur.fetchone()

    # No Day found
    if dayID is None:
        cur.close()
        logging.warning("Unable to find day {} in database".format(data["dateStr"]))
        return stdRet(-1,"Unable to find day {} in database".format(data["dateStr"]))

    # No month found
    if monthId is None:
        cur.close()
        logging.warning("Unable to find month for {} in database".format(data["dateStr"]))
        return stdRet(-1,"Unable to find month for {} in database".format(data["dateStr"]))

    cur.execute("""INSERT INTO break_duties (ra_id, hall_id, month_id, day_id, point_val)
                    VALUES ({}, {}, {}, {}, {});""".format(raId, hallId, monthId, dayID, ptVal))

    conn.commit()

    cur.close()

    logging.info("Successfully added new Break Duty for Hall {} and Month {}".format(hallId, monthId))

    return jsonify(stdRet(1,"successful"))

@app.route("/api/deleteBreakDuty", methods=["POST"])
@login_required
def deleteBreakDuty():
        userDict = getAuth()

        data = request.json
        fName, lName = data["raName"].split()
        hallId = userDict["hall_id"]
        dateStr = data["dateStr"]

        if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
            logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
            return jsonify(stdRet(-1,"NOT AUTHORIZED"))

        logging.debug("Deleted Break Duty RA Name: {}".format(fName + " " + lName))
        logging.debug("HallID: {}".format(hallId))
        # Expected as x-x-xxxx
        logging.debug("DateStr: {}".format(dateStr))

        cur = conn.cursor()

        cur.execute("SELECT id FROM ra WHERE first_name LIKE '{}' AND last_name LIKE '{}' AND hall_id = {};".format(fName,lName,userDict["hall_id"]))
        raId = cur.fetchone()

        cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE('{}', 'MM/DD/YYYY');".format(data["dateStr"]))
        dayID, monthId = cur.fetchone()

        if raId is not None and dayID is not None and monthId is not None:
            cur.execute("""DELETE FROM break_duties
                            WHERE ra_id = {}
                            AND hall_id = {}
                            AND day_id = {}
                            AND month_id = {}""".format(raId[0], hallId, dayID, monthId))

            conn.commit()

            cur.close()

            logging.info("Successfully deleted duty")
            return jsonify(stdRet(1,"successful"))

        else:

            cur.close()

            logging.info("Unable to locate beak duty to delete: RA {}, Date {}".format(fName + " " + lName, dateStr))
            return jsonify({"status":0,"error":"Unable to find parameters in DB"})

#     -- Error Handling --

@app.route("/error/<string:msg>")
def err(msg):
    logging.info("Rendering error page")
    return render_template("error.html", errorMsg=msg)

if __name__ == "__main__":

    local = os.environ["USE_ADHOC"]
    if local:
        logging.basicConfig(format='%(asctime)s.%(msecs)d %(levelname)s: %(message)s', \
                            datefmt='%H:%M:%S', \
                            level=logLevel, \
                            #filename="scheduleServer_DEBUG.log", \
                            #filemode="w"
                            )

        app.run(ssl_context="adhoc", debug=True)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logLevel)
        app.run()
