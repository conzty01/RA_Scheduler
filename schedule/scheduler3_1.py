from schedule.ra_sched import Schedule, Day, RA
from calendar import Calendar
from datetime import datetime
from pythonds import Stack
import logging

class State:
    # This class is used to store information regarding the current "state" of
    #  the DFS traversal.
    #
    # The breakdown of the parameters that this object takes to initialize are:
    #
    #     date              = Date object for the current state.
    #     raList            = A sorted list of unvisited RA candidates for the
    #                          given date.
    #     lastDateAssigned  = A dictionary containing information regarding the
    #                          last day each of the RAs were assigned
    #     numDoubleDays     = A dictionary containing information regarding the
    #                          number of double days an RA has already been
    #                          assigned.
    #     editable          = Boolean denoting if this state can is allowed to
    #                          be changed/reevaluated. This is used to denote
    #                          whether this particular date/duty was preset.

    def __init__(self, day, raList, lastDateAssigned, numDoubleDays, \
                 ldaTolerance, nddTolerance, predetermined=False):
        self.curDay = day
        self.lda = lastDateAssigned
        self.ndd = numDoubleDays
        self.ldaTol = ldaTolerance
        self.nddTol = nddTolerance

        self.predetermined = predetermined

        # If this state has been predetermined, then the first RA in the raList
        #  will always be selected as the for duty on this day.
        if self.predetermined:
            self.candList = raList

        elif len(raList) == 0:
            # Else if the provided raList is empty, then do not attempt to calculate
            #  an ordered candidate list (results in divide by 0 error if allowed)
            self.candList = raList

        else:
            # Otherwise we will calculate the ordered candidate list for this state.
            self.candList = self.getSortedWorkableRAs(raList, self.curDay, self.lda,\
                                        self.curDay.isDoubleDay(), self.ndd, \
                                        self.curDay.getPoints(), self.ldaTol, self.nddTol)

    def __deepcopy__(self):
        return State(self.curDay, self.candList, self.lda.copy(), self.ndd.copy(), \
                    self.ldaTol, self.nddTol, self.predetermined)

    def deepcopy(self):
        return self.__deepcopy__()

    def restoreState(self):
        return (self.curDay, self.candList, self.lda , self.ndd)

    def hasEmptyCandList(self):
        return len(self.candList) == 0

    def returnedFromPreviousState(self):
        return self.curDay.numberOnDuty() > 0

    def isDoubleDay(self):
        return self.curDay.isDoubleDay()

    def getNextCandidate(self):
        return self.candList.pop(0)

    def assignNextRA(self):
        # Assign the next candidate RA for curDay's duty

        # Get the next candidate RA for the curDay's duty
        candRA = self.getNextCandidate()

        # Assign the candidate RA for th curDay's duty
        self.curDay.addRA(candRA)

        # Update lastDateAssigned
        self.lda[candRA] = self.curDay.getDate()

        # If doubleDay, then update numDoubleDays
        if self.isDoubleDay():
            self.ndd[candRA] += 1

        # Return the selected candidate RA
        return candRA

    def getSortedWorkableRAs(self, raList, day, lastDateAssigned, isDoubleDay,\
            numDoubleDays, datePts, ldaTolerance, nddTolerance):
        # Create and return a new sorted list of RAs that are available for duty
        #  on the provided day.

        # Calculate the average number of points amongst RAs
        s = 0
        for ra in raList:
            s += ra.getPoints()

        ptsAvg = s / len(raList)

        #print("  Average Points:",ptsAvg)

        # If isDoubleDay, calculate the average number of double days
        #  assigned amongst RAs
        if isDoubleDay:
            s = 0
            for ra in numDoubleDays:
                s += numDoubleDays[ra]

            doubleDayAvg = s / len(numDoubleDays)
            #print("  Double Day Average:",doubleDayAvg)

        else:
            # Default to -1 when not a doubleDay
            doubleDayAvg = -1


        retList = []    # List to be returned containing all workable RAs

        #print("  Removing candidates")
        # Get rid of the unavailable candidates
        for ra in raList:
            #print("    ",ra)
            isCand = True

            # If an RA has a conflict with the duty shift
            #print(day.getDate() in ra.getConflicts())
            if day.getDate() in ra.getConflicts():
                isCand = False
                #print("      Removed: Conflict")

            # If an RA has been assigned a duty recently
            #  This is skipped when the LDA is 0, meaning the RA has not been
            #  assigned for duty yet this month.
            if lastDateAssigned[ra] != 0 and \
               day.getDate() - lastDateAssigned[ra] < ldaTolerance:
                isCand = False
                #print("      Removed: Recent Duty")

            # If it is a double duty day
            if isDoubleDay:
                # If an RA has been assigned more double day duties than
                #  the nddTolerance over the doubleDayAvg
                if numDoubleDays[ra] > ((1 + nddTolerance) * doubleDayAvg):
                    isCand = False
                    #print("      Removed: Double Day Overload")

            # If an RA meets the necessary criteria
            if isCand:
                retList.append(ra)
                #print("      Valid Candidate")


        def genCandScore(ra,day,lastDateAssigned,numDoubleDays,isDoubleDay,\
                datePts,doubleDayAvg,ptsAvg):
            # This function generates the candidate score of the RA
            #  For simplicity's sake, all variables aside from 'ra' are values

            # Base value is the number of points an RA has
            weight = ra.getPoints()

            # Add the difference between the number of points an RA has and the
            #  average number of points for all the RAs. This value could be
            #  negative, in which case, it will push the ra futher towards the front
            weight += ra.getPoints() - ptsAvg

            # Subtract the number of days since the RA was last assigned
            weight -= day - lastDateAssigned

            # If it is a doubleDay
            if isDoubleDay:
                # Add the difference between the number of doubleDays an RA has
                #  and the average number of doubleDays for all the RAs.
                weight += numDoubleDays - doubleDayAvg

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
        #print("  Sorting")
        retList.sort(key=lambda ra: genCandScore(ra,day.getDate(),lastDateAssigned[ra],\
                                        numDoubleDays[ra],isDoubleDay,datePts,\
                                        doubleDayAvg,ptsAvg))

        return retList

