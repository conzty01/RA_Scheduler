from flask_login import current_user
from flask import redirect, url_for
import datetime
import logging

# import the appGlobals for these functions to use
import appGlobals as ag

# --------------------------
# --   Helper Functions   --
# --------------------------


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
    # Create a standard return object to help simplify/unify API responses
    #  going back to the client when no additional data is to be sent.
    #
    #  This function accepts the following parameters and packages them into
    #  a dictionary object with the same keys:
    #
    #     status  <int>  -  the status of the message which indicates whether an operation
    #                        was successful or if it encountered an error.
    #     msg     <str>  -  the message that should be associated with the provided status

    logging.debug("Generate Standard Return")

    # Return standard return object back with the provided configuration.
    return {"status": status, "msg": msg}


def fileAllowed(filename):
    # Return a boolean denoting whether a particular file should be allowed to be
    #  uploaded based on its filename. Only files with extensions that are in the
    #  ALLOWED_EXTENSIONS global variable will be accepted.
    #
    #  This function accepts the following parameters:
    #
    #     filename  <str>  -  the full name of a file that is to be checked

    logging.debug("Checking if file is allowed")

    # Ensure that the filename has an extension in it and ensure that that extension
    #  is in the ALLOWED_EXTENSIONS global variable.
    return ('.' in filename) and (filename.rsplit('.', 1)[1].lower() in ag.ALLOWED_EXTENSIONS)


def getSchoolYear(month, year):
    # Return a tuple of 2 strings that denote the start and end date of the school year that
    #  the provided month and year belong to.
    #
    #  This function accepts the following parameters:
    #
    #     month  <int>  -  the integer value representing the month following the standard
    #                       gregorian calendar convention.
    #     year   <str>  -  the integer value representing the calendar year following the
    #                       standard gregorian calendar convention.

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

    # Concatenate the calculated years to the start and end date strings
    start = str(startYear) + '-08-01'
    end = str(endYear) + '-07-31'

    logging.debug("Start: " + start)
    logging.debug("End: " + end)

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