from flask import render_template, request, jsonify, Blueprint, abort
from schedule.rabbitConnectionManager import RabbitConnectionManager
from flask_login import login_required
from psycopg2 import Error
import logging
import os

# Import the appGlobals for this blueprint to use
import appGlobals as ag

# Import the needed functions from other parts of the application
from helperFunctions.helperFunctions import getAuth, stdRet, getCurSchoolYear, getSchoolYear
from staff.staff import getRAStats, addRAPointModifier

schedule_bp = Blueprint("schedule_bp", __name__,
                        template_folder="templates",
                        static_folder="static")

# Connect to the RabbitMQ instance
schedulerQueueConn = RabbitConnectionManager(
    os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost:5672/%2f'),
    os.environ.get('RABBITMQ_SCHEDULER_QUEUE', 'genSched')
)


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
    authedUser = getAuth()

    # If the user is not at least an AHD
    if authedUser.auth_level() < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {}".format(authedUser.ra_id()))

        # Raise an 403 Access Denied HTTP Exception that will be handled by flask
        abort(403)

    # Get the information for the current school year.
    #  This will be used to calculate duty points for the RAs.
    start, end = getCurSchoolYear()

    # Call getRAStats to get information on the number of Duty
    # points each RA has for the current school year
    ptDict = getRAStats(authedUser.hall_id(), start, end)

    logging.debug("Point Dict: {}".format(ptDict))

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Load the necessary hall settings from the DB
    cur.execute("SELECT duty_flag_label FROM hall_settings WHERE res_hall_id = %s", (authedUser.hall_id(),))
    # Load the query result
    dfl = cur.fetchone()[0]

    # Check to see if the google calendar integration is set up
    cur.execute(
        "SELECT EXISTS (SELECT token FROM google_calendar_info WHERE res_hall_id = %s)",
        (authedUser.hall_id(),)
    )
    # Load the query result
    gCalConn = cur.fetchone()[0]

    # Create a custom settings dictionary
    custSettings = {
        "dutyFlagLabel": dfl,
        "gCalConnected": gCalConn
    }

    # Merge the base options into the custom settings dictionary to simplify passing
    #  settings into the template renderer.
    custSettings.update(ag.baseOpts)

    logging.debug("Custom Settings Dict: {}".format(custSettings))

    # Query the DB for a list of all of the RAs and their information for the user's staff.
    cur.execute("""
        SELECT ra.id, ra.first_name, ra.last_name, ra.color 
        FROM ra JOIN staff_membership AS sm ON (ra.id = sm.ra_id)
        WHERE sm.res_hall_id = %s 
        ORDER BY ra.first_name ASC;""", (authedUser.hall_id(),))

    # Load the RA query results
    raList = cur.fetchall()

    # Sort alphabetically by last name of RA
    ptDictSorted = sorted(ptDict.items(), key=lambda kv: kv[1]["name"].split(" ")[1])

    # Query the DB for the latest scheduler requests for the hall being viewed.
    cur.execute("""
        SELECT id, status, created_date
        FROM scheduler_queue
        WHERE res_hall_id = %s
        ORDER BY created_date DESC
        LIMIT (10);""", (authedUser.hall_id(),))

    # Load the query results
    schedulerQueueList = cur.fetchall()
    logging.debug(schedulerQueueList)

    return render_template("schedule/editSched.html", raList=raList, auth_level=authedUser.auth_level(),
                           ptDict=ptDictSorted, curView=3, opts=custSettings, hall_name=authedUser.hall_name(),
                           linkedHalls=authedUser.getAllAssociatedResHalls(), schedQueueList=schedulerQueueList)


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
    #     allColors      <bool>  -  a boolean that, if set to True, will associate the
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
    #           "extendedProps": {
    #               "dutyType": "std",
    #               "flagged": <duties.flagged>,
    #               "pts": <duties.point_val>
    #           }
    #        }
    #     ]

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if start is None and end is None and hallId is None and showAllColors is None:
        # If the hallId, start, end, and showAllColors are None, then
        #  this method was called from a remote client.

        # Get the user's information from the database
        authedUser = getAuth()

        # Set the value of hallId from the userDict
        hallId = authedUser.hall_id()

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
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD'),
               duties.flagged, duties.point_val
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

            if not fromServer and authedUser.ra_id() == row[3]:
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
            "extendedProps": {
                "dutyType": "std",
                "flagged": row[5],
                "pts": row[6]
            }
        })

    # If this API method was called from the server
    if fromServer:
        # Then return the result as-is
        return res

    else:
        # Otherwise return a JSON version of the result
        return jsonify(res)


