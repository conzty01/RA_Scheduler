from flask import render_template, request, Blueprint, abort
from flask_login import login_required
from psycopg2.extras import Json
from calendar import month_name
import logging

# Import the appGlobals for this blueprint to use
import appGlobals as ag

# Import the needed functions from other parts of the application
from helperFunctions.helperFunctions import getAuth, stdRet, packageReturnObject

# Create the blueprint representing these routes
hall_bp = Blueprint("hall_bp", __name__,
                    template_folder="templates",
                    static_folder="static")

# ---------------------
# --      Views      --
# ---------------------

@hall_bp.route("/")
@login_required
def manHall():
    # The landing page for this blueprint that will display the Hall Settings
    #  to the user and provide a way for them to edit said settings.

    # Authenticate the user against the DB
    authedUser = getAuth()

    # If the user is not at least an HD
    if authedUser.auth_level() < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to reach Manage Hall page"
                     .format(authedUser.ra_id()))

        # Raise an 403 Access Denied HTTP Exception that will be handled by flask
        abort(403)

    # Render and return the appropriate template.
    return render_template("hall/hall.html", opts=ag.baseOpts, curView=4,
                           settingList=getHallSettings(authedUser.hall_id()),
                           auth_level=authedUser.auth_level(), hall_name=authedUser.hall_name(),
                           linkedHalls=authedUser.getAllAssociatedResHalls())


# ---------------------
# --   API Methods   --
# ---------------------

@hall_bp.route("/api/getHallSettings", methods=["GET"])
@login_required
def getHallSettings(hallId=None):
    # API Method used to return an object containing the list of hall settings
    #  for the desired hall.
    #
    #  If called from the server, this function accepts the following parameters:
    #
    #     hallId  <int>  -  an integer representing the id of the desired residence
    #                        hall in the res_hall table.
    #
    #  If called from a client, this function does not accept any parameters, but
    #  rather, uses the hall id that is associated with the user.
    #
    #  This method returns an object with the following specifications:
    #
    #     [
    #        {
    #           "settingName": ""
    #           "settingDesc": ""
    #           "settingVal": ""
    #        },
    #        ...
    #     ]

    # Assume this API was called from the server and verify that this is true.
    fromServer = True
    if hallId is None:
        # If hallId is None, then this method was called from a remote client.

        # Get the user's information from the database
        authedUser = getAuth()
        # Set the value of hallId from the userDict
        hallId = authedUser.hall_id()
        # Mark that this method was not called from the server
        fromServer = False

        # Check to see if the user is authorized to view these settings
        # If the user is not at least an HD
        if authedUser.auth_level() < 3:
            # Then they are not permitted to see this view.

            # Log the occurrence.
            logging.info("User Not Authorized - RA: {} attempted to get Hall Settings"
                         .format(authedUser.ra_id()))

            # Notify the user that they are not authorized.
            return packageReturnObject(stdRet(-1, "NOT AUTHORIZED"), fromServer)

    logging.debug("Retrieving Hall Setting information for Hall: {}, From Server: {}"
                  .format(hallId, fromServer))

    # Create the setting list that will be returned
    settingList = []

    # Create a DB cursor
    cur = ag.conn.cursor()

    # -------------------------------
    # --   Non-Standard Settings   --
    # -------------------------------

    # Get the hall name
    cur.execute("SELECT name FROM res_hall WHERE id = %s", (hallId,))

    # Assemble the Residence Hall Name Setting information in a temporary dict
    hallName = cur.fetchone()[0]
    tmp = {
        "settingVal": hallName,
        "settingData": hallName
    }

    # Update the tmp dict with the setting name and description from the
    # settingDescMap dictionary
    tmp.update(settingDescMap["hallName"])

    # Add the Hall Name settings to the settingList
    settingList.append(tmp)

    # Get the Google Calendar Information
    cur.execute("""SELECT EXISTS 
                      (SELECT token 
                       FROM google_calendar_info
                       WHERE res_hall_id = %s)""", (hallId,))

    # Assemble the Google Calendar Integration information in a temporary dict
    connected = "Connected" if cur.fetchone()[0] else "Not Connected"
    tmp = {
        "settingVal": connected,
        "settingData": connected
    }

    # Update the tmp dict with the setting name and description from the
    # settingDescMap dictionary
    tmp.update(settingDescMap["gCalInt"])

    # Add the Google Calendar Integration settings to the settingList
    settingList.append(tmp)

    # ---------------------------
    # --   Standard Settings   --
    # ---------------------------

    # Query the hall settings from the hall_settings table
    cur.execute("""
    SELECT year_start_mon, year_end_mon, duty_config, auto_adj_excl_ra_pts, 
           flag_multi_duty, duty_flag_label
    FROM hall_settings
    WHERE res_hall_id = %s
    """, (hallId,))

    # Load the query result into appropriate variables so that we can group
    #  them as desired
    yearStartMon, yearEndMon, \
    dutyConfig, autoAdjExclRAPts, \
    flagMultiDuty, flagLabel = cur.fetchone()

    # Create a dictionary to map the DB results to the settingDescMap keys
    settingGroupMap = {
        "yearStartEnd": {
            "settingVal": "{} - {}".format(month_name[yearStartMon], month_name[yearEndMon]),
            "settingData": {"start": yearStartMon, "end": yearEndMon}
        },
        "dutyConfig": {
            "settingVal": "Configured",
            "settingData": dutyConfig
        },
        "autoAdjExclRAPts": {
            "settingVal": "Enabled" if autoAdjExclRAPts else "Disabled",
            "settingData": autoAdjExclRAPts
        },
        "multiDutyFlag": {
            "settingVal": "'{}' label {}".format(flagLabel, "Enabled" if flagMultiDuty else "Disabled"),
            "settingData": {"flag": flagMultiDuty, "label": flagLabel}
        }
    }

    # Close the DB cursor
    cur.close()

    # Iterate through the keys of the settingGroupMap
    for key in settingGroupMap.keys():

        # Create a dictionary for the respective setting
        tmp = settingGroupMap[key]

        # Update the dictionary with the appropriate setting name and description
        tmp.update(settingDescMap[key])

        # Append the setting to the settingList
        settingList.append(tmp)

    # Return the settings
    return packageReturnObject(settingList, fromServer)


