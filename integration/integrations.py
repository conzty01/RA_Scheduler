from flask import request, jsonify, redirect, url_for, Blueprint
from integration.gCalIntegration import gCalIntegratinator
from flask_login import login_required
from calendar import monthrange
from io import BytesIO
import logging
import pickle

# Import the appGlobals for this blueprint to use
import appGlobals as ag

# Import the needed functions from other parts of the application
from helperFunctions.helperFunctions import getAuth, stdRet, formatDateStr
from schedule.schedule import getSchedule2
from breaks.breaks import getBreakDuties

integration_bp = Blueprint("integration_bp", __name__,
                           template_folder="templates",
                           static_folder="static")

# Instantiate gCalIntegratinator
gCalInterface = gCalIntegratinator()


# ------------------------------------
# --   Integration Helper Methods   --
# ------------------------------------

def createGoogleCalendar(calInfoId):
    # Create a Secondary Google Calendar for the provided hall using the Google
    #  Calendar Account information stored in the DB.
    #
    #  Required Auth Level: None
    #
    #  This function accepts the following parameters and packages them into
    #  a dictionary object with the same keys:
    #
    #     calInfoId  <int>  -  integer representing the google_calendar_info.id
    #                           field in the DB that should be used to find the
    #                           appropriate account credentials.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the calendar creation was successful
    #     -1 : the calendar creation was unsuccessful

    # Create a DB cursor
    cur = ag.conn.cursor()

    logging.debug("Searching for the Hall's Calendar Information")

    # Query the DB for the hall's credentials
    cur.execute("SELECT token FROM google_calendar_info WHERE id = %s", (calInfoId,))

    # Load the result from the DB
    memview = cur.fetchone()

    # Check the query result to see if we were able to locate the desired credentials
    if memview is None:
        # If we were NOT able to locate the desired credentials

        # Log the occurrence.
        logging.info("No Google Calendar token found for Id: {}".format(calInfoId))

        # Return a failed standard return
        return jsonify(stdRet(-1, "No Token Found"))

    # If there is a token in the DB it will be returned as a MemoryView Object

    logging.debug("Converting Google Calendar Token to pickle")

    # Convert the MemoryView object to BytesIO object that we can use more easily.
    tmp = BytesIO(memview[0])

    # Convert the BytesIO object to a google.oauth2.credentials.Credentials object
    #  This is done by unpickling the BytesIO
    token = pickle.load(tmp)

    logging.debug("Creating Google Calendar")

    # Call the gCalInterface's createGoogleCalendar method to create the calendar
    #  on Google's side of things. This method will return the calId associated
    #  with the new Google Calendar.
    calId = gCalInterface.createGoogleCalendar(token)

    logging.debug("Updating Google Calendar Information")

    # Add the calendar_id into the Google Calendar Info table
    cur.execute("""UPDATE google_calendar_info
                   SET calendar_id = %s
                   WHERE id = %s""", (calId, calInfoId))

    # Commit the changes to the DB
    ag.conn.commit()

    # Return a successful standard return
    return stdRet(1, "successful")


# -------------------------------------
# --   Integration Process Methods   --
# -------------------------------------