@schedule_bp.route("/api/runScheduler", methods=["POST"])
def queueScheduler():
    # API Method that queues a request to run the duty scheduler
    #  for the given Res Hall and month. Any users associated with
    #  the staff that have an auth_level of HD will not be scheduled.
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
    #      1 : the duty scheduling request was successfully queued
    #     -1 : an error occurred while queuing the scheduling request
    #
    #  If the scheduling request was successfully queued, then the message of the standard
    #  return will be the SQID that the user can use to check the status of the scheduling
    #  request.

    # Get the user's information from the database
    authedUser = getAuth()

    # Check to see if the user is authorized to run the scheduler
    # If the user is not at least an AHD
    if authedUser.auth_level() < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to run scheduler."
                     .format(authedUser.ra_id()))

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
            noDutyList = [int(d) for d in request.json["noDuty"].split(", ")]

        else:
            # Otherwise if there are no values passed in noDuty, set
            #  noDutyList to an empty list
            noDutyList = []

        # Check to see if values have been passed through the
        #  eligibeRAs parameter
        if request.json["eligibleRAs"] != "":
            # If eligibleRAs is not "", then attempt to parse out the values
            eligibleRAs = [int(i) for i in request.json["eligibleRAs"]]

        else:
            # Otherwise if there are no values passed in eligibleRAs, then
            # set eligibleRAs to an empty list
            eligibleRAs = []

    except ValueError as ve:
        # If a ValueError occurs, then there was an issue parsing out the
        #  monthNum, year, noDuty-dates or the ra.ids from the request json.

        # Log the occurrence
        logging.warning("Error Parsing Request Values for Scheduler: {}"
                        .format(ve))

        # Notify the user of the error
        return jsonify(
            stdRet(-1, "Error Parsing Scheduler Request Parameters. Please refresh and try again.")
        )

    except KeyError as ke:
        # If a KeyError occurs, then there was an expected value in the
        #  request json that was missing.

        # Log the occurrence
        logging.warning("Error Loading Request Values for Scheduler: {}"
                        .format(ke))

        # Notify the user of the error
        return jsonify(stdRet(-1, "Missing Scheduler Parameters. Please refresh and try again."))

    # Set the value of the hallId from the userDict
    hallId = authedUser.hall_id()

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Add a record in the scheduler_queue table for this request
    cur.execute(
        "INSERT INTO scheduler_queue (res_hall_id, created_ra_id) VALUES (%s, %s) RETURNING id, created_date, status;",
        (hallId, authedUser.ra_id())
    )

    # Commit the changes to the DB
    ag.conn.commit()

    # Fetch the new record's ID
    sqid, created_date, status = cur.fetchone()

    # Close the DB cursor
    cur.close()

    # Create the body of the rabbitMQ message with the below attributes:
    #      |- resHallID         <int>
    #      |- monthNum          <int>
    #      |- year              <int>
    #      |- eligibleRAList    <lst<int>>
    #      |- noDutyList        <lst<int>>

    msgBody = {
        "resHallID": hallId,
        "monthNum": monthNum,
        "year": year,
        "eligibleRAList": eligibleRAs,
        "noDutyList": noDutyList
    }

    # Queue up the scheduler request message.
    if not schedulerQueueConn.publishMsg(msgBody, {"sqid": sqid}):
        # If the channel gave us an error, then re-establish the RabbitMQ connection.

        # Notify the user to try again
        return jsonify(stdRet(-1, "Connection to message broker interrupted. Please try again."))

    logging.info("Successfully queued scheduler request {} for Res Hall: {}".format(sqid, hallId))

    # Notify the user of the successful schedule generation!
    return jsonify({"status": status, "created_date": created_date.strftime("%m/%d/%y"), "sqid": sqid})


