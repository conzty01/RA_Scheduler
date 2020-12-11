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


@hall_bp.route("/api/getHallSettings", methods=["GET"])
@login_required
def getHallSettings(hallId=None):
    # Return an object containing the list of Hall Settings for the desired Hall

    fromServer = True
    if hallId is None:          # Effectively: If API was called from the client and not from the server
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False

        # Check to see if the user is authorized to view these settings
        if userDict["auth_level"] < 3:
            logging.info("User Not Authorized - RA: {} attempted to get Hall Settings".format(userDict["ra_id"]))
            return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    logging.debug("Retrieving Hall Setting information for Hall: {}, From Server: {}".format(hallId, fromServer))

    # Create the setting list that will be returned
    settingList = []

    cur = ag.conn.cursor()

    # Get the hall name
    cur.execute("SELECT name FROM res_hall WHERE id = %s", (hallId,))

    tmp = {"settingName": "Residence Hall Name",
           "settingDesc": "The name of the Residence Hall.",
           "settingVal": cur.fetchone()[0]}

    # Add the hall settings to the settingList
    settingList.append(tmp)

    # Get the Google Calendar Information
    cur.execute("""SELECT EXISTS 
                      (SELECT token 
                       FROM google_calendar_info
                       WHERE res_hall_id = %s)""", (hallId,))

    tmp = {"settingName": "Google Calendar Integration",
           "settingDesc": "Connecting a Google Calendar account allows AHDs and HDs to export a given month's duty schedule to Google Calendar.",
           "settingVal": "Connected" if cur.fetchone()[0] else "Not Connected"}

    settingList.append(tmp)

    if fromServer:
        return settingList
    else:
        return jsonify(settingList)


@hall_bp.route("/api/saveHallSettings", methods=["POST"])
@login_required
def saveHallSettings():
    # Save the hall settings received

    userDict = getAuth()

    # Ensure that the user is at least an AHD
    if userDict["auth_level"] < 3:
        logging.info("User Not Authorized - RA: {} attempted to overwrite Hall Settings for : {}"
                     .format(userDict["ra_id"], userDict["hall_id"]))

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

            return jsonify(stdRet(0, "NOT AUTHORIZED"))

        else:
            # Otherwise go ahead and update the value.

            logging.info("User: {} is updating Hall Setting: '{}' for Hall: {}".format(userDict["ra_id"],
                                                                                       setName, userDict["hall_id"]))

            cur.execute("UPDATE res_hall SET name = %s WHERE id = %s", (setVal, userDict["hall_id"]))

            ag.conn.commit()

            cur.close()

            # set the return value to successful
            return jsonify(stdRet(1, "successful"))

    else:
        # We are attempting to update a setting that does not require any special attention.

        # Currently there are no other settings to be modified so this is just a placeholder
        #  for future implementation.
        pass

    cur.close()

    # Return the result back to the client.
    return jsonify(stdRet(1, "successful"))
