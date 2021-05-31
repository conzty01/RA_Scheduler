import pika
import psycopg2
from schedule import scheduler4_1
import copy as cp
import logging
import calendar
from schedule.ra_sched import RA
import os
from logging.config import dictConfig
from json import loads, dumps, JSONDecodeError
from scheduleServer import app
import atexit


# import the needed functions from other parts of the application
from helperFunctions.helperFunctions import getSchoolYear
from staff.staff import getRAStats, addRAPointModifier


# Connect to RabbitMQ and PostgreSQL

# Load configuration variables from the environment with fallback values
rabbitSchedulerQueue = os.environ.get('RABBITMQ_SCHEDULER_QUEUE', 'genSched')
rabbitSchedulerErrorQueue = os.environ.get('RABBITMQ_SCHEDULER_FAILURE_QUEUE', 'genSchedErrs')
rabbitSchedulerQueueLimit = int(os.environ.get('RABBITMQ_SCHEDULER_QUEUE_LIMIT', '1'))
psqlConnectionStr = os.environ.get('DATABASE_URL', 'postgres:///ra_sched')
rabbitConnectionStr = os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost:5672/%2f')

# Establish DB connection
dbConn = psycopg2.connect(psqlConnectionStr)

# Parse the URL parameters from the connection url
params = pika.URLParameters(rabbitConnectionStr)

# Create a blocking connection with the parsed parameters
rabbitConn = pika.BlockingConnection(params)

# Configure the app so that we can use parts of it from this worker process.

# Disable the login_required decorator
app.config["LOGIN_DISABLED"] = True
# Reinitialize the Login Manager to accept the new configuration
app.login_manager.init_app(app)


def startup():
    # Start up the worker process and begin consuming RabbitMQ messages.

    logging.info("Connecting to '{}' message queue channel.".format(rabbitSchedulerQueue))

    # Start a channel
    channel = rabbitConn.channel()

    # Connect to the genSched queue
    channel.queue_declare(queue=rabbitSchedulerQueue)

    # Connect to the durable genSchedFailures queue
    channel.queue_declare(
        queue=rabbitSchedulerErrorQueue,
        durable=True
    )

    # Set the runScheduler as the callback function to consume messages
    channel.basic_consume(
        rabbitSchedulerQueue,
        parseMessage
    )

    # Configure the channel so that RabbitMQ does not send a given worker process
    #  more than 'rabbitSchedulerQueueLimit' number of messages at a time.
    #  https://www.rabbitmq.com/tutorials/tutorial-two-python.html
    channel.basic_qos(
        prefetch_count=rabbitSchedulerQueueLimit
    )

    logging.info("Begin consuming messages from '{}'".format(rabbitSchedulerQueue))

    # Start consuming
    channel.start_consuming()


def teardown():
    # Close the necessary connections and clean up after ourselves
    dbConn.close()
    rabbitConn.close()