@schedule_bp.route("/api/checkSchedulerStatus", methods=["GET"])
@login_required
def checkSchedulerStatus(sqid=None):
    # API method to check the status of the schedule generation
    #  for a given scheduler queue ID.
    #
    #  Required Auth Level: >= AHD
    #
    #  If called from the server, this function accepts the following parameters:
    #
    #     sqid  <int>  -  an integer representing the scheduler queue ID for the
    #                      schedule being generated.
    #
    #  If called from a client, the following parameters are required:
    #
    #     sqid  <int>  -  an integer representing the scheduler queue ID for the
    #                      schedule being generated.
    #
    #  This method returns a standard return object whose status and message are
    #  the status and reason associated with the scheduler queue record. If no
    #  record can be found, then return a status of -1 and reason of "Record
    #  Not Found".

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if sqid is None:
        # If the SQID is None, then this method was called from a remote client.

        # Get the user's information from the database
        authedUser = getAuth()

        # Check to see if the user is authorized to query schedule statuses
        # If the user is not at least an AHD
        if authedUser.auth_level() < 2:
            # Then they are not permitted to see this view.

            # Log the occurrence.
            logging.warning(
                "User Not Authorized - RA: {} attempted to view schedule status."
                .format(authedUser.ra_id())
            )

            # Notify the user that they are not authorized.
            return jsonify(stdRet(-1, "NOT AUTHORIZED"))

        # Get the SQID from the request
        sqid = request.args.get("sqid")

        # Mark that this method was not called from the server
        fromServer = False

    logging.debug("Check Scheduler Status - SQID: {}".format(sqid))

    # Create a cursor object
    cur = ag.conn.cursor()

    # Fetch the status and reason of the provided scheduler queue record.
    cur.execute("SELECT status, reason FROM scheduler_queue WHERE id = %s", (sqid,))

    # Load the results to memory
    res = cur.fetchone()

    logging.debug("Check status DB result: {}".format(res))

    # Check to see if we received a result
    if res is not None:
        # If there is a result, then unpack the result
        status, reason = res

    else:
        # Otherwise set the status and reason appropriately
        status = -1
        reason = "Record Not Found - {}".format(sqid)

    # Close the cursor
    cur.close()

    # If this API method was called from the server
    if fromServer:
        # Then return the result as-is
        return {"status": status, "msg": reason, "sqid": sqid}

    else:
        # Otherwise return a JSON version of the result
        return jsonify({"status": status, "msg": reason, "sqid": sqid})


@schedule_bp.route("/api/getSchedulerQueueItemInfo", methods=["GET"])
@login_required
def getScheduleQueueItemInfo(sqid=None, resHallID=None):
    # API method to return information regarding the schedule generation
    #  for a given scheduler queue ID.
    #
    #  Required Auth Level: >= AHD
    #
    #  If called from the server, this function accepts the following parameters:
    #
    #     sqid        <int>  -  an integer representing the scheduler queue ID for the
    #                            schedule being generated.
    #     resHallID   <int>  -  an integer representing the Res Hall ID for the
    #                            schedule queue item being requested.
    #
    #  If called from a client, the following parameters are required:
    #
    #     sqid  <int>  -  an integer representing the scheduler queue ID for the
    #                      schedule being generated.
    #
    #  This method returns an object with the following specifications:
    #
    #     {
    #        "status": <scheduler_queue.status>,
    #        "reason": <scheduler_queue.reason>,
    #        "requestDatetime": <scheduler_queue.created_date>,
    #        "requestingRA": <ra.first_name> <ra.last_name>,
    #        "sqid": <scheduler_queue.id>
    #     }

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if sqid is None and resHallID is None:
        # If the SQID is None, then this method was called from a remote client.

        # Get the user's information from the database
        authedUser = getAuth()

        # Check to see if the user is authorized to query schedule statuses
        # If the user is not at least an AHD
        if authedUser.auth_level() < 2:
            # Then they are not permitted to see this view.

            # Log the occurrence.
            logging.warning(
                "User Not Authorized - RA: {} attempted to view schedule queue details."
                .format(authedUser.ra_id())
            )

            # Notify the user that they are not authorized.
            return jsonify(stdRet(-1, "NOT AUTHORIZED"))

        try:
            # Get the SQID from the request
            sqid = int(request.args.get("sqid"))

        except ValueError:
            # If there was an issue, then return an error notification

            # Log the occurrence
            logging.warning("Unable to parse SQID from getScheduleQueueItemInfo API request")

            # Notify the user that there was an error
            return jsonify(stdRet(-1, "Invalid SQID"))

        # Get the user's res hall ID
        resHallID = authedUser.hall_id()

        # Mark that this method was not called from the server
        fromServer = False

    logging.debug("Get Scheduler Info - SQID: {}, Hall: {}".format(sqid, resHallID))

    # Create a cursor object
    cur = ag.conn.cursor()

    # Fetch the desired information of the provided scheduler queue record.
    cur.execute("""
        SELECT sq.status, sq.reason, sq.created_date, CONCAT(ra.first_name,' ',ra.last_name), sq.id
        FROM scheduler_queue AS sq JOIN ra ON (ra.id = sq.created_ra_id)
        WHERE sq.id = %s
        AND sq.res_hall_id = %s
        ORDER BY sq.created_date DESC
    """, (sqid, resHallID))

    # Load the results to memory
    res = cur.fetchone()

    logging.debug("Get Scheduler Info DB result: {}".format(res))

    # Check to see if we received a result
    if res is not None:
        # If there is a result, then pack the result
        ret = {
            "status": res[0],
            "reason": res[1],
            "requestDatetime": res[2],
            "requestingRA": res[3],
            "sqid": res[4]
        }

    else:
        # Otherwise set the status and reason appropriately
        ret = {
            "status": -99,
            "reason": "Record Not Found - {}".format(sqid),
            "requestDatetime": None,
            "requestingRA": None,
            "sqid": 0
        }

    # Close the cursor
    cur.close()

    # If this API method was called from the server
    if fromServer:
        # Then return the result as-is
        return ret

    else:
        # Otherwise return a JSON version of the result
        return jsonify(ret)


