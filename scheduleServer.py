from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
from flask_dance.contrib.google import make_google_blueprint, google
from flask_bootstrap import Bootstrap
from scheduler import scheduling
from ra_sched import RA
import datetime
import psycopg2
import calendar
import os

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
Bootstrap(app)
# Setup for flask_dance with oauth
app.secret_key = os.environ["SECRET_KEY"]
blueprint = make_google_blueprint(
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    scope=["profile", "email"]
)
app.register_blueprint(blueprint, url_prefix="/login")

conn = psycopg2.connect(os.environ["DATABASE_URL"])
# Format date and time information for calendar
ct = datetime.datetime.now()
fDict = {"text_month":calendar.month_name[(ct.month+2)%12], "num_month":(ct.month+2)%12, "year":(ct.year if ct.month <= 12 else ct.year+1)}
cDict = {"text_month":calendar.month_name[ct.month], "num_month":ct.month, "year":ct.year}
cc = calendar.Calendar(6) #format calendar so Sunday starts the week

#     -- Helper Functions --

def getAuth():
    if not google.authorized:                                                   # If the user is not authorized by Google
        return redirect(url_for("google.login"))                                # Then redirect the user to the login page
    resp = google.get("/oauth2/v2/userinfo")
    try:
        assert resp.ok, resp.text                                               # Make sure that the login is valid (This might only be needed on the index)
    except AssertionError:                                                      # If the login is not valid
        return redirect(url_for("google.login"))                                # Then redirect the user to the login page

    jsonResp = resp.json()
    uEmail = jsonResp["email"]                                                  # The email returned from Google
    cur = conn.cursor()
    cur.execute("SELECT ra_id, auth_level FROM users WHERE email = '{}';".format(uEmail))
    res = cur.fetchone()                                                        # Get user info from the database

    if res == None:                                                             # If user does not exist, go to error url
        return redirect(url_for(".err",msg="No user found with email: {}".format(uEmail)))

    return {"uEmail":uEmail,"ra_id":res[0],"auth_level":res[1]}

#     -- Views --

@app.route("/")
def index():
    userDict = getAuth()                                                        # Get the user's info from our database
    if type(userDict) != dict:                                                  # If the result is not a dictionary
        return userDict                                                         # Then it should be a redirect to either an error page or Google for login

    resp = make_response(render_template("index.html",calDict=cDict,auth_level=userDict["auth_level"],
                                         cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"])))

    resp.set_cookie("ra_email",userDict["uEmail"])                               # Set cookie for use on other pages
    return resp

@app.route("/conflicts")
def conflicts():
    cur = conn.cursor()
    cur2 = conn.cursor()
    cur.execute("SELECT id, first_name, last_name FROM ra WHERE hall_id = 1 ORDER BY last_name ASC;")
    cur2.execute("SELECT id, name FROM res_hall;")
    return render_template("conflicts.html", calDict=fDict, auth_level=1, hall_list=cur2.fetchall(), \
                            cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]), ras=cur.fetchall())

@app.route("/editSched")
def editSched():
    cur = conn.cursor()
    cur.execute("SELECT id, first_name, last_name, points FROM ra WHERE hall_id = 1 ORDER BY points DESC;")
    return render_template("editSched.html", calDict=cDict, raList=cur.fetchall(), auth_level=3, \
                            cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]))

@app.route("/staff")
def manStaff():
    return render_template("staff.html")

#     -- Functional --

@app.route("/enterConflicts/", methods=['POST'])
def processConflicts():
    print("HELLO")
    ra_id = 1
    hallId = 3
    month = 6
    year = 2017
    insert_cur = conn.cursor()

    dateList = []
    for key in request.form:
        if "d" in key:
            dateList.append(key.split("d")[-1])

    for d in dateList:

        insert_cur.execute("INSERT INTO conflicts (ra_id, day_id) VALUES ({},{});"\
                            .format(ra_id,d))

    conn.commit()

    print("DONE")
    return index()

@app.route("/runIt/")
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

    conn.commit()