@hall_bp.route("/api/saveHallSettings", methods=["POST"])
@login_required
def saveHallSettings():
    # API Method used to save changes made to the Hall Settings for the user's hall.
    #
    #  This method is currently unable to be called from the server.
    #
    #  If called from a client, the following parameters are required:
    #
    #     name   <str>  -  The name of the Hall Setting that has been changed.
    #     value  <ukn>  -  The new value for the setting that has been altered.
    #
    #  This method returns a standard return object whose status is one of the
    #  following:
    #
    #      1 : the save was successful
    #      0 : the user does not belong to the provided hall
    #     -1 : the save was unsuccessful


    # Get the user's information from the database
    authedUser = getAuth()

    # Check to see if the user is authorized to alter these settings
    # If the user is not at least an HD
    if authedUser.auth_level() < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to overwrite Hall Settings for : {}"
                     .format(authedUser.ra_id(), authedUser.hall_id()))

        # Notify the user that they are not authorized.
        return packageReturnObject(stdRet(-1, "NOT AUTHORIZED"))

    # Get the name and value of the setting that was changed.
    data = request.json
    setName = data["name"]
    setVal = data["value"]

    logging.debug("Setting Name: {}".format(setName))
    logging.debug("Setting Value: {}".format(setVal))

    # Create a cursor
    cur = ag.conn.cursor()

    # Make sure that the user belongs to the hall whose settings are being changed
    cur.execute("""SELECT res_hall.id
                   FROM res_hall JOIN staff_membership AS sm ON (sm.res_hall_id = res_hall.id)
                   WHERE sm.ra_id = %s;""", (authedUser.ra_id(),))

    # Load the query result
    dbHallId = cur.fetchone()

    # Check to see if we have a valid result
    if dbHallId is None:
        # If we returned no values, then something fishy is going on.
        #  Simply return a not authorized message and stop processing.

        logging.info("User Not Authorized - RA: {} attempted to overwrite Hall Settings for : {}"
                     .format(authedUser.ra_id(), authedUser.hall_id()))

        # Close the DB cursor
        cur.close()

        # Indicate to the client that the user does not belong to the provided hall
        return packageReturnObject(stdRet(0, "NOT AUTHORIZED"))

    # Log that the user is updating the provided setting for the given hall
    logging.info("User: {} is updating Hall Setting: '{}' for Hall: {}"
                 .format(authedUser.ra_id(), setName, authedUser.hall_id()))

    # Otherwise, figure out what setting we are attempting to change and whether
    #  it should be handled in a special way.
    if setName == "Residence Hall Name":
        # We are attempting to update the res_hall.name field in the DB

        # Update the setting
        cur.execute("UPDATE res_hall SET name = %s WHERE id = %s", (setVal, authedUser.hall_id()))
        # Commit the change to the DB
        ag.conn.commit()

        # Close the DB cursor
        cur.close()

        # Return a successful result
        return packageReturnObject(stdRet(1, "successful"))

    elif setName == "Duty Configuration":
        # We are attempting to update the hall_settings.duty_config field in the DB

        # Update the setting
        cur.execute("UPDATE hall_settings SET duty_config = %s WHERE res_hall_id = %s;",
                    (Json(setVal), authedUser.hall_id()))

        # Commit the change to the DB
        ag.conn.commit()

        # Close the DB cursor
        cur.close()

        # Return a successful result
        return packageReturnObject(stdRet(1, "successful"))

    elif setName == "Defined School Year":
        # We are attempting to update the hall_settings.year_start_mon and
        #  hall_settings.year_end_mon fields in the DB.

        # Update the setting
        cur.execute("""UPDATE hall_settings 
                       SET year_start_mon = %s, year_end_mon = %s
                       WHERE res_hall_id = %s;""",
                    (setVal["start"], setVal["end"], authedUser.hall_id()))

        # Commit the change to the DB
        ag.conn.commit()

        # Close the DB cursor
        cur.close()

        # Return a successful result
        return packageReturnObject(stdRet(1, "successful"))

    elif setName == "Multi-Duty Day Flag":
        # We are attempting to update the hall_settings.flag_multi_duty and
        #  hall_settings.duty_flag_label fields in the DB.

        # Update the setting
        cur.execute("""UPDATE hall_settings 
                       SET flag_multi_duty = %s, duty_flag_label = %s
                       WHERE res_hall_id = %s;""",
                    (bool(setVal["flag"]), setVal["label"], authedUser.hall_id()))

        # Commit the change to the DB
        ag.conn.commit()

        # Close the DB cursor
        cur.close()

        # Return a successful result
        return packageReturnObject(stdRet(1, "successful"))

    elif setName == "Automatic RA Point Adjustment":
        # We are attempting to update the hall_settings.auto_adj_excl_ra_pts

        cur.execute("UPDATE hall_settings SET auto_adj_excl_ra_pts = %s WHERE res_hall_id = %s;",
                    (setVal, authedUser.hall_id()))

        # Commit the change to the DB
        ag.conn.commit()

        # Close the DB cursor
        cur.close()

        # Return a successful result
        return packageReturnObject(stdRet(1, "successful"))

    else:
        # We are attempting to update a setting that does not require any special attention.

        # Currently there are no other settings to be modified so this is just a placeholder
        #  for future implementation.

        logging.warning("Unable to handle Hall Setting: {}".format(setName))

    # Close the DB cursor
    cur.close()

    # Indicate to the client that the save was successful
    return packageReturnObject(stdRet(0, "Unknown Setting Provided"))