@schedule_bp.route("/api/getRecentSchedulerRequests", methods=["GET"])
@login_required
def getRecentSchedulerRequests(resHallID=None):
    # API method to return the 10 latest scheduler requests for the given
    #  residence hall.
    #
    #  Required Auth Level: >= AHD
    #
    #  If called from the server, this function accepts the following parameters:
    #
    #     resHallID   <int>  -  an integer representing the Res Hall ID for the
    #                            schedule queue item being requested.
    #
    #  If called from a client, the method does not require any additional
    #  parameters.
    #
    #  This method returns an object with the following specifications:
    #
    #     {
    #        <scheduler_queue.id 1> : {
    #           "created_date": <scheduler_queue.created_date>,
    #           "status": <scheduler_queue.status>
    #        },
    #        <scheduler_queue.id 2> : {
    #           "created_date": <scheduler_queue.created_date>,
    #           "status": <scheduler_queue.status>
    #        },
    #        ...
    #     }

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if resHallID is None:
        # If the SQID is None, then this method was called from a remote client.

        # Get the user's information from the database
        authedUser = getAuth()

        # Check to see if the user is authorized to query schedule statuses
        # If the user is not at least an AHD
        if authedUser.auth_level() < 2:
            # Then they are not permitted to see this view.

            # Log the occurrence.
            logging.warning(
                "User Not Authorized - RA: {} attempted to view latest schedule queue requests."
                    .format(authedUser.ra_id())
            )

            # Notify the user that they are not authorized.
            return jsonify(stdRet(-1, "NOT AUTHORIZED"))

        # Get the user's res hall ID
        resHallID = authedUser.hall_id()

        # Mark that this method was not called from the server
        fromServer = False

    logging.debug("Get Scheduler Requests - Hall: {}".format(resHallID))

    # Create a cursor object
    cur = ag.conn.cursor()

    # Query the DB for the latest scheduler requests for the hall being viewed.
    cur.execute("""
            SELECT id, status, created_date
            FROM scheduler_queue
            WHERE res_hall_id = %s
            ORDER BY created_date DESC
            LIMIT (10);""", (resHallID,))

    # Load the query results
    schedulerQueueList = cur.fetchall()

    # Format the results into the expected format
    res = {}
    for sqid, status, created_date in schedulerQueueList:
        res[sqid] = {
            "created_date": created_date.strftime("%m/%d/%y"),
            "status": status
        }

    # Close the cursor
    cur.close()

    # If this API method was called from the server
    if fromServer:
        # Then return the result as-is
        return res

    else:
        # Otherwise return a JSON version of the result
        return jsonify(res)


