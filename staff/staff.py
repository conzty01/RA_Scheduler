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

@staff_bp.route("/api/getStats", methods=["GET"])
@login_required
def getRAStats(hallId=None, startDateStr=None, endDateStr=None, maxBreakDay=None):
    # API Hook that will get the RA stats for a given month.
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  The server will then query the database for the appropriate statistics
    #  and send back a json object.

    fromServer = True
    if hallId is None and startDateStr is None \
        and endDateStr is None and maxBreakDay is None:                         # Effectively: If API was called from the client and not from the server

        userDict = getAuth()                                                    # Get the user's info from our database
        hallId = userDict["hall_id"]
        fromServer = False
        startDateStr = request.args.get("start")
        endDateStr = request.args.get("end")

    logging.debug("Get RA Stats - FromServer: {}".format(fromServer))

    res = {}

    cur = ag.conn.cursor()

    breakDutyStart = startDateStr

    if maxBreakDay is None:
        # If maxBreakDay is None, then we should calculate the TOTAL number of points
        #  that each RA has for the course of the period specified (including
        #  all break duties).

        breakDutyEnd = endDateStr

    else:
        # If maxBreakDay is NOT None, then we should calculate the number of REGULAR
        #  duty points plus the number of BREAK duty points for the specified month.

        breakDutyEnd = maxBreakDay

    logging.debug("breakDutyStart: {}".format(breakDutyStart))
    logging.debug("breakDutyEnd: {}".format(breakDutyEnd))


    cur.execute("""SELECT ra.id, ra.first_name, ra.last_name, COALESCE(ptQuery.pts,0)
               FROM
               (
                   SELECT combined_res.rid AS rid, CAST(SUM(combined_res.pts) AS INTEGER) AS pts
                   FROM
                   (
                      SELECT ra.id AS rid, SUM(duties.point_val) AS pts
                      FROM duties JOIN day ON (day.id=duties.day_id)
                                  JOIN ra ON (ra.id=duties.ra_id)
                      WHERE duties.hall_id = {}
                      AND duties.sched_id IN
                      (
                         SELECT DISTINCT ON (schedule.month_id) schedule.id
                         FROM schedule
                         WHERE schedule.hall_id = {}
                         AND schedule.month_id IN
                         (
                             SELECT month.id
                             FROM month
                             WHERE month.year >= TO_DATE('{}', 'YYYY-MM-DD')
                             AND month.year <= TO_DATE('{}', 'YYYY-MM-DD')
                         )
                         ORDER BY schedule.month_id, schedule.created DESC, schedule.id DESC
                      )
                      GROUP BY rid

                      UNION

                      SELECT ra.id AS rid, SUM(break_duties.point_val) AS pts
                      FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                                        JOIN ra ON (ra.id=break_duties.ra_id)
                      WHERE break_duties.hall_id = {}
                      AND day.date BETWEEN TO_DATE('{}', 'YYYY-MM-DD')
                                       AND TO_DATE('{}', 'YYYY-MM-DD')
                      GROUP BY rid
                   ) AS combined_res
                   GROUP BY combined_res.rid
               ) ptQuery
               RIGHT JOIN ra ON (ptQuery.rid = ra.id)
               WHERE ra.hall_id = {};""".format(hallId, hallId, startDateStr, \
                                                endDateStr, hallId, breakDutyStart, \
                                                breakDutyEnd, hallId))

    raList = cur.fetchall()

    for ra in raList:
        res[ra[0]] = { "name": ra[1] + " " + ra[2], "pts": ra[3] }

    cur.close()
    if fromServer:
        # If this function call is from the server, simply return the results
        return res
    else:
        # Otherwise, if this function call is from the client, return the
        #  results as a JSON response object.
        return jsonify(res)

@staff_bp.route("/api/getStaffInfo", methods=["GET"])
@login_required
def getStaffStats():
    userDict = getAuth()

    if userDict["auth_level"] < 3:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    cur = ag.conn.cursor()

    cur.execute("""SELECT ra.id, first_name, last_name, email, date_started, res_hall.name, color, auth_level
                 FROM ra JOIN res_hall ON (ra.hall_id = res_hall.id)
                 WHERE hall_id = {} ORDER BY ra.id DESC;""".format(userDict["hall_id"]))

    start, end = getCurSchoolYear()
    pts = getRAStats(userDict["hall_id"], start, end)

    ret = {"raList": cur.fetchall(), "pts":pts}

    return jsonify(ret)

@staff_bp.route("/api/changeStaffInfo", methods=["POST"])
@login_required
def changeStaffInfo():
    userDict = getAuth()                                                        # Get the user's info from our database

    hallId = userDict["hall_id"]

    if userDict["auth_level"] < 3:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    data = request.json

    cur = ag.conn.cursor()
    cur.execute("""UPDATE ra
                   SET first_name = '{}', last_name = '{}',
                       date_started = TO_DATE('{}', 'YYYY-MM-DD'),
                       color = '{}', email = '{}', auth_level = {}
                   WHERE id = {};
                """.format(data["fName"],data["lName"], \
                        data["startDate"],data["color"], \
                        data["email"],data["authLevel"], \
                        data["raID"]))

    ag.conn.commit()
    cur.close()
    return jsonify(stdRet(1,"successful"))

