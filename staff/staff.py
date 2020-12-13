from flask import render_template, request, jsonify, redirect, url_for, Blueprint
from flask_login import login_required
from psycopg2 import IntegrityError
import logging

# Import the appGlobals for this blueprint to use
import appGlobals as ag

# Import the needed functions from other parts of the application
from helperFunctions.helperFunctions import getAuth, stdRet, getCurSchoolYear, fileAllowed

staff_bp = Blueprint("staff_bp", __name__,
                     template_folder="templates",
                     static_folder="static")

# ---------------------
# --      Views      --
# ---------------------

@staff_bp.route("/")
@login_required
def manStaff():
    # The landing page for this blueprint that will display the list of
    #  staff members to the user and provide a way for them to edit individual
    #  staff members' information and add or remove staff as well.
    #
    #  Required Auth Level: >= HD
    #

    # Get the user's info from our database
    userDict = getAuth()

    # If the user is not at least an HD
    if userDict["auth_level"] < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Get the information for the current school year.
    #  This will be used to calculate duty points for the RAs.
    start, end = getCurSchoolYear()

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for a list of all of the RAs for the hall and their information.
    cur.execute("""SELECT ra.id, first_name, last_name, email, date_started, res_hall.name, color, auth_level 
                   FROM ra JOIN res_hall ON (ra.hall_id = res_hall.id) 
                   WHERE hall_id = %s ORDER BY ra.id ASC;
                """, (userDict["hall_id"],))

    # Get each of the RA's duty statistics for the current school year.
    ptStats = getRAStats(userDict["hall_id"], start, end)

    # Render and return the appropriate template.
    return render_template("staff/staff.html", raList=cur.fetchall(), auth_level=userDict["auth_level"],
                           opts=ag.baseOpts, curView=4, hall_name=userDict["hall_name"], pts=ptStats)


# ---------------------
# --   API Methods   --
# ---------------------