@schedule_bp.route("/api/alterDuty", methods=["POST"])
@login_required
def alterDuty():
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
    #     flag     <bool> -  a boolean used to denote whether or not this duty should
    #                         be flagged in the DB.
    #     pts      <int>  -  an integer denoting the number of points that should be
    #                         awarded for this duty.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the save was successful
    #      0 : the save was unsuccessful
    #     -1 : an error occurred while scheduling

    # Get the user's information from the database
    authedUser = getAuth()

    # Check to see if the user is authorized to alter duties
    # If the user is not at least an AHD
    if authedUser.auth_level() < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to alter duty for Hall: {}"
                     .format(authedUser.ra_id(), authedUser.hall_id()))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Load the data from the request json
    data = request.json

    logging.debug("New RA id: {}".format(data["newId"]))
    logging.debug("Old RA Name: {}".format(data["oldName"]))
    logging.debug("HallID: {}".format(authedUser.hall_id()))
    # Expected as x/x/xxxx
    logging.debug("DateStr: {}".format(data["dateStr"]))

    # Split the old RA's name into its two DB components
    fName, lName = data["oldName"].split()

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the RA that is to be assigned for this duty.
    cur.execute("SELECT ra_id FROM staff_membership WHERE ra_id = %s AND res_hall_id = %s;",
                (data["newId"], authedUser.hall_id()))

    # Load the query results
    raParams = cur.fetchone()

    # Check to see if we did not find an RA for the user's Hall.
    if raParams is None:
        # If we did not, log the occurrence.
        logging.warning("Alter Duty - unable to locate RA: {} for Hall: {}"
                        .format(data["newId"], authedUser.hall_id()))

        # Close the DB cursor
        cur.close()

        # Notify the user and stop processing
        return jsonify(stdRet(0, "New Assigned RA is Not a Valid Selection"))

    # Query the DB for the RA that is currently assigned for the duty.
    cur.execute("""
        SELECT ra.id 
        FROM ra JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE ra.first_name LIKE %s 
        AND ra.last_name LIKE %s 
        AND sm.res_hall_id = %s""", (fName, lName, authedUser.hall_id()))

    # Load the query results
    oldRA = cur.fetchone()

    # Check to see if we did not find an RA for the user's Hall.
    if oldRA is None:
        # If we did not, log the occurrence.
        logging.warning("Alter Duty - unable to locate RA: {} {} for Hall: {}"
                        .format(fName, lName, authedUser.hall_id()))

        # Close the DB cursor
        cur.close()

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

        # Close the DB cursor
        cur.close()

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Invalid Date"))

    else:
        # Otherwise, unpack the query results
        dayID, monthId = rawDay

    # Query the DB for the schedule that the duty belongs to
    cur.execute("SELECT id FROM schedule WHERE hall_id = %s AND month_id = %s ORDER BY created DESC, id DESC;",
                (authedUser.hall_id(), monthId))

    # Load the query results
    schedId = cur.fetchone()

    # Check to see if we did not find an RA for the user's Hall.
    if schedId is None:
        # If we did not, log the occurrence.
        logging.warning("Alter Duty - unable to locate schedule for Month: {}, Hall: {}"
                        .format(monthId, authedUser.hall_id()))

        # Close the DB cursor
        cur.close()

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Unable to validate schedule."))

    # Execute an UPDATE statement to alter the duty in the DB
    cur.execute("""UPDATE duties
                   SET ra_id = %s,
                       point_val = %s,
                       flagged = %s
                   WHERE hall_id = %s
                   AND day_id = %s
                   AND sched_id = %s
                   AND ra_id = %s
                   """, (raParams[0], data["pts"], data["flag"],
                         authedUser.hall_id(), dayID, schedId[0],
                         oldRA[0]))

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
    #     flag     <bool> -  a boolean used to denote whether or not this duty should
    #                         be flagged in the DB.
    #     pts      <int>  -  an integer denoting the number of points that should be
    #                         awarded for this duty.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the save was successful
    #      0 : the save was unsuccessful
    #     -1 : an error occurred while scheduling

    # Get the user's information from the database
    authedUser = getAuth()

    # Check to see if the user is authorized to add duties
    # If the user is not at least an AHD
    if authedUser.auth_level() < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to add a duty for Hall: {}"
                     .format(authedUser.ra_id(), authedUser.hall_id()))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Load the provided data from the request json
    data = request.json

    logging.debug("New RA id: {}".format(data["id"]))
    logging.debug("HallID: {}".format(authedUser.hall_id()))
    # Expected as x-x-xxxx
    logging.debug("DateStr: {}".format(data["dateStr"]))

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the given RA
    cur.execute("SELECT ra_id FROM staff_membership WHERE ra_id = %s AND res_hall_id = %s;",
                (data["id"], authedUser.hall_id()))

    # Load the query result
    raId = cur.fetchone()

    # Check to see if we were able to find the given RA in the DB
    #  for the user's hall.
    if raId is None:
        # If not, then log the occurrence.
        logging.warning("Add Duty - unable to locate RA: {} for Hall: {}"
                        .format(data["id"], authedUser.hall_id()))

        # Close the DB cursor
        cur.close()

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

        # Close the DB cursor
        cur.close()

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Invalid Date"))

    else:
        # Otherwise, unpack the query results
        dayID, monthId = rawDay

    # Query the DB for the schedule that this duty should belong to.
    cur.execute("SELECT id FROM schedule WHERE hall_id = %s AND month_id = %s ORDER BY created DESC, id DESC;",
                (authedUser.hall_id(), monthId))

    # Load the query results
    schedId = cur.fetchone()

    # Check to see if we did not find a schedule fitting the day and hall.
    if schedId is None:
        # If we did not, then create an entry in the schedule table for this Duty.
        # log the occurrence.
        logging.info("Add Duty - unable to locate schedule for Month: {}, Hall: {} - Creating new schedule."
                     .format(monthId, authedUser.hall_id()))

        # Insert the schedule entry into the DB
        cur.execute("INSERT INTO schedule (hall_id, month_id, created) VALUES (%s, %s, NOW()) RETURNING id",
                    (authedUser.hall_id(), monthId))

        # Load the schedule ID from the DB
        schedId = cur.fetchone()

    # Execute an INSERT statement to have the duty created in the duties table
    cur.execute("""INSERT INTO duties (hall_id, ra_id, day_id, sched_id, point_val, flagged)
                    VALUES (%s, %s, %s, %s, %s, %s);""",
                (authedUser.hall_id(), raId[0], dayID, schedId[0], data["pts"], data["flag"]))

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
    authedUser = getAuth()

    # Check to see if the user is authorized to delete duties
    # If the user is not at least an AHD
    if authedUser.auth_level() < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to delete duty for Hall: {}"
                     .format(authedUser.ra_id(), authedUser.hall_id()))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Load the data from the request json
    data = request.json

    logging.debug("Deleted Duty RA Name: {}".format(data["raName"]))
    logging.debug("HallID: {}".format(authedUser.hall_id()))
    # Expected as x-x-xxxx
    logging.debug("DateStr: {}".format(data["dateStr"]))

    # Split the old RA's name into its two DB components
    fName, lName = data["raName"].split()

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the given RA
    cur.execute("""
        SELECT ra.id 
        FROM ra JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE ra.first_name LIKE %s 
        AND ra.last_name LIKE %s 
        AND sm.res_hall_id = %s;""", (fName, lName, authedUser.hall_id()))

    # Load the query results
    raId = cur.fetchone()

    # Check to see if we did not find an RA for the user's Hall.
    if raId is None:
        # If we did not, log the occurrence.
        logging.warning("Delete Duty - unable to locate RA: {} {} for Hall: {}"
                        .format(fName, lName, authedUser.hall_id()))

        # Close the DB cursor
        cur.close()

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

        # Close the DB cursor
        cur.close()

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Invalid Date"))

    else:
        # Otherwise, unpack the query results
        dayID, monthId = rawDay

    # Query the DB for the schedule that the duty belongs to
    cur.execute("SELECT id FROM schedule WHERE hall_id = %s AND month_id = %s ORDER BY created DESC, id DESC;",
                (authedUser.hall_id(), monthId))

    # Load the result from the DB
    schedId = cur.fetchone()

    # Check to see if we did not find a schedule fitting the day and hall.
    if schedId is None:
        # If we did not, log the occurrence.
        logging.warning("Delete Duty - unable to locate schedule for Month: {}, Hall: {}"
                        .format(monthId, authedUser.hall_id()))

        # Close the DB cursor
        cur.close()

        # Notify the user and stop processing
        return jsonify(stdRet(0, "Unable to validate schedule."))

    # Execute DELETE statement to remove the provided duty from the DB
    cur.execute("""DELETE FROM duties
                    WHERE ra_id = %s
                    AND hall_id = %s
                    AND day_id = %s
                    AND sched_id = %s""",
                (raId[0], authedUser.hall_id(), dayID, schedId[0]))

    # Commit the changes to the DB
    ag.conn.commit()

    # Close the DB cursor
    cur.close()

    logging.info("Successfully deleted Duty: {} for Hall: {}"
                 .format(data["dateStr"], authedUser.hall_id()))

    # Notify the user that the delete was successful
    return jsonify(stdRet(1, "successful"))


