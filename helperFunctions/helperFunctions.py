from flask_login import current_user
from flask import abort, jsonify
from calendar import monthrange
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
    #     res_halls   <lst>  -  a list containing dicts with info about the Res Halls that the user is associated with.
    #       |
    #       |- name         <str>  - the name of the res_hall record
    #       |- id           <int>  - the id of the res_hall record
    #       |- auth_level   <int>  - the numeric value corresponding with the user's authorization level for this hall

    #  NOTE: The first hall in the res_halls dictionary should be used as the currently
    #         selected hall by the user.

    logging.debug("Start getAuth")

    # The email returned from Google
    uEmail = current_user.username
    uID = current_user.id

    #logging.debug(uEmail)

    # Create a DB cursor
    cur = ag.conn.cursor()

    # Query the DB for the user
    cur.execute("""
            SELECT ra.id, ra.first_name, ra.last_name, 
                   sm.res_hall_id, sm.auth_level, res_hall.name,
                   school.id, school.name
            FROM "user" JOIN ra ON ("user".ra_id = ra.id)
                        JOIN staff_membership AS sm ON (ra.id = sm.ra_id)
                        JOIN res_hall ON (sm.res_hall_id = res_hall.id)
                        JOIN school ON (school.id = res_hall.school_id)
            WHERE username = %s
            AND res_hall.enabled = TRUE
            ORDER BY sm.selected DESC""", (uEmail,))

    # Get user info from the database
    res = cur.fetchall()

    # Close the DB cursor
    cur.close()

    logging.debug("DB Result: {}".format(res))

    # Check to see if we found any records for the user
    if len(res) == 0:
        # If the user does not exist, go to error url
        logging.warning("Unable to locate RA associated with user")

        # Raise an 401 Unauthorized HTTP Exception that will be handled by flask
        abort(401)

    # Otherwise, pull the RA's information from the first record and create the dictionary
    #  to be returned
    uEmail = uEmail
    ra_id = res[0][0]
    fName = res[0][1]
    lName = res[0][2]
    res_halls = []

    # Iterate through the records and pull the res_hall data from them
    for row in res:
        res_halls.append({
            "id": row[3],
            "auth_level": row[4],
            "name": row[5],
            "school_id": row[6],
            "school_name": row[7]
        })

    logging.debug("getAuth Complete")

    # Return our authentication dictionary
    return AuthenticatedUser(uEmail, ra_id, fName, lName, res_halls)


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


def getSchoolYear(month, year, hallID):
    # Return a tuple of 2 datetime objects that denote the start and end date of
    #  the school year that the provided month and year belong to.
    #
    #  This function accepts the following parameters:
    #
    #     month    <int>  -  an integer value representing the month following the standard
    #                         gregorian calendar convention.
    #     year     <int>  -  an integer value representing the calendar year following the
    #                         standard gregorian calendar convention.
    #     hallID   <int>  -  an integer value representing the res_hall.id of the hall in question.

    # Ensure the provided month and year are integers
    month = int(month)
    year = int(year)

    logging.debug("Calculate School Year: {} {}".format(month, year))

    # Create a new cursor object
    cur = ag.conn.cursor()

    # Get the configured start and end month for the given Res Hall
    cur.execute("SELECT year_start_mon, year_end_mon FROM hall_settings WHERE res_hall_id = %s", (hallID,))

    startMon, endMon = cur.fetchone()

    if month >= startMon:
        # If the provided month is equal to the configured start month or later,
        #  then the current year is the startYear
        startYear = year
        endYear = year + 1

    else:
        # If the provided month is earlier than the configured start month,
        #  then the current year is the endYear
        startYear = year - 1
        endYear = year

    # Create date objects to represent the start and end dates
    start = datetime.date(startYear, startMon, 1)
    end = datetime.date(endYear, endMon, monthrange(endYear, endMon)[-1])

    logging.debug("Start: {}".format(start))
    logging.debug("End: {}".format(end))

    return start, end


def getCurSchoolYear(hallID):
    # Calculate what school year it is based on the current date and return a tuple
    #  of strings that represent the start and end date of the school year.

    logging.debug("Calculate Current School Year")

    # Get the integer value for the current month.
    month = datetime.date.today().month

    # Get the integer value for the current year.
    year = datetime.date.today().year

    # Call getSchoolYear, passing it the current month and year and return the value
    return getSchoolYear(month, year, hallID)