@staff_bp.route("/api/getStats", methods=["GET"])
@login_required
def getRAStats(hallId=None, startDateStr=None, endDateStr=None, maxBreakDay=None):
    # API Method that will calculate and return the RA duty statistics for a given month.
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
    #     maxBreakDay   <str>  -  a string representing the latest break duty that should be
    #                              included for the duty points calculation.
    #
    #  If called from a client, the following parameters are required:
    #
    #     start  <str>  -  a string representing the first day that should be included
    #                       for the duty points calculation.
    #     end    <str>  -  a string representing the last day that should be included
    #                       for the duty points calculation.
    #
    #  This method returns an object with the following specifications:
    #
    #     {
    #        <ra.id 1> : {
    #           "name": ra.first_name + " " + ra.last_name,
    #           "pts": <number of duty points for RA 1>
    #        },
    #        <ra.id 2> : {
    #           "name": ra.first_name + " " + ra.last_name,
    #           "pts": <number of duty points for RA 2>
    #        },
    #        ...
    #     }

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if hallId is None and startDateStr is None \
            and endDateStr is None and maxBreakDay is None:
        # If the HallId, startDateStr, endDateStr and MaxBreakDay are None, then
        #  this method was called from a remote client.

        # Get the user's information from the database
        userDict = getAuth()
        # Set the value of hallId from the userDict
        hallId = userDict["hall_id"]
        # Get the startDateStr and endDateStr from the request arguments
        startDateStr = request.args.get("start")
        endDateStr = request.args.get("end")
        # Mark that this method was not called from the server
        fromServer = False

    logging.debug("Get RA Stats - FromServer: {}".format(fromServer))

    # Create the result object to be returned
    res = {}

    # Create a DB cursor
    cur = ag.conn.cursor()

    # This method assumes that the first break duty that should be included in this
    #  calculation is the same date as the one indicated in the startDateStr.
    breakDutyStart = startDateStr

    # Check to see if the maxBreakDay has been assigned.
    if maxBreakDay is None:
        # If maxBreakDay is None, then we should calculate the TOTAL number of points
        #  that each RA has for the course of the period specified (including
        #  all break duties).

        # Set the breakDutyEnd date to be the same as the endDateStr
        breakDutyEnd = endDateStr

    else:
        # If maxBreakDay is NOT None, then we should calculate the number of REGULAR
        #  duty points plus the number of BREAK duty points for the specified month.

        # Set the breakDutyEnd date to tbe the same as the maxBreakDay
        breakDutyEnd = maxBreakDay

    logging.debug("breakDutyStart: {}".format(breakDutyStart))
    logging.debug("breakDutyEnd: {}".format(breakDutyEnd))

    # Query the DB for all of the duties within the provided timeframe and add up the points
    #  for each RA.
    cur.execute("""SELECT ra.id, ra.first_name, ra.last_name, COALESCE(ptQuery.pts,0)
               FROM
               (
                   SELECT combined_res.rid AS rid, CAST(SUM(combined_res.pts) AS INTEGER) AS pts
                   FROM
                   (
                      SELECT ra.id AS rid, SUM(duties.point_val) AS pts
                      FROM duties JOIN day ON (day.id=duties.day_id)
                                  JOIN ra ON (ra.id=duties.ra_id)
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
                             WHERE month.year >= TO_DATE(%s, 'YYYY-MM-DD')
                             AND month.year <= TO_DATE(%s, 'YYYY-MM-DD')
                         )
                         ORDER BY schedule.month_id, schedule.created DESC, schedule.id DESC
                      )
                      GROUP BY rid

                      UNION

                      SELECT ra.id AS rid, SUM(break_duties.point_val) AS pts
                      FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                                        JOIN ra ON (ra.id=break_duties.ra_id)
                      WHERE break_duties.hall_id = %s
                      AND day.date BETWEEN TO_DATE(%s, 'YYYY-MM-DD')
                                       AND TO_DATE(%s, 'YYYY-MM-DD')
                      GROUP BY rid
                   ) AS combined_res
                   GROUP BY combined_res.rid
               ) ptQuery
               RIGHT JOIN ra ON (ptQuery.rid = ra.id)
               WHERE ra.hall_id = %s;""", (hallId, hallId, startDateStr,
                                           endDateStr, hallId, breakDutyStart,
                                           breakDutyEnd, hallId))

    # Get the result from the DB
    raList = cur.fetchall()

    # Iterate through the raList from the DB and assembled the return result
    #  in the format outlined in the comments at the top of this method.
    for ra in raList:
        res[ra[0]] = {"name": ra[1] + " " + ra[2], "pts": ra[3]}

    # Close the DB cursor
    cur.close()

    # If this API method was called from the server
    if fromServer:
        # Then return the result as-is
        return res

    else:
        # Otherwise return a JSON version of the result
        return jsonify(res)


@staff_bp.route("/api/getStaffInfo", methods=["GET"])
@login_required
def getStaffStats():
    # API Method that will calculate and return the RA duty statistics as for the
    #  user's staff for the current school year.
    #
    #  Required Auth Level: >= HD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, this function does not accept any parameters, but
    #  rather, uses the hall id that is associated with the user.
    #
    #  This method returns an object with the following specifications:
    #
    #     {
    #        raList : [
    #           [<ra.id 1>,<ra.first_name 1>,<ra.last_name 1>,<ra.email 1>,
    #            <ra.date_started 1>,<res_hall.name>,<ra.color 1>,<ra.auth_level 1>],
    #           [...],
    #           ...
    #        ],
    #        pts : {
    #           <ra.id 1> : {
    #              "name": ra.first_name + " " + ra.last_name,
    #              "pts": <number of duty points for RA 1>
    #           },
    #           <ra.id 2> : {
    #              "name": ra.first_name + " " + ra.last_name,
    #              "pts": <number of duty points for RA 2>
    #           },
    #           ...
    #        }
    #     }

    # Get the user's information from the database
    userDict = getAuth()

    # Check to see if the user is authorized to view this information
    # If the user is not at least an HD
    if userDict["auth_level"] < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the list of RAs for the given res hall.
    cur.execute("""SELECT ra.id, first_name, last_name, email, date_started, res_hall.name, color, auth_level
                 FROM ra JOIN res_hall ON (ra.hall_id = res_hall.id)
                 WHERE hall_id = %s ORDER BY ra.id DESC;""", (userDict["hall_id"],))

    # Get the information for the current school year.
    #  This will be used to calculate duty points for the RAs.
    start, end = getCurSchoolYear()

    # Get each of the RA's duty statistics for the current school year.
    pts = getRAStats(userDict["hall_id"], start, end)

    # Assemble the return result object.
    ret = {"raList": cur.fetchall(), "pts": pts}

    # return a JSON version of the return result
    return jsonify(ret)


