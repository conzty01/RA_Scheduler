from flask import render_template, request, jsonify, Blueprint
from flask_login import login_required
import logging
import os

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
    userDict = getAuth()

    # If the user is not at least an AHD
    if userDict["auth_level"] < 2:
        # Then they are not permitted to see this view.

        # Log the occurrence.
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))

        # Notify the user that they are not authorized.
        return jsonify(stdRet(-1, "NOT AUTHORIZED"))

    # Get the information for the current school year.
    #  This will be used to calculate break duty points for the RAs.
    start, end = getCurSchoolYear()

    logging.debug(start)
    logging.debug(end)

    # Call getRABreakStats to get information on the number of Break Duty
    # points each RA has for the current school year
    bkDict = getRABreakStats(userDict["hall_id"], start, end)

    logging.debug(str(bkDict))

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the necessary information about the staff's RAs.
    cur.execute("SELECT id, first_name, last_name, color FROM ra WHERE hall_id = %s ORDER BY first_name ASC;",
                (userDict["hall_id"],))

    # Render and return the appropriate template
    return render_template("breaks/editBreaks.html", raList=cur.fetchall(), auth_level=userDict["auth_level"],
                           bkDict=sorted(bkDict.items(), key=lambda x: x[1]["name"].split(" ")[1] ),
                           curView=3, opts=ag.baseOpts, hall_name=userDict["hall_name"])


# ---------------------
# --   API Methods   --
# ---------------------

@breaks_bp.route("/api/getRABreakStats", methods=["GET"])
@login_required
def getRABreakStats(hallId=None,startDateStr=None,endDateStr=None):
    # API Hook that will get the RA stats for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  The server will then query the database for the appropriate statistics
    #  and send back a json object.

    fromServer = True
    if hallId is None and startDateStr is None and endDateStr is None:          # Effectively: If API was called from the client and not from the server
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False
        startDateStr = request.args.get("start")
        endDateStr = request.args.get("end")

    logging.debug("Get RA Break Duty Stats - FromServer: {}".format(fromServer))

    res = {}

    cur = ag.conn.cursor()

    cur.execute("""SELECT ra.id, ra.first_name, ra.last_name, COALESCE(numQuery.count, 0)
                   FROM (SELECT ra.id AS rid, COUNT(break_duties.id) AS count
                         FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                                           JOIN ra ON (ra.id=break_duties.ra_id)
                         WHERE break_duties.hall_id = {}
                         AND day.date BETWEEN TO_DATE('{}', 'YYYY-MM-DD')
                                          AND TO_DATE('{}', 'YYYY-MM-DD')
                        GROUP BY rid) AS numQuery
                   RIGHT JOIN ra ON (numQuery.rid = ra.id)
                   WHERE ra.hall_id = {};""".format(hallId, startDateStr, \
                        endDateStr, hallId))

    raList = cur.fetchall()

    for ra in raList:
        res[ra[0]] = { "name": ra[1] + " " + ra[2], "count": ra[3] }

    cur.close()
    if fromServer:
        # If this function call is from the server, simply return the results
        return res
    else:
        # Otherwise, if this function call is from the client, return the
        #  results as a JSON response object.
        return jsonify(res)

@breaks_bp.route("/api/getBreakDuties", methods=["GET"])
@login_required
def getBreakDuties(hallId=None, start=None, end=None, showAllColors=False):
    userDict = getAuth()

    fromServer = True
    if start is None and end is None and hallId is None:                    # Effectively: If API was called from the client and not from the server
        start = request.args.get("start").split("T")[0]                         # No need for the timezone in our current application
        end = request.args.get("end").split("T")[0]                             # No need for the timezone in our current application

        showAllColors = request.args.get("allColors") == "true"                 # Should all colors be displayed or only the current user's colors

        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False

    cur = ag.conn.cursor()

    cur.execute("""
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD')
        FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                          JOIN month ON (month.id=break_duties.month_id)
                          JOIN ra ON (ra.id=break_duties.ra_id)
        WHERE break_duties.hall_id = {}
        AND month.year >= TO_DATE('{}','YYYY-MM')
        AND month.year <= TO_DATE('{}','YYYY-MM')
    """.format(hallId,start,end))

    res = []

    for row in cur.fetchall():

        if not(showAllColors):
            # If the desired behavior is to not show all of the unique RA colors
            #  then check to see if the current user is the ra on the duty being
            #  added. If it is the ra, show their unique color, if not, show the
            #  same color.
            if userDict["ra_id"] == row[3]:
                c = row[2]
            else:
                c = "#2C3E50"

        # If the desired behavior is to show all of the unique RA colors, then
        #  simply set their color.
        else:
            c = row[2]

        res.append({
            "id": row[3],
            "title": row[0] + " " + row[1],
            "start": row[4],
            "color": c,
            "extendedProps": {"dutyType":"brk"}
        })

    if fromServer:
        return res
    else:
        return jsonify(res)

