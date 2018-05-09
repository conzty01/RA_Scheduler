import calendar
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
    def __init__(self,d,numDutySlots=0,ras=set()):
        self.date = d
        if ras:
            self.ras = ras
            self.numDutySlots = len(ras)
        else:
            self.numDutySlots = numDutySlots
            self.ras = set()

    def __str__(self):
        return "{} on {}".format(self.ras,self.date)

    def __repr__(self):
        return "Day(Date: {}, Number of Duty Slots: {}, RAs: {})".format(self.date,self.numDutySlots,self.ras)

    def __iter__(self):
        for ra in self.ras:
            yield ra

    def addRA(self,ra):
        if len(self.ras) < self.numDutySlots:
            self.ras.add(ra)
        else:
            raise Exception("Cannot assign RA, {}, for duty. Duty Limit reached- \
                             NumSlots: {}, RAs: {}".format(ra,self.numDutySlots,self.ras))

    def removeRA(self,ra):
        self.ras.remove(ra)

    def numberDutySlots(self):
        return self.numDutySlots

    def addDutySlot(self,amt=1):
        self.numDutySlots += num

    def numberOnDuty(self):
        return len(self.ras)

    def getRAs(self):
        return self.ras

class Schedule:

    def __init__(self,year,month,noDutyDates=[],sched=[],doubleDays=(4,5)):

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
                    if d[0] in noDutyDates: # If the date is not a day without duty
                        self.schedule.append(Day(date(year,month,d[0]),numDutySlots=0))
                    else:
                        if d[1] in doubleDays:
                            # If the day of the week should have two RAs on duty
                            #  By default, this is Friday and Saturday: (4,5)
                            self.schedule.append(Day(date(year,month,d[0]),numDutySlots=2))
                        else:
                            self.schedule.append(Day(date(year,month,d[0]),numDutySlots=1))

    def __repr__(self):
        return "Schedule({})".format(self.schedule)

    def __iter__(self):
        for d in self.schedule:
            yield d

    def numDays(self):
        return len(self.schedule)

    def getDate(self,date):
        return self.schedule[date-1] # The 1st of a month is at position 0 in the list

    def addRA(self,date,ra):
        self.schedule[date-1].addRA(ra)

    def removeRA(self,date,ra):
        self.schedule[date-1].removeRA(ra)



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