@integration_bp.route("/GCalRedirect", methods=["GET"])
@login_required
def returnGCalRedirect():
    # API Method that initializes the process for connecting a Google
    #  Calendar Account to the hall associated with the user.
    #
    #  Required Auth Level: >= HD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, no parameters are required.
    #
    #  This method returns Flask redirect to redirect the user to
    #  the Google Authorization URL to take the next steps for
    #  connecting a Google Calendar Account on Google's side of things.

    # Get the user's information from the database
    userDict = getAuth()

    # Check to see if the user is authorized to view these settings
    # If the user is not at least an HD
    if userDict["auth_level"] < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to connect Google Calendar for Hall: {} -G"
                     .format(userDict["ra_id"], userDict["hall_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Get the authorization url and state from the Google Calendar Interface
    authURL, state = gCalInterface.generateAuthURL(ag.baseOpts["HOST_URL"] + "/int/GCalAuth")

    # Create the DB cursor object
    cur = ag.conn.cursor()

    logging.debug("Checking for previously associated calendar for Hall: {}".format(userDict["hall_id"]))

    # Check to see if a Google Calendar has been associated with the given hall.
    #  This is used to keep track of the incoming authorization response
    cur.execute("SELECT id FROM google_calendar_info WHERE res_hall_id = %s",
                (userDict["hall_id"], ))

    # Load the result from the DB
    res = cur.fetchone()

    # If there is not a calendar already associated with the hall
    if res is None:
        # Then insert a new row with the authorization state so that
        #  we can find it again later when the Authorization Response
        #  comes in.
        logging.debug("Insert new row into Google Calendar Info table")

        # Execute the INSERT statement to add the new row into the DB
        cur.execute("""INSERT INTO google_calendar_info (res_hall_id, auth_state) 
                        VALUES (%s, %s)""", (userDict["hall_id"], state))

    else:
        # Otherwise update the entry for the appropriate hall with the current state
        logging.debug("Updating previous Google Calendar Info Row: {}".format(res[0]))

        cur.execute("UPDATE google_calendar_info SET auth_state = %s WHERE id = %s",
                    (state, res[0]))

    logging.debug("Committing auth state to DB for Hall: {}".format(userDict["hall_id"]))

    # Commit the changes to the DB
    ag.conn.commit()

    # Redirect the user to the Google Authorization URL
    return redirect(authURL)


@integration_bp.route("/GCalAuth", methods=["GET"])
@login_required
def handleGCalAuthResponse():
    # API Method that handles the Google Calendar authorization response
    #  and generates Google Calendar credentials that are saved in the DB.
    #
    #  Required Auth Level: >= HD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     state  <str>  -  a string denoting the authorization
    #                       state associated with this authorization
    #                       response.
    #
    #  This method returns a Flask redirect to redirect the user to
    #  the hall_bp.manHall page.

    # Get the user's information
    userDict = getAuth()

    # Check to see if the user is authorized to add Google Calendar
    #  Integration.
    # If the user is not at least an HD
    if userDict["auth_level"] < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to connect Google Calendar for Hall: {} -R"
                     .format(userDict["ra_id"], userDict["hall_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Get the state that was passed back by the authorization response.
    #  This is used to map the request to the response
    state = request.args.get("state")

    logging.debug("Found state in request")

    # Create DB cursor object
    cur = ag.conn.cursor()

    logging.debug("Searching for hall associated with state")

    # Query the DB to identify which hall maps to the given auth state
    cur.execute("SELECT id FROM google_calendar_info WHERE auth_state = %s", (state,))

    # Load the result from the query
    calInfoId = cur.fetchone()

    # Check to see if we have a result
    if calInfoId is None:
        # If not, stop processing
        logging.debug("Associated hall not found")

        # Notify the user of this issue.
        return jsonify(stdRet(-1, "Invalid State Received"))

    # Get the credentials from the Google Calendar Interface
    creds = gCalInterface.handleAuthResponse(request.url,
                                             ag.baseOpts["HOST_URL"] + "integration/int/GCalAuth")

    logging.debug("Received user credentials from interface")

    # Create BytesIO to hold the pickled credentials
    tmp = BytesIO()

    # Dump the pickled credentials into the BytesIO
    pickle.dump(creds, tmp)

    # Set the read position back to the beginning of the buffer.
    #  Without doing this, pickle.load will get an EOF error.
    tmp.seek(0)

    logging.debug("Created credential pickle")

    # Insert the credentials in the DB for the respective res_hall
    cur.execute("""UPDATE google_calendar_info
                   SET token = %s ,
                       auth_state = NULL
                   WHERE id = %s;""",
                (tmp.getvalue(), calInfoId[0]))

    # Create a Secondary Google Calendar with Google that we can export
    #  the schedule to.
    res = createGoogleCalendar(calInfoId[0])

    # If the calendar creation failed...
    if res["status"] < 0:
        # Then log the occurrence
        logging.warning("Unable to Create Google Calendar for Hall: {} - Rolling back changes"
                        .format(userDict["hall_id"]))

        # And rollback the Google Calendar Account Connection creation
        ag.conn.rollback()

        # TODO: I suspect that this rollback statement is unnecessary and possibly cumbersome
        #        in an environment where multiple DB changes are made in short proximity to
        #        each other. At this time, however, I do not have any evidence of this and will
        #        leave the result as-is.

    else:
        # Otherwise commit the changes made to the DB
        ag.conn.commit()

    logging.info("Google Calendar Creation complete for Hall: {}".format(userDict["hall_id"]))

    # Return the user back to the Manage Hall page
    return redirect(url_for("hall_bp.manHall"))


@integration_bp.route("/disconnectGCal", methods=["GET"])
@login_required
def disconnectGoogleCalendar():
    # API Method that disconnect the Google Calendar for the requesting
    #  user's Res Hall.
    #
    #  Required Auth Level: >= HD
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, no parameters are required.
    #
    #  This method returns a Flask redirect to redirect the user to
    #  the hall_bp.manHall page.

    # Get the user's information from the database
    userDict = getAuth()

    # Check to see if the user is authorized to disconnect Google
    #  Calendar Integration.
    # If the user is not at least an HD
    if userDict["auth_level"] < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to disconnect Google Calendar for Hall: {}"
                     .format(userDict["ra_id"], userDict["hall_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Create the cursor
    cur = ag.conn.cursor()

    # Delete the google_calendar_info record for the appropriate hall.
    cur.execute("DELETE FROM google_calendar_info WHERE res_hall_id = %s;", (userDict["hall_id"], ))

    # Redirect user back to Manage Hall page
    return redirect(url_for("manHall"))


# ---------------------
# --   API Methods   --
# ---------------------

@integration_bp.route("/api/exportToGCal", methods=["GET"])
@login_required
def exportToGCal():
    # API Method that exports the given schedule to the Google
    #  Calendar associated with the user's Res Hall.
    #
    #  Required Auth Level: >= AHD
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
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the export was successful
    #      0 : the user's Res Hall must reconnect the Google Calendar Account
    #     -1 : the export was unsuccessful

    # Get the user's information
    userDict = getAuth()

    # Check to see if the user is authorized to export to Google Calendar
    # If the user is not at least an AHD
    if userDict["auth_level"] < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to export schedule to Google Calendar"
                     .format(userDict["ra_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    logging.info("Attempting to export Schedule to Google Calendar")

    # First up, get the Google Calendar credentials from the DB

    logging.debug("Retrieving Google Calendar info from DB for Hall: {}".format(userDict["hall_id"]))

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the calendar_id and token associated with the user's Res Hall
    cur.execute("SELECT calendar_id, token FROM google_calendar_info WHERE res_hall_id = %s",
                (userDict["hall_id"], ))

    # Load the data from the query
    res = cur.fetchone()

    # Check to see if we got a result
    if res is None:
        # If we returned no values, the Res Hall has not completed the
        #  authorization process.

        logging.info("No Google Calendar token found for Hall: {}".format(userDict["hall_id"]))

        # We will need to let the user know that they will need
        #  to connect/reconnect their Google Calendar Account.
        return jsonify(stdRet(0, "No Token Found"))

    else:
        # Otherwise, if we have a result, then split the data into its components
        gCalId, memview = res

    logging.debug("GCalId: {}".format(gCalId))

    # If there is a token in the DB it will be returned as a MemoryView object

    # Convert the MemoryView object object to BytesIO object
    tmp = BytesIO(memview)

    # Convert the BytesIO object to a google.oauth2.credentials.Credentials object
    #  This is done by unpickling the object
    token = pickle.load(tmp)

    logging.debug("Google Calendar information found.")

    # Load the month/schedule information from the request args
    #  and create the start and end strings
    monthNum = int(request.args.get("monthNum"))
    year = int(request.args.get("year"))

    # Format the start and end date strings
    start = formatDateStr(1, monthNum, year)
    end = formatDateStr(monthrange(year, monthNum)[-1], monthNum, year)

    logging.debug("Retrieving schedule information for MonthNum: {} and Year: {}".format(monthNum, year))

    # Get the appropriate regular-duty schedule from the DB
    #  Should be able to leverage existing RADSA API
    regSched = getSchedule2(start=start, end=end,
                            hallId=userDict["hall_id"], showAllColors=True)

    # Get the appropriate break-duty schedule from the DB
    #  Should be able to leverage existing RADSA API
    breakSched = getBreakDuties(start=start, end=end,
                                hallId=userDict["hall_id"], showAllColors=True)

    logging.debug("Exporting schedule to Google Calendar.")

    # Pass the combined regular and break duty schedule to the Integratinator to be exported.
    status = gCalInterface.exportScheduleToGoogleCalendar(token, gCalId, regSched + breakSched)

    # If the export failed
    if status < 0:
        # Log that an error was encountered for future reference.
        logging.warning("Error: {} encountered while exporting to Google Calendar for Hall: {}".format(status, userDict["hall_id"]))

        # Then we will need to let the user know that they will need
        #  to connect/reconnect their Google Calendar Account. This is
        #  a default suggestion as there currently is no implementation
        #  that gives us a more granular look at what went wrong.
        return jsonify(stdRet(0, "Reconnect Google Calendar Account"))

    # Otherwise report that it was a success!
    return jsonify(stdRet(1, "successful"))