def parseMessage(ch, method, properties, body):
    # Parse the received rabbitMQ message for the information needed to
    #  run the scheduler.
    #
    #  This function accepts the following parameters:
    #
    #     channel       <pika.channel.Channel>      -  The channel which the message was received from.
    #     method        <pika.spec.Basic.Deliver>   -  The method used to retrieve the message.
    #     properties    <pika.spec.BasicProperties> -  Metadata about the message. We expect to have a
    #                                                   header with key "sqid" which is the id of the
    #                                                   corresponding record in the scheduler_queue
    #                                                   table.
    #     body          <bytes>                     -  A bytes array containing the received message.
    #      |
    #      |- resHallID         <int>
    #      |- monthNum          <int>
    #      |- year              <int>
    #      |- eligibleRAList    <lst<int>>
    #      |- noDutyList        <lst<int>>

    logging.info("Message Received.")

    # Convert the body from a bytes array to a string
    strBody = body.decode("utf-8")

    # Set the default state to NOT run the scheduler
    clearToRunScheduler = False

    # Set the default state to update the scheduler_queue record
    updateSQRecord = True

    # Create a default status and reason in case weird things happen.
    #  These should be overridden by the end of processing this message.
    status = -99
    reason = ""

    # Attempt to parse the body into a JSON object
    try:
        # Grab the Scheduler_Queue ID
        msgSQID = properties.headers["sqid"]

        # Parse the json from the body
        parsedParams = loads(strBody)

        # With all of the necessary information, we can run the scheduler
        clearToRunScheduler = True

    except (TypeError, KeyError):
        # If we receive a KeyError, then that means we could not find the
        #  expected "sqid" header.

        # Log the occurrence
        logging.exception("Received message from '{}' with no 'sqid' header.".format(rabbitSchedulerQueue))

        # Since the SQID is the only way for us to know what record in the DB
        #  is associated with this message, and we were unable to get the SQID,
        #  then send this message to the error queue with a sqid of -1.
        forwardMsgToErrorQueue(
            ch,
            "Received message from '{}' with no 'sqid' header.".format(rabbitSchedulerQueue),
            strBody,
            -1
        )

        # Set the state to NOT update the scheduler_queue record since we don't have a SQID
        updateSQRecord = False

    except JSONDecodeError:
        # If we receive a JSONDecodeError, then consider the message to be
        #  invalid for one reason or another.

        # Log the occurrence
        logging.exception("Unable to decode message body into JSON for SQID: {}".format(msgSQID))

        # Update the status and reason to reflect what occurred here.
        status = -2
        reason = "Unable to parse scheduler request."

        # Forward the message to the Error Queue where it can be looked into in further detail.
        forwardMsgToErrorQueue(
            ch,
            "Unable to decode message body into JSON for SQID: {}".format(rabbitSchedulerQueue),
            strBody,
            msgSQID
        )

    # If we have been cleared to run the scheduler...
    if clearToRunScheduler:
        # Then do so!
        status, reason = runScheduler(**parsedParams)

    # If we should update the scheduler_queue record with these results
    if updateSQRecord:
        # Update the status and reason of the corresponding scheduler_queue record
        cur = dbConn.cursor()
        cur.execute("""
            UPDATE scheduler_queue
            SET status = %s,
                reason = %s
            WHERE id = %s
        """, (status, reason, msgSQID))
        dbConn.commit()
        cur.close()


    # Acknowledge that we have received and handled the message.
    ch.basic_ack(delivery_tag=method.delivery_tag)

    logging.info("Message Processing Complete.")


def forwardMsgToErrorQueue(ch, reason, forwardedMsg, sqid):
    # Forward the provided message to the error queue for future review.

    # Create the message body
    msgBody = {
        "failure_reason": reason,
        "forwarded_message_body": forwardedMsg
    }

    # Queue up the Error message.
    ch.basic_publish(
        exchange="",
        routing_key=rabbitSchedulerErrorQueue,
        # Convert the msgBody to a JSON string and encode it in a byte array for pika
        body=bytes(dumps(msgBody), "utf-8"),
        properties=pika.BasicProperties(
            headers={"sqid": sqid},
            # Make the message persistent
            delivery_mode=2
        )
    )

    logging.info("Forwarded message to '{}' failure queue.".format(rabbitSchedulerErrorQueue))


