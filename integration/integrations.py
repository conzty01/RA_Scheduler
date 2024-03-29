from flask import request, redirect, url_for, Blueprint, abort
from integration.gCalIntegration import gCalIntegratinator
from flask_login import login_required
from psycopg2 import IntegrityError
from calendar import monthrange
from io import BytesIO
import logging
import pickle

# Import the appGlobals for this blueprint to use
import appGlobals as ag

# Import the needed functions from other parts of the application
from helperFunctions.helperFunctions import getAuth, stdRet, formatDateStr, packageReturnObject
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

        # Close the DB cursor
        cur.close()

        # Return a failed standard return
        return stdRet(-1, "No Token Found")

    # If there is a token in the DB it will be returned as a MemoryView Object

    logging.debug("Converting Google Calendar Token to pickle")

    # Convert the MemoryView object to BytesIO object that we can use more easily.
    tmp = BytesIO(memview[0])

    # Convert the BytesIO object to a google.oauth2.credentials.Credentials object
    #  This is done by unpickling the BytesIO
    token = pickle.load(tmp)

    logging.debug("Creating Google Calendar")

    # Build a try/except to catch any issues that arise during the calendar
    #  creation process.
    try:
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
        retStatus = stdRet(1, "successful")

    except gCalIntegratinator.InvalidCalendarCredentialsError as e:
        # If we receive an InvalidCalendarCredentialsError, then that means the
        #  credentials we parsed are not the expected credentials object.

        # Log the occurrence
        logging.error("Calendar Creation - Invalid Credential Object: Received {} Object".format(token))

        # We should notify the user that they will need to attempt to reconnect
        #  their Google Calendar Account.
        retStatus = stdRet(-1, "Reconnect Google Calendar Account")

    except gCalIntegratinator.ExpiredCalendarCredentialsError as e:
        # If we receive an ExpiredCalendarCredentialsError, then we were unable to
        #  refresh the user's credentials.

        # Log the occurrence
        logging.error("Calendar Creation - Unable to Refresh Google Calendar Credentials: "
                      "Expired - {}, Refresh Token - {}".format(token.expired, bool(token.refresh_token)))

        # We should notify the user that they will need to reconnect their Google Calendar Account.
        retStatus = stdRet(-1, "Reconnect Google Calendar Account")

    except gCalIntegratinator.UnexpectedError as e:
        # If we receive an UnexpectedError, then something happened during when validating credentials.

        # Log the occurrence
        logging.error("Calendar Creation - Unexpected Error Occurred During: {} - {}"
                      .format(e.exceptionLocation, e.wrappedException))

        # We should notify the user that an error occurred
        retStatus = stdRet(-1, "Unexpected Error Occurred. Please try again later.")

    except gCalIntegratinator.CalendarCreationError as e:
        # If we receive a CalendarCreationError, then we were unable to create a new Google Calendar.

        # Log the occurrence
        logging.error("Calendar Creation - Unable to Create new Google Calendar: {}".format(str(e)))

        # We should notify the user that an error occurred
        retStatus = stdRet(-1, "Unable to Create new Google Calendar. Please try again later.")

    except IntegrityError as e:
        # If we receive a psycopg2.IntegrityError, then we had an issue updating the DB.

        # Log the occurrence
        logging.error("Calendar Creation - Unable to Create new Google Calendar: Integrity Error")

        # In order for the server to recover the DB connection, we must rollback the change
        ag.conn.rollback()

        # We should notify the user that an error occurred
        retStatus = stdRet(-1, "Unexpected Error Occurred. Please try again later.")

    # Close the DB cursor
    cur.close()

    # Return a successful standard return
    return retStatus


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
    authedUser = getAuth()

    # Check to see if the user is authorized to view these settings
    # If the user is not at least an HD
    if authedUser.auth_level() < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to connect Google Calendar for Hall: {} -G"
                     .format(authedUser.ra_id(), authedUser.hall_id()))

        # Raise an 403 Access Denied HTTP Exception that will be handled by flask
        abort(403)

    # Get the authorization url and state from the Google Calendar Interface
    authURL, state = gCalInterface.generateAuthURL(ag.baseOpts["HOST_URL"] + "/int/GCalAuth")

    # Create the DB cursor object
    cur = ag.conn.cursor()

    logging.debug("Checking for previously associated calendar for Hall: {}".format(authedUser.hall_id()))

    # Check to see if a Google Calendar has been associated with the given hall.
    #  This is used to keep track of the incoming authorization response
    cur.execute("SELECT id FROM google_calendar_info WHERE res_hall_id = %s",
                (authedUser.hall_id(), ))

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
                        VALUES (%s, %s)""", (authedUser.hall_id(), state))

    else:
        # Otherwise update the entry for the appropriate hall with the current state
        logging.debug("Updating previous Google Calendar Info Row: {}".format(res[0]))

        cur.execute("UPDATE google_calendar_info SET auth_state = %s WHERE id = %s",
                    (state, res[0]))

    logging.debug("Committing auth state to DB for Hall: {}".format(authedUser.hall_id()))

    # Commit the changes to the DB
    ag.conn.commit()

    # Close the DB cursor
    cur.close()

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
    authedUser = getAuth()

    # Check to see if the user is authorized to add Google Calendar
    #  Integration.
    # If the user is not at least an HD
    if authedUser.auth_level() < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to connect Google Calendar for Hall: {} -R"
                     .format(authedUser.ra_id(), authedUser.hall_id()))

        # Raise an 403 Access Denied HTTP Exception that will be handled by flask
        abort(403)

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

        # Close the DB cursor
        cur.close()

        # Notify the user of this issue.
        return packageReturnObject(stdRet(-1, "Invalid State Received"))

    # Get the credentials from the Google Calendar Interface
    creds = gCalInterface.handleAuthResponse(request.url,
                                             ag.baseOpts["HOST_URL"] + "/int/GCalAuth")

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
        logging.warning("Unable to Create Google Calendar for Hall: {}" .format(authedUser.hall_id()))

    else:
        # Otherwise commit the changes made to the DB
        ag.conn.commit()

    logging.info("Google Calendar Creation complete for Hall: {}".format(authedUser.hall_id()))

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
    authedUser = getAuth()

    # Check to see if the user is authorized to disconnect Google
    #  Calendar Integration.
    # If the user is not at least an HD
    if authedUser.auth_level() < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to disconnect Google Calendar for Hall: {}"
                     .format(authedUser.ra_id(), authedUser.hall_id()))

        # Raise an 403 Access Denied HTTP Exception that will be handled by flask
        abort(403)

    # Create the cursor
    cur = ag.conn.cursor()

    # Delete the google_calendar_info record for the appropriate hall.
    cur.execute("DELETE FROM google_calendar_info WHERE res_hall_id = %s;", (authedUser.hall_id(), ))

    # Commit the changes to the DB
    ag.conn.commit()

    # Close the DB cursor
    cur.close()

    # Redirect user back to Manage Hall page
    return redirect(url_for("hall_bp.manHall"))


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
    authedUser = getAuth()

    # Check to see if the user is authorized to export to Google Calendar
    # If the user is not at least an AHD
    if authedUser.auth_level() < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to export schedule to Google Calendar"
                     .format(authedUser.ra_id()))

        # Notify the user that they are not authorized.
        return packageReturnObject(stdRet(-1, "NOT AUTHORIZED"))

    logging.info("Attempting to export Schedule to Google Calendar")

    # First up, get the Google Calendar credentials from the DB

    logging.debug("Retrieving Google Calendar info from DB for Hall: {}".format(authedUser.hall_id()))

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the calendar_id and token associated with the user's Res Hall
    cur.execute("SELECT calendar_id, token FROM google_calendar_info WHERE res_hall_id = %s",
                (authedUser.hall_id(), ))

    # Load the data from the query
    res = cur.fetchone()

    # Check to see if we got a result
    if res is None:
        # If we returned no values, the Res Hall has not completed the
        #  authorization process.

        logging.info("No Google Calendar token found for Hall: {}".format(authedUser.hall_id()))

        # Close the DB cursor
        cur.close()

        # We will need to let the user know that they will need
        #  to connect/reconnect their Google Calendar Account.
        return packageReturnObject(stdRet(0, "No Token Found"))

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
                            hallId=authedUser.hall_id(), showAllColors=True)

    # Get the appropriate break-duty schedule from the DB
    #  Should be able to leverage existing RADSA API
    breakSched = getBreakDuties(start=start, end=end,
                                hallId=authedUser.hall_id(), showAllColors=True)

    logging.debug("Exporting schedule to Google Calendar.")

    # Get the label for flagged duties for the Hall from the DB
    cur.execute("SELECT duty_flag_label FROM hall_settings WHERE res_hall_id = %s", (authedUser.hall_id(),))

    # Load the flag label
    flaggedDutyLabel = cur.fetchone()[0]

    try:
        # Pass the combined regular and break duty schedule to the Integratinator to be exported.
        gCalInterface.exportScheduleToGoogleCalendar(token, gCalId, regSched + breakSched, flaggedDutyLabel)

        # Notify the user that the export was successful
        retStatus = stdRet(1, "successful")

    except gCalIntegratinator.InvalidCalendarCredentialsError as e:
        # If we receive an InvalidCalendarCredentialsError, then that means the
        #  credentials we parsed are not the expected credentials object.

        # Log the occurrence
        logging.error("Exporting Schedule - Invalid Credential Object: Received {} Object".format(token))

        # We should notify the user that they will need to attempt to reconnect
        #  their Google Calendar Account.
        retStatus = stdRet(-1, "Reconnect Google Calendar Account")

    except gCalIntegratinator.ExpiredCalendarCredentialsError as e:
        # If we receive an ExpiredCalendarCredentialsError, then we were unable to
        #  refresh the user's credentials.

        # Log the occurrence
        logging.error("Exporting Schedule - Unable to Refresh Google Calendar Credentials: "
                      "Expired - {}, Refresh Token - {}".format(token.expired, bool(token.refresh_token)))

        # We should notify the user that they will need to reconnect their Google Calendar Account.
        retStatus = stdRet(-1, "Reconnect Google Calendar Account")

    except gCalIntegratinator.UnexpectedError as e:
        # If we receive an UnexpectedError, then something happened during when validating credentials.

        # Log the occurrence
        logging.error("Exporting Schedule - Unexpected Error Occurred During: {} - {}"
                      .format(e.exceptionLocation, e.wrappedException))

        # We should notify the user that an error occurred
        retStatus = stdRet(-1, "Unexpected Error Occurred. Please try again later.")

    except gCalIntegratinator.CalendarCreationError as e:
        # If we receive a CalendarCreationError, then we were unable to create a new Google Calendar.

        # Log the occurrence
        logging.error("Exporting Schedule - Unable to Create new Google Calendar: {}".format(str(e)))

        # We should notify the user that an error occurred
        retStatus = stdRet(-1, "Unable to Create new Google Calendar. Please try again later.")

    except gCalIntegratinator.ScheduleExportError as e:
        # If we receive a ScheduleExportError, then we had an issue exporting the schedule to Google Calendar.

        # Log the occurrence
        logging.error("Exporting Schedule - Error Received When Exporting: {}".format(e.wrappedException))

        # We should notify the user that an error occurred
        retStatus = stdRet(-1, "Unexpected Error Occurred. Please try again later.")

    # Close the DB cursor
    cur.close()

    # Otherwise report that it was a success!
    return packageReturnObject(retStatus)
