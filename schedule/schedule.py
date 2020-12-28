from flask import render_template, request, jsonify, Blueprint
from flask_login import login_required
from psycopg2 import IntegrityError
from schedule import scheduler4_0
from schedule.ra_sched import RA
import copy as cp
import calendar
import logging

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
def getSchedule2(start=None, end=None, hallId=None, showAllColors=None):
    # API Method used to return the regularly scheduled duties for the given hall
    #  and timeframe. This method also allows for specification on whether or not
    #  the returned duties should be associated with their RA's respective colors
    #  or a default color. Regardless of this value, any duties associated with
    #  the user are associated with their color.
    #
    #  Required Auth Level: None
    #
    #  If called from the server, this function accepts the following parameters:
    #
    #     start          <str>   -  a string representing the first day that should
    #                                be included for the returned RA conflicts.
    #     end            <str>   -  a string representing the last day that should
    #                                be included for the returned RA conflicts.
    #     hallId         <int>   -  an integer representing the id of the desired
    #                                residence hall in the res_hall table.
    #     showAllColors  <bool>  -  a boolean that, if set to True, will associate the
    #                                returned duties with their RA's respective color.
    #                                Setting this to False will associate each duty
    #                                with the default color of #2C3E50.
    #
    #  If called from a client, the following parameters are required:
    #
    #     start          <str>   -  a string representing the first day that should be included
    #                                for the returned RA conflicts.
    #     end            <str>   -  a string representing the last day that should be included
    #                                for the returned RA conflicts.
    #     showAllColors  <bool>  -  a boolean that, if set to True, will associate the
    #                                returned duties with their RA's respective color.
    #                                Setting this to False will associate each duty
    #                                with the default color of #2C3E50.
    #
    #  This method returns an object with the following specifications:
    #
    #     [
    #        {
    #           "id": <ra.id>,
    #           "title": <ra.first_name> + " " + <ra.last_name>,
    #           "start": <day.date>,
    #           "color": <ra.color or "#2C3E50">,
    #           "extendedProps": {"dutyType": "std"}
    #        }
    #     ]

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if start is None and end is None and hallId is None and showAllColors is None:
        # If the hallId, start, end, and showAllColors are None, then
        #  this method was called from a remote client.

        # Get the user's information from the database
        userDict = getAuth()

        # Set the value of hallId from the userDict
        hallId = userDict["hall_id"]

        # Get the start and end string values from the request arguments.
        #  Since we utilize the fullCal.js library, we know that the request
        #  also contains timezone information that we do not care about in
        #  this method. As a result, the timezone information is split out
        #  immediately.
        start = request.args.get("start").split("T")[0]
        end = request.args.get("end").split("T")[0]

        # Load the showAllColors from the request arguments
        showAllColors = request.args.get("allColors") == "true"

        # Mark that this method was not called from the server
        fromServer = False

    logging.debug("Get Schedule - From Server: {}".format(fromServer))

    # Create the result object to be returned
    res = []

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the regularly scheduled duties for the given Res Hall and timeframe.
    cur.execute("""
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD')
        FROM duties JOIN day ON (day.id=duties.day_id)
                    JOIN RA ON (ra.id=duties.ra_id)
        WHERE duties.hall_id = %s
        AND duties.sched_id IN
                (
                SELECT DISTINCT ON (schedule.month_id) schedule.id
                FROM schedule
                WHERE schedule.hall_id = %s
                AND schedule.month_id IN
                    (
                        SELECT month.id
                        FROM month
                        WHERE month.year >= TO_DATE(%s,'YYYY-MM')
                        AND month.year <= TO_DATE(%s,'YYYY-MM')
                    )
                ORDER BY schedule.month_id, schedule.created DESC, schedule.id DESC
                )
        AND day.date >= TO_DATE(%s,'YYYY-MM-DD')
        AND day.date <= TO_DATE(%s,'YYYY-MM-DD')
        ORDER BY day.date ASC;
    """, (hallId, hallId, start[:-3], end[:-3], start, end))

    # Load the results from the DB
    rawRes = cur.fetchall()
    logging.debug("RawRes: {}".format(rawRes))

    # Iterate through the rawRes from the DB and assemble the return result
    #  in the format outlined in the comments at the top of this method.
    for row in rawRes:
        # First check to see if the ra is the same as the user.
        #  If so, then display their color; otherwise, display a generic color.

        # logging.debug("Ra is same as user? {}".format(userDict["ra_id"] == row[3]))

        # If the desired behavior is to NOT show all of the unique RAs' colors...
        if not(showAllColors):

            # Then check to see if the current user is the RA on the duty being
            #  added. If this method was called from the server, then there is no
            #  concept of the current user and thus the default color should be used.

            if not fromServer and userDict["ra_id"] == row[3]:
                # If it is the RA, then show their unique color
                c = row[2]

            else:
                # If it is NOT the RA, then show the default color.
                c = "#2C3E50"

        else:
            # If the desired behavior is to show all of the unique RA colors, then
            #  simply set their respective color.
            c = row[2]

        # Append a newly created dictionary object containing the information for this
        #  duty to the return object.
        res.append({
            "id": row[3],
            "title": row[0] + " " + row[1],
            "start": row[4],
            "color": c,
            "extendedProps": {"dutyType": "std"}
        })

    # If this API method was called from the server
    if fromServer:
        # Then return the result as-is
        return res

    else:
        # Otherwise return a JSON version of the result
        return jsonify(res)


