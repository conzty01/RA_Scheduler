from flask import render_template, request, jsonify, Blueprint
from flask_login import login_required
import logging

# Import the appGlobals for this blueprint to use
import appGlobals as ag

# Import the needed functions from other parts of the application
from helperFunctions.helperFunctions import getAuth, stdRet

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
    userDict = getAuth()

    # If the user is not at least an HD
    if userDict["auth_level"] < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to reach Manage Hall page".format(userDict["ra_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Render and return the appropriate template.
    return render_template("hall/hall.html", opts=ag.baseOpts, curView=4,
                           settingList=getHallSettings(userDict["hall_id"]),
                           auth_level=userDict["auth_level"], hall_name=userDict["hall_name"])


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
        userDict = getAuth()
        # Set the value of hallId from the userDict
        hallId = userDict["hall_id"]
        # Mark that this method was not called from the server
        fromServer = False

        # Check to see if the user is authorized to view these settings
        # If the user is not at least an HD
        if userDict["auth_level"] < 3:
            # Then they are not permitted to see this view.

            # Log the occurrence.
            logging.info("User Not Authorized - RA: {} attempted to get Hall Settings".format(userDict["ra_id"]))

            # Notify the user that they are not authorized.
            return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    logging.debug("Retrieving Hall Setting information for Hall: {}, From Server: {}".format(hallId, fromServer))

    # Create the setting list that will be returned
    settingList = []

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Get the hall name
    cur.execute("SELECT name FROM res_hall WHERE id = %s", (hallId,))

    # Assemble the Residence Hall Name Setting information in a temporary dict
    tmp = {"settingName": "Residence Hall Name",
           "settingDesc": "The name of the Residence Hall.",
           "settingVal": cur.fetchone()[0]}

    # Add the Hall Name settings to the settingList
    settingList.append(tmp)

    # Get the Google Calendar Information
    cur.execute("""SELECT EXISTS 
                      (SELECT token 
                       FROM google_calendar_info
                       WHERE res_hall_id = %s)""", (hallId,))

    # Assemble the Google Calendar Integration information in a temporary dict
    tmp = {"settingName": "Google Calendar Integration",
           "settingDesc": "Connecting a Google Calendar account allows AHDs and " +
                          "HDs to export a given month's duty schedule to Google Calendar.",
           "settingVal": "Connected" if cur.fetchone()[0] else "Not Connected"}

    # Add the Google Calendar Integration settings to the settingList
    settingList.append(tmp)

    # Close the DB cursor
    cur.close()

    # If this API method was called from the server
    if fromServer:
        # Then return the settingList as-is
        return settingList

    else:
        # Otherwise return a JSON version of the settingList
        return jsonify(settingList)


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
    userDict = getAuth()

    # Check to see if the user is authorized to alter these settings
    # If the user is not at least an HD
    if userDict["auth_level"] < 3:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {} attempted to overwrite Hall Settings for : {}"
                     .format(userDict["ra_id"], userDict["hall_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Get the name and value of the setting that was changed.
    data = request.json
    setName = data["name"]
    setVal = data["value"]

    logging.debug("Setting Name: {}".format(setName))
    logging.debug("Setting Value: {}".format(setVal))

    # Create a cursor
    cur = ag.conn.cursor()

    # Figure out what setting we are attempting to change and whether
    # is should be handled in a special way.

    if setName == "Residence Hall Name":
        # We are attempting to update the res_hall.name field in the DB

        # Make sure that the user belongs to that Hall
        cur.execute("""SELECT res_hall.id
                       FROM res_hall JOIN ra ON (ra.hall_id = res_hall.id)
                       WHERE ra.id = %s;""", (userDict["ra_id"],))

        dbHallId = cur.fetchone()

        if dbHallId is None:
            # If we returned no values, then something fishy is going on.
            #  Simply return a not authorized message and stop processing.

            logging.info("User Not Authorized - RA: {} attempted to overwrite Hall Settings for : {}"
                         .format(userDict["ra_id"], userDict["hall_id"]))

            # Close the DB cursor
            cur.close()

            # Indicate to the client that the user does not belong to the provided hall
            return jsonify(stdRet(0, "NOT AUTHORIZED"))

        else:
            # Otherwise go ahead and update the value.

            # log that the user is updating the provided setting for the given hall
            logging.info("User: {} is updating Hall Setting: '{}' for Hall: {}".format(userDict["ra_id"],
                                                                                       setName, userDict["hall_id"]))

            # Update the setting
            cur.execute("UPDATE res_hall SET name = %s WHERE id = %s", (setVal, userDict["hall_id"]))
            # Commit the change to the DB
            ag.conn.commit()

            # Close the DB cursor
            cur.close()

            # set the return value to successful
            return jsonify(stdRet(1, "successful"))

    else:
        # We are attempting to update a setting that does not require any special attention.

        # Currently there are no other settings to be modified so this is just a placeholder
        #  for future implementation.
        pass

    # Close the DB cursor
    cur.close()

    # Indicate to the client that the save was successful
    return jsonify(stdRet(1, "successful"))