@schedule_bp.route("/api/getTradeRequestsForUser", methods=["GET"])
@login_required
def getUserTradeRequests(authedUser=None):
    # API method to return any duty trade requests that the user could
    #  accept. This includes trade requests for duties that the user
    #  has as well as trade requests that are not for a particular user.
    #
    #  Required Auth Level: None
    #
    #  If called from the server, this function accepts the following parameters:
    #
    #     authedUser   <AuthenticatedUser>  -  an AuthenticatedUser object for the
    #                                          user whose duty trade requests are
    #                                          being fetched.
    #
    #  If called from a client, the method does not require any additional
    #  parameters.
    #
    #  This method returns an object with the following specifications:
    #
    #     [
    #       {
    #         "id": <duty_trade_requests.id>,
    #         "traderName": <ra.first_name> + " " + <ra.last_name>,
    #         "tradeWithSpecificUser": True if <duty_trade_requests.trade_with_ra_id> else False
    #         "date": <day.date>
    #       },
    #       ...
    #     ]

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if authedUser is None:
        # If the authedUser is None, then this method was called from a remote client.

        # Get the user's information from the database
        authedUser = getAuth()

        # Mark that this method was not called from the server
        fromServer = False

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for a list of pending trade requests that pertain to the user.
    cur.execute(
        """SELECT dtr.id, CONCAT(trader.first_name, ' ', trader.last_name), dtr.trade_with_ra_id, trade_duty_day.date
        FROM duty_trade_requests AS dtr 
            JOIN duties AS trade_duty ON (dtr.trade_duty_id = trade_duty.id)
            JOIN day AS trade_duty_day ON (trade_duty_day.id = trade_duty.day_id)
            JOIN ra AS trader ON (dtr.trader_ra_id = trader.id)
        WHERE (dtr.trade_with_ra_id IS NULL 
            OR dtr.trade_with_ra_id = %s)
        AND dtr.res_hall_id = %s
        AND dtr.status = 0
        ORDER BY trade_duty_day.date ASC;""",
        (authedUser.ra_id(), authedUser.hall_id())
    )

    # Parse and assemble trade requests
    tradeRequests = []
    for req in cur.fetchall():
        tradeRequests.append({
            "id": req[0],
            "traderName": req[1],
            "tradeWithSpecificUser": True if req[2] is not None else False,
            "date": req[3] if fromServer else req[3].strftime('%Y/%m/%d'),
        })

    # If this API method was called from the server
    if fromServer:
        # Then return the result as-is
        return tradeRequests

    else:
        # Otherwise return a JSON version of the result
        return jsonify(tradeRequests)


