from flask_login import current_user
from flask import redirect, url_for
import logging
import datetime
import os

import psycopg2

import appGlobals as ag


def getAuth():
    # Validate the user against the DB and return
    #  the user's information in a dictionary with
    #  the following keys:
    #
    #     uEmail      <str>  -  the user's email
    #     ra_id       <int>  -  the id of the user's ra table record
    #     name        <str>  -  the combined first_name and last_name of the user in the ra table
    #     hall_id     <int>  -  the id of the res_hall record that is associated with the user
    #     auth_level  <int>  -  the numeric value corresponding with the user's authorization level
    #     hall_name   <str>  -  the name of the res_hall record that is associated with the user

    logging.debug("Start getAuth")

    # The email returned from Google
    uEmail = current_user.username

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the user
    cur.execute("""
            SELECT ra.id, username, first_name, last_name, hall_id, auth_level, res_hall.name
            FROM "user" JOIN ra ON ("user".ra_id = ra.id)
                        JOIN res_hall ON (ra.hall_id = res_hall.id)
            WHERE username = '{}';""".format(uEmail))

    # Get user info from the database
    res = cur.fetchone()

    # If user does not exist, go to error url
    if res is None:
        logging.warning("No user found with email: {}".format(uEmail))

        # Be sure to close the cursor before leaving
        cur.close()
        return redirect(url_for("err", msg="No user found with email: {}".format(uEmail)))

    # Otherwise, close the cursor and return the userDict
    cur.close()
    return {
        "uEmail": uEmail,
        "ra_id": res[0],
        "name": res[2]+" "+res[3],
        "hall_id": res[4],
        "auth_level": res[5],
        "hall_name": res[6]
    }

def stdRet(status, msg):
    # Helper function to create a standard return object to help simplify code
    #  going back to the client when no additional data is to be sent.
    logging.debug("Generate Standard Return")
    return {"status":status,"msg":msg}

def fileAllowed(filename):
    logging.debug("Checking if file is allowed")
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validateUpload(partList):
    logging.debug("Validating Upload")
    pl = []
    for i in partList:
        i.replace("%","")
        i.replace(";","")
        i.replace("\\","")

        pl.append(i)

    valid = True
    reasons = []

    if len(partList) != 6:
        valid = False
        reasons.append("Expected 5 Parameters, Received: {}".format(len(partList)))
        logging.debug("PartList: "+str(partList))

    else:
        fName, lName, email, start, color, role = pl

        # Check Email Address
        if "@" not in email and "." not in email:
            valid = False
            reasons.append(fName+" "+lName+" - Invalid Email Address: "+email)
            logging.debug("RA Email: "+email)

        # Check Start Date
        splitDate = start.split("/")
        if len(splitDate) != 3 or "-" in start or int(splitDate[0]) > 12 or \
            int(splitDate[1]) > 31 or int(splitDate[2]) < 1:
            valid = False
            reasons.append(fName+" "+lName+" - Invalid Start Date: "+start)
            logging.debug("RA Start Date: "+start)

        # Check Color
        if len(color) != 7:
            valid = False
            reasons.append(fName+" "+lName+" - Invalid Color Format: {} Must be in 6-digit, hex format preceeded by a '#'".format(color))
            logging.debug("RA Color: "+color)

    return pl, valid, reasons

def getSchoolYear(month, year):
    # Figure out what school year we are looking for
    logging.debug("Calculate School Year: {} {}".format(month, year))

    if int(month) >= 8:
        # If the current month is August or later
        #  then the current year is the startYear
        startYear = int(year)
        endYear = int(year) + 1

    else:
        # If the current month is earlier than August
        #  then the current year is the endYear
        startYear = int(year) - 1
        endYear = int(year)

    # TODO: Currently, a school year is considered from August to August.
    #        Perhaps this should be configurable by the AHD/HDs?

    start = str(startYear) + '-08-01'
    end = str(endYear) + '-07-31'

    logging.debug("Start: "+ start)
    logging.debug("End: "+ end)

    return start, end

def getCurSchoolYear():
    # Figure out what school year we are looking for
    logging.debug("Calculate Current School Year")
    month = datetime.date.today().month
    year = datetime.date.today().year

    return getSchoolYear(month, year)

def formatDateStr(day, month, year, format="YYYY-MM-DD", divider="-"):
    # Generate a date string so that it follows the provided format.

    # Make sure the day is two digits
    if day < 10:
        dayStr = "0" + str(day)
    else:
        dayStr = str(day)

    # Make sure the month is two digits
    if month < 10:
        monthStr = "0" + str(month)
    else:
        monthStr = str(month)

    # Figure out what the desired format is
    #  this can be done by splitting the format string
    #  by the divider and checking each part to see
    #  if it contains a "Y", "M", or "D"

    partList = format.split(divider)

    result = ""
    for part in partList:
        if "Y" in part.upper():
            result += str(year)

        elif "M" in part.upper():
            result += monthStr

        elif "D" in part.upper():
            result += dayStr

        # Add the divider to the result
        result += divider

    return result[:-1]