def schedule(raList,year,month,noDutyDates=[],doubleDays=(4,5),doublePts=2, \
    doubleNum=2,doubleDates=set(),doubleDateNum=2,doubleDatePts=1,
    ldaTolerance=8,nddTolerance=.1,prevDuties=[]):
    # This algorithm will schedule RAs for duties based on ...
    #
    # The algorithm returns a Schedule object that contains Day objects which, in
    #  turn, contain RA objects that have been scheduled for that day.
    #
    # The breakdown of the parameters that this algorithm accepts is as follows:
    #
    #     raList        = list containing RA objects that are to be scheduled
    #     year          = year for scheduling
    #     month         = month for scheduling
    #     noDutyDates   = list of Date objects that represent dates where no RAs
    #                      should be on duty.
    #     doubleDays    = set containing integers denoting the day of the week
    #                      where multiple RAs should be scheduled. These integers
    #                      line up with the representation that is in the datetime
    #                      module. The mapping is as follows:
    #
    #                       Mon, Tues, Wed, Thurs, Fri, Sat, Sun
    #                        0    1     2     3     4    5    6
    #
    #     doublePts     = number of points that are earned on a double day
    #     doubleNum     = number of RAs to be assigned on a double day
    #     doubleDates   = set containing integers denoting the date of the month
    #                      where multiple RAs should be assigned. This is different
    #                      than the 'doubleDays' set in that it represents *dates*
    #                      where multiple RAs should be assigned-- not *days of the
    #                      week*. If a date happens to be in both the doubleDates
    #                      set and the doubleDays set, it acts like a double day.
    #     doubleDateNum = number of RAs to be assigned on a double date
    #     doubleDatePts = number of points that are earned on a double date
    #     ldaTolerance  = number of days before an RA is to be considered for duty
    #     nddTolerance  = tolerance for whether an RA should be considered for
    #                      duty on a double day. This tolerance helps prevent RAs
    #                      from being scheduled for two consective double days in
    #                      a row since they could be many days apart
    #     prevDuties    = list containing tuples of an RA object and date object
    #                      that cooresponds with the last few days of duty of the
    #                      previous month. This helps prevent RAs from being
    #                      assigned for duties in close succession at the
    #                      change of the month.

    logging.info("Starting Scheduling Process")

    def createDateDict(year,month,noDutyDates,doubleDays,doublePts,doubleNum, \
            doubleDates,doubleDateNum,doubleDatePts):
        # Create and return the dictionary that describes how to get from one day
        #  to another. The keys are the numeric date of a given day and the value
        #  is the numeric date of the day that should follow the given day. The
        #  first "day" in the dictionary is always 0 and the last key will have the
        #  value of -1 to deliminate that there are no more days in the chain.
        #  An example can be seen below.

        #     dateDict = { 0: 1, 1: 2, 2: 3, 3: 3.1, 3.1: 4, 4: -1 }

        # In the above example, the start day is 0 which points to day 1 which in
        #  turn points to day 2, which points to day 3. Day 3 has two duties that
        #  need to be assigned which is why key 3 points to 3.1 and key 3.1 points
        #  to key 4. To the algorithm, the fact that Day 3 has two duties does not
        #  matter, but this convention allows the date dictionary to be more human
        #  readable.

        dateDict = {}
        prevDay = Day(0,-1)
        for curMonthDay, curWeekDay in Calendar().itermonthdays2(year,month):
            # The iterator returned from the loop yields a tuple that
            #  contains an integer for the day of the week and the date
            #  of the month. The mapping of the day of the week is as follows:
            #
            #           Mon, Tues, Wed, Thurs, Fri, Sat, Sun
            #            0    1     2     3     4    5    6
            #
            # If the day of the week is 0, that means that that respective
            #  date belongs to either the next or previous month.

            # If the current month day belongs to the month being scheduled...
            if curMonthDay != 0:

                # If the date is not a day with duty, then skip it
                if curMonthDay not in noDutyDates:

                    if (curWeekDay in doubleDays):
                        # If the day of the week is a double day and should have
                        #  multiple RAs on duty.
                        #  By default, this is Friday and Saturday: (4,5)

                        # Current date and point val
                        d1 = Day(curMonthDay,curWeekDay,customPointVal=doublePts,isDoubleDay=True)
                        dateDict[prevDay] = d1      # <- Set to the previous day

                        d_ = d1
                        for i in range(1, doubleNum):
                            # Create the sub days such that if d1 = 1,
                            #  then d_ will equal 1.1, 1.2, 1.3 etc...

                            # Second node for current date and point val
                            tmp = Day(curMonthDay,curWeekDay,id=i,customPointVal=doublePts,isDoubleDay=True)
                            dateDict[d_] = tmp
                            d_ = tmp

                        # Set the previous day
                        prevDay = d_

                    elif (curMonthDay in doubleDates):
                        # If the date is a double date and should have multiple
                        #  RAs on duty.

                        # Current date and point val
                        d1 = Day(curMonthDay,curWeekDay,customPointVal=doubleDatePts,isDoubleDay=True)
                        dateDict[prevDay] = d1      # <- Set to the previous day

                        d_ = d1
                        for i in range(1, doubleDateNum):
                            # Create the sub days such that if d1 = 1,
                            #  then d_ will equal 1.1, 1.2, 1.3 etc...

                            # Second node for current date and point val
                            tmp = Day(curMonthDay,curWeekDay,id=i,customPointVal=doubleDatePts,isDoubleDay=True)
                            dateDict[d_] = tmp
                            d_ = tmp

                        # Set the previous day
                        prevDay = d_

                    else:
                        # Set the previous day to reference the current day
                        cmd = Day(curMonthDay,curWeekDay,customPointVal=1,isDoubleDay=False)
                        dateDict[prevDay] = cmd
                        prevDay = cmd

                    # Set the last day
                    dateDict[prevDay] = Day(-1,-1)

        return dateDict

    def createPreviousDuties(raList,prevDuties):

        lastDateAssigned = {}   # <- Dictionary of RA keys to lists of dates
        numDoubleDays = {}      # <- Dictionary of RA keys to int of the number of double duty days

        # Initialize lastDateAssigned and numDoubleDays for each RA
        for r in raList:
            numDoubleDays[r] = 0
            lastDateAssigned[r] = 0

        # Prime the lastDateAssigned from the prevDuties
        for ra, dDate in prevDuties:
            lastDateAssigned[ra] = dDate
        return numDoubleDays, lastDateAssigned


    # Create and prime the numDoubleDays and lastDateAssigned dicts with the
    #  data from the previous month's schedule.
    numDoubleDays, lastDateAssigned = createPreviousDuties(raList,prevDuties)

    # Create calendar
    logging.debug(" Creating Calendar")
    cal = createDateDict(year,month,noDutyDates,doubleDays,doublePts,doubleNum, \
                doubleDates,doubleDateNum,doubleDatePts)

    logging.debug(" Finished Creating Calendar")

    stateStack = Stack()    # Stack of memory states for traversing the dates
    # The stack contains tuples of the following objects:
    #       0: Date object for the given state
    #       1: The sorted, unvisited RA candidate list
    #       2: The lastDateAssigned dictionary
    #       3: The numDoubleDays dictionary

    logging.debug(" Initializing First Day")
    # Initialize the first day
    curDay = cal[Day(0,-1)]

    # Prime the stack with the first day and raList
    startState = State(curDay, raList, lastDateAssigned, numDoubleDays, \
                        ldaTolerance, nddTolerance)

    stateStack.push(startState)

    logging.debug(" Finished Initializing First Day")

    logging.debug(" Beginning Scheduling")
    while not stateStack.isEmpty() and curDay.getDate() != -1:

        # Get the current working state off the stack
        curState = stateStack.pop()
        curDay, candList, lastDateAssigned, numDoubleDays = curState.restoreState()

        # logging.debug("""  -- TOP OF SCHEDULE LOOP --
        #                     Current Day: {}
        #                     Candidate List: {}
        #                     lastDateAssigned: {}
        #                     numDoubleDays: {}
        #               """.format(curDay,candList,lastDateAssigned,numDoubleDays))
        #input("  Hit 'Enter' to continue ")

        # If there are no more candidate RAs for a given day, then go back to
        #  the previous state.
        if curState.hasEmptyCandList():
            #logging.debug("   NO CANDIDATES")
            continue

        # Check to see if we have come back from a subsequent state. This will
        #  be asserted if an RA has been assigned a duty for the current day.
        if curState.returnedFromPreviousState():
            # If we are returning from a subsequent day, then remove the RA(s)
            #  that was assigned.
            #logging.debug("   REVISTED DAY")
            curDay.removeAllRAs()

        candRA = curState.assignNextRA()
        #logging.debug("   Chosen RA: {}".format(candRA))

        # Put the updated current state back on the stateStack
        curStateCopy = curState.deepcopy()
        stateStack.push(curStateCopy)

        # Get the next Day
        nextDay = cal[curDay]

        # Generate the next State
        nextState = State(nextDay, raList, lastDateAssigned, numDoubleDays, \
                            ldaTolerance, nddTolerance)

        # If there is at least one RA that can be scheduled for the next day,
        #  or the current day is the end of the month, then add the next day to
        #  the stateStack. Otherwise, we will need to try a different path on
        #  the current state
        if not(nextState.hasEmptyCandList()) or nextDay.getDate() == -1:
            #logging.debug("   MOVING TO NEXT DAY")
            # Add the next day on the stack
            stateStack.push(nextState)

            curDay = nextDay    # Move on to the next day

        #input()

    logging.debug(" Finished Scheduling")

    # We've made it out of the scheduling loop meaning we either were not able to
    #  find a solution, or we were successful

    if stateStack.isEmpty():
        # If the stateStack is empty, then the algorithm could not create a
        #  schedule with zero conflicts.
        logging.info(" Could Not Generate Schedule")
        return []


    def parseSchedule(cal):
        #logging.debug("Parsing Generated Schedule")
        # Generate and return the schedule object
        sched = []
        prev = Day(-1,-1)
        #logging.debug(" Calendar Length: {}".format(len(cal)))
        #logging.debug(" Calendar keys: {}".format(sorted(cal.keys())))
        for key in sorted(cal.keys()):

            day = cal[key]
            # logging.debug(""" -- Top of Parsing Loop --
            #                     Prev: {}
            #                     Key: {}
            #                     Day: {}
            #             """.format(prev,key,day))
            d = day.getDate()

            # If the date is the same as the previous date, and the date is not -1
            if d == prev.getDate() and d != -1:
                # Then combine this day with the previous
                #logging.debug("   Same as previous")
                # Add a duty slot
                prev.addDutySlot()

                # Add the RA without adding points
                prev.addRaWithoutPoints(day.getRAs()[0])

            else:
                #logging.debug("   New Day")
                # Add the previous day to the schedule
                sched.append(prev)

                #  and mark the current day as the new prev
                prev = day

            #input()

        logging.debug("Finished Parsing Schedule")

        # Return the completed schedule (minus the first entry as it was just
        #  a part of the loop-and-a-half)
        return sched[1:]

    logging.info("Finished Scheduling Process")

    return Schedule(year,month,noDutyDates,parseSchedule(cal),doubleDays,doubleDates)


