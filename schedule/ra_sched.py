from datetime import date
import calendar
import random


class RA:
    """ Object for abstracting the idea of a Resident Assistant (RA) in the RA Duty Scheduler Application.

        This class is intended to be used to pass organized data to various parts of the application.

        Args:
            firstName    (str):    A string representing the first name of the RA.
            lastName     (str):    A string representing the last name of the RA.
            raID         (int):    An integer denoting the ID of the RA.
            hallID       (int):    An integer denoting the ID of the Residence Hall that the RA
                                    is assigned duties for.
            dateStarted  (date):   A date object that represents the date that the RA began
                                    employment as a Resident Assistant.
            conflicts    (lst):    A list of objects (typically strings or datetime objects) that
                                    represent dates on which the RA has a duty conflict and should
                                    not be assigned for duty.
            points       (int):    An integer denoting the accumulative number of points the RA has
                                    earned through their assigned monthly duties.
    """

    def __init__(self, firstName, lastName, raID, hallID, dateStarted, conflicts=None, points=0):

        # First name of the RA
        self.firstName = firstName

        # Last name of the RA
        self.lastName = lastName

        # Calculate the full name of the RA
        self.fullName = firstName + " " + lastName

        # ID of the RA
        self.id = raID

        # ID of the Residence Hall that the RA belongs to
        self.hallId = hallID

        # Conflicts of the RA
        self.conflicts = [] if conflicts is None else list(conflicts)

        # Date representing the date that the RA began employment
        self.dateStarted = dateStarted

        # Points earned by the RA through their assigned monthly duties
        self.points = points

    def __str__(self):
        # Return a string representing the RA object
        return "{} has {} points".format(self.fullName, self.points)

    def __repr__(self):
        # Return a string representing the RA object
        return "RA(Id: {}, Name: {})".format(self.id, self.firstName)

    def __iter__(self):
        # Iterate through the RA's duty conflicts
        for c in self.conflicts:
            yield c

    def __eq__(self, other):
        # RA objects are considered to be equal if all of the following
        #  attributes are equal:
        #
        #    fullName
        #    id
        #    hallId
        #    dateStarted

        return self.fullName == other.fullName and \
               self.id == other.id and \
               self.hallId == other.hallId and \
               self.dateStarted == other.dateStarted

    def __hash__(self):
        # Return a hash of the RA object that is based on a tuple of the
        #  following attributes:
        #
        #    fullName
        #    id
        #    hallId
        #    dateStarted

        return hash((self.fullName, self.id, self.hallId, str(self.dateStarted)))

    def __lt__(self, other):
        # Sort by comparing the number of points RAs have.

        # If two RAs have the same number of points, then randomly
        #  return True or False. This is to reduce the possibility that
        #  the same set or RAs are scheduled consecutively several weeks
        #  in a row.

        # Check to see if this RA has the same number of points as the
        #  other RA.
        if self.getPoints() != other.getPoints():
            # If the points are not equal, then check to see
            #  if this RA has fewer points than the other RA.
            return self.getPoints() < other.getPoints()

        else:
            # If the points are equal, then randomly choose
            #  whether or not this RA should be considered
            #  to come before the other RA.
            return 1 == random.randint(0, 1)

    def __deepcopy__(self, memo):
        # Return a new RA object with all of the same attributes
        #  as this RA.
        return RA(
            str(self.firstName),
            str(self.lastName),
            int(self.id),
            int(self.hallId),
            date.fromordinal(self.dateStarted.toordinal()),
            list(self.conflicts),
            int(self.points)
        )

    def getConflicts(self):
        # Return the RA's conflicts
        return self.conflicts

    def getId(self):
        # Return the RA's ID
        return self.id

    def getStartDate(self):
        # Return the RA's start date
        return self.dateStarted

    def getPoints(self):
        # Return the RA's points
        return self.points

    def addPoints(self, amt):
        # Add the given amount to the RA's points
        self.points += amt

    def removePoints(self, amt):
        # Remove the given amount from the RA's points
        self.points -= amt

    def getName(self):
        # Return the RA's full name
        return self.fullName

    def getHallId(self):
        # Return the RA's Res Hall ID
        return self.hallId