def runScheduler(resHallID, monthNum, year, noDutyList, eligibleRAList):
    # Run the duty scheduler for the given Res Hall and month. Any users associated with the staff
    #  that have an auth_level of HD will NOT be scheduled.
    #
    #  When called, the following parameters are required:
    #
    #     resHallID       <int>  -  an integer representing the res_hall.id of the Res Hall
    #                                that the scheduler should be run for.
    #     monthNum        <int>  -  an integer representing the numeric month number for
    #                                the desired month using the standard gregorian
    #                                calendar convention.
    #     year            <int>  -  an integer denoting the year for the desired time period
    #                                using the standard gregorian calendar convention.
    #     noDutyList      <str>  -  a string containing comma separated integers that represent
    #                                a date in the month in which no duty should be scheduled.
    #                                If set to an empty string, then all days in the month will
    #                                be scheduled.
    #     eligibleRAList  <str>  -  a string containing comma separated integers that represent
    #                                the ra.id for all RAs that should be considered for duties.
    #                                If set to an empty string, then all ras with an auth_level
    #                                of less than HD will be scheduled.
    #     requestID       <int>  -  an integer representing the scheduler_queue.id for the
    #                                corresponding request record in the DB.
    #
    #  This method returns the following items:
    #
    #      status  <int>  -  an integer denoting what the result of the schedule process was.
    #        |
    #        |-   1 : the duty scheduling was successful
    #        |-  -1 : the duty scheduling was unsuccessful
    #        |-  -2 : an error occurred while scheduling
    #
    #      reason  <str>  -  a string containing a brief explanation of why the result occurred.

    # Check to see if values have been passed through the
    #  eligibeRAs parameter
    if len(eligibleRAList) != 0:
        # Create a formatted psql string to add to the query that loads
        #  the necessary information from the DB
        eligibleRAStr = "AND ra.id IN ({});".format(str(eligibleRAList)[1:-1])

    else:
        # Otherwise if there are no values passed in eligibleRAs, then
        # set eligibleRAStr to ";" to end the query string
        eligibleRAStr = ";"

    # Create a DB cursor
    cur = dbConn.cursor()

    # Query the DB for the given month
    cur.execute("SELECT id, year FROM month WHERE num = %s AND EXTRACT(YEAR FROM year) = %s",
                (monthNum, year))

    # Load the results from the DB
    monthRes = cur.fetchone()

    # Check to see if the query returned a result
    if monthRes is None:
        # If not, then log the occurrence
        logging.warning("Unable to find month {}/{} in DB.".format(monthNum, year))

        # Return the appropriate status and reason
        return -1, "Unable to find month {}/{} in DB.".format(monthNum, year)

    else:
        # Otherwise, unpack the monthRes into monthId and year
        monthId, date = monthRes

    logging.debug("MonthId: {}".format(monthId))

    # -- Get all eligible RAs and their conflicts --

    # Query the DB for all of the eligible RAs for a given hall, and their
    #  conflicts for the given month excluding any ra table records with
    #  an auth_level of 3 or higher.
    cur.execute("""
        SELECT ra.first_name, ra.last_name, ra.id, sm.res_hall_id, sm.start_date,
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
        JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE sm.res_hall_id = %s
        AND sm.auth_level < 3 {}
    """.format(eligibleRAStr), (monthId, resHallID))

    # Load the result from the DB
    partialRAList = cur.fetchall()

    # Get the start date for the school year. This will be used
    #  to calculate how many points each RA has up to the month
    #  being scheduled.
    start, _ = getSchoolYear(date.month, date.year)

    # Get the end from the DB. The end date will be the first day
    #  of the month being scheduled. This will prevent the scheduler
    #  from using the number of points an RA had during a previous
    #  run of the scheduler for this month.
    cur.execute("SELECT year FROM month WHERE id = %s", (monthId,))

    # Load the value from the DB and convert it to a string in the expected format
    end = cur.fetchone()[0].isoformat()

    # Get the number of days in the given month
    _, dateNum = calendar.monthrange(date.year, date.month)

    # Calculate and format maxBreakDay which is the latest break duty that should be
    #  included for the duty points calculation.
    maxBreakDuty = "{:04d}-{:02d}-{:02d}".format(date.year, date.month, dateNum)

    with app.test_request_context():
        # Get the RA statistics for the given hall within the flask app context
        ptsDict = getRAStats(resHallID, start, end, maxBreakDay=maxBreakDuty)

    logging.debug("ptsDict: {}".format(ptsDict))

    # Assemble the RA list with RA objects that have the individual RAs' information
    ra_list = []
    for res in partialRAList:
        # Add up the RA's duty points and any point modifier
        pts = ptsDict[res[2]]["pts"]["dutyPts"] + ptsDict[res[2]]["pts"]["modPts"]

        # Parse out the date information since we only use the day in this implementation
        parsedConflictDays = [dateObject.day for dateObject in res[5]]

        # Append the newly created RA to the ra_list
        ra_list.append(
            RA(
                res[0],                 # First Name
                res[1],                 # Last Name
                res[2],                 # RA ID
                res[3],                 # Hall ID
                res[4],                 # Start Date
                parsedConflictDays,     # Conflicts
                pts                     # Points
            )
        )

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
    logging.debug("Hall Id: {}".format(resHallID))
    logging.debug("Year: {}".format(date.year))
    logging.debug('MonthNum: {0:02d}'.format(monthNum))
    logging.debug("LDAT: {}".format(ldat))

    # Query the DB for the last 'x' number of duties from the previous month so that we
    #  do not schedule RAs back-to-back between months.
    cur.execute("""SELECT ra.first_name, ra.last_name, ra.id, sm.res_hall_id,
                          sm.start_date, day.date - TO_DATE(%s, 'YYYY-MM-DD'),
                          duties.flagged
                  FROM duties JOIN day ON (day.id=duties.day_id)
                              JOIN ra ON (ra.id=duties.ra_id)
                              JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
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
    """, (endMonthStr + "-01", resHallID, resHallID, startMonthStr, endMonthStr,
          endMonthStr + "-01", ldat, endMonthStr + "-01"))

    # Load the query results from the DB
    prevDuties = cur.fetchall()

    # Create shell RA objects that will hash to the same value as their respective RA objects.
    #  This hash is how we map the equivalent RA objects together. These shell RAs will be put
    #  in a tuple containing the RA, the number of days from the duty date to the beginning of
    #  the next month, and a boolean whether or not that duty was flagged.
    #     Ex: (RA Shell, No. days since last duty, Whether the duty is flagged)
    prevRADuties = [(RA(d[0], d[1], d[2], d[3], d[4]), d[5], d[6]) for d in prevDuties]

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
    """.format(monthId, resHallID))

    # Load the results from the DB and convert the value to an int.
    breakDuties = [int(row[0]) for row in cur.fetchall()]
    logging.debug("Break Duties: {}".format(breakDuties))

    # Attempt to run the scheduler using deep copies of the raList and noDutyList.
    #  This is so that if the scheduler does not resolve on the first run, we
    #  can modify the parameters and try again with a fresh copy of the raList
    #  and noDutyList.
    copy_raList = cp.deepcopy(ra_list)
    copy_noDutyList = cp.copy(noDutyList)

    # Load the Res Hall's settings for the scheduler
    cur.execute("""SELECT duty_config, auto_adj_excl_ra_pts, flag_multi_duty 
                   FROM hall_settings
                   WHERE res_hall_id = %s""", (resHallID,))
    dutyConfig, autoExcAdj, flagMultiDuty = cur.fetchone()

    # AutoExcAdj is a currently unused feature that allows the scheduler to
    #  automatically create point_modifiers for RAs that have been excluded from
    #  being scheduled for the given month. This feature is unreleased because
    #  if the user sets this to true and then runs the scheduler more than once
    #  for the same month, there is no way for the application to know if it
    #  created any point_modifiers for the excluded RAs of the previous run so
    #  that it can remove them from the system/algorithm. As a result, any
    #  point_modifiers created in this manner will just grow and grow until
    #  an HD goes in and manually alters the point_modifier.modifier value.
    # TODO: Figure out how to address the above comment. Possibly implement a
    #        draft system so that AHD+ users can view a scheduler run before
    #        publishing it to the rest of staff?

    regNumAssigned = dutyConfig["reg_duty_num_assigned"]
    mulNumAssigned = dutyConfig["multi_duty_num_assigned"]
    regDutyPts = dutyConfig["reg_duty_pts"]
    mulDutyPts = dutyConfig["multi_duty_pts"]
    mulDutyDays = dutyConfig["multi_duty_days"]

    # Set completed to False and successful to False by default. These values
    #  will be manipulated in the while loop below as necessary.
    completed = False
    successful = False
    while not completed:
        # While we are not finished scheduling, create a candidate schedule
        sched = scheduler4_1.schedule(copy_raList, year, monthNum, doubleDateNum=mulNumAssigned,
                                      doubleDatePts=mulDutyPts, noDutyDates=copy_noDutyList,
                                      doubleDays=mulDutyDays, doublePts=mulDutyPts,
                                      ldaTolerance=ldat, doubleNum=mulNumAssigned,
                                      prevDuties=prevRADuties, breakDuties=breakDuties,
                                      setDDFlag=flagMultiDuty, regDutyPts=regDutyPts,
                                      regNumAssigned=regNumAssigned)

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
                     .format(resHallID, monthNum, year))

        # Notify the user of this result
        return -1, "Unable to Generate Schedule."

    # Add a record to the schedule table in the DB get its ID
    cur.execute("INSERT INTO schedule (hall_id, month_id, created) VALUES (%s, %s, NOW()) RETURNING id;",
                (resHallID, monthId))

    # Load the query result
    schedId = cur.fetchone()[0]

    # Commit the changes to the DB
    dbConn.commit()

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

    # Create a dictionary to add up all of the averages
    avgPtDict = {}

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
            for s in d.iterDutySlots():
                # Retrieve the RA object that is assigned to this duty slot
                r = s.getAssignment()

                # Add the necessary information to the dutyDayStr
                dutyDayStr += "({},{},{},{},{},{}),".format(resHallID, r.getId(), days[d.getDate()],
                                                            schedId, d.getPoints(), s.getFlag())

                # Check to see if the RA has already been added to the dictionary
                if r in avgPtDict.keys():
                    # If so, add the points to the dict
                    avgPtDict[r.getId()] += d.getPoints()
                else:
                    # Otherwise, initialize the RA's entry with this day's points.
                    avgPtDict[r.getId()] = d.getPoints()

        else:
            # Otherwise, if there are no RAs assigned for duty on this day,
            #  then add the day to the noDutyDayStr
            noDutyDayStr += "({},{},{},{}),".format(resHallID, days[d.getDate()], schedId, d.getPoints())

    # Attempt to save the schedule to the DBgit s
    try:
        # If there were days added to the dutyDayStr
        if dutyDayStr != "":
            # Then insert all of the duties that were scheduled for the month into the DB
            cur.execute("""
            INSERT INTO duties (hall_id, ra_id, day_id, sched_id, point_val, flagged) 
            VALUES {};
            """.format(dutyDayStr[:-1]))

        # If there were days added to the noDutyDayStr
        if noDutyDayStr != "":
            # Then insert all of the blank duty values for days that were not scheduled
            cur.execute("""
                    INSERT INTO duties (hall_id, day_id, sched_id, point_val) VALUES {};
                    """.format(noDutyDayStr[:-1]))

    except psycopg2.IntegrityError:
        # If we encounter an IntegrityError, then that means we attempted to insert a value
        #  into the DB that was already in there.

        # Log the occurrence
        logging.warning(
            "IntegrityError encountered when attempting to save duties for Schedule: {}. Rolling back changes."
                .format(schedId)
        )

        # Rollback the changes to the DB
        dbConn.rollback()

        # Notify the user of this issue.
        return -2, "Unable to Generate Schedule. Please try again later."

    # If autoExcAdj is set, then create adjust the excluded RAs' points
    if autoExcAdj and len(eligibleRAStr) > 1:
        logging.info("Adjusting Excluded RA Point Modifiers")

        # Select all RAs in the given hall whose auth_level is below 3 (HD)
        #  that were not included in the eligibleRAs list
        cur.execute("""
            SELECT ra_id 
            FROM staff_membership 
            WHERE ra_id NOT IN %s 
            AND res_hall_id = %s""", (tuple(eligibleRAList), resHallID))

        raAdjList = cur.fetchall()

        # Calculate the average number of points earned for the month.
        sum = 0
        for ra in avgPtDict.keys():
            sum += avgPtDict[ra]

        # Calculate the average using floor division
        avgPointGain = sum // len(avgPtDict.keys())

        logging.info("Average Point Gain: {} for Schedule: {}".format(avgPointGain, schedId))
        logging.debug("Number of excluded RAs: {}".format(len(raAdjList)))
        # logging.debug(str(avgPtDict))

        # Iterate through the excluded RAs and add point modifiers
        #  to them.
        for ra in raAdjList:
            addRAPointModifier(ra[0], resHallID, avgPointGain)

    # Commit changes to the DB
    dbConn.commit()

    # Close the DB cursor
    cur.close()

    logging.info("Successfully Generated Schedule: {}".format(schedId))

    # Notify the user of the successful schedule generation!
    return 1, "successful"


if __name__ == "__main__":
    atexit.register(teardown)
    startup()