@schedule_bp.route("/api/getAddTradeInfo", methods=["GET"])
@login_required
def getAdditionalTradeInfo():
    # API method to return additional information about the provided
    #  trade duty request. NOTE: Trade request information will not
    #  be returned if the trade request ID does not belong to the
    #  user's selected Res Hall.
    #
    #  Required Auth Level: None
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     tradeReqID  <int>  -  an integer representing the ID of the
    #                            trade duty request desired.
    #
    #  This method returns an object with the following specifications:
    #
    #     {
    #       "trDuty": {
    #         "flagged": <duties.flagged>,
    #         "label": <hall_settings.duty_flag_label>
    #       },
    #       "exDuty": {
    #         "date": <day.date>,
    #         "flagged": <duties.flagged>
    #       }
    #       "tradeReason": <duty_trade_requests.trade_reason>
    #     }

    # Get the user's information from the database
    authedUser = getAuth()

    try:
        # Get the trade request ID from the request
        tradeReqID = int(request.args.get("tradeReqID"))

    except ValueError:
        # If there was an issue, then return an error notification

        # Log the occurrence
        logging.warning("Unable to parse duty trade request ID from getAdditionalTradeInfo API request")

        # Notify the user that there was an error
        return jsonify(stdRet(-1, "Invalid trade request ID"))

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the additional duty trade information.
    cur.execute(
        """SELECT trade_duty.flagged, exchange_duty_day.date, exchange_duty.flagged, dtr.trade_reason
        FROM duty_trade_requests AS dtr
            JOIN duties AS trade_duty ON (dtr.trade_duty_id = trade_duty.id)
            LEFT JOIN duties AS exchange_duty ON (dtr.exchange_with_duty_id = exchange_duty.id)
            LEFT JOIN day AS exchange_duty_day ON (exchange_duty_day.id = exchange_duty.day_id)
            LEFT JOIN ra AS trade_with_ra ON (dtr.trade_with_ra_id = trade_with_ra.id)
        WHERE dtr.res_hall_id = %s
        AND dtr.id = %s;""",
        (authedUser.hall_id(), tradeReqID)
    )

    # Fetch the results
    res = cur.fetchone()

    # If the result is not None, then parse and package the result
    if res is not None:

        # Grab the flagged duty label.
        cur.execute("SELECT duty_flag_label FROM hall_settings WHERE res_hall_id = %s", (authedUser.hall_id(),))

        # Load the query result
        dfl = cur.fetchone()[0]

        # Assemble the return object
        ret = {
            "trDuty": {
                "flagged": res[0],
                "label": dfl
            },
            "exDuty": {
                "date": res[1].strftime("%Y/%m/%d") if res[1] is not None else None,
                "flagged": res[2]
            },
            "tradeReason": res[3]
        }

    else:
        # Set the return result to an empty dictionary
        ret = dict()

    # Return the result to the user.
    return jsonify(ret)


