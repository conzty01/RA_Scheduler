from flask import render_template, request, jsonify, Blueprint
from flask_login import login_required
from ra_sched import RA
import scheduler4_0
import copy as cp
import psycopg2
import logging
import calendar

# Import the appGlobals for this blueprint to use
import appGlobals as ag

# Import the needed functions from other parts of the application
from helperFunctions.helperFunctions import getAuth, stdRet, getCurSchoolYear, getSchoolYear
from staff.staff import getRAStats

schedule_bp = Blueprint("schedule_bp", __name__,
                        template_folder="templates",
                        static_folder="static")

# ---------------------
# --      Views      --
# ---------------------

@schedule_bp.route("/editSched")
@login_required
def editSched():
    # The landing page for this blueprint that will display the Hall Settings
    #  to the user and provide a way for them to edit said settings.
    #
    #  Required Auth Level: >= AHD

    # Authenticate the user against the DB
    userDict = getAuth()

    # If the user is not at least an AHD
    if userDict["auth_level"] < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Get the information for the current school year.
    #  This will be used to calculate duty points for the RAs.
    start, end = getCurSchoolYear()

    # Call getRAStats to get information on the number of Duty
    # points each RA has for the current school year
    ptDict = getRAStats(userDict["hall_id"], start, end)

    logging.debug("Point Dict: {}".format(ptDict))

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for a list of all of the RAs and their information for the user's staff.
    cur.execute("SELECT id, first_name, last_name, color FROM ra WHERE hall_id = %s ORDER BY first_name ASC;",
                (userDict["hall_id"],))

    # Sort alphabetically by last name of RA
    ptDictSorted = sorted(ptDict.items(), key=lambda kv: kv[1]["name"].split(" ")[1])

    return render_template("schedule/editSched.html", raList=cur.fetchall(), auth_level=userDict["auth_level"],
                           ptDict=ptDictSorted, curView=3, opts=ag.baseOpts, hall_name=userDict["hall_name"])


# ---------------------
# --   API Methods   --
# ---------------------

@schedule_bp.route("/api/getSchedule", methods=["GET"])
@login_required
def getSchedule2(start=None,end=None,hallId=None, showAllColors=None):
    # API Hook that will get the requested schedule for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  The server will then query the database for the appropriate schedule
    #  and send back a jsonified version of the schedule. If no month and
    #  subsequently no schedule is found in the database, the server will
    #  return an empty list

    fromServer = True
    if start is None and end is None and hallId is None and showAllColors is None:                    # Effectively: If API was called from the client and not from the server
        start = request.args.get("start").split("T")[0]                         # No need for the timezone in our current application
        end = request.args.get("end").split("T")[0]                             # No need for the timezone in our current application

        showAllColors = request.args.get("allColors") == "true"                 # Should all colors be displayed or only the current user's colors

        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False

    logging.debug("Get Schedule - From Server: {}".format(fromServer))
    res = []

    cur = ag.conn.cursor()

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
        # logging.debug("Ra is same as user? {}".format(userDict["ra_id"] == row[3]))
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
            "extendedProps": {"dutyType": "std"}
        })

    if fromServer:
        return res
    else:
        return jsonify(res)

@schedule_bp.route("/api/runScheduler", methods=["POST"])
def runScheduler(hallId=None, monthNum=None, year=None):

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
    cur = ag.conn.cursor()

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
    #  RAs by 2 then adding 1. For example, with a staff_manager of 15, the LDA Tolerance
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

                logging.info("DECREASE LDAT: {}".format(ldat))
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
    ag.conn.commit()
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
        ag.conn.rollback()

    ag.conn.commit()

    cur.close()

    logging.info("Successfully Generated Schedule: {}".format(schedId))

    if fromServer:
        return stdRet(1,"successful")
    else:
        return jsonify(stdRet(1,"successful"))

@schedule_bp.route("/api/changeRAonDuty", methods=["POST"])
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

    cur = ag.conn.cursor()

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

        ag.conn.commit()

        cur.close()

        ret = stdRet(1,"successful")
        # ret["pointDict"] = getRAStats(userDict["hall_id"], start, end)

        return jsonify(ret)

    else:
        # Something is not in the DB

        cur.close()

        return jsonify(stdRet(0,"Unable to find parameters in DB"))

@schedule_bp.route("/api/addNewDuty", methods=["POST"])
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

    cur = ag.conn.cursor()

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

    ag.conn.commit()

    cur.close()

    logging.debug("Successfully added new duty")
    return jsonify(stdRet(1,"successful"))

@schedule_bp.route("/api/deleteDuty", methods=["POST"])
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

    cur = ag.conn.cursor()

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

        ag.conn.commit()

        cur.close()

        logging.info("Successfully deleted duty")
        return jsonify(stdRet(1,"successful"))

    else:

        cur.close()

        logging.info("Unable to locate duty to delete")
        return jsonify({"status":0,"error":"Unable to find parameters in DB"})
