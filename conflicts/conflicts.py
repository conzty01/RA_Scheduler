from flask import render_template, request, Blueprint, abort
from flask_login import login_required
import logging

# Import the appGlobals for this blueprint to use
import appGlobals as ag

# Import the needed functions from other parts of the application
from helperFunctions.helperFunctions import getAuth, stdRet, getCurSchoolYear, packageReturnObject

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
    authedUser = getAuth()

    # Get the current school year information
    yearStart, yearEnd = getCurSchoolYear(authedUser.hall_id())

    # Create a custom settings dict
    custSettings = {
        "yearStart": yearStart,
        "yearEnd": yearEnd
    }

    # Merge the base options into the custom settings dictionary to simplify passing
    #  settings into the template renderer.
    custSettings.update(ag.baseOpts)

    # Render and return the appropriate template.
    return render_template("conflicts/conflicts.html", auth_level=authedUser.auth_level(), curView=2,
                           opts=custSettings, hall_name=authedUser.hall_name(),
                           linkedHalls=authedUser.getAllAssociatedResHalls())


@conflicts_bp.route("/editCons")
@login_required
def editCons():
    # An additional view for this blueprint that will render a calendar
    #  which displays all of the duty conflicts entered for the user's
    #  Res Hall.
    #
    #  Required Auth Level: >= AHD

    # Authenticate the user against the DB
    authedUser = getAuth()

    # If the user is not at least an AHD
    if authedUser.auth_level() < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to reach Edit Conflicts page for Hall: {}"
                     .format(authedUser.ra_id(), authedUser.hall_id()))

        # Raise an 403 Access Denied HTTP Exception that will be handled by flask
        abort(403)

    # Get the current school year information
    yearStart, yearEnd = getCurSchoolYear(authedUser.hall_id())

    # Create a custom settings dict
    custSettings = {
        "yearStart": yearStart,
        "yearEnd": yearEnd
    }

    # Merge the base options into the custom settings dictionary to simplify passing
    #  settings into the template renderer.
    custSettings.update(ag.baseOpts)

    # Create a DB Cursor
    cur = ag.conn.cursor()

    # Query the database for a list of all of the RAs for the user's staff.
    cur.execute("""
        SELECT ra.id, first_name, last_name, color 
        FROM ra JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE sm.res_hall_id = %s 
        ORDER BY ra.first_name ASC;""", (authedUser.hall_id(),))

    # Render and return the appropriate template.
    return render_template("conflicts/editCons.html", raList=cur.fetchall(), auth_level=authedUser.auth_level(),
                           curView=3, opts=custSettings, hall_name=authedUser.hall_name(),
                           linkedHalls=authedUser.getAllAssociatedResHalls())


# ---------------------
# --   API Methods   --
# ---------------------

@conflicts_bp.route("/api/getUserConflicts", methods=["GET"])
@login_required
def getUserConflicts():
    # API Method used to return the requested conflicts for a given user and month.
    #
    #  Required Auth Level: None
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

    # Get the user's information from the database
    authedUser = getAuth()

    # Get the monthNum and year from the request arguments
    monthNum = int(request.args.get("monthNum"))
    year = int(request.args.get("year"))

    # Set the value of hallId and raID from the userDict
    hallId = authedUser.hall_id()
    raID = authedUser.ra_id()

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

        # Close the DB cursor
        cur.close()

        # Simply return an empty list
        return packageReturnObject({"conflicts": []})

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

    # Close the DB cursor
    cur.close()

    # Otherwise return a JSON version of the result
    return packageReturnObject({"conflicts": ret})