class Day:
    """ Object for abstracting the idea of a Day in the RA Duty Scheduler Application.

        This class is intended to be used to pass organized data to various parts of the application.

        Args:
            date            (date):   A date object containing information regarding the date of this
                                       Day object.
            dow             (int):    An integer representing the day-of-the-week of this Day object.
                                       The mapping of the day of the week is as follows:
                                              Mon, Tues, Wed, Thurs, Fri, Sat, Sun
                                               0    1     2     3     4    5    6
            numDutySlots    (int):    An integer denoting the number of RAs that can be assigned for
                                       duty on this day.
            ras             (lst):    A list containing RA objects that should be assigned for duty
                                       on this day. If provided, the numDutySlots will be equal to
                                       the length of provided list.
            customPointVal  (int):    An integer denoting the number of points that should be earned
                                       for each slot of duty on this day. If no custom value is
                                       provided, then the number of points will be based on the
                                       number of duty slots for this day. 2 or more duty slots will
                                       result in 2 points and 1 slot will result in 1 point.
            dayID           (int):    An integer representing the unique ID of the day object.
            isDoubleDay     (bool):   A boolean denoting whether or not the day should be considered
                                       a day where more than one RA should be assigned for duty and,
                                       as a result, more than one point should be earned per RA.
            flagDutySlot    (bool):   A boolean denoting whether or not a duty slot should be flagged
                                       as being considered a special slot. If more that one duty slot
                                       is configured for a given day, this will only flag one (1)
                                       duty slot. If set to True, the last duty slot will be flagged.
    """

    def __init__(self, date, dow, numDutySlots=1, ras=None, customPointVal=0, dayID=0,
                 isDoubleDay=False, flagDutySlot=False):
        # The date of the Day object
        self.date = date

        # The day of the week
        self.dow = dow

        # Whether the Day should be considered a double-day
        self.isdd = isDoubleDay

        # The unique ID of the day
        self.id = dayID

        # Whether the day should be considered for manual review
        self.review = False

        # Set the value of flagDutySlot
        self.flagDutySlot = flagDutySlot

        # If an RA list has been provided
        if ras is not None:
            # Set the RA list with assigned duty slots
            self.ras = [self.DutySlot(ra) for ra in ras]

            # If we should flag a duty slot
            if self.flagDutySlot:
                # Then flag the last duty slot in the list
                self.ras[-1].setFlag(True)

            # Also set the number of duty slots to be the
            #  length of the RA list.
            self.numDutySlots = len(ras)

        else:
            # Set the number of duty slots for this day.
            self.numDutySlots = numDutySlots

            # Initialize the empty ra list
            self.ras = []

        # Check to see if a custom point value has been provided.
        if customPointVal == 0:

            # If no custom value is provided, then calculate the
            #  point value based on the number of duty slots.
            if numDutySlots > 1:
                # If there are more than one duty slot,
                #  set the point value to 2.
                self.pointVal = 2

            else:
                # Otherwise set the point value to 1.
                self.pointVal = 1

        else:
            # If a custom point value is provided, set that as the
            #  point value for this day.
            self.pointVal = customPointVal

    def __str__(self):
        # Return a string representing the Day object
        return "Day({}.{})".format(self.date, self.id)

    def __repr__(self):
        # Return a string representing the Day object
        return self.__str__()

    def __iter__(self):
        # Iterate through the RAs that are assigned
        #  for duty on this Day
        for slot in self.ras:
            yield slot.getAssignment()

    def __lt__(self, other):
        # Sort by comparing the date of the two Days
        return self.getDate() < other.getDate()

    def __hash__(self):
        # Return a hash of the Day object that is based on
        #  the date and ID.
        return hash(self.date) + hash(self.id)

    def __eq__(self, other):
        # Day objects are considered to be equal if their
        #  dates are equal.
        return self.date == other.date

    def __contains__(self, other):
        # Return True if the "other" object is in any of the
        #  duty slots.

        # Set some variables used in finding the object
        i = 0
        upperBound = len(self.ras)
        found = False

        # While the appropriate duty slot has not been found and
        #  we have not gotten to the end of the ra list...
        while not found and i < upperBound:
            # Peek the assigned duties list and see if its the object
            if other == self.ras[i].getAssignment():
                # If it is, then set found to True
                found = True

            else:
                # Otherwise move to the next index
                i += 1

        # Check to see if we found the RA
        if found:
            # If so, then return True
            return True

        # Otherwise return False
        return False

    def addRA(self, ra):
        # Add an RA to the list of RAs that are assigned
        #  to be on duty for this Day. This method will
        #  also add the Day's point value to the RA's total.

        # Check to see if all of the duty slots have already
        #  been filled.
        if len(self.ras) < self.numDutySlots:
            # If there is still room, append the RA to the list
            self.ras.append(self.DutySlot(ra))

            # And add the point values awarded for this duty to
            #  the RA.
            ra.addPoints(self.pointVal)

            # Check to see if we need to set any flags
            if self.flagDutySlot:
                # Then check to see if this was the last duty that
                #  can be added.
                if len(self.ras) >= self.numDutySlots:
                    # If so, then flag this duty.
                    self.ras[-1].setFlag(True)

        else:
            # If all of the duty slots have already been filled,
            #  throw an Overflow exception.
            raise OverflowError("Limit for number on duty exceeded.")

    def addRaWithoutPoints(self, ra):
        # Add an RA to the list of RAs that are assigned
        #  to be on duty for this Day. This method will NOT
        #  add any points to the RA's total.

        # Check to see if all of the duty slots have already
        #  been filled.
        if len(self.ras) < self.numDutySlots:
            # If there is still room, append the RA to the list
            self.ras.append(self.DutySlot(ra))

            # Check to see if we need to set any flags
            if self.flagDutySlot:
                # Then check to see if this was the last duty that
                #  can be added.
                if len(self.ras) >= self.numDutySlots:
                    # If so, then flag this duty.
                    self.ras[-1].setFlag(True)

        else:
            # If all of the duty slots have already been filled,
            #  throw an Overflow exception.
            raise OverflowError("Limit for number on duty exceeded.")

    def removeRA(self, ra):
        # Remove and return the given RA from the list of RAs on duty.

        # First, remove the Day's points from the RA's total.

        # Iterate through the duty slots and find the RA

        # Set some variables used in finding the RA
        i = 0
        upperBound = len(self.ras)
        found = False

        # While the appropriate duty slot has not been found and
        #  we have not gotten to the end of the ra list...
        while not found and i < upperBound:
            # Peek the assigned duties list and see if its the RA
            if ra == self.ras[i].getAssignment():
                # If it is, then set found to True
                found = True

            else:
                # Otherwise move to the next index
                i += 1

        # Check to see if we found the RA
        if found:
            # If so, then remove the Day's points from the RA's total.
            ra.removePoints(self.pointVal)

            # Then remove and return the RA object.
            return self.ras.pop(i).getAssignment()

        else:
            # Otherwise we were unable to find the RA so return None
            return None

    def removeAllRAs(self):
        # Remove and return all RAs from the list of RAs on duty.

        # Create a temporary list that will be returned
        tmp = []

        # Iterate through all of the RAs assigned for duty.
        for slot in self.ras:
            # Remove the Day's points from the RA's total.
            slot.getAssignment().removePoints(self.pointVal)

            # Add the RA to the tmp list
            tmp.append(slot.getAssignment())

        # Reset the RA list to an empty list.
        self.ras = []

        # Return the temporary reference to the list
        return tmp

    def numberDutySlots(self):
        # Return the number of duty slots that are available.
        return self.numDutySlots

    def addDutySlot(self, amt=1):
        # Add an additional number of duty slots to the Day.
        #  By default, this will increase the number of
        #  available duty slots by 1.
        self.numDutySlots += amt

    def getPoints(self):
        # Return the number of points that are awarded for
        #  being assigned for duty on this day.
        return self.pointVal

    def getDate(self):
        # Return the date of this day.
        return self.date

    def getDoW(self):
        # Return the day-of-the-week for this day
        return self.dow

    def getId(self):
        # Return the ID of this day
        return self.id

    def numberOnDuty(self):
        # Return the number of RAs assigned for duty
        #  on this day.
        return len(self.ras)

    def isDoubleDay(self):
        # Return whether or not this day should be
        #  considered a double-day.
        return self.isdd

    def getRAs(self):
        # Return the list of RA's assigned for duty
        #  on this day.
        return [slot.getAssignment() for slot in self.ras]

    def setReview(self, val=True):
        # Set this day as being in need of manual review.
        self.review = val

    def getReview(self):
        # Return whether or not this day should be manually
        #  reviewed.
        return self.review

    def combineDay(self, otherDay):
        # Merge the duty slots of the provided other day into this one.

        # Ensure that we are dealing with a Day object
        if type(otherDay) != Day:
            # If not, raise a Type error exception
            raise TypeError("Cannot combine Day object with type: {}".format(type(otherDay)))

        # Check to ensure that after combining, we will not have not
        #  exceeded the number of duty slots for this day
        if len(self.ras) + len(otherDay.ras) > self.numDutySlots:
            # If so, throw an Overflow exception
            raise OverflowError("Limit for number on duty exceeded.")

        # Otherwise, append the otherDay's duty slots to this day's
        #  duty slots
        for s in otherDay.ras:
            self.ras.append(s)

    def iterDutySlots(self):
        # Iterate through the Duty Slots for the day
        for slot in self.ras:
            yield slot

    def nextDutySlotIsFlagged(self):
        # Return whether or not the next open Duty Slot should be flagged

        # Do we even need to worry about flagged duty slots?
        if self.flagDutySlot:
            # If so, then the value to be returned will be a boolean
            #  of whether or not the next assigned duty slot will be
            #  the last available duty slot for the Day.
            return self.numberOnDuty() + 1 == self.numDutySlots

        else:
            # If not, then return False
            return False

    def getLastDutySlotAssignment(self):
        # Return the RA that was assigned to the last Duty Slot
        return self.ras[-1].getAssignment() if len(self.ras) > 0 else None

    # ------------------------
    # -- Supporting Classes --
    # ------------------------
    class DutySlot:
        """ Object for abstracting the idea of a duty slot within a Day object.

            This class is intended to be used to attach metadata to a particular duty.

            Args:
                assignee    (RA):     An RA object that has been scheduled for this duty.
                flagged     (bool):   A boolean denoting whether or not the duty slot should be
                                       flagged as a special duty.
        """

        def __init__(self, assignee=None, flagged=False):
            # If this object is created with an assigned RA,
            #  set it to the duty slot.
            self.slot = assignee

            # Set whether or not this duty slot should be flagged as special
            self.flagged = flagged

        def isAssigned(self):
            # Return whether or not this duty slot has been assigned.
            return self.slot is not None

        def assignRA(self, ra):
            # Assign the provided RA to the duty slot.
            self.slot = ra

        def setFlag(self, val):
            # Set the value of the flag
            self.flagged = val

        def getFlag(self):
            # Return the value of the flag
            return self.flagged

        def getAssignment(self):
            # Return the RA on duty
            return self.slot

        def removeAssignment(self):
            # Remove and return the assigned RA

            # Set the assigned RA to a temporary variable
            tmp = self.slot

            # Clear out the duty slot assignment
            self.slot = None

            # Return the unassigned RA
            return tmp