@staff_bp.route("/api/changeStaffInfo", methods=["POST"])
@login_required
def changeStaffInfo():
    # API Method that updates an RA record with the provided information.
    #
    #  Required Auth Level: >= HD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     fName      <str>  -  The new value for the RA's first name (ra.first_name)
    #     lName      <str>  -  The new value for the RA's last name (ra.last_name)
    #     startDate  <str>  -  The new date string value for the RA's start date
    #                           (ra.start_date). Must be provided in YYYY-MM-DD format.
    #     color      <str>  -  The new value for the RA's color (ra.color)
    #     email      <str>  -  The new value for the RA's email (ra.email)
    #     authLevel  <int>  -  An integer denoting the authorization level for the RA.
    #                           Must be an integer value in the range: 1-3.
    #     raID       <int>  -  An integer denoting the row id for the desired RA in the
    #                           ra table.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the save was successful
    #      0 : the client does not belong to the same hall as the provided RA
    #     -1 : the save was unsuccessful

    # Get the user's information from the database
    userDict = getAuth()

    # Check to see if the user is authorized to alter RA information
    # If the user is not at least an HD
    if userDict["auth_level"] < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Load the data provided by the client
    data = request.json

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Check to ensure that the client belongs on the same staff as the
    #  RA whose information is being altered.
    cur.execute("SELECT hall_id = %s FROM ra WHERE ra.id = %s;", (userDict["hall_id"], data["raID"]))

    if not cur.fetchone()[0]:
        # If the client does not belong to the same hall, then something fishy is going on.
        #  Simply return a not authorized message and stop processing.

        logging.info("User Not Authorized - RA: {} attempted to overwrite RA Info for : {}"
                     .format(userDict["ra_id"], data["raID"]))

        # Close the DB cursor
        cur.close()

        # Indicate to the client that the user does not belong to the provided hall
        return jsonify(stdRet(0, "NOT AUTHORIZED"))

    else:
        # Otherwise go ahead and update the RA's information

        cur.execute("""UPDATE ra
                       SET first_name = %s, last_name = %s,
                           date_started = TO_DATE(%s, 'YYYY-MM-DD'),
                           color = %s, email = %s, auth_level = %s
                       WHERE id = %s;
                    """, (data["fName"], data["lName"], data["startDate"], data["color"],
                          data["email"], data["authLevel"], data["raID"]))

        # Commit the changes to the DB
        ag.conn.commit()

        # Close the DB cursor
        cur.close()

    # Indicate to the client that the save was successful
    return jsonify(stdRet(1, "successful"))


@staff_bp.route("/api/removeStaffer", methods=["POST"])
@login_required
def removeStaffer():
    # API Method that removes a staff member from the client's res hall. The staff
    #  member that is removed is then associated with the 'Not Assigned' record in
    #  the res_hall table.
    #
    #  Required Auth Level: >= HD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     raID  <int>  -  An integer denoting the row id for the desired RA in the
    #                      ra table.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the removal was successful
    #      0 : the client does not belong to the same hall as the provided RA
    #     -1 : the removal was unsuccessful

    # Get the user's information from the database
    userDict = getAuth()

    # Check to see if the user is authorized to remove the staff member
    # If the user is not at least an HD
    if userDict["auth_level"] < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Load the raID from the request's JSON
    raID = request.json

    # Check to ensure that the client belongs on the same staff as the
    #  RA whose information is being altered.

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the provided RA
    cur.execute("SELECT hall_id = %s FROM ra WHERE ra.id = %s;", (userDict["hall_id"], raID))

    if not cur.fetchone()[0]:
        # If the client does not belong to the same hall, then something fishy is going on.
        #  Simply return a not authorized message and stop processing.

        logging.info("User Not Authorized - RA: {} attempted to overwrite RA Info for : {}"
                     .format(userDict["ra_id"], raID))

        # Close the DB cursor
        cur.close()

        # Indicate to the client that the user does not belong to the provided hall
        return jsonify(stdRet(0, "NOT AUTHORIZED"))

    else:
        # Otherwise go ahead and remove the RA from the hall
        cur.execute("UPDATE ra SET hall_id = 0 WHERE id = %s;", (raID,))

        # Commit the change to the DB
        ag.conn.commit()

        # Close the DB cursor
        cur.close()

    # Indicate to the client that the save was successful
    return jsonify(stdRet(1, "successful"))