@conflicts_bp.route("/api/getRAConflicts", methods=["GET"])
@login_required
def getRAConflicts(startDateStr=None, endDateStr=None, raID=-1, hallID=None):
    # API Method used to return all conflicts for either a given RA or Res Hall.
    #
    #  Required Auth Level: >= AHD
    #
    #  If called from the server, this function accepts the following parameters:
    #
    #    startDateStr  <str>  -  a string representing the first day that should be included
    #                             for the returned RA conflicts.
    #    endDateStr    <str>  -  a string representing the last day that should be included
    #                             for the returned RA conflicts.
    #    raID          <int>  -  an integer denoting the row id for the RA in the
    #                             ra table whose conflicts should be returned.
    #                             If a value of -1 is passed, then all conflicts for the
    #                             user's staff will be returned.
    #    hallID        <int>  -  an integer denoting the row id for the Res Hall
    #                             in the res_hall table whose staff conflicts should
    #                             be returned.
    #
    #  NOTE: If both the raID and hallID are provided, preference will be given
    #         to the raID with the hallID being used to verify that the user
    #         belongs to the provided Res Hall. If the user does not belong to
    #         the provided hall, then an empty list is returned.
    #
    #  If called from a client, the following parameters are required:
    #
    #     start      <str>  -  a string representing the first day that should be included
    #                           for the returned RA conflicts.
    #     end        <str>  -  a string representing the last day that should be included
    #                           for the returned RA conflicts.
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

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if startDateStr is None and endDateStr is None:
        # If the startDateStr, and endDateStr are None, then
        #  this method was called from a remote client.

        # Get the user's info from our database
        authedUser = getAuth()

        # Mark that the API was called from the client
        fromServer = False

        # If the user is not at least an AHD
        if authedUser.auth_level() < 2:
            # Then they are not permitted to see this view.

            # Log the occurrence.
            logging.info("User Not Authorized - RA: {} attempted to view staff conflicts for Hall: {}"
                         .format(authedUser.ra_id(), authedUser.hall_id()))

            # Notify the user that they are not authorized.
            return packageReturnObject(stdRet(-1, "NOT AUTHORIZED"), fromServer)

        # Set the value of hallId from the userDict
        hallID = authedUser.hall_id()

        try:
            # Attempt to get the raID from the request arguments
            raID = int(request.args.get("raID"))

        except ValueError:
            # If there was an issue, then return an error notification

            # Log the occurrence
            logging.warning("Unable to parse RA ID from getRAConflicts API request")

            # Notify the user of the error
            return packageReturnObject(stdRet(-1, "Invalid RA ID"), fromServer)

        # Get the start and end string values from the request arguments.
        #  Since we utilize the fullCal.js library, we know that the request
        #  also contains timezone information that we do not care about in
        #  this method. As a result, the timezone information is split out
        #  immediately.
        startDateStr = request.args.get("start").split("T")[0]
        endDateStr = request.args.get("end").split("T")[0]

    logging.debug("HallId: {}".format(hallID))
    logging.debug("RaId: {}".format(raID))
    logging.debug("Start Date: {}".format(startDateStr))
    logging.debug("End Date: {}".format(endDateStr))
    logging.debug("RaId == -1? {}".format(int(raID) != -1))

    # Check to see if the raId has been specified
    if int(raID) != -1:
        # If an raID has been provided, then create an additional
        #  clause that will be appended to a later PSQL statement
        addStr = "AND conflicts.ra_id = {}".format(raID)

    else:
        # Otherwise, create an empty string to replace the additional
        #  PSQL clause.
        addStr = ""

    logging.debug(addStr)

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the conflicts for the given month and append the additional clause generated above.
    cur.execute("""
        SELECT conflicts.id, ra.first_name, ra.last_name, TO_CHAR(day.date, 'YYYY-MM-DD'), ra.color
        FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                       JOIN month ON (month.id=day.month_id) 
                       JOIN ra ON (ra.id = conflicts.ra_id)
                       JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE sm.res_hall_id = %s
        AND month.year >= TO_DATE(%s, 'YYYY-MM')
        AND month.year <= TO_DATE(%s, 'YYYY-MM') 
        {};""".format(addStr), (hallID, startDateStr, endDateStr))

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

    # Close the DB Cursor
    cur.close()

    # Return the result
    return packageReturnObject(res, fromServer)


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
        authedUser = getAuth()

        # Mark that this method was not called from the server
        fromServer = False

        # If the user is not at least an AHD
        if authedUser.auth_level() < 2:
            # Then they are not permitted to see this view.

            # Log the occurrence.
            logging.info(
                "User Not Authorized - RA: {} attempted to view staff conflicts numbers for Hall: {}"
                    .format(authedUser.ra_id(), authedUser.hall_id())
            )

            # Notify the user that they are not authorized.
            return packageReturnObject(stdRet(-1, "NOT AUTHORIZED"), fromServer)

        # Set the value of the hallId from the userDict
        hallId = authedUser.hall_id()

        # Get the value for monthNum and year from the request arguments.
        monthNum = request.args.get("monthNum")
        year = request.args.get("year")

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
        JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE sm.res_hall_id  = %s
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

    # Return the results
    return packageReturnObject(res, fromServer)


