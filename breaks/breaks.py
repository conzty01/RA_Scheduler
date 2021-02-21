from flask import render_template, request, jsonify, Blueprint, abort
from flask_login import login_required
import logging

# Import the appGlobals for this blueprint to use
import appGlobals as ag

# Import the needed functions from other parts of the application
from helperFunctions.helperFunctions import getAuth, stdRet, getCurSchoolYear

breaks_bp = Blueprint("breaks_bp", __name__,
                      template_folder="templates",
                      static_folder="static")

# ---------------------
# --      Views      --
# ---------------------

@breaks_bp.route("/editBreaks", methods=['GET'])
@login_required
def editBreaks():
    # The landing page for this blueprint that will display a calendar that
    #  users can interact with to view, add, edit, and remove break duties.
    #  RA break statistics will also be displayed in a side panel for the
    #  AHD to use.
    #
    #  Required Auth Level: >= AHD

    # Get the user's info from our database
    authedUser = getAuth()

    # If the user is not at least an AHD
    if authedUser.auth_level() < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {}".format(authedUser.ra_id()))

        # Raise an 403 Access Denied HTTP Exception that will be handled by flask
        abort(403)

    # Get the information for the current school year.
    #  This will be used to calculate break duty points for the RAs.
    start, end = getCurSchoolYear()

    logging.debug(start)
    logging.debug(end)

    # Call getRABreakStats to get information on the number of Break Duty
    # points each RA has for the current school year
    bkDict = getRABreakStats(authedUser.hall_id(), start, end)

    logging.debug(str(bkDict))

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the necessary information about the staff's RAs.
    cur.execute("""
        SELECT ra.id, ra.first_name, ra.last_name, ra.color
        FROM ra JOIN staff_membership AS sm ON (ra.id = sm.ra_id)
        WHERE sm.res_hall_id = %s ORDER BY ra.first_name ASC;
        """, (authedUser.hall_id(),))

    # Render and return the appropriate template
    return render_template("breaks/editBreaks.html", raList=cur.fetchall(), auth_level=authedUser.auth_level(),
                           bkDict=sorted(bkDict.items(), key=lambda x: x[1]["name"].split(" ")[1]),
                           curView=3, opts=ag.baseOpts, hall_name=authedUser.hall_name(),
                           linkedHalls=authedUser.getAllAssociatedResHalls())


# ---------------------
# --   API Methods   --
# ---------------------

@breaks_bp.route("/api/getRABreakStats", methods=["GET"])
@login_required
def getRABreakStats(hallId=None, startDateStr=None, endDateStr=None):
    # API Method that will calculate a staff's RA Break Duty statistics for the given
    #  time period. This method does not calculate the number of points an RA has
    #  due to breaks, but rather counts the number of break duties the RA has been
    #  assigned to for the given time period.
    #
    #  Required Auth Level: None
    #
    #  If called from the server, this function accepts the following parameters:
    #
    #     hallId        <int>  -  an integer representing the id of the desired residence
    #                              hall in the res_hall table.
    #     startDateStr  <str>  -  a string representing the first day that should be included
    #                              for the duty points calculation.
    #     endDateStr    <str>  -  a string representing the last day that should be included
    #                              for the duty points calculation.
    #
    #  If called from a client, the following parameters are required:
    #
    #     start  <str>  -  a string representing the first day that should be included
    #                       for the break duty count calculation.
    #     end    <str>  -  a string representing the last day that should be included
    #                       for the duty count calculation.
    #
    #  This method returns an object with the following specifications:
    #
    #     {
    #        <ra.id 1> : {
    #           "name": ra.first_name + " " + ra.last_name,
    #           "count": <number of break duties RA 1 has>
    #        },
    #        <ra.id 2> : {
    #           "name": ra.first_name + " " + ra.last_name,
    #           "count": <number of break duties RA 2 has>
    #        },
    #        ...
    #     }

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if hallId is None and startDateStr is None and endDateStr is None:
        # If the hallId, startDateStr, and endDateStr are None, then
        #  this method was called from a remote client.

        # Get the user's information from the database
        authedUser = getAuth()
        # Set the value of hallId from the userDict
        hallId = authedUser.hall_id()

        # Get the startDateStr and endDateStr from the request arguments
        startDateStr = request.args.get("start")
        endDateStr = request.args.get("end")

        # Mark that this method was not called from the server.
        fromServer = False

    logging.debug("Get RA Break Duty Stats - FromServer: {}".format(fromServer))

    # Create the result object to be returned
    res = {}

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the list of RAs on the provided staff and the count of break
    #  duties that they have been assigned to for the given time period.
    cur.execute("""
        SELECT ra.id, ra.first_name, ra.last_name, COALESCE(numQuery.count, 0)
        FROM ra LEFT JOIN (
            SELECT ra_id as rid, COUNT(break_duties.id)
            FROM break_duties JOIN day ON (day.id = break_duties.day_id)
            WHERE day.date BETWEEN TO_DATE(%s, 'YYYY-MM-DD') AND TO_DATE(%s, 'YYYY-MM-DD')
            GROUP BY ra_id
        ) AS numQuery ON (ra.id = numQuery.rid)
        JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE sm.res_hall_id = %s
    """, (startDateStr, endDateStr, hallId))

    # Load the results from the DB
    raList = cur.fetchall()

    # Iterate through the raList from the DB and assemble the return result
    #  in the format outlined in the comments at the top of this method.
    for ra in raList:
        res[ra[0]] = {"name": ra[1] + " " + ra[2], "count": ra[3]}

    # Close the DB cursor
    cur.close()

    # If this API method was called from the server
    if fromServer:
        # Then return the result as-is
        return res

    else:
        # Otherwise, return a JSON version of the result
        return jsonify(res)