class Schedule:
    """ Object for abstracting the idea of a Duty Schedule for the RA Duty Scheduler Application.

        This class is intended to be used to pass organized data to various parts of the application.

        Args:
            year         (int)    An integer denoting the year in which this Schedule object belongs to.
            month        (int)    An integer denoting the month of the year in which this Schedule object
                                   is depicting.
            noDutyDates  (lst)    A list of days for the given month and year that should not have any
                                   duties assigned to them.
            sched        (lst)    A list representing an already created Schedule object.
            doubleDays   (tuple)  A tuple containing integers representing days of the week that should
                                   have two duty slots.
            doubleDates  (lst)    A list containing dates for the given month and year that should
                                   have two duty slots. These dates are separate from days of the
                                   week handled in the doubleDays tuple.
    """

    # Initialize the Schedule class's possible statuses
    ERROR = -3      # An error was encountered and a schedule was unable to be generated
    FAIL = -2       # A schedule was unable to be generated
    WARNING = -1    # A schedule was generated, but the user should be made aware of something
    DEFAULT = 0     # A blank schedule
    SUCCESS = 1     # A schedule was generated successfully

    def __init__(self, year, month, noDutyDates=None, sched=None, doubleDays=(4, 5),
                 doubleDates=None, notes=None, status=DEFAULT):
        # Whether the schedule should be set for manual review
        self.review = False

        # A set of the Days in the schedule that should be manually reviewed
        self.reviewDays = set()

        # A list of the days in which no duty should be scheduled
        self.noDutyDates = [] if noDutyDates is None else list(noDutyDates)

        # A tuple containing the days of the week that should have two duty slots
        self.doubleDays = doubleDays

        # A list containing dates which should have two duty slots
        self.doubleDates = [] if doubleDates is None else list(doubleDates)

        # A list of note objects
        self.schedNotes = [] if notes is None else list(notes)

        # The status of the schedule object
        self.status = status

        # If 'sched' is defined...
        if sched is not None:
            # then use this as the defined schedule.
            self.schedule = list(sched)

        else:
            # Since a schedule was not previously defined, generate a blank schedule.

            # Set the schedule to an empty list to start
            self.schedule = []

            # Iterate through the days of the desired month
            for d, dow in calendar.Calendar().itermonthdays2(year, month):
                # The iterator returned from the loop yields a tuple that
                #  contains an integer for the day of the week and the date
                #  of the month. The mapping of the day of the week is as follows:
                #
                #           Mon, Tues, Wed, Thurs, Fri, Sat, Sun
                #            0    1     2     3     4    5    6
                #
                # If the date is 0, that means that that respective
                #  date belongs to the next or previous month.

                # Check to see if the current date belongs to this month
                if d != 0:

                    # Check to see if this date should not have a duty scheduled on it
                    if d in noDutyDates:
                        # If no duty should be scheduled, create a Day object with
                        #  no duty slots and append it to the schedule
                        self.schedule.append(
                            Day(
                                date(year, month, d),
                                dow,
                                numDutySlots=0
                            )
                        )

                    else:

                        # Check to see if the day should have two duty slots due
                        #  to the day of the week that the day falls on.
                        if dow in doubleDays:
                            # If the day is considered a double-day, then add the
                            #  date to the doubleDates attribute.
                            self.doubleDates.append(date)

                            # Add a Day object with two duty slots to the schedule
                            self.schedule.append(
                                Day(
                                    date(year, month, d),
                                    dow,
                                    numDutySlots=2
                                )
                            )

                        else:
                            # Otherwise, if the date is not a double-day
                            #  then it should only have one RA on duty
                            self.schedule.append(
                                Day(
                                    date(year, month, d),
                                    dow,
                                    numDutySlots=1
                                )
                            )

    def __repr__(self):
        # Return a string representing the Schedule Object
        return "Schedule({})".format(self.schedule)

    def __iter__(self):
        # Iterate through the schedule
        for d in self.schedule:
            yield d

    def __len__(self):
        # Return the length of the schedule
        return len(self.schedule)

    def sort(self):
        # Sort the schedule so that the days are in
        #  reverse order (ex: 31 - 1)
        self.schedule.sort(reverse=True)

    def numDays(self):
        # Return the number of days in the schedule
        return len(self.schedule)

    def getDate(self, date):
        # Return the day at desired 1-based index

        # If the provided index is outside the bounds
        #  of the schedule.
        if date < 1 or date > len(self.schedule):

            # Raise an Index Error
            raise IndexError("Dates are indexed from 1 to {}, index given: {}"
                             .format(len(self.schedule), date))
        else:
            # Index into the schedule and return the entry

            # The 1st of a month is at position 0 in the list
            return self.schedule[date-1]

    def addRA(self, date, ra):
        # Add the provided RA to the provided Day for duty
        self.getDate(date).addRA(ra)

    def removeRA(self, date, ra):
        # Remove the provided RA from the provided duty Day
        self.getDate(date).removeRA(ra)

    def setReview(self):
        # Set the schedule as being in need of manual review
        self.review = True

    def addReviewDay(self, day):
        # Add the provided day to the list of days needing review
        #  for this schedule
        self.reviewDays.add(day)

    def getReviewDays(self):
        # Get a list of days that should be reviewed
        return self.reviewDays

    def shouldReview(self):
        # Return whether this schedule should be manually reviewed.
        return self.review

    def getStatus(self):
        # Return the schedule's status
        return self.status

    # ------------------------
    # -- Supporting Classes --
    # ------------------------
    class Note:
        """ Object for holding user-relevant metadata about a Schedule object.

            This class is intended to be used to attach metadata to a particular schedule.

            Args:
                msg     (str):    A string containing the user-relevant information.
                status  (int):    An integer denoting the status of the message.
        """

        def __init__(self, msg, status):
            # Set the associated parameters
            self.msg = msg
            self.status = status

        def __repr__(self):
            return "<Note status:{}, msg:{}>".format(self.status, self.msg)

        def __str__(self):
            return self.msg

        def __eq__(self, other):
            # Return True if the other Note object has the same message and status
            return self.msg == other.msg and self.status == other.status

    def addNote(self, msg, status=DEFAULT):
        # Create a new Note object and add it to the schedule's
        #  schedNotes list.
        self.schedNotes.append(self.Note(msg, status))

    def getNotes(self):
        # Return the list of notes associated with the schedule.
        return self.schedNotes