@conflicts_bp.route("/api/enterConflicts/", methods=['POST'])
@login_required
def processConflicts():
    # API Method used to process and save the client's submitted duty conflicts.
    #
    #  Required Auth Level: None
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     monthNum   <int>       -  an integer representing the numeric month number for
    #                                the desired month using the standard gregorian
    #                                calendar convention.
    #     year       <int>       -  an integer denoting the year for the desired time period
    #                                using the standard gregorian calendar convention.
    #     conflicts  <lst<str>>  -  a list containing strings representing dates that the
    #                                user has a duty conflict with.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the save was successful
    #     -1 : the save was unsuccessful

    logging.debug("Process Conflicts")

    # Get the user's information from the database
    authedUser = getAuth()

    logging.debug(str(request.json))

    # Get the value for monthNum, year, and conflicts from the request arguments.
    monthNum = request.json["monthNum"]
    year = request.json["year"]
    conflicts = request.json["conflicts"]

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for all of the previously entered conflicts for the
    #  remote user.
    cur.execute("""SELECT TO_CHAR(day.date, 'YYYY-MM-DD')
                   FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                                  JOIN staff_membership AS sm ON (sm.ra_id = conflicts.ra_id)
                                  JOIN month ON (month.id = day.month_id)
                   WHERE num = %s
                   AND EXTRACT(YEAR from year) = %s
                   AND sm.res_hall_id = %s
                   AND sm.ra_id = %s;""",
                (monthNum, year, authedUser.hall_id(), authedUser.ra_id()))

    # Load the results from the DB
    prevConflicts = cur.fetchall()

    # Create a set object of all of the conflicts returned from the
    #  previous query.
    prevSet = set([i[0] for i in prevConflicts])

    # Create a set object of all of the conflicts provided by the
    #  remote user.
    newSet = set(conflicts)

    # Get a set of dates that were previously entered but are not in the latest.
    # These items should be removed from the DB.
    deleteSet = prevSet.difference(newSet)

    # Get a set of dates that have been submitted that were not previously.
    # These items should be inserted into the DB.
    addSet = newSet.difference(prevSet)

    logging.debug("DataConflicts: {}".format(conflicts))
    logging.debug("PrevSet: {}".format(prevSet))
    logging.debug("NewSet: {}".format(newSet))
    logging.debug("DeleteSet: {}, {}".format(deleteSet, str(deleteSet)[1:-1]))
    logging.debug("AddSet: {}, {}".format(addSet, str(addSet)[1:-1]))

    # Set a flag to indicate that we have not made any changes to the DB
    madeChanges = False

    # If there are conflicts that should be removed from the DB
    if len(deleteSet) > 0:
        # Then remove them from the DB

        # Execute a DELETE statement to remove the previously entered conflicts
        #  that are no longer needed.
        cur.execute("""
            DELETE FROM conflicts
            WHERE conflicts.day_id IN (
                SELECT conflicts.day_id
                FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                WHERE TO_CHAR(day.date, 'YYYY-MM-DD') IN %s
                AND conflicts.ra_id = %s
            );""", (tuple(deleteSet), authedUser.ra_id()))

        # Set the flag to indicate that we have made changes to the DB
        madeChanges = True

    # If there are conflicts that should be added to the DB
    if len(addSet) > 0:

        # Then add them to the DB

        # Execute an INSERT statement to add conflicts that were not
        #  previously entered in the DB.
        cur.execute("""INSERT INTO conflicts (ra_id, day_id)
                        SELECT %s, day.id FROM day
                        WHERE TO_CHAR(day.date, 'YYYY-MM-DD') IN %s
                        """, (authedUser.ra_id(), tuple(addSet)))

        # Set the flag to indicate that we have made changes to the DB
        madeChanges = True

    # Check to see if we have made any DB changes
    if madeChanges:
        # If so, commit the changes to the DB
        ag.conn.commit()

    # Close the DB cursor
    cur.close()

    # Indicate to the client that the save was successful
    return packageReturnObject(stdRet(1, "successful"))