if __name__ == "__main__":
    test = {0:1, 1:2, 2:2.1, 2.1:3, 3:3.1, 3.1:4,
            4:5, 5:6, 6:7, 7:8, 8:9, 9:9.1, 9.1:10,
            10:10.1, 10.1:11, 11:12, 12:13, 13:14,
            14:15, 15:16, 16:16.1, 16.1:17, 17:17.1,
            17.1:18, 18:19, 19:20, 20:21, 21:22, 22:23, 23:23.1,
            23.1:24, 24:24.1, 24.1:25, 25:26, 26:27, 27:28,
            28:29, 29:30, 30:30.1, 30.1:31, 31:31.1, 31.1:-1}

    import random

    raList = []
    i = 0
    for name in "abcdefghijklmnop":
        upper = random.randint(0,10)
        c = []
        while len(c) < upper:
            cnum = random.randint(1,32)
            if cnum not in c:
                c.append(cnum)

        print(c)
        raList.append(RA(name,name,i,1,None,conflicts=c,points=random.randint(0,5)))


    """raList = [RA("a","a",1,None,None),
              RA("b","b",2,None,None),
              RA("c","c",3,None,None),
              RA("d","d",4,None,None),
              RA("e","e",5,None,None),
              RA("f","f",6,None,None),
              RA("g","g",7,None,None),
              RA("h","h",8,None,None),
              RA("i","i",9,None,None),
              RA("j","j",10,None,None),
              RA("k","k",11,None,None),
              RA("l","l",12,None,None),
              RA("m","m",13,None,None),
              RA("n","n",14,None,None),
              RA("o","o",15,None,None),
              RA("p","p",16,None,None)]"""

    r = schedule(raList,2019,9)

    for day in r:
        print(day)
        for ra in day.getRAs():
            print(" ", ra)