@breaks_bp.route("/api/addBreakDuty", methods=["POST"])
def addBreakDuty():
    userDict = getAuth()

    data = request.json

    selID = data["id"]
    hallId = userDict["hall_id"]
    ptVal = data["pts"]
    dateStr = data["dateStr"]

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    cur = ag.conn.cursor()

    # Validate that the RA desired exists and belongs to the same hall
    cur.execute("SELECT id FROM ra WHERE id = {} AND hall_id = {};".format(selID, hallId))
    raId = cur.fetchone()

    if raId is None:
        cur.close()
        logging.warning("Unable to find RA {} in hall {}".format(selID,hallId))
        ret = stdRet(-1,"Unable to find RA {} in hall {}".format(selID,hallId))

    else:
        # Extract the id from the tuple
        raId = raId[0]

    # Get the month and day IDs necessary to associate a record in break_duties
    cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE('{}', 'YYYY-MM-DD');".format(dateStr))
    dayID, monthId = cur.fetchone()

    # No Day found
    if dayID is None:
        cur.close()
        logging.warning("Unable to find day {} in database".format(data["dateStr"]))
        return stdRet(-1,"Unable to find day {} in database".format(data["dateStr"]))

    # No month found
    if monthId is None:
        cur.close()
        logging.warning("Unable to find month for {} in database".format(data["dateStr"]))
        return stdRet(-1,"Unable to find month for {} in database".format(data["dateStr"]))

    cur.execute("""INSERT INTO break_duties (ra_id, hall_id, month_id, day_id, point_val)
                    VALUES ({}, {}, {}, {}, {});""".format(raId, hallId, monthId, dayID, ptVal))

    ag.conn.commit()

    cur.close()

    logging.info("Successfully added new Break Duty for Hall {} and Month {}".format(hallId, monthId))

    return jsonify(stdRet(1,"successful"))

@breaks_bp.route("/api/deleteBreakDuty", methods=["POST"])
@login_required
def deleteBreakDuty():
        userDict = getAuth()

        data = request.json
        fName, lName = data["raName"].split()
        hallId = userDict["hall_id"]
        dateStr = data["dateStr"]

        if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
            logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
            return jsonify(stdRet(-1,"NOT AUTHORIZED"))

        logging.debug("Deleted Break Duty RA Name: {}".format(fName + " " + lName))
        logging.debug("HallID: {}".format(hallId))
        # Expected as x-x-xxxx
        logging.debug("DateStr: {}".format(dateStr))

        cur = ag.conn.cursor()

        cur.execute("SELECT id FROM ra WHERE first_name LIKE '{}' AND last_name LIKE '{}' AND hall_id = {};".format(fName,lName,userDict["hall_id"]))
        raId = cur.fetchone()

        cur.execute("SELECT id, month_id FROM day WHERE date = TO_DATE('{}', 'MM/DD/YYYY');".format(data["dateStr"]))
        dayID, monthId = cur.fetchone()

        if raId is not None and dayID is not None and monthId is not None:
            cur.execute("""DELETE FROM break_duties
                            WHERE ra_id = {}
                            AND hall_id = {}
                            AND day_id = {}
                            AND month_id = {}""".format(raId[0], hallId, dayID, monthId))

            ag.conn.commit()

            cur.close()

            logging.info("Successfully deleted duty")
            return jsonify(stdRet(1,"successful"))

        else:

            cur.close()

            logging.info("Unable to locate beak duty to delete: RA {}, Date {}".format(fName + " " + lName, dateStr))
            return jsonify({"status":0,"error":"Unable to find parameters in DB"})
