from flask_login import UserMixin, current_user, LoginManager, login_required, login_user, logout_user
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask.wrappers import Response
from scheduler import scheduling
from ra_sched import RA
import scheduler3_0
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
            SELECT ra.id, username, first_name, last_name, hall_id, auth_level
            FROM "user" JOIN ra ON ("user".ra_id = ra.id)
            WHERE username = '{}';""".format(uEmail))
    res = cur.fetchone()                                                        # Get user info from the database

    if res == None:                                                             # If user does not exist, go to error url
        cur.close()
        return redirect(url_for(".err",msg="No user found with email: {}".format(uEmail)))

    cur.close()
    return {"uEmail":uEmail,"ra_id":res[0],"name":res[2]+" "+res[3],
            "hall_id":res[4],"auth_level":res[5]}

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
    return render_template("index.html",calDict=cDict,auth_level=userDict["auth_level"], \
                            cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]))

@app.route("/conflicts")
def conflicts():
    userDict = getAuth()                                                        # Get the user's info from our database

    # If current month is December, update the year
    #  to display the proper month
    if fDict["num_month"] == 12:
        year = fDict["year"] + 1
    else:
        year = fDict["year"]

    return render_template("conflicts.html", calDict=fDict, auth_level=userDict["auth_level"], \
                            cal=cc.monthdays2calendar(year,fDict["num_month"]))

@app.route("/editSched")
@login_required
def editSched():
    userDict = getAuth()                                                        # Get the user's info from our database
    cur = conn.cursor()
    cur.execute("SELECT id, first_name, last_name, points, color FROM ra WHERE hall_id = {} ORDER BY last_name, first_name ASC;".format(userDict["hall_id"]))
    return render_template("editSched.html", calDict=cDict, raList=cur.fetchall(), auth_level=userDict["auth_level"], \
                            cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]))

@app.route("/staff")
@login_required
def manStaff():
    userDict = getAuth()                                                        # Get the user's info from our database
    cur = conn.cursor()
    cur.execute("SELECT ra.id, first_name, last_name, email, date_started, res_hall.name, points, color, auth_level \
     FROM ra JOIN res_hall ON (ra.hall_id = res_hall.id) \
     WHERE hall_id = {} ORDER BY ra.id ASC;".format(userDict["hall_id"]))
    return render_template("staff.html",raList=cur.fetchall(),auth_level=userDict["auth_level"])

#     -- Functional --

@app.route("/api/enterConflicts/", methods=['POST'])
@login_required
def processConflicts():
    userDict = getAuth()                                                        # Get the user's info from our database

    ra_id = userDict["ra_id"]
    hallId = userDict["hall_id"]

    print(request.json)
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

@app.route("/runIt/")
@login_required
def popDuties():
    cur = conn.cursor()
    cur.execute("SELECT year FROM month ORDER BY year DESC;")
    d = cur.fetchone()[0]
    year = d.year
    month = 5

    cur.execute("""SELECT first_name, last_name, id, hall_id,date_started, cons.array_agg, points FROM ra JOIN (SELECT ra_id, ARRAY_AGG(days.date) FROM conflicts JOIN (SELECT id, date FROM day WHERE month_id = 4) AS days ON (conflicts.day_id = days.id) GROUP BY ra_id) AS cons ON (ra.id = cons.ra_id) WHERE ra.hall_id = 1;""")

    raList = [RA(res[0],res[1],res[2],res[3],res[4],res[5],res[6]) for res in cur.fetchall()]
    noDutyList = [24,25,26,27,28,29,30,31]

    sched = scheduling(raList,year,month,noDutyDates=noDutyList)

    days = {}
    cur.execute("SELECT id, date FROM day WHERE month_id = 4;")
    for res in cur.fetchall():
        print(str(res[1]))
        days[str(res[1])] = res[0]

    print(days)

    for d in sched:
        if d.numberOnDuty() > 0:
            for r in d:
                h = hash(str(d.getDate()))
                cur.execute("""
                    INSERT INTO duties (hall_id,ra_id,day_id,sched_id) VALUES (1,{},{},2);
                    """.format(r.getId(),days[str(d.getDate())]))
        else:
            cur.execute("""
                INSERT INTO duties (hall_id,day_id,sched_id) VALUES (1,{},2);
                """.format(days[str(d.getDate())]))

    cur.close()
    conn.commit()

#     -- api --

@app.route("/api/testAPI", methods=["GET"])
def testAPI():
    #runScheduler3(1,12,2020)

    return jsonify([1])

@app.route("/api/getStats", methods=["GET"])
@login_required
def getRAStats(hallId=None):
    # API Hook that will get the RA stats for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  The server will then query the database for the appropriate statistics
    #  and send back a json object.

    fromServer = True
    if hallId == None:                                                          # Effectively: If API was called from the client and not from the server
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False
    res = []

    cur = conn.cursor()
    cur.execute("SELECT id, first_name, last_name FROM ra WHERE hall_id = {} ORDER BY last_name ASC;".format(hallId))
    raList = cur.fetchall()

    for ra in raList:                                                           # Append ras and their info to RAList
        cur.execute("SELECT SUM(point_val) FROM duties WHERE ra_id = {}".format(ra[0]))
        pts = cur.fetchone()
        if type(pts) == type(None):
            pts = (0,)
        res.append({"id":ra[0],"name":ra[1]+" "+ra[2],"pts":pts[0]})

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
                ORDER BY schedule.month_id, schedule.created DESC
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

@app.route("/api/runScheduler", methods=["GET"])
def runScheduler3(hallId=None, monthNum=None, year=None):
    # TODO: Add ability to query double dates and no duty days from arg values

    # API Hook that will run the scheduler for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  Additionally, the dates that should no have duties are also sent via
    #  request.args and can either be a string of comma separated integers
    #  ("1,2,3,4") or an empty string ("").
    #print("SCHEDULER")
    userDict = getAuth()                                                        # Get the user's info from our database
    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify("NOT AUTHORIZED")

    fromServer = True
    if monthNum == None and year == None and hallId == None:                    # Effectively: If API was called from the client and not from the server
        monthNum = int(request.args.get("monthNum"))
        year = int(request.args.get("year"))
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False
    res = {}

    try:                                                                        # Try to get the proper information from the request
        year = int(request.args["year"])
        month = int(request.args["monthNum"])+1
        if request.args["noDuty"] != "":
            noDutyList = [int(d) for d in request.args["noDuty"].split(",")]
        else:
            noDutyList = []

    except:                                                                     # If error, send back an error message
        return jsonify("ERROR")

    hallId = userDict["hall_id"]
    cur = conn.cursor()

    cur.execute("SELECT id FROM month WHERE num = {} AND EXTRACT(YEAR FROM year) = {}".format(month,year))
    monthId = cur.fetchone()[0]                                                 # Get the month_id from the database
    print(monthId)

    if monthId == None:                                                         # If the database does not have the correct month
        return jsonify("ERROR")                                                 # Send back an error message

    # Select all RAs in a particular hall whose auth_level is below 3 (HD)
    #  as well as all of their respective conflicts for a given month
    queryStr = """
        SELECT first_name, last_name, id, hall_id, date_started,
               COALESCE(cons.array_agg, ARRAY[]::date[]), points
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
        WHERE ra.hall_id = {} AND
              ra.auth_level < 3;
    """.format(monthId, hallId)

    cur.execute(queryStr)       # Query the database for the appropriate RAs and their respective information

    ra_list = [RA(res[0],res[1],res[2],res[3],res[4],res[5],res[6]) for res in cur.fetchall()]

    # Create the Schedule
    sched = scheduler3_0.schedule(ra_list,year,month,noDutyDates=noDutyList)
    #print(sched)

    if len(sched) == 0:
        return jsonify("UNABLE TO GENERATE SCHEDULE")

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
    for d in sched:
        # If there are RAs assigned to this day
        if d.numberOnDuty() > 0:
            for r in d:
                try:
                    cur.execute("""
                        INSERT INTO duties (hall_id,ra_id,day_id,sched_id) VALUES ({},{},{},{});
                        """.format(hallId,r.getId(),days[d.getDate()],schedId)) # Add the assigned duty to the database
                    cur.execute("UPDATE ra SET points = points + {} WHERE id = {};".format(d.getPoints(),r.getId()))
                    conn.commit()
                except psycopg2.IntegrityError:
                    #print("ROLLBACK")
                    conn.rollback()
        else:
            try:
                cur.execute("""
                    INSERT INTO duties (hall_id,day_id,sched_id) VALUES ({},{},{});
                    """.format(hallId,days[d.getDate()],schedId))               # Add the unassigned duty to the database (These should be the dates in the noDutyList)
                conn.commit()                                                   # Commit additions to the database
            except psycopg2.IntegrityError:
                #print("ROLLBACK")
                conn.rollback()

    conn.commit()

    ret = {"schedule":getSchedule(month,year,hallId),"raStats":getRAStats(hallId)}
    #ret = 1
    #print(ret)
    cur.close()

    if fromServer:
        return ret
    else:
        return jsonify(ret)


@app.route("/api/runScheduler_old", methods=["GET"])
@login_required
def runScheduler(hallId=None, monthNum=None, year=None):
    # API Hook that will run the scheduler for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  Additionally, the dates that should no have duties are also sent via
    #  request.args and can either be a string of comma separated integers
    #  ("1,2,3,4") or an empty string ("").
    userDict = getAuth()                                                        # Get the user's info from our database
    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify("NOT AUTHORIZED")

    fromServer = True
    if monthNum == None and year == None and hallId == None:                    # Effectively: If API was called from the client and not from the server
        monthNum = int(request.args.get("monthNum"))
        year = int(request.args.get("year"))
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False
    res = {}

    try:                                                                        # Try to get the proper information from the request
        year = int(request.args["year"])
        month = int(request.args["monthNum"])+1
        noDutyList = request.args["noDuty"].split(",")
    except:                                                                     # If error, send back an error message
        return jsonify("ERROR")

    hallId = userDict["hall_id"]
    cur = conn.cursor()

    cur.execute("SELECT id FROM month WHERE num = {} AND year = TO_DATE('{}','YYYY')".format(month,year))
    monthId = cur.fetchone()[0]                                                 # Get the month_id from the database

    if monthId == None:                                                         # If the database does not have the correct month
        return jsonify("ERROR")                                                 # Send back an error message

    cur.execute("""SELECT first_name, last_name, id, hall_id,
                          date_started, cons.array_agg, points
                   FROM ra JOIN (SELECT ra_id, ARRAY_AGG(days.date)
                                 FROM conflicts JOIN (SELECT id, date FROM day
                                                      WHERE month_id = {}) AS days
                                 ON (conflicts.day_id = days.id)
                                 GROUP BY ra_id) AS cons
                            ON (ra.id = cons.ra_id)
                    WHERE ra.hall_id = {};""".format(monthId,hallId))           # Query the database for the appropriate RAs and their respective information

    ra_list = [RA(res[0],res[1],res[2],res[3],res[4],res[5],res[6]) for res in cur.fetchall()]
    # The above line creates a list of RA objects reflecting the RAs for the appropriate hall

    sched = scheduling(ra_list,year,month,noDutyDates=noDutyList)               # Run the scheduler
    cur.execute("INSERT INTO schedule (hall_id,month_id,created) VALUES ({},{},NOW());".format(hallId,monthId))
    conn.commit()                                                               # Add the schedule to the database
    cur.execute("SELECT id FROM schedule WHERE hall_id = {} AND month_id = {} ORDER BY created DESC, id DESC;".format(hallId,monthId))
    schedId = cur.fetchone()[0]                                                 # Get the id of the schedule that was just created

    days = {}                                                                   # Dictionary mapping the day id to the date
    cur.execute("SELECT id, date FROM day WHERE month_id = {};".format(monthId))
    for res in cur.fetchall():
        days[res[1]] = res[0]                                                   # Populate dictionary with results from the database

    for d in sched:                                                             # Iterate through the schedule
        if d.numberOnDuty() > 0:                                                # If there are RAs assigned to this day
            for r in d:
                try:
                    cur.execute("""
                        INSERT INTO duties (hall_id,ra_id,day_id,sched_id) VALUES ({},{},{},{});
                        """.format(hallId,r.getId(),days[d.getDate()],schedId)) # Add the assigned duty to the database
                    cur.execute("UPDATE ra SET points = points + {} WHERE id = {};".format(d.getPoints(),r.getId()))
                    conn.commit()
                except psycopg2.IntegrityError:
                    conn.rollback()
        else:
            try:
                cur.execute("""
                    INSERT INTO duties (hall_id,day_id,sched_id) VALUES ({},{},{});
                    """.format(hallId,days[d.getDate()],schedId))               # Add the unassigned duty to the database (These should be the dates in the noDutyList)
                conn.commit()                                                   # Commit additions to the database
            except psycopg2.IntegrityError:
                conn.rollback()

    conn.commit()

    ret = {"schedule":getSchedule(month,year,hallId),"raStats":getRAStats(hallId)}
    cur.close()
    if fromServer:
        return ret
    else:
        return jsonify(ret)

@app.route("/api/getEditInfo", methods=["GET"])
@login_required
def getEditInfo(hallId=None, monthNum=None, year=None):
    # API Hook that will get a the list of RAs along with their conflicts for a.
    #  given month. The month will be given via request.args as 'monthNum' and
    #  'year'. The server will then query the database for the conflicts and
    #  and return them along with a list of the RAs

    userDict = getAuth()                                                        # Get the user's info from our database
    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify("NOT AUTHORIZED")

    fromServer = True
    if monthNum == None and year == None and hallId == None:                    # Effectively: If API was called from the client and not from the server
        monthNum = int(request.args.get("monthNum")) + 1
        year = int(request.args.get("year"))
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False
    res = []
    cur = conn.cursor()

    print(monthNum,year)

    cur.execute("SELECT id FROM month WHERE num = {} AND year = TO_DATE('{}','YYYY')".format(monthNum,year))
    monthId = cur.fetchone()[0]

    cur.execute("SELECT id, first_name, last_name, points FROM ra WHERE hall_id = {};".format(hallId))
    ra_list = cur.fetchall()

    for raRes in ra_list:
        raDict = {"id":raRes[0],"name":raRes[1]+" "+raRes[2][0]+".","points":raRes[3]}
        cur.execute("""SELECT day.date
                       FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                                      JOIN month ON (day.month_id = month.id)
                       WHERE day.month_id = {} AND conflicts.ra_id = {};""".format(monthId,raRes[0]))

        conList = cur.fetchall()
        c = []
        for con in conList:
            c.append(con[0])

        raDict["conflicts"] = c                                                 # Add conflicts to the RA Dict
        res.append(raDict)                                                      # Append RA Dict to results list

    if fromServer:
        return res
    else:
        return jsonify(res)

@app.route("/api/changeStaffInfo", methods=["POST"])
@login_required
def changeStaffInfo():
    userDict = getAuth()                                                        # Get the user's info from our database

    hallId = userDict["hall_id"]

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify("NOT AUTHORIZED")

    data = request.json

    cur = conn.cursor()
    cur.execute("""UPDATE ra
                   SET first_name = '{}', last_name = '{}', hall_id = {},
                       date_started = TO_DATE('{}', 'YYYY-MM-DD'),
                       points = {}, color = '{}', email = '{}', auth_level = {}
                   WHERE id = {};
                """.format(data["fName"],data["lName"],hallId, \
                        data["startDate"],data["points"],data["color"], \
                        data["email"],data["authLevel"], data["raID"]))

    conn.commit()
    cur.close()
    return data["raID"]

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
    INSERT INTO ra (first_name,last_name,hall_id,date_started,points,color,email,auth_level)
    VALUES ('{}','{}',{},NOW(),0,'{}','{}','{}')
    RETURNING id;
    """.format(data["fName"],data["lName"],userDict["hall_id"],data["color"], \
                data["email"],data["authLevel"]))

    conn.commit()
    newId = cur.fetchone()[0]

    cur.execute("""SELECT ra.id, first_name, last_name, email, date_started, res_hall.name, points, color, auth_level
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
        return jsonify("NOT AUTHORIZED")

    data = request.json
    print("New RA id:", data["newId"])
    print("Old RA Name:", data["oldName"])
    print("HallID: ", userDict["hall_id"])
    # Expected as x/x/xxxx
    print("DateStr: ", data["dateStr"])

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

    cur.execute("SELECT id FROM schedule WHERE hall_id = {} AND month_id = {} ORDER BY created DESC;".format(userDict["hall_id"],monthId))
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

        return jsonify({"id":raParams[0],"name":raParams[1]+" "+raParams[2],"color":raParams[3],"dateStr":data["dateStr"]})

    else:
        # Something is not in the DB

        cur.close()

        return jsonify({"error":"Unable to find parameters in DB"})


@app.route("/api/addNewDuty", methods=["POST"])
@login_required
def addNewDuty():
    userDict = getAuth()

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        return jsonify("NOT AUTHORIZED")

    data = request.json

    print("New RA id:", data["id"])
    print("HallID: ", userDict["hall_id"])
    # Expected as x-x-xxxx
    print("DateStr: ", data["dateStr"])

    cur = conn.cursor()

    cur.execute("SELECT id, first_name, last_name, color FROM ra WHERE id = {} AND hall_id = {};".format(data["id"],userDict["hall_id"]))
    raParams = cur.fetchone()

    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE('{}', 'YYYY-MM-DD');".format(data["dateStr"]))
    dayID, monthId = cur.fetchone()

    cur.execute("SELECT id FROM schedule WHERE hall_id = {} AND month_id = {} ORDER BY created DESC;".format(userDict["hall_id"],monthId))
    schedId = cur.fetchone()

    if raParams is not None and dayID is not None and schedId is not None:
        cur.execute("""INSERT INTO duties (hall_id, ra_id, day_id, sched_id)
                        VALUES ({}, {}, {}, {});""".format(userDict["hall_id"], raParams[0], dayID, schedId[0]))

        conn.commit()

        cur.close()

        return jsonify({"id":raParams[0],"name":raParams[1]+" "+raParams[2],"color":raParams[3],"dateStr":data["dateStr"]})

    else:
        # Something is not in the DB

        cur.close()

        return jsonify({"error":"Unable to find parameters in DB"})


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