#     -- api --

@app.route("/api/testAPI", methods=["GET"])
def testAPI():
    cookie = request.cookies.get("username")
    print(request.cookies)
    print(cookie)
    for v in request.args:
        print(v)


    year = 2018
    month = 5
    ra_list = [RA("Ryan","E",1,1,datetime.date(2017,8,22),[datetime.date(year,month,1),datetime.date(year,month,10),datetime.date(year,month,11)]),
               RA("Sarah","L",1,2,datetime.date(2017,8,22),[datetime.date(year,month,2),datetime.date(year,month,12),datetime.date(year,month,22)]),
               RA("Steve","B",1,3,datetime.date(2017,8,22),[datetime.date(year,month,3),datetime.date(year,month,13),datetime.date(year,month,30)]),
               RA("Tyler","C",1,4,datetime.date(2017,8,22),[datetime.date(year,month,4),datetime.date(year,month,14)]),
               RA("Casey","K",1,5,datetime.date(2017,8,22),[datetime.date(year,month,5)])]

    s2 = scheduling(ra_list,year,month,[datetime.date(year,month,14),datetime.date(year,month,15),datetime.date(year,month,16),datetime.date(year,month,17)])

    return jsonify(s2)

@app.route("/api/getSchedule", methods=["GET"])
def getSchedule(monthNum=None,year=None,hallId=None):
    # API Hook that will get the requested schedule for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  The server will then query the database for the appropriate schedule
    #  and send back a jsonified version of the schedule. If no month and
    #  subsequently no schedule is found in the database, the server will
    #  return a blank calendar for that month.

    def missingInfo(year,monthNum):
        # This function generates a blank calendar to return to the client for
        #  the given year and monthNum (1-12)
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

    if monthNum == None and year == None and hallId == None:                    # Effectively: If API was called from the client and not from the server
        monthNum = int(request.args.get("monthNum"))
        year = int(request.args.get("year"))
        hallId = 1  # Default to Brandt until login is done.
    res = {}

    cur = conn.cursor()
    # Get the id, number and name for the month in question
    cur.execute("SELECT id, num, name FROM month WHERE num = {} AND year = to_date('{}','YYYY')".format(monthNum,year))
    m = cur.fetchone()

    if m == None:
        # If there is not a month matching the criteria, then a blank calendar
        #  will be generated and returned.
        return missingInfo(year,monthNum)

    cur.execute("SELECT id FROM schedule WHERE hall_id = {} AND month_id = {} ORDER BY created DESC;".format(hallId,m[0]))
    s = cur.fetchone()

    if s == None:
        # If there is not a schedule matching the criteria, then a blank calendar
        #  will be generated and returned.
        return missingInfo(year,monthNum)

    res["month"] = m[2]                                                         # Set the month name

    cur.execute("""SELECT ra.first_name, ra.last_name, ra.color, day.date, ra.id
                   FROM duties JOIN day ON (day.id=duties.day_id) JOIN ra ON (ra.id=duties.ra_id)
                   WHERE duties.hall_id = {} AND duties.sched_id = {}
                   ORDER BY day.date ASC;""".format(hallId,s[0]))                    # Get the duty schedule
    # hall_id is Brandt until login is made --------^

    date_res = cur.fetchall()
    prev_month_days = (calendar.weekday(year,monthNum,1)+1)%7
    # The line above determines the number of days at the beginning of the month that
    # belong to the previous month. Essentially, it maps the days of the week so that
    # Sunday is 0 and Saturday is 6. For example, if the expression returns 2, then
    # that means that the month in question starts on Tuesday.

    datesLst = []                                                               # This list will contain lists that represent each week in the month

    prev_month_dates = []                                                       # This list contains the days on the calendar that belong to the previous month
    for i in range(prev_month_days):
        prev_month_dates.append({"date":0,"ras":[]})

    week_lst = prev_month_dates
    prev_date = None
    prev_entry = None
    for d in date_res:                                                          # For each day in the duty schedule

        if len(week_lst) == 7:                                                  # If the length of the week is 7 days
            datesLst.append(week_lst)                                           # Start working on a new week
            week_lst = []

        if d[3] == prev_date:                                                   # If another RA was already assigned to the date
            prev_entry["ras"].append({"name":d[0]+" "+d[1][0]+".",              # Then we only need to add this RA to the last entry
                                        "bgColor":d[2],
                                        "bdColor":"#"+hex(int('0x'+d[2][1:],16)-0x2c2540)[2:], # Converting a str of a hex number to an int, subtracting a value, then converting to str of hex
                                        "id":d[4]})
        else:
            week_lst.append({"date":d[3].day,"ras":[{"name":d[0]+" "+d[1][0]+".", # Else create a new date dictionary and add the appropriate information
                                                     "bgColor":d[2],
                                                     "bdColor":"#"+hex(int('0x'+d[2][1:],16)-0x2c2540)[2:], # Converting a str of a hex number to an int, subtracting a value, then converting to str of hex
                                                     "id":d[4]}]})
            prev_entry = week_lst[-1]                                           # Keep track of the last entry made

        prev_date = d[3]                                                        # Update prev_date for the next duty assignment

    while len(week_lst) < 7:                                                    # Add any days that belong to the next month
        week_lst.append({"date":0,"ras":[]})

    datesLst.append(week_lst)                                                   # Add the week to the dateLst
    res["dates"] = datesLst                                                     # Add the dateLst to the result dict


    return jsonify(res)