@breaks_bp.route("/api/getBreakDuties", methods=["GET"])
@login_required
def getBreakDuties(hallId=None, start=None, end=None, showAllColors=False, raId=-1):
    # API Method that will calculate a staff's RA Break Duty statistics for the given
    #  time period. This method does not calculate the number of points an RA has
    #  due to breaks, but rather counts the number of break duties the RA has been
    #  assigned to for the given time period.
    #
    #  Required Auth Level: >= AHD
    #
    #  If called from the server, this function accepts the following parameters:
    #
    #     hallId         <int>  -  an integer representing the id of the desired residence
    #                               hall in the res_hall table.
    #     start          <str>  -  a string representing the first day that should be included
    #                               for the returned duty schedule.
    #     end            <str>  -  a string representing the last day that should be included
    #                               for the returned duty schedule.
    #     showAllColors  <bool> -  a boolean value representing whether the returned duty
    #                               schedule should include the RA's ra.color value or if
    #                               the generic value '#2C3E50' should be returned. Setting
    #                               this value to True will return the RA's ra.color value.
    #                               By default this parameter is set to False.
    #
    #     raId           <int>  -  an integer representing the id of the RA that should be
    #                               considered the requesting user. By default this value is
    #                               set to -1 which indicates that no RA should be considered
    #                               the requesting user.
    #
    #  If called from a client, the following parameters are required:
    #
    #     start      <str>  -  a string representing the first day that should be included
    #                           for the returned duty schedule.
    #     end        <str>  -  a string representing the last day that should be included
    #                           for the returned duty schedule.
    #     allColors  <bool> -  a boolean value representing whether the returned duty
    #                           schedule should include the RA's ra.color value or if
    #                           the generic value '#2C3E50' should be returned. Setting
    #                           this value to True will return the RA's ra.color value.
    #
    #     NOTE: Regardless of what value is specified for allColors, the if the ra.id
    #            that is associated with the user appears in the break schedule, the
    #            ra.color associated with the user will be displayed. This is so that
    #            the user can more easily identify when they are on duty.
    #
    #  This method returns an object with the following specifications:
    #
    #     [
    #        {
    #             "id": <ra.id>,
    #             "title": <ra.first_name + " " + ra.last_name>,
    #             "start": <string value of day.date associated with the scheduled duty>,
    #             "color": <ra.color OR #2C3E50 if allColors/showAllColors is False>,
    #             "extendedProps": {
    #                 "dutyType": "brk",
    #                 "pts": <break_duties.point_val>
    #             }
    #         },
    #         ...
    #     ]
    #

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if start is None and end is None and hallId is None:
        # If the HallId, start and end are None, then
        #  this method was called from a remote client.

        # Get the start and end string values from the request arguments.
        #  Since we utilize the fullCal.js library, we know that the request
        #  also contains timezone information that we do not care about in
        #  this method. As a result, the timezone information is split out
        #  immediately.
        start = request.args.get("start").split("T")[0]
        end = request.args.get("end").split("T")[0]

        # Get the value for allColors from the request arguments.
        showAllColors = request.args.get("allColors") == "true"

        # Get the user's information from the database
        authedUser = getAuth()
        # Set the value of the hallId from the userDict
        hallId = authedUser.hall_id()
        # Set the value of the raId from the userDict
        raId = authedUser.ra_id()
        # Mark that this method was not called from the server
        fromServer = False

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the break duty schedule for the given hall and timeframe.
    cur.execute("""
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD'),
               break_duties.point_val
        FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                          JOIN month ON (month.id=break_duties.month_id)
                          JOIN ra ON (ra.id=break_duties.ra_id)
        WHERE break_duties.hall_id = %s
        AND month.year >= TO_DATE(%s,'YYYY-MM')
        AND month.year <= TO_DATE(%s,'YYYY-MM')
    """, (hallId, start, end))

    # Create the result object to be returned
    res = []

    # Iterate through the query result (each day of the break schedule) and assemble
    #  the return result in the format outlined in the comments at the top of this method.
    for row in cur.fetchall():

        # If showAllColors is False, then the desired behavior is to NOT show all of
        # the unique RA colors.
        if not(showAllColors):
            # Check to see if the current user is the RA on the duty being added
            #  to the result list.
            if raId == row[3]:
                # If it is the RA, then use their color value
                c = row[2]

            else:
                # Otherwise use the generic color value
                c = "#2C3E50"

        else:
            # Otherwise, if the desired behavior is to show all of the unique RA colors,
            #  then simply set their color.
            c = row[2]

        # Append the assigned break duty to the result list using the values returned
        #  from the query and the color calculated above.
        res.append({
            "id": row[3],
            "title": row[0] + " " + row[1],
            "start": row[4],
            "color": c,
            "extendedProps": {
                "dutyType": "brk",
                "pts": row[5]
            }
        })
    
    # Close the DB cursor
    cur.close()

    # If this API method was called from the server
    if fromServer:
        # Then return the result as-is
        return res

    else:
        # Otherwise return a JSON version of the result
        return jsonify(res)