def formatDateStr(day, month, year, format="YYYY-MM-DD", divider="-"):
    # Generate a date string using the provided day, month, and year values
    #  that adheres to the provided format.
    #
    #  This function accepts the following parameters:
    #
    #     day      <int>  -  the integer value representing the day following the standard
    #                         gregorian calendar convention.
    #     month    <int>  -  the integer value representing the month following the
    #                         standard gregorian calendar convention.
    #     year     <int>  -  the integer value representing the calendar year following the
    #                         standard gregorian calendar convention.
    #     format   <str>  -  a string denoting the expected desired format for the date string.
    #                         In this format, Y denotes year, M denotes month, and D denotes day.
    #                         By default, this value is "YYYY-MM-DD".
    #     divider  <str>  -  a string denoting the character that divides the parts of the format
    #                         input string. By default, this value is "-".

    # Make sure the day consists of two digits
    if day < 10:
        # If the value of the day is less than 10, then python only represents it
        #  with a single digit.
        dayStr = "0" + str(day)

    else:
        dayStr = str(day)

    # Make sure the month consists of two digits
    if month < 10:
        # If the value of the month is less than 10, then python only represents it
        #  with a single digit.
        monthStr = "0" + str(month)

    else:
        monthStr = str(month)

    # Figure out what the desired format is
    #  this can be done by splitting the format string
    #  by the divider and checking each part to see
    #  if it contains a "Y", "M", or "D"

    # split the format string into parts using the divider
    partList = format.split(divider)

    # Create the result string that will be returned
    result = ""
    # Iterate through the format string parts
    for part in partList:

        # If the current part contains a "Y"
        if "Y" in part.upper():
            # Then add the year to the date string
            result += str(year)

        elif "M" in part.upper():
            # Else if the current part contains an "M"
            # Then add the month to the date string
            result += monthStr

        elif "D" in part.upper():
            # Else if the current part contains a "D"
            # Then add the day to the date string
            result += dayStr

        # Add the divider to the result
        result += divider

    # Return the resulting date string excluding the lingering divider symbol
    #  at the end.
    return result[:-1]


def packageReturnObject(obj, fromServer=False):
    # Package up the provided object. If the fromServer parameter is set to
    #  True, then the object will be returned as-is. If it is set to False,
    #  then a serialized version of the object is returned.
    #
    #  This function accepts the following parameters:
    #
    #     obj          <obj>   -  Object to be packaged
    #     fromServer   <bool>  -  Boolean denoting whether the object should
    #                              be packaged as a Flask response or not.

    # If the method was called from the server
    if fromServer:
        # Then return the result as-is
        return obj

    else:
        # Otherwise return a JSON version of the result
        return jsonify(obj)


class AuthenticatedUser:
    """ Object for abstracting the idea of an Authenticated User in the RA Duty Scheduler Application

        This class is intended to be used to pass organized data regarding authenticated users to
        various parts of the application.

        Args:
            email      (str):   A string representing the "user".username field for this user.
            raID       (int):   An integer representing the ra.id field for this user.
            fName      (str):   A string representing the ra.first_name field for this user.
            lName      (str):   A string representing the ra.last_name field for this user.
            resHalls   (lst):   A list containing dicts with info about the Res Halls that the user is associated with.
               |- name         <str>  - the name of the res_hall record
               |- id           <int>  - the id of the res_hall record
               |- auth_level   <int>  - the numeric value corresponding with the user's auth_level for this hall
               |- school_id    <int>  - the id of the school record associated with the res_hall record
               |- school_name  <str>  - the name of the school associated with the res_hall record

        NOTE: The first hall in the res_halls list will be used as user's currently selected Res Hall.

    """
    def __init__(self, email, raID, fName, lName, resHalls):
        self.__email = email
        self.__ra_id = raID
        self.__fName = fName
        self.__lName = lName
        self.__resHalls = resHalls
        self.__selectedHall = resHalls[0]

    def email(self):
        # Return the email associated with the user
        return self.__email

    def ra_id(self):
        # Return the ID associated with the user's RA record
        return self.__ra_id

    def first_name(self):
        # Return the first name associated with the user's RA record
        return self.__fName

    def last_name(self):
        # Return the last name associated with the user's RA record
        return self.__lName

    def name(self):
        # Return the full name associated with the user's RA record
        return self.__fName + " " + self.__lName

    def hall_id(self):
        # Return the ID associated with the user's currently selected Res Hall
        return self.__selectedHall["id"]

    def auth_level(self):
        # Return the auth_level associated with the user's currently selected Res Hall
        return self.__selectedHall["auth_level"]

    def hall_name(self):
        # Return the name associated with the user's currently selected Res Hall
        return self.__selectedHall["name"]

    def getAllAssociatedResHalls(self):
        # Return all halls that the user's RA record is associated with
        return self.__resHalls

    def selectResHall(self, index):
        # Mark the Res Hall at the provided index as being the user's currently selected
        #  Res Hall.
        self.__selectedHall = self.__resHalls[index]