@app.route("/api/runScheduler", methods=["GET"])
def runScheduler(hallId, month, year):
    # API Hook that will run the scheduler for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  Additionally, the dates that should no have duties are also sent via
    #  request.args and can either be a string of comma separated integers
    #  ("1,2,3,4") or an empty string ("").
    try:                                                                        # Try to get the proper information from the request
        year = int(request.args["year"])
        month = int(request.args["monthNum"])
        noDutyList = request.args["noDuty"].split(",")
    except:                                                                     # If error, send back an error message
        return jsonify("ERROR")
    hallId = 1  # Default to Brandt until login is finished

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

    sched = scheduling(raList,year,month,noDutyDates=noDutyList)                # Run the scheduler
    cur.execute("INSERT INTO schedule (hall_id,month_id,created) VALUES ({},{},NOW());".format(hallId,monthId))
    conn.commit()                                                               # Add the schedule to the database
    cur.execute("SELECT id FROM schedule WHERE hall_id = {} AND month_id = {} ORDER BY created DESC;".format(hallId,monthId))
    schedId = cur.fetchone()[0]                                                 # Get the id of the schedule that was just created

    days = {}                                                                   # Dictionary mapping the day id to the date
    cur.execute("SELECT id, date FROM day WHERE month_id = {};".format(monthId))
    for res in cur.fetchall():
        days[res[1]] = res[0]                                                   # Populate dictionary with results from the database

    for d in sched:                                                             # Iterate through the schedule
        if d.numberOnDuty() > 0:                                                # If there are RAs assigned to this day
            for r in d:
                cur.execute("""
                    INSERT INTO duties (hall_id,ra_id,day_id,sched_id) VALUES ({},{},{},{});
                    """.format(hallId,r.getId(),days[d.getDate()],schedId))     # Add the assigned duty to the database
        else:
            cur.execute("""
                INSERT INTO duties (hall_id,day_id,sched_id) VALUES ({},{},{});
                """.format(hallId,days[d.getDate()],schedId))                   # Add the unassigned duty to the database (These should be the dates in the noDutyList)

    conn.commit()                                                               # Commit additions to the database

    resp = {}                                                                   # Begin to create the JSON response to the client
    res["schedule"] = getSchedule(month,year,hallId)                            # Get the formatted schedule from the database
    res["raStats"] = None

    return resp

#     -- Error Handling --

@app.route("/error/<string:msg>")
def err(msg):
    return render_template("error.html", errorMsg=msg)

if __name__ == "__main__":
    app.run(debug=True)