@breaks_bp.route("/api/addBreakDuty", methods=["POST"])
def addBreakDuty():
    # API Method that adds a break duty into the client's Res Hall's schedule.
    #
    #  Required Auth Level: >=AHD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     id       <int> -  an integer representing the ra.id for the RA that should
    #                        be assigned to the break duty.
    #     pts      <int> -  an integer representing how many points the new break duty
    #                        should be worth.
    #     dateStr  <str> -  a string representing the date that the break duty should
    #                        occur on.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the save was successful
    #      0 : the client does not belong to the same hall as the provided RA
    #     -1 : the save was unsuccessful

    # Get the user's information from the database
    authedUser = getAuth()

    # Check to see if the user is authorized to alter RA information
    # If the user is not at least an AHD
    if authedUser.auth_level() < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to add Break Duty for Hall: {}"
                     .format(authedUser.ra_id(), authedUser.hall_id()))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Load the data provided by the client
    data = request.json

    # Set the values of the selID, ptVal, and dateStr with the
    #  data passed from the client.
    selRAID = data["id"]
    ptVal = data["pts"]
    dateStr = data["dateStr"]

    # Set the hallId from the hall associated with the requesting user.
    hallId = authedUser.hall_id()

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Validate that the RA desired exists and belongs to the same hall
    cur.execute("SELECT ra_id FROM staff_membership WHERE ra_id = %s AND res_hall_id = %s;", (selRAID, hallId))

    # Load the result from the DB
    raId = cur.fetchone()

    if raId is None:
        # If the result is None, then the desired RA is not associated with
        #  the user's hall.

        # Close the DB cursor
        cur.close()

        # Log the occurrence
        logging.warning("Unable to find RA {} in hall {}".format(selRAID, hallId))

        # Notify the client of the issue.
        return jsonify(stdRet(0, "Unable to find RA: {} in Hall: {}".format(selRAID, hallId)))

    else:
        # Otherwise, since psycopg2 returns DB results as a tuple,
        #  extract the id from the resulting tuple.
        raId = raId[0]

    # Query the DB for the month and day IDs necessary to associate a record in break_duties
    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE(%s, 'YYYY-MM-DD');", (dateStr,))

    # Load the result from the DB and unpack it into the dayID and monthId variables.
    dayID, monthId = cur.fetchone()

    # Validate our query results
    if dayID is None:
        # If the dayID is None, then there is not a day in the DB for the desired dateStr.

        # Close the DB cursor
        cur.close()

        # Log the occurrence
        logging.warning("Unable to find day {} in database".format(data["dateStr"]))

        # Notify the client of the issue
        return jsonify(stdRet(-1, "Unable to find day {} in database".format(data["dateStr"])))

    if monthId is None:
        # If the monthId is None, then there is not a month in the DB for the desired dateStr.

        # Close the DB cursor
        cur.close()

        # Log the occurrence
        logging.warning("Unable to find month for {} in database".format(data["dateStr"]))

        # Notify the client of the issue
        return jsonify(stdRet(-1, "Unable to find month for {} in database".format(data["dateStr"])))

    # After we have a dayID and monthId for the date, insert the new break duty into the DB
    cur.execute("""INSERT INTO break_duties (ra_id, hall_id, month_id, day_id, point_val)
                    VALUES (%s, %s, %s, %s, %s);""", (raId, hallId, monthId, dayID, ptVal))

    # Commit the changes to the DB
    ag.conn.commit()

    # Close the DB cursor
    cur.close()

    # Log the successful addition of the new break duty
    logging.info("Successfully added new Break Duty for Hall: {} and Month: {}".format(hallId, monthId))

    # Indicate to the client that the save was successful
    return jsonify(stdRet(1, "successful"))