class State:
    """ Object for storing information regarding the current "state" of the Scheduler's DFS traversal.

        Args:
            day                 (Day):     Day object for the current state.
            raList              (lst):     A sorted list of unvisited RA candidates for the
                                            given date.
            lastDateAssigned    (dict):    A dictionary containing information regarding the
                                            last day each of the RAs were assigned to duty
            numDoubleDays       (dict):    A dictionary containing information regarding the
                                            number of double days an RA has already been
                                            assigned.
            ldaTolerance        (int):     An integer denoting the number of days before an RA
                                            should be considered for another duty.
            nddTolerance        (float):   An integer denoting the number of double
            numFlagDuties       (dict):    A dictionary containing information regarding the
                                            the number of flagged duties each RA has been
                                            assigned for the month.
            predetermined       (bool):    Boolean denoting if this state can is allowed to
                                            be changed/reevaluated. This is used to denote
                                            whether this particular date/duty was preset.
            overrideConflicts   (bool):    Boolean denoting whether or not to allow for the
                                            overriding of duty conflicts when necessary.
    """

    def __init__(self, day, raList, lastDateAssigned, numDoubleDays, ldaTolerance,
                 nddTolerance, numFlagDuties, predetermined=False, overrideConflicts=False):
        # The current day of the state
        self.curDay = day

        # The Last Date Assigned Dictionary of the state
        self.lda = lastDateAssigned

        # The Number of Double Days Dictionary of the state
        self.ndd = numDoubleDays

        # The Last Duty Assigned Tolerance of the state
        self.ldaTol = ldaTolerance

        # The Next Double Day Tolerance of the state
        self.nddTol = nddTolerance

        # The Number of Flag Duties Dictionary of the state
        self.nfd = numFlagDuties

        # Whether the state was predetermined
        self.predetermined = predetermined

        # Whether or not to override duty conflicts if needed
        self.overrideCons = overrideConflicts

        # If this state has been predetermined, then the first RA in the raList
        #  will always be selected as the for duty on this day.
        if self.predetermined:
            # Set the provided raList as the candidate list
            self.candList = raList

        elif len(raList) == 0:
            # Else if the provided raList is empty, then do not attempt to calculate
            #  an ordered candidate list (results in divide by 0 error if allowed)
            self.candList = list()
            self.conList = list()

        else:
            # Otherwise we will calculate the ordered candidate list and
            #  conflict list for this state.
            self.candList, self.conList = self.getSortedWorkableRAs(
                raList, self.curDay, self.lda, self.curDay.isDoubleDay(),
                self.ndd, self.curDay.getPoints(), self.ldaTol,
                self.nddTol, self.nfd
            )

    def __deepcopy__(self):
        # Return a new State object with all of the same attributes as this State
        return State(
            self.curDay,
            self.candList,
            self.lda.copy(),
            self.ndd.copy(),
            self.ldaTol,
            self.nddTol,
            self.nfd.copy(),
            self.predetermined,
            self.overrideCons
        )

    def __copy__(self):
        # Return a new State object that is a shallow copy of this State
        return State(
            self.curDay,
            self.candList,
            self.lda,
            self.ndd,
            self.ldaTol,
            self.nddTol,
            self.nfd,
            self.predetermined,
            self.overrideCons
        )

    def __eq__(self, other):
        # Return True if this state is considered equal to
        #  the other state

        # Check to ensure that the other object is indeed
        #  a State object
        if type(other) != State:
            # If not, then raise a TypeError
            raise TypeError("Cannot compare State object with {} object".format(type(other)))

        return self.curDay.getDate() == other.curDay.getDate() and \
            self.curDay.getId() == other.curDay.getId() and \
            self.ldaTol == other.ldaTol and \
            self.nddTol == other.nddTol and \
            self.candList == other.candList and \
            self.predetermined == other.predetermined

    def __lt__(self, other):
        # Return True if this state is considered less than
        #  the other state.

        # Check to ensure that the other object is indeed
        #  a State object
        if other is None:
            # If the other object is None, then return True
            return True

        elif not isinstance(other, State):
            # If not, then raise a TypeError
            raise TypeError("'<' not supported between instances of 'State' and '{}'".format(type(other)))

        # Otherwise, return whether or this object's curDay is less than the other's
        return self.curDay.getId() < other.curDay.getId()

    def __gt__(self, other):
        # Return True if this state is considered greater than
        #  the other state.

        # Check to ensure that the other object is indeed
        #  a State object
        if other is None:
            # If the other object is None, then return True
            return True

        elif not isinstance(other, State):
            # If the other object is not a State object, then raise a TypeError
            raise TypeError("'>' not supported between instances of 'State' and '{}'".format(type(other)))

        # Otherwise, return whether or this object's curDay is greater than the other's
        return self.curDay.getId() > other.curDay.getId()

    def deepcopy(self):
        # Call the __deepcopy__ magic method
        return self.__deepcopy__()

    def copy(self):
        # Call the __copy__ magic method
        return self.__copy__()

    def restoreState(self):
        # Return the values of the current state
        return self.curDay, self.candList, self.lda, self.ndd, self.nfd

    def hasEmptyCandList(self):
        # Return a boolean denoting whether the candidate list is empty or not
        return len(self.candList) == 0

    def hasEmptyConList(self):
        # Return a boolean denoting whether the conflict list is empty or not
        return len(self.conList) == 0

    def returnedFromPreviousState(self):
        # Return a boolean denoting whether this state has been visited again
        #  from another subsequent state. This is used to indicate whether the
        #  algorithm reached a dead-end and had to turn around.

        # This is asserted if an RA has been assigned a duty for the current day.
        return self.curDay.numberOnDuty() > 0

    def isDoubleDay(self):
        # Return a boolean denoting whether the current day of the state is
        #  considered a double-day.
        return self.curDay.isDoubleDay()

    def getNextCandidate(self):
        # Remove and return the next duty candidate
        return self.candList.pop(0)

    def assignNextRA(self):
        # Assign the next candidate RA for curDay's duty

        # Get the next candidate RA for the curDay's duty
        candRA = self.getNextCandidate()

        # Assign the candidate RA for the curDay's duty
        self.curDay.addRA(candRA)

        # Update lastDateAssigned
        self.lda[candRA] = self.curDay.getDate()

        # If doubleDay, then update numDoubleDays
        if self.isDoubleDay():
            self.ndd[candRA] += 1

        # Return the selected candidate RA
        return candRA

    def getSortedWorkableRAs(self, raList, day, lastDateAssigned, isDoubleDay,
                             numDoubleDays, datePts, ldaTolerance, nddTolerance,
                             numFlagDuties):
        # Create and return a new sorted list of RAs that are available for duty
        #  on the provided day. Also create and return a new sorted list of RAs
        #  that are NOT available for duty on the provided day.

        # Initialize the conflict list
        conList = []

        # Calculate the average number of points amongst RAs
        # Set the sum to 0
        s = 0
        # Iterate through all of the RAs and add up all of their points
        for ra in raList:
            s += ra.getPoints()

        # Calculate the average number of points per RA
        ptsAvg = s / len(raList)

        # print("  Average Points:",ptsAvg)

        # If isDoubleDay, calculate the average number of double-duty days
        #  assigned amongst RAs as well as the average number of flagged
        #  duties assigned amongst RAs.
        if isDoubleDay:
            # Set the sum to 0
            s = 0
            # Iterate through all of the ras in the numDoubleDays Dictionary
            for ra in numDoubleDays:
                # Add up all of the number of double-duty days that have been assigned
                s += numDoubleDays[ra]

            # Calculate the average number of double-days per RA
            doubleDayAvg = s / len(numDoubleDays)
            # print("  Double Day Average:",doubleDayAvg)

            # Set the sum to 0
            s = 0
            # Iterate through all of the RAs in the numFlagDuties Dictionary
            for ra in numFlagDuties:
                # Add upp all of the number of flagged duties that have been assigned
                s += numFlagDuties[ra]

            # Calculate the average number of flagged duties per RA
            flagDutyAvg = s / len(numFlagDuties)

        else:
            # Default to -1 when not a double-duty day
            doubleDayAvg = -1
            flagDutyAvg = -1

        # Initialize the list to be returned containing all workable RAs
        retList = []

        # print("  Removing candidates")
        # Iterate over the raList and get rid of the candidates who are not
        #  available for duty on this date.
        for ra in raList:
            # print("    ",ra)
            # Start by assuming this RA is a duty candidate
            isCand = True

            # If an RA has a conflict with the duty shift
            # print(day.getDate() in ra.getConflicts())
            if day.getDate() in ra.getConflicts():
                # Then the RA is no longer a duty candidate
                isCand = False

                # print("      Removed: Conflict")

            # If an RA has been assigned a duty recently
            #  This is skipped when the LDA is 0, meaning the RA has not been
            #  assigned for duty yet this month.
            if lastDateAssigned[ra] != 0 and \
               day.getDate() - lastDateAssigned[ra] < ldaTolerance:
                # Then the RA is no longer a duty candidate
                isCand = False
                # print("      Removed: Recent Duty")

            # If it is a double duty day
            if isDoubleDay:
                # If an RA has been assigned more double-duty day duties than
                #  the nddTolerance over the doubleDayAvg
                if numDoubleDays[ra] > ((1 + nddTolerance) * doubleDayAvg):
                    # Then the RA is no longer a duty candidate
                    isCand = False
                    # print("      Removed: Double Day Overload")

            # If an RA meets the necessary criteria
            if isCand:
                # Then append them to the candidate list
                retList.append(ra)
                # print("      Valid Candidate")
            else:
                # Append the RA to the list of RAs that have
                #  conflicts with this date.
                conList.append(ra)

        def genCandScore(ra, day, lastDateAssigned, numDoubleDays, isDoubleDay,
                         datePts, doubleDayAvg, ptsAvg, numFlagDuties, flagDutyAvg):
            # This function generates the candidate score of the RA
            #  For simplicity's sake, all variables aside from 'ra' and 'day'
            #  are values.

            # Base value is the number of points an RA has
            weight = ra.getPoints()

            # Add the difference between the number of points an RA has and the
            #  average number of points for all the RAs. This value could be
            #  negative, in which case, it will push the ra further towards the front
            weight += ra.getPoints() - ptsAvg

            # Subtract the number of days since the RA was last assigned
            weight -= day.getDate() - lastDateAssigned

            # If it is a double-duty day
            if isDoubleDay:
                # Add the difference between the number of doubleDays an RA has
                #  and the average number of doubleDays for all the RAs.
                weight += numDoubleDays - doubleDayAvg

                # If the next duty slot for the day will be a flagged duty slot,
                if day.nextDutySlotIsFlagged():
                    # Add the difference between the number of flagged duties an RA has
                    #  and the average number of flag duties for all the RAs.
                    weight += numFlagDuties - flagDutyAvg

            # If the number of points from this day will throw the RA over
            #  the average...
            if ra.getPoints() + datePts > ptsAvg:
                # ... then add the number of points over the average
                weight += (ra.getPoints() + datePts) - ptsAvg

            else:
                # Otherwise subtract the difference between the average and the
                #  number of points the RA would have.
                weight -= ptsAvg - (ra.getPoints() + datePts)

            return weight

        # Sort the RAs from lowest candidate score to the highest.
        #  The following line sorts the retList using a lambda function as the
        #  key. The purpose of this lambda function is to wrap genCandScore
        #  so that it can be passed the necessary parameters that are within a
        #  scope that is beyond genCandScore. Additionally, these parameters can
        #  be recalculated for each RA that is passed to the lambda function.
        # print("  Sorting")
        retList.sort(
            key=lambda ra: genCandScore(
                ra, day, lastDateAssigned[ra],
                numDoubleDays[ra], isDoubleDay, datePts,
                doubleDayAvg, ptsAvg, numFlagDuties[ra],
                flagDutyAvg
            )
        )
        conList.sort(
            key=lambda ra: genCandScore(
                ra, day, lastDateAssigned[ra],
                numDoubleDays[ra], isDoubleDay, datePts,
                doubleDayAvg, ptsAvg, numFlagDuties[ra],
                flagDutyAvg
            )
        )

        return retList, conList

    def removeAssignedRAs(self):
        # Remove all of the assigned RAs from the current Day. This will also
        #  update the lastDutyAssigned, numDoubleDays and numFlagDuties dicts as
        #  necessary.

        # Iterate over all RAs assigned to duties on the current day
        for dutySlot in self.curDay.iterDutySlots():

            # Check to see if this slot has been assigned
            if dutySlot.isAssigned():
                # Get the assigned RA
                assignedRA = dutySlot.getAssignment()

                # Remove this day from the lastDateAssigned dict
                self.lda[assignedRA].pop()

                # If this day is a doubleDay
                if self.curDay.isDoubleDay():
                    # Then also decrement the numDoubleDays dict
                    self.ndd[assignedRA] -= 1

                # If this duty slot is flagged
                if dutySlot.getFlag():
                    # Then also decrement the numFlagDuties
                    self.nfd[assignedRA] -= 1

                # Lastly, remove the RA from duty
                self.curDay.removeRA(assignedRA)

            # If it is not assigned, skip this duty slot

    def getNextConflictCandidate(self):
        # Remove and return the next conflict candidate
        return self.conList.pop(0)

    def assignNextConflictRA(self):
        # Assign the next RA with a duty conflict on
        #  curDay's duty.

        # Get the next conflict RA for the curDay's duty
        conRA = self.getNextConflictCandidate()

        # If flagged duty, then update numFlagDuties
        if self.curDay.nextDutySlotIsFlagged():
            self.nfd[conRA] += 1

        # Assign the conflict RA for the curDay's duty
        self.curDay.addRA(conRA)

        # Update lastDateAssigned
        self.lda[conRA].append(self.curDay.getDate())

        # If doubleDay, then update numDoubleDays
        if self.isDoubleDay():
            self.ndd[conRA] += 1

        # Return the selected candidate RA
        return conRA

    def assignRA(self, ra):
        # Assign the provided RA for duty on this day.

        # If flagged duty, then update numFlagDuties
        if self.curDay.nextDutySlotIsFlagged():
            self.nfd[ra] += 1

        # Assign the candidate RA for the curDay's duty
        self.curDay.addRA(ra)

        # Update lastDateAssigned
        self.lda[ra].append(self.curDay.getDate())

        # If doubleDay, then update numDoubleDays
        if self.isDoubleDay():
            self.ndd[ra] += 1

        # Return the selected candidate RA
        return ra


if __name__ == "__main__":

    ra = RA("Tyler", "Conzett", 0, 1, "11/25/18", [1, 2, 3], 0)
    print(ra)

    d = Day(date(2018, 5, 21), numDutySlots=2)
    print(d)
    d.addRA(ra)
    print(d)

    sched = Schedule(2018, 5)
    #print(sched)

    for i in sched:
        print(i)