@schedule_bp.route("/api/acceptTradeRequest", methods=["POST"])
@login_required
def acceptTradeRequest():
    # API endpoint that can be used to accept a given duty trade
    #  request. NOTE: Trade requests CANNOT be accepted by users
    #  who are 1) not in the same Res Hall as the requesting user,
    #  and 2) the user who initiated the request themself, or 3)
    #  not the user that is being requested to trade with.
    #
    #  Required Auth Level: None
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     tradeReqID  <int>  -  an integer representing the ID of the
    #                            trade duty request desired.
    #
    #  This method returns an object with the following specifications:
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the trade was accepted successfully
    #      0 : the trade was NOT accepted successfully
    #     -1 : an error occurred during the trade procedure

    # Get the user's information from the database
    authedUser = getAuth()

    try:
        # Load the data from the request json
        data = request.json

        # Get the trade request ID from the request
        tradeReqID = int(data["tradeReqID"])

    except ValueError:
        # If there was an issue, then return an error notification

        # Log the occurrence
        logging.warning("Unable to parse duty trade request ID from getAdditionalTradeInfo API request")

        # Notify the user that there was an error
        return jsonify(stdRet(-1, "Invalid trade request ID"))

    logging.info("Processing Duty Trade Request")

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Get the duty trade request from the DB
    cur.execute(
        """SELECT trader_ra_id, trade_duty_id, trade_with_ra_id, exchange_with_duty_id
        FROM duty_trade_requests
        WHERE id = %s
        AND res_hall_id = %s
        AND status = 0
        AND (trade_with_ra_id = %s OR trade_with_ra_id is NULL);""",
        (tradeReqID, authedUser.hall_id(), authedUser.ra_id())
    )

    # Load the results
    tradeRequest = cur.fetchone()

    # Check to see if we were able to find the desired trade request.
    if tradeRequest is None:
        # This could be because for the following reasons:
        #   - The desired Trade Duty Request ID is not associated with the user's Res Hall
        #   - The user is not able to accept the desired Trade Duty Request ID.
        #   - The desired Trade Duty Request does not have a pending status.
        #   - The desired Trade Duty Request ID does not exist in the DB.

        # Notify the user that we were unable to find the desired Trade Request.
        return jsonify(stdRet(0, "Unable to find Trade Request."))

    # Unpack the query results
    traderID, tradeDutyID, tradeWithRAID, exchangeDutyID = tradeRequest

    # Check to ensure that we either have both a trade with RA and exchange duty or neither
    if (tradeWithRAID is None and exchangeDutyID is not None) or \
            (tradeWithRAID is not None and exchangeDutyID is None):
        # If we get here, then there appears to be a data integrity error.

        # Log the occurrence
        logging.warning("Trade Duty Request {} appears to be missing key values.".format(tradeReqID))

        # Notify the user that we ran into an issue
        return jsonify(stdRet(-1, "Unable to handle request, please try again later."))

    # Check to see if there is a duty/RA to exchange with
    if tradeWithRAID is not None and exchangeDutyID is not None:
        # There is a duty to exchange with-- adjust both duties as needed.

        try:
            # Assign the tradeWithRA to the tradeDuty
            cur.execute("UPDATE duties SET ra_id = %s WHERE id = %s;", (tradeWithRAID, tradeDutyID))

            # Assign the trader to the exchangeDuty
            cur.execute("UPDATE duties SET ra_id = %s WHERE id = %s;", (traderID, exchangeDutyID))

            # Commit the changes to the DB.
            ag.conn.commit()

        except Error as e:
            # An error was encountered while trying to update the duty.

            # Log the occurrence
            logging.exception(
                "PSQL error encountered while trading duties with exchanging: {}, {}".format(e.pgcode, e.pgerror)
            )

            # Rollback the commit
            ag.conn.rollback()

            # Notify the user that there was an error
            return jsonify(stdRet(-1, "Unable to handle request, please try again later."))

    else:
        # There is no duty to exchange with-- let the user accept the duty.

        try:
            # Update the existing duty record to point to the new RA.
            cur.execute("UPDATE duties SET ra_id = %s WHERE id = %s;", (authedUser.ra_id(), tradeReqID))
            # Commit the change to the DB.
            ag.conn.commit()

        except Error as e:
            # An error was encountered while trying to update the duty.

            # Log the occurrence
            logging.exception(
                "PSQL error encountered while trading duties without exchanging: {}, {}".format(e.pgcode, e.pgerror)
            )

            # Rollback the commit
            ag.conn.rollback()

            # Notify the user that there was an error
            return jsonify(stdRet(-1, "Unable to handle request, please try again later."))

    try:

        # Mark the trade duty request as complete
        cur.execute("UPDATE duty_trade_requests SET status = 1 WHERE id = %s", (tradeReqID, ))

        # Commit the change to the DB
        ag.conn.commit()

    except Error as e:
        # An error was encountered while trying to update the duty trade request

        # Log the occurrence
        logging.exception(
            "PSQL error encountered while trading duties without exchanging: {}, {}".format(e.pgcode, e.pgerror)
        )

        # Rollback the commit
        ag.conn.rollback()

        # Notify the user that there was an error
        return jsonify(stdRet(-1, "Unable to handle request, please try again later."))

    logging.info("Finished Duty Trade Processing")

    # Notify the user that the trade was successful
    return jsonify(stdRet(1, "successful"))
