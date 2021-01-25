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

    def __init__(self, firstName, lastName, raID, hallID, dateStarted, conflicts=[], points=0):

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
        self.conflicts = list(conflicts)

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
    """

    def __init__(self, date, dow, numDutySlots=1, ras=[], customPointVal=0, dayID=0, isDoubleDay=False):
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

        # If an RA list has been provided
        if ras:
            # Set the RA list
            self.ras = ras

            # Also set the number of duty slots to be the
            #  length of the RA list.
            self.numDutySlots = len(ras)

        else:
            # Set the number of duty slots for this day.
            self.numDutySlots = numDutySlots

            # Set the RA list to an empty list
            self.ras = list()

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
        for ra in self.ras:
            yield ra

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

    def addRA(self, ra):
        # Add an RA to the list of RAs that are assigned
        #  to be on duty for this Day. This method will
        #  also add the Day's point value to the RA's total.

        # Check to see if all of the duty slots have already
        #  been filled.
        if len(self.ras) < self.numDutySlots:
            # If there is still room, append the RA to the list
            self.ras.append(ra)

            # And add the point values awarded for this duty to
            #  the RA.
            ra.addPoints(self.pointVal)

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
            self.ras.append(ra)

        else:
            # If all of the duty slots have already been filled,
            #  throw an Overflow exception.
            raise OverflowError("Limit for number on duty exceeded.")

    def removeRA(self, ra):
        # Remove and return the given RA from the list of RAs on duty.

        # First, remove the Day's points from the RA's total.
        ra.removePoints(self.pointVal)

        # Then remove and return the RA object.
        return self.ras.remove(ra)

    def removeAllRAs(self):
        # Remove and return all RAs from the list of RAs on duty.

        # Create a temporary reference to the list that can be returned.
        tmp = self.ras

        # Iterate through all of the RAs assigned for duty.
        for ra in self.ras:
            # Remove the Day's points from the RA's total.
            ra.removePoints(self.pointVal)

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
        return self.ras

    def setReview(self):
        # Set this day as being in need of manual review.
        self.review = True

    def review(self):
        # Return whether or not this day should be manually
        #  reviewed.
        return self.review


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
    def __init__(self, year, month, noDutyDates=[], sched=[], doubleDays=(4, 5), doubleDates=[]):
        # Whether the schedule should be set for manual review
        self.review = False

        # A set of the Days in the schedule that should be manually reviewed
        self.reviewDays = set()

        # A list of the days in which no duty should be scheduled
        self.noDutyDates = list(noDutyDates)

        # A tuple containing the days of the week that should have two duty slots
        self.doubleDays = doubleDays

        # A list containing dates which should have two duty slots
        self.doubleDates = list(doubleDates)

        # If 'sched' is defined...
        if sched:
            # then use this as the defined schedule.
            self.schedule = sched

        else:
            # Since a schedule was not previously defined, generate a blank schedule.

            # Set the schedule to an empty list to start
            self.schedule = []

            # Iterate through the days of the desired month
            for date, dow in calendar.Calendar().itermonthdays2(year, month):
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
                if date != 0:

                    # Check to see if this date should not have a duty scheduled on it
                    if date in noDutyDates:
                        # If no duty should be scheduled, create a Day object with
                        #  no duty slots and append it to the schedule
                        self.schedule.append(
                            Day(
                                date(year, month, date),
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
                                    date(year, month, date),
                                    dow,
                                    numDutySlots=2
                                )
                            )

                        else:
                            # Otherwise, if the date is not a double-day
                            #  then it should only have one RA on duty
                            self.schedule.append(
                                Day(
                                    date(year, month, date),
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