@breaks_bp.route("/api/deleteBreakDuty", methods=["POST"])
@login_required
def deleteBreakDuty():
    # API Method that removes a break duty from the client's Res Hall's schedule.
    #
    #  Required Auth Level: >=AHD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     raName   <str> -  a string denoting the full name of the RA associated with
    #                        the break duty that should be removed.
    #     dateStr  <str> -  a string representing the date that the break duty should
    #                        occur on.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the save was successful
    #      0 : the client does not belong to the same hall as the provided RA
    #     -1 : the save was unsuccessful

    # Get the user's information from the database
    authedUser = getAuth()

    # Load the data provided by the client
    data = request.json

    # Set the values of the fName, lName, and dateStr with the
    #  data passed from the client. fName and lName are parsed
    #  from the raName splitting on the " " character.
    fName, lName = data["raName"].split()
    dateStr = data["dateStr"]

    # Set the hallId from the hall associated with the requesting user.
    hallId = authedUser.hall_id()

    # Check to see if the user is authorized to remove the staff member
    # If the user is not at least an AHD
    if authedUser.auth_level() < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {}attempted to add Break Duty for Hall: {}"
                     .format(authedUser.ra_id(), authedUser.hall_id()))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    logging.debug("Delete Break Duty - RA Name: {}".format(fName + " " + lName))
    logging.debug("Delete Break Duty - HallID: {}".format(hallId))

    # The dateStr is expected to be in the following format: x-x-xxxx
    logging.debug("DateStr: {}".format(dateStr))

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the RA that was provided and ensure that the RA is in the same hall as
    #  the requesting user.
    cur.execute("""
        SELECT ra.id 
        FROM ra JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE ra.first_name LIKE %s 
        AND ra.last_name LIKE %s 
        AND sm.res_hall_id = %s;""", (fName, lName, authedUser.hall_id()))

    # Load the result from the DB
    raId = cur.fetchone()

    # Query the DB for the day and month ids for the break duty on the provided day.
    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE(%s, 'MM/DD/YYYY');",
                (data["dateStr"],))

    # Load the results from the DB
    dayID, monthId = cur.fetchone()

    # Check to ensure that we have received id values from our previous queries.
    if raId is not None and dayID is not None and monthId is not None:
        # If the raId, dayID, and monthId are all not None, then
        #  we have found the desired ra, day and month in the DB
        #  and can delete it.

        # Delete the break duty from the DB
        cur.execute("""DELETE FROM break_duties
                        WHERE ra_id = %s
                        AND hall_id = %s
                        AND day_id = %s
                        AND month_id = %s""",
                    (raId[0], hallId, dayID, monthId))

        # Commit the changes to the DB
        ag.conn.commit()

        # Close the DB cursor
        cur.close()

        # Log the occurrence
        logging.info("Successfully deleted duty")

        # Indicate to the client that the delete was successful
        return jsonify(stdRet(1, "successful"))

    else:
        # Otherwise if any of the raId, dayID and monthIds are None,
        #  then we are missing a key component to delete this break duty.

        # Close the DB cursor
        cur.close()

        # Log the occurrence
        logging.info("Unable to locate beak duty to delete: RA {}, Date {}"
                     .format(fName + " " + lName, dateStr))

        # Indicate to the client that the delete was unsuccessful
        return jsonify(stdRet(-1, "Unable to find parameters in DB"))


