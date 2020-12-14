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
def getConflicts(monthNum=None,raID=None,year=None,hallId=None):
    # API Hook that will get the requested conflicts for a given user and month.
    #  The month will be given via request.args as 'monthNum' and 'year'.

    fromServer = True
    if monthNum is None and year is None and hallId is None and raID is None:                    # Effectively: If API was called from the client and not from the server
        monthNum = int(request.args.get("monthNum"))
        year = int(request.args.get("year"))

        userDict = getAuth()                                                    # Get the user's info from our database
        hallID = userDict["hall_id"]
        raID = userDict["ra_id"]
        fromServer = False

    logging.debug("Get Conflicts - From Server: {}".format(fromServer))

    logging.debug("MonthNum: {}, Year: {}, HallID: {}, raID: {}".format(monthNum, year, hallID, raID))

    cur = ag.conn.cursor()

    cur.execute("SELECT id FROM month WHERE num = {} AND EXTRACT(YEAR FROM year) = {}".format(monthNum, year))
    monthID = cur.fetchone()

    if monthID is None:
        logging.warning("No month found with Num = {}".format(monthNum))
        return jsonify(stdRet(-1,"No month found with Num = {}".format(monthNum)))

    else:
        monthID = monthID[0]

    cur.execute("""SELECT TO_CHAR(day.date, 'YYYY-MM-DD')
                   FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                   WHERE conflicts.ra_id = {}
                   AND day.month_id = {}""".format(raID, monthID, hallID))

    ret = [ d[0] for d in cur.fetchall() ]

    if fromServer:
        return ret
    else:
        return jsonify({"conflicts":ret})

@conflicts_bp.route("/api/getRAConflicts", methods=["GET"])
@login_required
def getRAConflicts():
    userDict = getAuth()

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    hallId = userDict["hall_id"]
    raId = request.args.get("raID")
    monthNum = request.args.get("monthNum")
    year = request.args.get("year")

    logging.debug("HallId: {}".format(hallId))
    logging.debug("RaId: {}".format(raId))
    logging.debug("MonthNum: {}".format(monthNum))
    logging.debug("Year: {}".format(year))
    logging.debug("RaId == -1? {}".format(int(raId) != -1))

    if int(raId) != -1:
        addStr = "AND conflicts.ra_id = {};".format(raId)
    else:
        addStr = ""

    logging.debug(addStr)

    cur = ag.conn.cursor()

    cur.execute("SELECT id FROM month WHERE num = {} AND EXTRACT(YEAR FROM year) = {}".format(monthNum, year))
    monthID = cur.fetchone()

    if monthID is None:
        logging.info("No month found with Num = {}".format(monthNum))
        return jsonify(stdRet(-1,"No month found with Num = {}".format(monthNum)))

    else:
        monthID = monthID[0]

    cur.execute("""SELECT conflicts.id, ra.first_name, ra.last_name, TO_CHAR(day.date, 'YYYY-MM-DD'), ra.color
                   FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                                  JOIN ra ON (ra.id = conflicts.ra_id)
                   WHERE day.month_id = {}
                   AND ra.hall_id = {}
                   {};""".format(monthID, hallId, addStr))

    conDates = cur.fetchall()
    logging.debug("ConDates: {}".format(conDates))

    res = []

    for d in conDates:
        res.append({
            "id": d[0],
            "title": d[1] + " " + d[2],
            "start": d[3],
            "color": d[4]
        })

    return jsonify(res)

@conflicts_bp.route("/api/getStaffConflicts", methods=["GET"])
@login_required
def getRACons(hallId=None,startDateStr=None,endDateStr=None):
    # API Hook that will get the conflicts for a given month and hall.
    #  The month will be given via request.args as 'start' and 'end'.
    #  The server will then query the database for the appropriate conflicts.

    fromServer = True
    if hallId is None and startDateStr is None and endDateStr is None:
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        startDateStr = request.args.get("start").split("T")[0]                  # No need for the timezone in our current application
        endDateStr = request.args.get("end").split("T")[0]                      # No need for the timezone in our current application

        fromServer = False

    logging.debug("Get Staff Conflicts - From Server: {}".format(fromServer))

    res = []

    cur = ag.conn.cursor()

    cur.execute("""
        SELECT ra.id, ra.first_name, ra.last_name, ra.color, TO_CHAR(day.date, 'YYYY-MM-DD')
        FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                       JOIN ra ON (conflicts.ra_id = ra.id)
        WHERE day.date >= TO_DATE('{}', 'YYYY-MM-DD')
        AND day.date <= TO_DATE('{}', 'YYYY-MM-DD')
        AND ra.hall_ID = {};
    """.format(startDateStr, endDateStr, hallId))

    rawRes = cur.fetchall()

    for row in rawRes:
        res.append({
            "id": row[0],
            "title": row[1] + " " + row[2],
            "start": row[4],
            "color": row[3]
        })

    if fromServer:
        return rawRes
    else:
        return jsonify(res)

@conflicts_bp.route("/api/getConflictNums", methods=["GET"])
@login_required
def getNumberConflicts(hallId=None,monthNum=None,year=None):

    fromServer = True
    if hallId is None and monthNum is None and year is None:
        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        monthNum = request.args.get("monthNum")
        year = request.args.get("year")

        fromServer = False

    if userDict["auth_level"] < 2:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    cur = ag.conn.cursor()

    cur.execute("""
        SELECT ra.id, COUNT(cons.id)
        FROM ra LEFT JOIN (
            SELECT conflicts.id, ra_id
            FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                           JOIN month ON (month.id = day.month_id)
            WHERE month.num = {}
            AND EXTRACT(YEAR FROM month.year) = {}
        ) AS cons ON (cons.ra_id = ra.id)
        WHERE ra.hall_id = {}
        GROUP BY ra.id;
    """.format(monthNum, year, hallId))

    res = {}
    for row in cur.fetchall():
        res[row[0]] = row[1]

    if fromServer:
        return res
    else:
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
