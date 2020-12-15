from flask import render_template, request, jsonify, Blueprint
from flask_login import login_required
import logging

# Import the appGlobals for this blueprint to use
import appGlobals as ag

# Import the needed functions from other parts of the application
from helperFunctions.helperFunctions import getAuth, stdRet

# Create the blueprint representing these routes
conflicts_bp = Blueprint("conflicts_bp", __name__,
                         template_folder="templates",
                         static_folder="static")

# ---------------------
# --      Views      --
# ---------------------

@conflicts_bp.route("/")
def conflicts():
    # The landing page for this blueprint that will render a calendar
    #  which displays the user's duty conflicts for the given month. The
    #  user can also interact with this calendar to add and remove duty
    #  conflicts for themselves.
    #
    #  Required Auth Level: None

    # Authenticate the user against the DB
    userDict = getAuth()

    # Render and return the appropriate template.
    return render_template("conflicts/conflicts.html", auth_level=userDict["auth_level"], curView=2,
                           opts=ag.baseOpts, hall_name=userDict["hall_name"])


@conflicts_bp.route("/editCons")
@login_required
def editCons():
    # An additional view for this blueprint that will render a calendar
    #  which displays all of the duty conflicts entered for the user's
    #  Res Hall.
    #
    #  Required Auth Level: >= AHD

    # Authenticate the user against the DB
    userDict = getAuth()

    # If the user is not at least an AHD
    if userDict["auth_level"] < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to reach Edit Conflicts page for Hall: {}"
                     .format(userDict["ra_id"], userDict["hall_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Create a DB Cursor
    cur = ag.conn.cursor()

    # Query the database for a list of all of the RAs for the user's staff.
    cur.execute("SELECT id, first_name, last_name, color FROM ra WHERE hall_id = %s ORDER BY first_name ASC;",
                (userDict["hall_id"],))

    # Render and return the appropriate template.
    return render_template("conflicts/editCons.html", raList=cur.fetchall(), auth_level=userDict["auth_level"],
                           curView=3, opts=ag.baseOpts, hall_name=userDict["hall_name"])


# ---------------------
# --   API Methods   --
# ---------------------

@conflicts_bp.route("/api/getConflicts", methods=["GET"])
@login_required
def getConflicts(monthNum=None, raID=None, year=None, hallId=None):
    # API Method used to return the requested conflicts for a given user and month.
    #
    #  Required Auth Level: None
    #
    #  If called from the server, this function accepts the following parameters:
    #
    #     monthNum  <int>  -  an integer representing the numeric month number for
    #                          the desired month using the standard gregorian
    #                          calendar convention.
    #     raID      <int>  -  an integer denoting the row id for the desired RA in the
    #                          ra table.
    #     year      <int>  -  an integer denoting the year for the desired time period
    #                          using the standard gregorian calendar convention.
    #     hallId    <int>  -  an integer representing the id of the desired residence
    #                          hall in the res_hall table.
    #
    #  If called from a client, the following parameters are required:
    #
    #     monthNum  <int>  -  an integer representing the numeric month number for
    #                          the desired month using the standard gregorian
    #                          calendar convention.
    #     year      <int>  -  an integer denoting the year for the desired time period
    #                          using the standard gregorian calendar convention.
    #
    #  This method returns an object with the following specifications:
    #
    #     {
    #        conflicts: [
    #           <Datetime object 1 for which the RA has a conflict>,
    #           <Datetime object 2 for which the RA has a conflict>,
    #           ...
    #        ]
    #     }

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if monthNum is None and year is None and hallId is None and raID is None:
        # If monthNum, year, HallId and raID are None, then this method
        #  was called from a remote client.

        # Get the user's information from the database
        userDict = getAuth()

        # Get the monthNum and year from the request arguments
        monthNum = int(request.args.get("monthNum"))
        year = int(request.args.get("year"))

        # Set the value of hallId and raID from the userDict
        hallId = userDict["hall_id"]
        raID = userDict["ra_id"]

        # Mark that this method was not called from the server
        fromServer = False

    logging.debug("Get Conflicts - From Server: {}".format(fromServer))

    logging.debug("MonthNum: {}, Year: {}, HallID: {}, raID: {}".format(monthNum, year, hallId, raID))

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the month that matches the provided monthNum and year
    cur.execute("SELECT id FROM month WHERE num = %s AND EXTRACT(YEAR FROM year) = %s", (monthNum, year))

    # Load the result from the DB
    monthID = cur.fetchone()

    # Check to see if we did not find a result
    if monthID is None:
        # If monthID is None, then we were unable to locate the desired month in the DB

        # Log the occurrence.
        logging.warning("No month found with Num = {} and Year = {}".format(monthNum, year))

        # Simply return an empty list
        return jsonify({"conflicts": []})

    else:
        # Otherwise extract the monthID from the query result
        monthID = monthID[0]

    # Query the DB to find all of the user's duty conflicts.
    cur.execute("""SELECT TO_CHAR(day.date, 'YYYY-MM-DD')
                   FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                   WHERE conflicts.ra_id = %s
                   AND day.month_id = %s""", (raID, monthID))

    # Iterate through the query result and begin for form
    #  the return object in the format specified in the
    #  comment at the top of this method.
    ret = [d[0] for d in cur.fetchall()]

    # If this API method was called from the server
    if fromServer:
        # Then return the result as-is
        return ret

    else:
        # Otherwise return a JSON version of the result
        return jsonify({"conflicts": ret})


@conflicts_bp.route("/api/getRAConflicts", methods=["GET"])
@login_required
def getRAConflicts():
    # API Method used to return all conflicts for a given ra. If an raID of -1
    #  is specified, then the result will include conflicts for all RA's on the
    #  user's staff.
    #
    #  Required Auth Level: None
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     monthNum  <int>  -  an integer representing the numeric month number for
    #                          the desired month using the standard gregorian
    #                          calendar convention.
    #     year      <int>  -  an integer denoting the year for the desired time period
    #                          using the standard gregorian calendar convention.
    #     raID      <int>  -  an integer denoting the row id for the RA in the
    #                          ra table whose conflicts should be returned.
    #                          If a value of -1 is passed, then all conflicts for the
    #                          user's staff will be returned.
    #
    #  This method returns an object with the following specifications:
    #
    #     [
    #        {
    #           "id": <conflict.id>,
    #           "title": <ra.first_name + " " + ra.last_name>,
    #           "start": <string value of day.date associated with the duty conflict>,
    #           "color": <ra.color>
    #        },
    #        ...
    #     ]

    # Get the user's info from our database
    userDict = getAuth()

    # Currently, there is no auth_level requirement for this method.
    # # If the user is not at least an AHD
    # if userDict["auth_level"] < 2:
    #     # Then they are not permitted to see this view.
    #
    #     # Log the occurrence.
    #     logging.info("User Not Authorized - RA: {} attempted to view staff conflicts for Hall: {}"
    #                  .format(userDict["ra_id"], userDict["hall_id"]))
    #
    #     # Notify the user that they are not authorized.
    #     return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Set the value of hallId from the userDict
    hallId = userDict["hall_id"]

    # Get the raID, monthNum, and year from the request arguments
    raId = request.args.get("raID")
    monthNum = request.args.get("monthNum")
    year = request.args.get("year")

    logging.debug("HallId: {}".format(hallId))
    logging.debug("RaId: {}".format(raId))
    logging.debug("MonthNum: {}".format(monthNum))
    logging.debug("Year: {}".format(year))
    logging.debug("RaId == -1? {}".format(int(raId) != -1))

    # Check to see if the raId has been specified
    if int(raId) != -1:
        # If an raId has been provided, then create an additional
        #  clause that will be appended to a later PSQL statement
        addStr = "AND conflicts.ra_id = {};".format(raId)

    else:
        # Otherwise, create an empty string to replace the additional
        #  PSQL clause.
        addStr = ""

    logging.debug(addStr)

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB to retrieve the month.id associated with the provided monthNum and year
    cur.execute("SELECT id FROM month WHERE num = %s AND EXTRACT(YEAR FROM year) = %s",
                (monthNum, year))

    # Load the result from the query
    monthID = cur.fetchone()

    # Check to see if the query result is None
    if monthID is None:
        # If the monthID is None, then we were unable to find a month in the DB
        #  that had the provided monthNum and year.
        logging.warning("No month found with Num = {} and Year = {}".format(monthNum, year))

        # Notify the client of this issue.
        return jsonify(stdRet(-1, "No month found with Num = {} and Year = {}".format(monthNum, year)))

    else:
        # Otherwise extract the month id value from the query result.
        monthID = monthID[0]

    # Query the DB for the conflicts for the given month and append the additional clause generated above.
    cur.execute("""SELECT conflicts.id, ra.first_name, ra.last_name, TO_CHAR(day.date, 'YYYY-MM-DD'), ra.color
                   FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                                  JOIN ra ON (ra.id = conflicts.ra_id)
                   WHERE day.month_id = %s
                   AND ra.hall_id = %s
                   {};""".format(addStr), (monthID, hallId))

    # Load the results from the query.
    conDates = cur.fetchall()

    logging.debug("ConDates: {}".format(conDates))

    # Create the result object to be returned
    res = []

    # Iterate through the conDates from the DB and assemble the return result
    #  in the format outlined in the comments at the top of this method.
    for d in conDates:
        res.append({
            "id": d[0],
            "title": d[1] + " " + d[2],
            "start": d[3],
            "color": d[4]
        })

    # Return the conflict result to the client
    return jsonify(res)


@conflicts_bp.route("/api/getStaffConflicts", methods=["GET"])
@login_required
def getRACons(hallId=None, startDateStr=None, endDateStr=None):
    # API Method used to return all duty conflicts for each RA that is part of
    #  the given Res Hall staff.
    #
    #  Required Auth Level: >= AHD
    #
    #  If called from the server, this function accepts the following parameters:
    #
    #     monthNum  <int>  -  an integer representing the numeric month number for
    #                          the desired month using the standard gregorian
    #                          calendar convention.
    #     raID      <int>  -  an integer denoting the row id for the desired RA in the
    #                          ra table.
    #     year      <int>  -  an integer denoting the year for the desired time period
    #                          using the standard gregorian calendar convention.
    #     hallId    <int>  -  an integer representing the id of the desired residence
    #                          hall in the res_hall table.
    #
    #  If called from a client, the following parameters are required:
    #
    #     start      <str>  -  a string representing the first day that should be included
    #                           for the returned RA conflicts.
    #     end        <str>  -  a string representing the last day that should be included
    #                           for the returned RA conflicts.
    #
    #  This method returns an object with the following specifications:
    #
    #     [
    #        {
    #           "id": <ra.id>,
    #           "title": <ra.first_name + " " + ra.last_name>,
    #           "start": <string value of day.date associated with the duty conflict>,
    #           "color": <ra.color>,
    #        },
    #        ...
    #     ]

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if hallId is None and startDateStr is None and endDateStr is None:
        # If the hallId, startDateStr, and endDateStr are None, then
        #  this method was called from a remote client.

        # Get the user's information from the database
        userDict = getAuth()

        # If the user is not at least an AHD
        if userDict["auth_level"] < 2:
            # Then they are not permitted to see this view.

            # Log the occurrence.
            logging.info("User Not Authorized - RA: {} attempted to view staff conflicts for Hall: {}"
                         .format(userDict["ra_id"], userDict["hall_id"]))

            # Notify the user that they are not authorized.
            return jsonify(stdRet(-1, "NOT AUTHORIZED"))

        # Set the value of hallId from the userDict
        hallId = userDict["hall_id"]

        # Get the start and end string values from the request arguments.
        #  Since we utilize the fullCal.js library, we know that the request
        #  also contains timezone information that we do not care about in
        #  this method. As a result, the timezone information is split out
        #  immediately.
        startDateStr = request.args.get("start").split("T")[0]
        endDateStr = request.args.get("end").split("T")[0]

        # Mark that this method was not called from the server
        fromServer = False

    logging.debug("Get Staff Conflicts - From Server: {}".format(fromServer))

    # Create the result object to be returned
    res = []

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for all of the RA duty conflicts for the requested staff.
    cur.execute("""
        SELECT ra.id, ra.first_name, ra.last_name, ra.color, TO_CHAR(day.date, 'YYYY-MM-DD')
        FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                       JOIN ra ON (conflicts.ra_id = ra.id)
        WHERE day.date >= TO_DATE(%s, 'YYYY-MM-DD')
        AND day.date <= TO_DATE(%s, 'YYYY-MM-DD')
        AND ra.hall_ID = %s;
    """, (startDateStr, endDateStr, hallId))

    # Load the result from the DB
    rawRes = cur.fetchall()

    # Iterate through the rawRes from the DB and assemble the return result
    #  in the format outlined in the comments at the top of this method.
    for row in rawRes:
        res.append({
            "id": row[0],
            "title": row[1] + " " + row[2],
            "start": row[4],
            "color": row[3]
        })

    # If this API method was called from the server
    if fromServer:
        # Then return the result as-is
        return rawRes

    else:
        # Otherwise return a JSON version of the result
        return jsonify(res)


@conflicts_bp.route("/api/getConflictNums", methods=["GET"])
@login_required
def getNumberConflicts(hallId=None, monthNum=None, year=None):
    # API Method used to return a count of the number of conflicts each RA
    #  has submitted for a given month and Res Hall.
    #
    #  Required Auth Level: >= AHD
    #
    #  If called from the server, this function accepts the following parameters:
    #
    #     hallId    <int>  -  an integer representing the id of the desired residence
    #                          hall in the res_hall table.
    #     monthNum  <int>  -  an integer representing the numeric month number for
    #                          the desired month using the standard gregorian
    #                          calendar convention.
    #     year      <int>  -  an integer denoting the year for the desired time period
    #                          using the standard gregorian calendar convention.
    #
    #  If called from a client, the following parameters are required:
    #
    #     monthNum  <int>  -  an integer representing the numeric month number for
    #                          the desired month using the standard gregorian
    #                          calendar convention.
    #     year      <int>  -  an integer denoting the year for the desired time period
    #                          using the standard gregorian calendar convention.
    #
    #  This method returns an object with the following specifications:
    #
    #     {
    #        <ra.id 1> : <number of conflicts for the given timeframe>,
    #        <ra.id 2> : <number of conflicts for the given timeframe>,
    #        ...
    #     }

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if hallId is None and monthNum is None and year is None:
        # If the HallId, monthNum and year are None, then
        #  this method was called from a remote client.

        # Get the user's information from the database
        userDict = getAuth()

        # If the user is not at least an AHD
        if userDict["auth_level"] < 2:
            # Then they are not permitted to see this view.

            # Log the occurrence.
            logging.info("User Not Authorized - RA: {} attempted to view staff conflicts numbers for Hall: {}"
                         .format(userDict["ra_id"], userDict["hall_id"]))

            # Notify the user that they are not authorized.
            return jsonify(stdRet(-1, "NOT AUTHORIZED"))

        # Set the value of the hallId from the userDict
        hallId = userDict["hall_id"]

        # Get the value for monthNum and year from the request arguments.
        monthNum = request.args.get("monthNum")
        year = request.args.get("year")

        # Mark that this method was not called from the server
        fromServer = False

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB to retrieve the counts of duty conflicts for each
    #  staff member associated with the provided Res Hall.
    cur.execute("""
        SELECT ra.id, COUNT(cons.id)
        FROM ra LEFT JOIN (
            SELECT conflicts.id, ra_id
            FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                           JOIN month ON (month.id = day.month_id)
            WHERE month.num = %s
            AND EXTRACT(YEAR FROM month.year) = %s
        ) AS cons ON (cons.ra_id = ra.id)
        WHERE ra.hall_id = %s
        GROUP BY ra.id;
    """, (monthNum, year, hallId))

    # Create the result object to be returned
    res = {}

    # Iterate through the query result and assemble the return result
    #  in the format outlined in the comments at the top of this method.
    for row in cur.fetchall():
        res[row[0]] = row[1]

    # Close the DB cursor
    cur.close()

    # If this API method was called from the server
    if fromServer:
        # Then return the result as-is
        return res

    else:
        # Otherwise, return a JSON version of the result
        return jsonify(res)


@conflicts_bp.route("/api/enterConflicts/", methods=['POST'])
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

    cur = ag.conn.cursor()

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

    cur = ag.conn.cursor()
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

    ag.conn.commit()
    cur.close()
    return jsonify(stdRet(1,"successful"))                                          # Send the user back to the main page (Not utilized by client currently)