@breaks_bp.route("/api/changeBreakDuty", methods=["POST"])
@login_required
def changeBreakDuty():
    # API Method that changes the RA assigned to a given break duty
    #  in the client's Res Hall's schedule from one RA on the staff
    #  to another.
    #
    #  Required Auth Level: >=AHD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     oldName  <str> -  a string denoting the full name of the RA associated with
    #                        the break duty that should be changed.
    #     newId    <int> -  an integer representing the ra.id for the RA that should be
    #                        assigned for the break duty.
    #     dateStr  <str> -  a string representing the date of the break duty.
    #     pts      <int> -  an integer denoting the number of points that should be
    #                        awarded for this duty.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the save was successful
    #      0 : the client does not belong to the same hall as the provided RA
    #     -1 : the save was unsuccessful

    # Get the user's information from the database
    authedUser = getAuth()

    # Check to see if the user is authorized to change break duty assignments
    # If the user is not at least an AHD
    if authedUser.auth_level() < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to alter break duty for Hall: {}"
                     .format(authedUser.ra_id(), authedUser.hall_id()))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Load the provided data from the request's JSON
    data = request.json

    logging.debug("New RA id: {}".format(data["newId"]))
    logging.debug("Old RA Name: {}".format(data["oldName"]))
    logging.debug("HallID: {}".format(authedUser.hall_id()))

    # The dateStr is expected to be in the following format: x/x/xxxx
    logging.debug("DateStr: {}".format(data["dateStr"]))

    # Set the values of the fName, lName, and dateStr with the
    #  data passed from the client. fName and lName are parsed
    #  from the raName splitting on the " " character.
    fName, lName = data["oldName"].split()

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the RA that is desired to be on the duty. This query also helps
    #  to ensure that the requested RA is on the same staff as the client.
    cur.execute("SELECT ra_id FROM staff_membership WHERE ra_id = %s AND res_hall_id = %s;",
                (data["newId"], authedUser.hall_id()))

    # Load the results from the DB
    raParams = cur.fetchone()

    # Query the DB for the RA that is currently assigned to the duty. This query also helps
    #  to ensure that the currently assigned RA is on the same staff as the client.
    cur.execute("""
        SELECT ra.id 
        FROM ra JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE ra.first_name LIKE %s 
        AND ra.last_name LIKE %s 
        AND sm.res_hall_id = %s""",
                (fName, lName, authedUser.hall_id()))

    # Load the results from the DB
    oldRA = cur.fetchone()

    # Query the DB for the day and month ids for the break duty on the provided day.
    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE(%s, 'MM/DD/YYYY');",
                (data["dateStr"],))

    # Load the results from the DB
    dayID, monthId = cur.fetchone()

    # Check to ensure that we have received valid results from our previous
    #  three queries.
    if raParams is None or dayID is None or monthId is None or oldRA is None:
        # If raParams, dayID, monthId, or oldRA are None,
        #  then that means we are missing a key part of the
        #  puzzle to locate the exact break duty to alter.

        # Close the DB cursor
        cur.close()

        # Log the occurrence
        logging.warning("Unable to find all necessary Break Duty parameters for in database.")

        # Notify the client of the issue
        return jsonify(stdRet(0, "Unable to find all necessary Break Duty parameters in database."))

    # Otherwise, if we have all the necessary pieces,
    #  go ahead and update the appropriate break duty
    cur.execute("""UPDATE break_duties
                   SET ra_id = %s,
                       point_val = %s
                   WHERE hall_id = %s
                   AND day_id = %s
                   AND month_id = %s
                   AND ra_id = %s
                """, (raParams[0], data["pts"], authedUser.hall_id(), dayID, monthId, oldRA[0]))

    # Commit the changes to the DB
    ag.conn.commit()

    # Close the DB cursor
    cur.close()

    # Indicate to the client that the delete was unsuccessful
    return jsonify(stdRet(1, "successful"))