# ----------------------
# --  Helper Objects  --
# ----------------------
# The settingDescMap is a dictionary object which will be used to store and recall the human-
#  friendly name and description of each of the hall settings that are stored in the DB.
#  Effectively, this is a dictionary that describes all of the setting groups that an HD+ can
#  interact with in the manage hall page.
settingDescMap = {
    "hallName": {
        "settingName": "Residence Hall Name",
        "settingDesc": "The name of the Residence Hall."
    },
    "gCalInt": {
        "settingName": "Google Calendar Integration",
        "settingDesc": "Connecting a Google Calendar account allows AHDs and " +
                       "HDs to export a given month's duty schedule to Google Calendar."
    },
    "yearStartEnd": {
        "settingName": "Defined School Year",
        "settingDesc": "The start and end dates that outline the beginning and end of "
                       "the school year."
    },
    "dutyConfig": {
        "settingName": "Duty Configuration",
        "settingDesc": "The configuration for how the duty scheduler should schedule a given " +
                       "month's duties."
    },
    "autoAdjExclRAPts": {
        "settingName": "Automatic RA Point Adjustment",
        "settingDesc": "Automatically create point modifiers for RAs that have been excluded " +
                       "from being scheduled for duty for a given month. If enabled, the point " +
                       "modifier will be equal to the average number of points that were awarded " +
                       "for the month."
    },
    "multiDutyFlag": {
        "settingName": "Multi-Duty Day Flag",
        "settingDesc": "On days with multiple duties, automatically flag one duty slot with a " +
                       "customized label."
    }
}
