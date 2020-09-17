from ra_sched import Schedule, Day, RA
from calendar import Calendar
from datetime import datetime
from pythonds import Stack

# TODO: Allow the algorithm to take into account when the RA was last assigned
#        duty in the previous month.

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

    def getSortedWorkableRAs(raList,day,lastDateAssigned,isDoubleDay,\
            numDoubleDays,datePts,ldaTolerance,nddTolerance):
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
    cal = createDateDict(year,month,noDutyDates,doubleDays,doublePts,doubleNum, \
                doubleDates,doubleDateNum,doubleDatePts)

    stateStack = Stack()    # Stack of memory states for traversing the dates
    # The stack contains tuples of the following objects:
    #       0: Date object for the given state
    #       1: The sorted, unvisited RA candidate list
    #       2: The lastDateAssigned dictionary
    #       3: The numDoubleDays dictionary

    # Initialize the first day
    curDay = cal[Day(0,-1)]

    # Prime the stack with the first day and raList
    stateStack.push((curDay,
                     getSortedWorkableRAs(raList,curDay,lastDateAssigned,\
                                          curDay.isDoubleDay(),numDoubleDays,\
                                          curDay.getPoints(),ldaTolerance,nddTolerance),
                     lastDateAssigned,
                     numDoubleDays))

    while not stateStack.isEmpty() and curDay.getDate() != -1:
        # Get the current working state off the stack
        curDay, candList, lastDateAssigned, numDoubleDays = stateStack.pop()
        #print("--------------------")
        #print("  Current Day:", curDay)
        #print("  Candidate List:", candList)
        #print("  lastDateAssigned:", lastDateAssigned)
        #print("  numDoubleDays:", numDoubleDays)
        #input("  Hit 'Enter' to continue ")

        # If there are no more candidate RAs for a given day, then go back to
        #  the previous state.
        if len(candList) == 0:
            #print("   NO CANDIDATES")
            continue

        # Check to see if we have come back from a subsequent state. This will
        #  be asserted if an RA has been assigned a duty for the current day.
        if curDay.numberOnDuty() > 0:
            # If we are returning from a subsequent day, then remove the RA(s)
            #  that was assigned.
            #print("   REVISTED DAY")
            curDay.removeAllRAs()

        # Get the next candidate RA for the curDay's duty
        candRA = candList.pop(0)

        # Assign the candidate RA for the curDay's duty
        curDay.addRA(candRA)
        #print("   Chosen RA:", candRA)

        # Update lastDateAssigned
        lastDateAssigned[candRA] = curDay.getDate()

        # If doubleDay, update numDoubleDays
        if curDay.isDoubleDay():
            numDoubleDays[candRA] += 1

        # Put the updated current state back on the stateStack
        stateStack.push((curDay,candList,lastDateAssigned.copy(),numDoubleDays.copy()))

        # Get the next Day
        nextDay = cal[curDay]

        #  Get the next Day's sorted raList
        nextList = getSortedWorkableRAs(raList,curDay,lastDateAssigned,\
                                        nextDay.isDoubleDay(),numDoubleDays,\
                                        nextDay.getPoints(),ldaTolerance,nddTolerance)

        # If there is at least one RA that can be scheduled for the next day,
        #  then add the current state and the next day to the stateStack. Otherwise,
        #  we will need to try a different path on the current state
        if len(nextList) != 0:
            #print("  MOVING TO NEXT DAY")
            # Add the next day on the stack
            stateStack.push((nextDay,nextList,lastDateAssigned,numDoubleDays))

            curDay = nextDay    # Move on to the next day

        #print("  REPEATING DAY")


    # We've made it out of the scheduling loop meaning we either were not able to
    #  find a solution, or we were successful

    if stateStack.isEmpty():
        # If the stateStack is empty, then the algorithm could not create a
        #  schedule with zero conflicts.
        return []


    def parseSchedule(cal):
        #print("==================")
        # Generate and return the schedule
        sched = []
        prev = Day(-1,-1)
        #print(len(cal))
        #print(sorted(cal.keys()))
        for key in sorted(cal.keys()):

            day = cal[key]
            #print("Prev", prev)
            #print("Key", key)
            #print("Day", day)
            d = day.getDate()

            # If the date is the same as the previous date, and the date is not -1
            if d == prev.getDate() and d != -1:
                # Then combine this day with the previous
                #print("  Same as previous")
                # Add a duty slot
                prev.addDutySlot()

                # Add the RA without adding points
                prev.addRaWithoutPoints(day.getRAs()[0])

            else:
                #print("  New Day")
                # Add the previous day to the schedule
                sched.append(prev)

                #  and mark the current day as the new prev
                prev = day

            #input()

        # Return the completed schedule (minus the first entry as it was just
        #  a part of the loop-and-a-half)
        return sched[1:]

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