@staff_bp.route("/api/removeStaffer", methods=["POST"])
@login_required
def removeStaffer():
    userDict = getAuth()

    if userDict["auth_level"] < 3:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    raID = request.json

    checkCur = ag.conn.cursor()
    checkCur.execute("SELECT hall_id FROM ra WHERE id = {};".format(raID))

    if userDict["hall_id"] != checkCur.fetchone()[0]:
        return jsonify("NOT AUTHORIZED")

    checkCur.close()

    cur = ag.conn.cursor()

    cur.execute("UPDATE ra SET hall_id = 0 WHERE id = {};".format(raID))
    ag.conn.commit()
    cur.close()

    return jsonify(raID)

@staff_bp.route("/api/addStaffer", methods=["POST"])
@login_required
def addStaffer():
    userDict = getAuth()

    if userDict["auth_level"] < 3:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    data = request.json

    checkCur = ag.conn.cursor()
    checkCur.execute("SELECT * FROM ra WHERE email = '{}';".format(data["email"]))
    checkRes = checkCur.fetchone()

    if checkRes is not None:
        cur = ag.conn.cursor()
        cur.execute("UPDATE ra SET hall_id = {} WHERE email = '{}';".format(userDict["hall_id"], data["email"]))
        ag.conn.commit()

        cur.execute("SELECT * FROM ra WHERE email = '{}';".format(data["email"]))
        ret = cur.fetchone()
        cur.close()
        return jsonify(ret)

    cur = ag.conn.cursor()

    cur.execute("""
    INSERT INTO ra (first_name,last_name,hall_id,date_started,color,email,auth_level)
    VALUES ('{}','{}',{},NOW(),'{}','{}','{}')
    RETURNING id;
    """.format(data["fName"],data["lName"],userDict["hall_id"],data["color"], \
                data["email"],data["authLevel"]))

    ag.conn.commit()
    newId = cur.fetchone()[0]

    cur.execute("""SELECT ra.id, first_name, last_name, email, date_started, res_hall.name, color, auth_level
     FROM ra JOIN res_hall ON (ra.hall_id = res_hall.id)
     WHERE ra.id = {};""".format(newId))
    raData = cur.fetchone()
    cur.close()

    return jsonify(raData)

@staff_bp.route("/api/importStaff", methods=["POST"])
@login_required
def importStaff():
    userDict = getAuth()

    if userDict["auth_level"] < 3:                                              # If the user is not at least an AHD
        logging.info("User Not Authorized - RA: {}".format(userDict["ra_id"]))
        return jsonify(stdRet(-1,"NOT AUTHORIZED"))

    logging.info("Import File: {}".format(request.files))
    if 'file' not in request.files:
        logging.info("No file part found")
        return jsonify(stdRet(0,"No File Part"))

    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename

    if file.filename == '':
        logging.info("No File Selected")
        return jsonify(stdRet(0,"No File Selected"))

    if file and fileAllowed(file.filename):
        dataStr = file.read().decode("utf-8")

        # Iterate through the rows of the dataStr
        #  The expected format for the csv contains
        #  a header row and is as follows:
        #  First Name, Last Name, Email, Date Started (MM/DD/YYYY), Color, Role

        #  Example:
        #  FName, LName-Hyphen, example@email.com, 05/28/2020, #OD1E76, RA
        logging.debug(dataStr)
        cur = ag.conn.cursor()
        for row in dataStr.split("\n")[1:]:
            if row != "":
                pl = [ part.strip() for part in row.split(",") ]
                logging.debug("PL: {}".format(pl))

                # Do some validation checking

                pl, valid, reasons = validateImportStaffUpload(pl)

                if not valid:
                    ret = stdRet("0","Invalid Formatting")
                    ret["except"] = reasons
                    logging.info("Invalid Formatting")
                    return jsonify(ret)

                if pl[-1] == "HD" and userDict["auth_level"] >= 3:
                    auth = 3
                elif pl[-1] == "AHD":
                    auth = 2
                else:
                    auth = 1

                logging.debug(auth)

                try:
                    cur.execute("""
                        INSERT INTO ra (first_name,last_name,hall_id,date_started,color,email,auth_level)
                        VALUES ('{}','{}',{},TO_DATE('{}','MM/DD/YYYY'),'{}','{}',{});
                        """.format(pl[0],pl[1],userDict["hall_id"],pl[3],pl[4],pl[2],auth))

                    ag.conn.commit()

                except IntegrityError:                                         # If the conflict entry already exists
                    logging.debug("Duplicate RA: {}, rolling back DB changes".format(pl))
                    ag.conn.rollback()                                                     # Rollback last commit so that Internal Error doesn't occur
                    cur.close()
                    cur = ag.conn.cursor()

        cur.close()

        return redirect(url_for(".manStaff"))

    else:
        logging.info("Unable to Import Staff")
        return redirect(url_for(".err",msg="Unable to Import Staff"))

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