@staff_bp.route("/api/addStaffer", methods=["POST"])
@login_required
def addStaffer():
    # API Method that adds a new staff member to the same res hall as the client.
    #
    #  Required Auth Level: >= HD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     fName      <str>  -  The value for the RA's first name (ra.first_name)
    #     lName      <str>  -  The value for the RA's last name (ra.last_name)
    #     color      <str>  -  The value for the RA's color (ra.color)
    #     email      <str>  -  The value for the RA's email (ra.email)
    #     authLevel  <int>  -  An integer denoting the authorization level for the RA.
    #                           Must be an integer value in the range: 1-3.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the addition was successful
    #      0 : the client does not belong to the same hall as the provided RA
    #     -1 : the addition was unsuccessful

    # Get the user's information from the database
    userDict = getAuth()

    # Check to see if the user is authorized to add a staffer
    # If the user is not at least an HD
    if userDict["auth_level"] < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to add Staff Member for Hall: {}"
                     .format(userDict["ra_id"], userDict["hall_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Load the data from the request's JSON
    data = request.json

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB to see if there is already an RA associated with the provided email.
    cur.execute("SELECT id FROM ra WHERE email = %s;", (data["email"],))

    # Load the result from the DB
    checkRes = cur.fetchone()

    # If there is a user with the provided email already
    if checkRes is not None:
        # Then update RA record to be associated with the new hall
        cur.execute("UPDATE ra SET hall_id = %s WHERE email = %s;", (userDict["hall_id"], data["email"]))

        # Commit the changes to the DB
        ag.conn.commit()

        # Notify the user that the change was successful
        return jsonify(stdRet(1, "successful"))

    # Otherwise create a new RA record in the ra table with the provided information.
    cur.execute("""INSERT INTO ra (first_name, last_name, hall_id, date_started, color, email, auth_level)
                   VALUES (%s, %s, %s, NOW(), %s, %s, %s)
                """, (data["fName"], data["lName"], userDict["hall_id"], data["color"],
                      data["email"], data["authLevel"]))

    # Commit the changes to the DB
    ag.conn.commit()

    # Notify the client that the save was successful
    return jsonify(stdRet(1, "successful"))


@staff_bp.route("/api/importStaff", methods=["POST"])
@login_required
def importStaff():
    # API Method that uses an uploaded file to import multiple staff members into
    #  the client's staff. The file must be either a .csv or .txt file that is in
    #  a specific format. An example of this format can be seen in the
    #  'importExample.csv' file located in this blueprint's static folder.
    #
    #  Required Auth Level: >= HD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     file  <TextIOWrapper>  -  an uploaded file that will be used to
    #                                import multiple staff members into the
    #                                client's staff.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the import was successful
    #      0 : there was an error transmitting the file to the server
    #     -1 : the import was unsuccessful

    # Get the user's information from the database
    userDict = getAuth()

    # Check to see if the user is authorized to import staff members
    # If the user is not at least an HD
    if userDict["auth_level"] < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to import staff to Hall: {}"
                     .format(userDict["ra_id"], userDict["hall_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    logging.info("Import File: {} for Hall: {}".format(request.files, userDict["hall_id"]))

    # If the key 'file' is not in the request.files object
    if 'file' not in request.files:
        # Then there was an issue uploading the file to the server
        logging.info("No file part found")

        # Notify the client that there was a transmission issue.
        return jsonify(stdRet(0, "There appears to have been an issue uploading the file. - No File Part Found"))

    # Otherwise load the file
    file = request.files['file']
    # NOTE: If the user does not select a file, the browser
    #        can submit an empty part without a filename.

    # Check to see if the browser uploaded an empty part
    #  without a filename.
    if file.filename == '':
        # If so, log the occurrence
        logging.info("No File Selected")

        # Notify the client that this issue occurred.
        return jsonify(stdRet(0, "No File Selected"))

    # Check to ensure that 1) we have a file and 2) the file type is allowed
    if file and fileAllowed(file.filename):

        # If so, decode and read the file into a string
        dataStr = file.read().decode("utf-8")

        logging.debug(dataStr)

        # Create a DB cursor
        cur = ag.conn.cursor()

        # Iterate through the rows of the dataStr and process them.
        #  The expected format for the csv contains a header row and is as follows:
        #  First Name, Last Name, Email, Date Started (MM/DD/YYYY), Color, Role
        #
        #  Example:
        #  FName, LName-Hyphen, example@email.com, 05/28/2020, #OD1E76, RA

        # Split the dataStr on the newline character and, since we expect a header
        #  row, skip the first item in the list.
        for row in dataStr.split("\n")[1:]:
            # If the row is not empty
            if row != "":
                # Then break out its parts splitting on the "," character
                #  and strip any excess whitespace off of the individual parts.
                pl = [part.strip() for part in row.split(",")]

                logging.debug("PL: {}".format(pl))

                # Do some validation checking of the parts to ensure that
                #  we have received the correct number of items, that each
                #  part doesn't contain any mischievous characters, and
                #  that each part is formatted as we would expect
                pl, valid, reasons = validateImportStaffUpload(pl)

                # Check to see if the parts list is valid.
                if not valid:
                    # If not, then create a standard return object informing
                    #  the client of this issue.
                    ret = stdRet(0, "Invalid File Formatting")

                    # Add an "except" key with the reasons provided by the
                    #  validateImportStaffUpload functions.
                    ret["except"] = reasons

                    # Log the instance
                    logging.info("Invalid Import Staff Formatting for Hall: {}"
                                 .format(userDict["hall_id"]))

                    # Notify the client of this issue.
                    return jsonify(ret)

                # Check the authorization level indicated by the row
                #  and translate the human-readable text into the values
                #  that will be stored in the DB.
                if pl[-1] == "HD":
                    # If the role is "HD", then set the auth to 3
                    auth = 3

                elif pl[-1] == "AHD":
                    # If the role is "AHD", then set the auth to 2
                    auth = 2

                else:
                    # Otherwise set the role to 1
                    # NOTE: This would include "RA" roles as well
                    #        as any strange roles that the user enters.
                    auth = 1

                logging.debug(str(auth))

                try:
                    # Attempt to add insert the new staff member into the RA table.
                    cur.execute("""
                        INSERT INTO ra (first_name,last_name,hall_id,date_started,color,email,auth_level)
                        VALUES (%s, %s, %s,TO_DATE(%s, 'MM/DD/YYYY'), %s, %s, %s);
                        """, (pl[0], pl[1], userDict["hall_id"], pl[3], pl[4], pl[2], auth))

                    # Commit the changes to the DB
                    ag.conn.commit()

                except IntegrityError:
                    # If the ra already exists in the DB
                    # Log the instance
                    logging.warning("Duplicate RA: {}, rolling back DB changes".format(pl))

                    # Roll back the DB prior to the inserting the duplicate
                    ag.conn.rollback()

                    # Close the cursor
                    cur.close()

                    # Create a new cursor to get a fresh start
                    cur = ag.conn.cursor()

        # When we are done iterating through all of the rows...
        # Close the DB cursor
        cur.close()

        # Redirect the user back to the Manage Staff page.
        return redirect(url_for("staff_bp.manStaff"))

    else:
        # If we do not have a file or the file type is not allowed,
        # Log the instance
        logging.info("Unable to Import Staff")

        # Redirect the user to an error page that will describe the issue
        return redirect(url_for(".err", msg="Unable to Import Staff\n\nAn error has occurred during the "
                                            "import process. Either a file was not received by the server "
                                            "or the file extension that was received was not allowed."))


def validateImportStaffUpload(partList):
    # Helper function designed for the staff_bp.importStaff endpoint that
    #  ensures that the provided row parts fit our expected schema.
    #
    #  This function accepts the following parameters:
    #
    #     partList  <lst<str>>  -  a list containing string values that have
    #                               been pulled from a row in the file provided
    #                               in the import staff process.
    #
    #  This function returns a tuple containing the following in order:
    #
    #     pl       <lst<str>>  -  a list containing string values that have
    #                              been derived and cleaned from the provided
    #                              partList input parameter.
    #     valid    <bool>      -  a boolean representing whether the parts in
    #                              the provided partList input parameter fits
    #                              the expected schema.
    #     reasons  <lst<str>>  -  a list containing string values that inform
    #                              the user what, if anything is incorrectly
    #                              formatted about this row.

    logging.debug("Validating Import Staff Upload")

    # Create the pl list that is to be returned
    pl = []

    # Iterate through the partList and remove any problematic characters
    for i in partList:
        i.replace("%", "")
        i.replace(";", "")
        i.replace("\\", "")

        # Append the cleaned string to pl
        pl.append(i)

    # Set the default state of valid to be True
    valid = True

    # Create the reasons list that is to be returned
    reasons = []

    # If the partList does not have only 6 items in it
    if len(partList) != 6:
        # Set the state to be invalid
        valid = False

        # Append the reason for the invalidation to the reasons list
        reasons.append("Expected 5 Parameters, Received: {}".format(len(partList)))

        logging.debug("PartList: {}".format(str(partList)))

    else:
        # If the partList has exactly 6 items, continue validation

        # Extract the individual parts from the partList
        fName, lName, email, start, color, role = pl

        # Validate the Email Address
        #  An email address is considered valid if it has an "@" and "." in it
        #  example: "test@email.com"
        if "@" not in email and "." not in email:
            # Set the state to be invalid
            valid = False

            # Append the reason for the invalidation to the reasons list
            reasons.append(fName+" "+lName+" - Invalid Email Address: "+email)

            logging.debug("RA Email: {}".format(str(email)))

        # Validate the Start Date
        #  A start date is considered valid if it is ordered as Month, Day, Year
        #  with the separator character being a "/".
        #  example: 12/09/2020

        # Attempt to split the date string on the "/" character
        splitDate = start.split("/")

        # If the splitDate does not contain exactly three parts, OR
        # If the start string contains an "-" OR
        # If the integer value of the first item in splitDate is greater than 12 or less than 1 OR
        # If the integer value of the second item in splitDate is greater than 31 or less than 1 OR
        # If the integer value of the third item in splitDate is less than 1970
        if len(splitDate) != 3 or \
                "-" in start or \
                int(splitDate[0]) > 12 or int(splitDate[0]) < 1 or \
                int(splitDate[1]) > 31 or int(splitDate[1]) < 1 or \
                int(splitDate[2]) < 1970:

            # Set the state to be invalid
            valid = False

            # Append the reason for the invalidation to the reasons list
            reasons.append(fName+" "+lName+" - Invalid Start Date: "+start)

            logging.debug("RA Start Date: {}".format(start))

        # Validate the Check Color
        # If the color is not exactly 7 digits or the color does not contain the "#" character
        if len(color) != 7 or "#" not in color:

            # Set the state to be invalid
            valid = False

            # Append the reason for the invalidation to the reasons list
            reasons.append(fName + " " + lName + " - " +
                           "Invalid Color Format: {} Must be in 6-digit, hex format preceded by a '#'".format(color))

            logging.debug("RA Color: {}".format(color))

    # Return the pl, valid, and reasons variables
    return pl, valid, reasons
