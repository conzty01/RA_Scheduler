import calendar
import random
from datetime import date

class RA:
    def __init__(self,firstName,lastName,id,hallId,dateStarted,conflicts=[],points=0):
        self.firstName = firstName
        self.lastName = lastName
        self.fullName = firstName + " " + lastName
        self.id = id
        self.hallId = hallId
        self.conflicts = conflicts
        self.dateStarted = dateStarted
        self.points = points

    def __str__(self):
        return "{} has {} points".format(self.fullName,self.points)

    def __repr__(self):
        return "RA(Id: {}, Name: {})".format(self.hallId,self.firstName)

    def __iter__(self):
        for c in self.conflicts:
            yield c

    def __eq__(self,other):
        return self.fullName == other.fullName and \
               self.id == other.id and \
               self.hallId == other.hallId and \
               self.conflicts == other.conflicts and \
               self.dateStarted == other.dateStarted and \
               self.points == other.points

    def __hash__(self):
        return hash((self.fullName,self.id,self.hallId,self.dateStarted))

    def __lt__(self,other):
        # Sort by comparing the number of points RAs have. If RAs have the same
        #  number of points, then randomly return True or False.
        if self.getPoints() != other.getPoints():
            return self.getPoints() < other.getPoints()
        else:
            return 1 == random.randint(0,1)

    def getConflicts(self):
        return self.conflicts

    def getId(self):
        return self.id

    def getStartDate(self):
        return self.dateStarted

    def getPoints(self):
        return self.points

    def addPoints(self,amt):
        self.points += amt

    def getName(self):
        return self.fullName

    def getHallId(self):
        return self.hallId

class Day:
    def __init__(self,d,numDutySlots=0,ras=set(),customPointVal=0):
        self.date = d
        self.review = False
        if ras:
            self.ras = ras
            self.numDutySlots = len(ras)
        else:
            self.numDutySlots = numDutySlots
            self.ras = set()

        if customPointVal == 0:
            if numDutySlots > 1:
                self.pointVal = 2
            else:
                self.pointVal = 1
        else:
            self.pointVal = customPointVal

    def __str__(self):
        return "{} with {} on duty".format(self.date,self.ras)

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        for ra in self.ras:
            yield ra

    def __lt__(self,other):
        if self.numberDutySlots() == other.numberDutySlots():
            if self.getDate() < other.getDate():
                return True
            else:
                return False

        elif self.numberDutySlots() > other.numberDutySlots():
            # This '>' is hardcoded for the expectation that we want to sort in
            #  reverse order, but we would still like earlier dates before later
            #  dates in a list.
            return True
        else:
            return False

    def __hash__(self):
        return hash(self.date)

    def __eq__(self,other):
        return self.date == other.date

    def addRA(self,ra):
        if len(self.ras) < self.numDutySlots:
            self.ras.add(ra)
            ra.addPoints(self.pointVal)
        else:
            raise OverflowError("Limit for number on duty exceeded.")

    def removeRA(self,ra):
        self.ras.remove(ra)

    def numberDutySlots(self):
        return self.numDutySlots

    def addDutySlot(self,amt=1):
        self.numDutySlots += amt

    def getPoints(self):
        return self.pointVal

    def getDate(self):
        return self.date

    def numberOnDuty(self):
        return len(self.ras)

    def getRAs(self):
        return self.ras

    def setReview(self):
        self.review = True

    def review(self):
        return self.review

class Schedule:

    def __init__(self,year,month,noDutyDates=[],sched=[],doubleDays=(4,5)):
        self.review = False
        self.reviewDays = set()
        self.noDutyDates = noDutyDates
        self.doubleDays = doubleDays
        self.doubleDates = []

        if sched:
            self.schedule = sched
        else:
            self.schedule = []

            for d in calendar.Calendar().itermonthdays2(year,month):
                # The iterator returned from the loop yields a tuple that
                #  contains an integer for the day of the week and the date
                #  of the month. The mapping of the day of the week is as follows:
                #
                #           Mon, Tues, Wed, Thurs, Fri, Sat, Sun
                #            0    1     2     3     4    5    6
                #
                # If the day of the week is 0, that means that that respective
                #  date belongs to the next or previous month.

                if d[0] != 0:
                    if d[0] in noDutyDates: # If the date is not a day with duty
                        self.schedule.append(Day(date(year,month,d[0]),numDutySlots=0))
                    else:
                        if d[1] in doubleDays:
                            # If the day of the week should have two RAs on duty
                            #  By default, this is Friday and Saturday: (4,5)
                            self.doubleDates.append(d[0])
                            self.schedule.append(Day(date(year,month,d[0]),numDutySlots=2))
                        else:
                            # Else the day should have one RA on duty
                            self.schedule.append(Day(date(year,month,d[0]),numDutySlots=1))

    def __repr__(self):
        return "Schedule({})".format(self.schedule)

    def __iter__(self):
        for d in self.schedule:
            yield d

    def sort(self):
        self.schedule.sort(reverse=True)

    def numDays(self):
        return len(self.schedule)

    def getDate(self,date):
        if date < 1 or date > len(self.schedule):
            raise IndexError("Dates are indexed from 1 to {}, index given: {}".format(len(self.schedule),date))
        else:
            return self.schedule[date-1] # The 1st of a month is at position 0 in the list

    def addRA(self,date,ra):
        self.getDate(date).addRA(ra)

    def removeRA(self,date,ra):
        self.getDate(date).removeRA(ra)

    def setReview(self):
        self.review = True

    def addReviewDay(self,day):
        self.reviewDays.add(day)

    def getReviewDays(self):
        return self.reviewDays

    def shouldReview(self):
        return self.review


if __name__ == "__main__":

    ra = RA("Tyler","Conzett",0,1,"11/25/18",[1,2,3],0)
    print(ra)

    d = Day(date(2018,5,21),numDutySlots=2)
    print(d)
    d.addRA(ra)
    print(d)

    sched = Schedule(2018,5)
    #print(sched)

    for i in sched:
        print(i)