@schedule_bp.route("/api/runScheduler", methods=["POST"])
def runScheduler():
    # API Method that runs the duty scheduler for the given
    #  Res Hall and month. Any users associated with the staff
    #  that have an auth_level of HD will not be scheduled.
    #
    #  Required Auth Level: >= AHD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     monthNum     <int>  -  an integer representing the numeric month number for
    #                             the desired month using the standard gregorian
    #                             calendar convention.
    #     year         <int>  -  an integer denoting the year for the desired time period
    #                             using the standard gregorian calendar convention.
    #     noDuty       <str>  -  a string containing comma separated integers that represent
    #                             a date in the month in which no duty should be scheduled.
    #                             If set to an empty string, then all days in the month will
    #                             be scheduled.
    #     eligibleRAs  <str>  -  a string containing comma separated integers that represent
    #                             the ra.id for all RAs that should be considered for duties.
    #                             If set to an empty string, then all ras with an auth_level
    #                             of less than HD will be scheduled.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the duty scheduling was successful
    #      0 : the duty scheduling was unsuccessful
    #     -1 : an error occurred while scheduling

    # Get the user's information from the database
    userDict = getAuth()

    # Check to see if the user is authorized to run the scheduler
    # If the user is not at least an AHD
    if userDict["auth_level"] < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to run scheduler."
                     .format(userDict["ra_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    logging.debug("Request.json: {}".format(request.json))

    # Attempt to load the needed data from the request.json object
    try:
        # Set the values of the monthNum, and year with the
        #  data passed from the client.
        monthNum = int(request.json["monthNum"])
        year = int(request.json["year"])

        # Check to see if values have been passed through the
        #  noDuty parameter
        if request.json["noDuty"] != "":
            # If noDuty is not "", then attempt to parse out the values
            noDutyList = [int(d) for d in request.json["noDuty"].split(",")]

        else:
            # Otherwise if there are no values passed in noDuty, set
            #  noDutyList to an empty list
            noDutyList = []

        # Check to see if values have been passed through the
        #  eligibeRAs parameter
        if request.json["eligibleRAs"] != "":
            # If eligibleRAs is not "", then attempt to parse out the values
            eligibleRAs = [int(i) for i in request.json["eligibleRAs"]]

            # Also create a formatted psql string to add to the query that loads
            #  the necessary information from the DB
            eligibleRAStr = "AND ra.id IN ({});".format(str(eligibleRAs)[1:-1])

        else:
            # Otherwise if there are no values passed in eligibleRAs, then
            # set eligibleRAStr to ";" to end the query string
            eligibleRAStr = ";"

    except ValueError as ve:
        # If a ValueError occurs, then there was an issue parsing out the
        #  monthNum, year, noDuty-dates or the ra.ids from the request json.

        # Log the occurrence
        logging.warning("Error Parsing Request Values for Scheduler: {}"
                        .format(ve))

        # Notify the user of the error
        return jsonify(stdRet(-1, "Error Parsing Scheduler Parameters"))

    except KeyError as ke:
        # If a KeyError occurs, then there was an expected value in the
        #  request json that was missing.

        # Log the occurrence
        logging.warning("Error Loading Request Values for Scheduler: {}"
                        .format(ke))

        # Notify the user of the error
        return jsonify(stdRet(-1, "Missing Scheduler Parameters"))

    # Set the value of the hallId from the userDict
    hallId = userDict["hall_id"]

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the given month
    cur.execute("SELECT id, year FROM month WHERE num = %s AND EXTRACT(YEAR FROM year) = %s",
                (monthNum, year))

    # Load the results from the DB
    monthRes = cur.fetchone()

    # Check to see if the query returned a result
    if monthRes is None:
        # If not, then log the occurrence
        logging.warning("Unable to find month {}/{} in DB".format(monthNum, year))

        # And notify the user
        return jsonify(stdRet(-1, "Unable to find month {}/{} in DB".format(monthNum, year)))

    else:
        # Otherwise, unpack the monthRes into monthId and year
        monthId, date = monthRes

    logging.debug("MonthId: {}".format(monthId))

    # -- Get all eligible RAs and their conflicts --

    # Query the DB for all of the eligible RAs for a given hall, and their
    #  conflicts for the given month excluding any ra table records with
    #  an auth_level of 3 or higher.
    cur.execute("""
        SELECT first_name, last_name, id, hall_id, date_started,
               COALESCE(cons.array_agg, ARRAY[]::date[])
        FROM ra LEFT OUTER JOIN (
            SELECT ra_id, ARRAY_AGG(days.date)
            FROM conflicts JOIN (
                SELECT id, date
                FROM day
                WHERE month_id = %s
                ) AS days
            ON (conflicts.day_id = days.id)
            GROUP BY ra_id
            ) AS cons
        ON (ra.id = cons.ra_id)
        WHERE ra.hall_id = %s
        AND ra.auth_level < 3 {}
    """.format(eligibleRAStr), (monthId, hallId))

    # Load the result from the DB
    partialRAList = cur.fetchall()

    # Get the start and end date for the school year. This will be used
    #  to calculate how many points each RA has for the given year.
    start, end = getSchoolYear(date.month, date.year)

    # Get the number of days in the given month
    _, dateNum = calendar.monthrange(date.year, date.month)

    # Calculate and format maxBreakDay which is the latest break duty that should be
    #  included for the duty points calculation.
    maxBreadDuty = "{:04d}-{:02d}-{:02d}".format(date.year, date.month, dateNum)

    # Get the RA statistics for the given hall
    ptsDict = getRAStats(userDict["hall_id"], start, end, maxBreakDay=maxBreadDuty)

    logging.debug("ptsDict: {}".format(ptsDict))

    # Assemble the RA list with RA objects that have the individual RAs' information
    ra_list = [RA(res[0], res[1], res[2], res[3], res[4], res[5], ptsDict[res[2]]["pts"]) for res in partialRAList]

    # Set the Last Duty Assigned Tolerance based on floor dividing the number of
    #  RAs by 2 then adding 1. For example, with a staff_manager of 15, the LDA Tolerance
    #  would be 8 days.

    # Calculate the last date assigned tolerance (LDAT) which is the number of days
    #  before an RA is to be considered again for a duty. This should start as
    #  one more than half of the number of RAs in the list. The scheduler algorithm
    #  will adjust this as needed if the value passed in does not generate a schedule.
    ldat = (len(ra_list) // 2) + 1

    # Query the DB for the last 'x' number of duties from the previous month so that we
    #  do not schedule RAs back-to-back between months.

    # 'x' is currently defined to be the last day assigned tolerance

    # Create a startMonthStr that can be used as the earliest boundary for the duties from the
    #  last 'x' duties from the previous month.
    # If the monthNum is 1 (If the desired month is January)
    if monthNum == 1:
        # Then the previous month is 12 (December) of the previous year
        startMonthStr = '{}-12'.format(date.year - 1)

    else:
        # Otherwise the previous month is going to be from the same year
        startMonthStr = '{}-{}'.format(date.year, "{0:02d}".format(monthNum - 1))

    # Generate the endMonthStr which is simply a dateStr that represents the
    #  first day of the month in which the scheduler should run.
    endMonthStr = '{}-{}'.format(date.year, "{0:02d}".format(monthNum))

    # Log this information for the debugger!
    logging.debug("StartMonthStr: {}".format(startMonthStr))
    logging.debug("EndMonthStr: {}".format(endMonthStr))
    logging.debug("Hall Id: {}".format(userDict["hall_id"]))
    logging.debug("Year: {}".format(date.year))
    logging.debug('MonthNum: {0:02d}'.format(monthNum))
    logging.debug("LDAT: {}".format(ldat))

    # Query the DB for the last 'x' number of duties from the previous month so that we
    #  do not schedule RAs back-to-back between months.
    cur.execute("""SELECT ra.first_name, ra.last_name, ra.id, ra.hall_id,
                          ra.date_started, day.date - TO_DATE(%s, 'YYYY-MM-DD')
                  FROM duties JOIN day ON (day.id=duties.day_id)
                              JOIN ra ON (ra.id=duties.ra_id)
                  WHERE duties.hall_id = %s
                  AND duties.sched_id IN (
                        SELECT DISTINCT ON (schedule.month_id) schedule.id
                        FROM schedule
                        WHERE schedule.hall_id = %s
                        AND schedule.month_id IN (
                            SELECT month.id
                            FROM month
                            WHERE month.year >= TO_DATE(%s, 'YYYY-MM')
                            AND month.year <= TO_DATE(%s, 'YYYY-MM')
                        )
                        ORDER BY schedule.month_id, schedule.created DESC, schedule.id DESC
                  )
                  
                  AND day.date >= TO_DATE(%s,'YYYY-MM-DD') - %s
                  AND day.date <= TO_DATE(%s,'YYYY-MM-DD') - 1
                  ORDER BY day.date ASC;
    """, (endMonthStr + "-01", hallId, hallId, startMonthStr, endMonthStr,
          endMonthStr + "-01", ldat, endMonthStr + "-01"))

    # Load the query results from the DB
    prevDuties = cur.fetchall()

    # Create shell RA objects that will hash to the same value as their respective RA objects.
    #  This hash is how we map the equivalent RA objects together.
    prevRADuties = [(RA(d[0], d[1], d[2], d[3], d[4]), d[5]) for d in prevDuties]

    logging.debug("PREVIOUS DUTIES: {}".format(prevRADuties))

    # Query the DB for a list of break duties for the given month.
    #  In version 4.0 of the scheduler, break duties essentially are treated
    #  like noDutyDates and are skipped in the scheduling process. As a result,
    #  only the date is needed.
    cur.execute("""
        SELECT TO_CHAR(day.date, 'DD')
        FROM break_duties JOIN day ON (break_duties.day_id = day.id)
        WHERE break_duties.month_id = {}
        AND break_duties.hall_id = {}
    """.format(monthId, userDict["hall_id"]))

    # Load the results from the DB and convert the value to an int.
    breakDuties = [int(row[0]) for row in cur.fetchall()]
    logging.debug("Break Duties: {}".format(breakDuties))

    # Attempt to run the scheduler using deep copies of the raList and noDutyList.
    #  This is so that if the scheduler does not resolve on the first run, we
    #  can modify the parameters and try again with a fresh copy of the raList
    #  and noDutyList.
    copy_raList = cp.deepcopy(ra_list)
    copy_noDutyList = cp.copy(noDutyList)

    # Set completed to False and successful to False by default. These values
    #  will be manipulated in the while loop below as necessary.
    completed = False
    successful = False
    while not completed:
        # While we are not finished scheduling, create a candidate schedule
        sched = scheduler4_0.schedule(copy_raList, year, monthNum,
                                      noDutyDates=copy_noDutyList, ldaTolerance=ldat,
                                      prevDuties=prevRADuties, breakDuties=breakDuties)

        # If we were unable to schedule with the previous parameters,
        if len(sched) == 0:
            # Then we should attempt to modify the previous parameters
            #  and try again.

            if ldat > 1:
                # If the LDATolerance is greater than 1
                #  then decrement the LDATolerance by 1 and try again

                logging.info("DECREASE LDAT: {}".format(ldat))
                ldat -= 1

                # Create new deep copies of the ra_list and noDutyList
                copy_raList = cp.deepcopy(ra_list)
                copy_noDutyList = cp.copy(noDutyList)

            else:
                # Otherwise the LDATolerance is not greater than 1. In this
                #  case, we were unable to successfully generate a schedule
                #  with the given parameters.
                completed = True

        else:
            # Otherwise, we were able to successfully create a schedule!
            #  Mark that we have completed so we may exit the while loop
            #  and mark that we were successful.
            completed = True
            successful = True

    logging.debug("Schedule: {}".format(sched))

    # If we were not successful in generating a duty schedule.
    if not successful:
        # Log the occurrence
        logging.info("Unable to Generate Schedule for Hall: {} MonthNum: {} Year: {}"
                     .format(userDict["hall_id"], monthNum, year))

        # Notify the user of this result
        return jsonify(stdRet(0, "Unable to Generate Schedule"))

    # Add a record to the schedule table in the DB get its ID
    cur.execute("INSERT INTO schedule (hall_id, month_id, created) VALUES (%s, %s, NOW()) RETURNING id;",
                (hallId, monthId))

    # Load the query result
    schedId = cur.fetchone()[0]

    # Commit the changes to the DB
    ag.conn.commit()

    logging.debug("Schedule ID: {}".format(schedId))

    # Map the day.id to the numeric date value used for the scheduling algorithm

    # Create the mapping object
    days = {}

    # Query the day table for all of the days within the given month.
    cur.execute("SELECT EXTRACT(DAY FROM date), id FROM day WHERE month_id = %s;", (monthId,))

    # Iterate through the results
    for res in cur.fetchall():
        # Map the date to the day.id
        days[res[0]] = res[1]

    # Iterate through the schedule and generate parts of an insert query that will ultimately
    #  add the duties to the DB
    dutyDayStr = ""
    noDutyDayStr = ""
    for d in sched:
        # Check to see if there is at least one RA assigned for duty
        #  on this day.
        if d.numberOnDuty() > 0:
            # If there is at least one RA assigned for duty on this day,
            #  then iterate over all of the RAs assigned for duty on this
            #  day and add them to the dutyDayStr
            for r in d:
                dutyDayStr += "({},{},{},{},{}),".format(hallId, r.getId(), days[d.getDate()],
                                                         schedId, d.getPoints())

        else:
            # Otherwise, if there are no RAs assigned for duty on this day,
            #  then add the day to the noDutyDayStr
            noDutyDayStr += "({},{},{},{}),".format(hallId, days[d.getDate()], schedId, d.getPoints())

    # Attempt to save the schedule to the DB
    try:
        # If there were days added to the dutyDayStr
        if dutyDayStr != "":
            # Then insert all of the duties that were scheduled for the month into the DB
            cur.execute("""
                    INSERT INTO duties (hall_id, ra_id, day_id, sched_id, point_val) VALUES {};
                    """.format(dutyDayStr[:-1]))

        # If there were days added to the noDutyDayStr
        if noDutyDayStr != "":
            # Then insert all of the blank duty values for days that were not scheduled
            cur.execute("""
                    INSERT INTO duties (hall_id, day_id, sched_id, point_val) VALUES {};
                    """.format(noDutyDayStr[:-1]))

    except IntegrityError:
        # If we encounter an IntegrityError, then that means we attempted to insert a value
        #  into the DB that was already in there.

        # Log the occurrence
        logging.warning(
            "IntegrityError encountered when attempting to save duties for Schedule: {}. Rolling back changes."
            .format(schedId))

        # Rollback the changes to the DB
        ag.conn.rollback()

        # Notify the user of this issue.
        return jsonify(stdRet(-1, "Unable to Generate Schedule"))

    # Commit changes to the DB
    ag.conn.commit()

    # Close the DB cursor
    cur.close()

    logging.info("Successfully Generated Schedule: {}".format(schedId))

    # Notify the user of the successful schedule generation!
    return jsonify(stdRet(1, "successful"))


@schedule_bp.route("/api/changeRAonDuty", methods=["POST"])
@login_required
def changeRAforDutyDay():
    # API Method will change the RA assigned for a given duty
    #  from one RA to another in the same hall.
    #
    #  Required Auth Level: >= AHD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     dateStr  <str>  -  a string denoting the duty for the user's hall that is
    #                         to be altered.
    #     newId    <int>  -  an integer representing the ra.id value for the RA that is
    #                         to be assigned for the given duty.
    #     oldName  <str>  -  a string containing the name of the RA that is currently
    #                         on duty for the given day.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the save was successful
    #      0 : the save was unsuccessful
    #     -1 : an error occurred while scheduling

    # Get the user's information from the database
    userDict = getAuth()

    # Check to see if the user is authorized to alter duties
    # If the user is not at least an AHD
    if userDict["auth_level"] < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to alter duty for Hall: {}"
                     .format(userDict["ra_id"], userDict["hall_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Load the data from the request json
    data = request.json

    logging.debug("New RA id: {}".format(data["newId"]))
    logging.debug("Old RA Name: {}".format(data["oldName"]))
    logging.debug("HallID: {}".format(userDict["hall_id"]))
    # Expected as x/x/xxxx
    logging.debug("DateStr: {}".format(data["dateStr"]))

    # Split the old RA's name into its two DB components
    fName, lName = data["oldName"].split()

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the RA that is to be assigned for this duty.
    cur.execute("SELECT id FROM ra WHERE id = %s AND hall_id = %s;",
                (data["newId"], userDict["hall_id"]))

    # Load the query results
    raParams = cur.fetchone()

    # Check to see if we did not find an RA for the user's Hall.
    if raParams is None:
        # If we did not, log the occurrence.
        logging.warning("Alter Duty - unable to locate RA: {} for Hall: {}"
                        .format(data["newId"], userDict["hall_id"]))

        # Notify the user and stop processing
        return jsonify(stdRet(0, "New Assigned RA is Not a Valid Selection"))

    # Query the DB for the RA that is currently assigned for the duty.
    cur.execute("SELECT id FROM ra WHERE first_name LIKE %s AND last_name LIKE %s AND hall_id = %s",
                (fName, lName, userDict["hall_id"]))

    # Load the query results
    oldRA = cur.fetchone()

    # Check to see if we did not find an RA for the user's Hall.
    if oldRA is None:
        # If we did not, log the occurrence.
        logging.warning("Alter Duty - unable to locate RA: {} {} for Hall: {}"
                        .format(fName, lName, userDict["hall_id"]))

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Unable to Locate Previously Assigned RA for Duty."))

    # Query the DB for the day that the duty occurs on
    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE(%s, 'MM/DD/YYYY');", (data["dateStr"],))

    # Load the query results
    rawDay = cur.fetchone()

    # Check to see if we did not find the given day.
    if rawDay is None:
        # If we did not, log the occurrence.
        logging.warning("Alter Duty - unable to find Day: {}"
                        .format(data["dateStr"]))

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Invalid Date"))

    else:
        # Otherwise, unpack the query results
        dayID, monthId = rawDay

    # Query the DB for the schedule that the duty belongs to
    cur.execute("SELECT id FROM schedule WHERE hall_id = %s AND month_id = %s ORDER BY created DESC, id DESC;",
                (userDict["hall_id"], monthId))

    # Load the query results
    schedId = cur.fetchone()

    # Check to see if we did not find an RA for the user's Hall.
    if schedId is None:
        # If we did not, log the occurrence.
        logging.warning("Alter Duty - unable to locate schedule for Month: {}, Hall: {}"
                        .format(monthId, userDict["hall_id"]))

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Unable to validate schedule."))

    # Execute an UPDATE statement to alter the duty in the DB
    cur.execute("""UPDATE duties
                   SET ra_id = %s
                   WHERE hall_id = %s
                   AND day_id = %s
                   AND sched_id = %s
                   AND ra_id = %s
                   """, (raParams[0], userDict["hall_id"],
                         dayID, schedId[0], oldRA[0]))

    # Commit the changes in the DB
    ag.conn.commit()

    # Close the DB cursor
    cur.close()

    # Notify the user that the save was a success
    return jsonify(stdRet(1, "successful"))


@schedule_bp.route("/api/addNewDuty", methods=["POST"])
@login_required
def addNewDuty():
    # API Method that will add a regularly scheduled duty
    #  with the assigned RA on the given day.
    #
    #  Required Auth Level: >= AHD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     dateStr  <str>  -  a string denoting the duty for the user's hall that is
    #                         to be altered.
    #     id       <int>  -  an integer representing the ra.id value for the RA that is
    #                         to be assigned for the given duty.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the save was successful
    #      0 : the save was unsuccessful
    #     -1 : an error occurred while scheduling

    # Get the user's information from the database
    userDict = getAuth()

    # Check to see if the user is authorized to add duties
    # If the user is not at least an AHD
    if userDict["auth_level"] < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to add a duty for Hall: {}"
                     .format(userDict["ra_id"], userDict["hall_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Load the provdied data from the request json
    data = request.json

    logging.debug("New RA id: {}".format(data["id"]))
    logging.debug("HallID: {}".format(userDict["hall_id"]))
    # Expected as x-x-xxxx
    logging.debug("DateStr: {}".format(data["dateStr"]))

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the given RA
    cur.execute("SELECT id FROM ra WHERE id = %s AND hall_id = %s;", (data["id"], userDict["hall_id"]))

    # Load the query result
    raId = cur.fetchone()

    # Check to see if we were able to find the given RA in the DB
    #  for the user's hall.
    if raId is None:
        # If not, then log the occurrence.
        logging.warning("Add Duty - unable to locate RA: {} for Hall: {}"
                        .format(data["id"], userDict["hall_id"]))

        # Notify the user and stop processing
        return jsonify(stdRet(-1, "Chosen RA is not a Valid Selection"))

    # Query the DB for the given day
    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE(%s, 'YYYY-MM-DD');", (data["dateStr"],))

    # Load the query results
    rawDay = cur.fetchone()

    # Check to see if we did not find the given day.
    if rawDay is None:
        # If we did not, log the occurrence.
        logging.warning("Add Duty - unable to find Day: {}"
                        .format(data["dateStr"]))

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Invalid Date"))

    else:
        # Otherwise, unpack the query results
        dayID, monthId = rawDay

    # Query the DB for the schedule that this duty should belong to.
    cur.execute("SELECT id FROM schedule WHERE hall_id = %s AND month_id = %s ORDER BY created DESC, id DESC;",
                (userDict["hall_id"], monthId))

    # Load the query results
    schedId = cur.fetchone()

    # Check to see if we did not find a schedule fitting the day and hall.
    if schedId is None:
        # If we did not, log the occurrence.
        logging.warning("Add Duty - unable to locate schedule for Month: {}, Hall: {}"
                        .format(monthId, userDict["hall_id"]))

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Unable to validate schedule."))

    # Execute an INSERT statement to have the duty created in the duties table
    cur.execute("""INSERT INTO duties (hall_id, ra_id, day_id, sched_id, point_val)
                    VALUES (%s, %s, %s, %s, %s);""",
                (userDict["hall_id"], raId[0], dayID, schedId[0], data["pts"]))

    # Commit the changes to the DB
    ag.conn.commit()

    # Close the DB cursor
    cur.close()

    logging.debug("Successfully added new duty")

    # Notify the user that the save was successful
    return jsonify(stdRet(1, "successful"))


@schedule_bp.route("/api/deleteDuty", methods=["POST"])
@login_required
def deleteDuty():
    # API Method that will delete a regularly scheduled duty
    #  with the given RA and day.
    #
    #  Required Auth Level: >= AHD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     dateStr  <str>  -  a string denoting the duty for the user's hall that is
    #                         to be altered.
    #     raName   <str>  -  a string containing the name of the RA that is currently
    #                         on duty for the given day.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the save was successful
    #      0 : the save was unsuccessful
    #     -1 : an error occurred while scheduling

    # Get the user's information from the database
    userDict = getAuth()

    # Check to see if the user is authorized to delete duties
    # If the user is not at least an AHD
    if userDict["auth_level"] < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to delete duty for Hall: {}"
                     .format(userDict["ra_id"], userDict["hall_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Load the data from the request json
    data = request.json

    logging.debug("Deleted Duty RA Name: {}".format(data["raName"]))
    logging.debug("HallID: {}".format(userDict["hall_id"]))
    # Expected as x-x-xxxx
    logging.debug("DateStr: {}".format(data["dateStr"]))

    # Split the old RA's name into its two DB components
    fName, lName = data["raName"].split()

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the given RA
    cur.execute("SELECT id FROM ra WHERE first_name LIKE %s AND last_name LIKE %s AND hall_id = %s;",
                (fName, lName, userDict["hall_id"]))

    # Load the query results
    raId = cur.fetchone()

    # Check to see if we did not find an RA for the user's Hall.
    if raId is None:
        # If we did not, log the occurrence.
        logging.warning("Delete Duty - unable to locate RA: {} {} for Hall: {}"
                        .format(fName, lName, userDict["hall_id"]))

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Unable to Verify Previously Assigned RA."))

    # Query the DB to find the day the duty belongs to
    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE(%s, 'MM/DD/YYYY');", (data["dateStr"],))

    # Load the query results
    rawDay = cur.fetchone()

    # Check to see if we did not find the given day.
    if rawDay is None:
        # If we did not, log the occurrence.
        logging.warning("Delete Duty - unable to find Day: {}"
                        .format(data["dateStr"]))

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Invalid Date"))

    else:
        # Otherwise, unpack the query results
        dayID, monthId = rawDay

    # Query the DB for the schedule that the duty belongs to
    cur.execute("SELECT id FROM schedule WHERE hall_id = %s AND month_id = %s ORDER BY created DESC, id DESC;",
                (userDict["hall_id"], monthId))

    # Load the result from the DB
    schedId = cur.fetchone()

    # Check to see if we did not find a schedule fitting the day and hall.
    if schedId is None:
        # If we did not, log the occurrence.
        logging.warning("Delete Duty - unable to locate schedule for Month: {}, Hall: {}"
                        .format(monthId, userDict["hall_id"]))

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Unable to validate schedule."))

    # Execute DELETE statement to remove the provided duty from the DB
    cur.execute("""DELETE FROM duties
                    WHERE ra_id = %s
                    AND hall_id = %s
                    AND day_id = %s
                    AND sched_id = %s""",
                (raId[0], userDict["hall_id"], dayID, schedId[0]))

    # Commit the changes to the DB
    ag.conn.commit()

    # Close the DB cursor
    cur.close()

    logging.info("Successfully deleted Duty: {} for Hall: {}"
                 .format(data["dateStr"], userDict["hall_id"]))

    # Notify the user that the delete was successful
    return jsonify(stdRet(1, "successful"))
