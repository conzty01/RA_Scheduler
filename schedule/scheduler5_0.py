from schedule.ra_sched import Schedule, Day, RA, State
from calendar import Calendar
from pythonds import Stack
import logging


def schedule(raList, year, month, noDutyDates=[], doubleDays=(4, 5), doublePts=2,
             doubleNum=2, doubleDates=set(), doubleDateNum=2, doubleDatePts=1,
             ldaTolerance=8, nddTolerance=.1, prevDuties=[], breakDuties=[],
             setDDFlag=False, regDutyPts=1, regNumAssigned=1, assignConflicts=False,
             conAssignState=None):
    # This algorithm will schedule RAs for duties based on ...
    #
    # The algorithm returns a Schedule object that contains Day objects which, in
    #  turn, contain RA objects that have been scheduled for that day.
    #
    # The breakdown of the parameters that this algorithm accepts is as follows:
    #
    #     raList          = list containing RA objects that are to be scheduled
    #     year            = year for scheduling
    #     month           = month for scheduling
    #     noDutyDates     = list of integers that represent dates where no RAs
    #                        should be on duty.
    #     doubleDays      = set containing integers denoting the day of the week
    #                        where multiple RAs should be scheduled. These integers
    #                        line up with the representation that is in the datetime
    #                        module. The mapping is as follows:
    #
    #                         Mon, Tues, Wed, Thurs, Fri, Sat, Sun
    #                          0    1     2     3     4    5    6
    #
    #     doublePts       = number of points that are earned on a double day
    #     doubleNum       = number of RAs to be assigned on a double day
    #     doubleDates     = set containing integers denoting the date of the month
    #                        where multiple RAs should be assigned. This is different
    #                        than the 'doubleDays' set in that it represents *dates*
    #                        where multiple RAs should be assigned-- not *days of the
    #                        week*. If a date happens to be in both the doubleDates
    #                        set and the doubleDays set, it acts like a double day.
    #     doubleDateNum   = number of RAs to be assigned on a double date
    #     doubleDatePts   = number of points that are earned on a double date
    #     ldaTolerance    = number of days before an RA is to be considered for duty
    #     nddTolerance    = tolerance for whether an RA should be considered for
    #                        duty on a double day. This tolerance helps prevent RAs
    #                        from being scheduled for two consecutive double days in
    #                        a row since they could be many days apart
    #     prevDuties      = list containing tuples of an RA object and date object
    #                        that corresponds with the last few days of duty of the
    #                        previous month. This helps prevent RAs from being
    #                        assigned for duties in close succession at the
    #                        change of the month.
    #     breakDuties     = list containing integers that represent dates where
    #                        the scheduler should skip due to the occurrence of a
    #                        previously scheduled break duty on that date.
    #     setDDFlag       = boolean representing whether or not to set the special
    #                        flag on one of the duties for double duty days.
    #     assignConflicts = boolean representing whether or not to assign RAs on
    #                        days they have entered conflicts for. This is only
    #                        used if there are no other eligible RAs available on
    #                        that day.
    #     conAssignState  = State object denoting the furthest state that was reached
    #                        before attempting to override conflicts. This object is
    #                        only used if the assignConflicts parameter is set to True.

    logging.info("Starting Scheduling Process")

    def createDateDict(year, month, noDutyDates, doubleDays, doublePts, doubleNum,
                       doubleDates, doubleDateNum, doubleDatePts, breakDuties,
                       setDDFlag):
        # Create and return the dictionary that describes how to get from one day
        #  to another. The keys are the numeric date of a given day and the value
        #  is the numeric date of the day that should follow the given day. The
        #  first "day" in the dictionary is always 0 and the last key will have the
        #  value of -1 to delineate that there are no more days in the chain.
        #  An example can be seen below.

        #     dateDict = { 0: 1, 1: 2, 2: 3, 3: 3.1, 3.1: 4, 4: -1 }

        # In the above example, the start day is 0 which points to day 1 which in
        #  turn points to day 2, which points to day 3. Day 3 has two duties that
        #  need to be assigned which is why key 3 points to 3.1 and key 3.1 points
        #  to key 4. To the algorithm, the fact that Day 3 has two duties does not
        #  matter, but this convention allows the date dictionary to be more human
        #  readable.

        dateDict = {}
        prevDay = Day(0, -1)
        for curMonthDay, curWeekDay in Calendar().itermonthdays2(year, month):
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

                # If the date is not a day with duty, or it is a break duty,
                #  then skip it
                if (curMonthDay not in noDutyDates) and (curMonthDay not in breakDuties):

                    if curWeekDay in doubleDays:
                        # If the day of the week is a double day and should have
                        #  multiple RAs on duty.
                        #  By default, this is Friday and Saturday: (4,5)

                        # Current date and point val
                        d1 = Day(curMonthDay, curWeekDay, customPointVal=doublePts, isDoubleDay=True)
                        dateDict[prevDay] = d1  # <- Set to the previous day

                        d_ = d1
                        for i in range(1, doubleNum):
                            # Create the sub days such that if d1 = 1,
                            #  then d_ will equal 1.1, 1.2, 1.3 etc...

                            # Second node for current date and point val
                            tmp = Day(
                                curMonthDay,
                                curWeekDay,
                                dayID=i,
                                customPointVal=doublePts,
                                isDoubleDay=True,
                                # Set the flagDutySlot value to True if setDDFlag is True
                                #  AND this is the last double-day duty slot for this day.
                                flagDutySlot=(setDDFlag and i == doubleNum - 1)
                            )
                            dateDict[d_] = tmp
                            d_ = tmp

                        # Set the previous day
                        prevDay = d_

                    elif curMonthDay in doubleDates:
                        # If the date is a double date and should have multiple
                        #  RAs on duty.

                        # Current date and point val
                        d1 = Day(curMonthDay, curWeekDay, customPointVal=doubleDatePts, isDoubleDay=True)
                        dateDict[prevDay] = d1  # <- Set to the previous day

                        d_ = d1
                        for i in range(1, doubleDateNum):
                            # Create the sub days such that if d1 = 1,
                            #  then d_ will equal 1.1, 1.2, 1.3 etc...

                            # Second node for current date and point val
                            tmp = Day(
                                curMonthDay,
                                curWeekDay,
                                dayID=i,
                                customPointVal=doubleDatePts,
                                isDoubleDay=True,
                                # Set the flagDutySlot value to True if setDDFlag is True
                                #  AND this is the last double-day duty slot for this day.
                                flagDutySlot=(setDDFlag and i == doubleDateNum - 1)
                            )
                            dateDict[d_] = tmp
                            d_ = tmp

                        # Set the previous day
                        prevDay = d_

                    else:
                        # Otherwise this is considered to be a regular duty day.

                        # Set the previous day to reference the current day
                        cmd = Day(
                            curMonthDay,
                            curWeekDay,
                            customPointVal=regDutyPts,
                            isDoubleDay=False
                        )
                        dateDict[prevDay] = cmd

                        # If the number of duty slots for regular duties is greater than 1...
                        #  then create the extra duties.
                        if regNumAssigned > 1:
                            d_ = d1
                            for i in range(1, regNumAssigned):
                                # Create the sub days such that if d1 = 1,
                                #  then d_ will equal 1.1, 1.2, 1.3 etc...

                                # Second node for current date and point val
                                tmp = Day(
                                    curMonthDay,
                                    curWeekDay,
                                    dayID=i,
                                    customPointVal=regDutyPts,
                                    isDoubleDay=True
                                )
                                dateDict[d_] = tmp
                                d_ = tmp

                            # Set the previous day
                            prevDay = d_

                        else:
                            # Otherwise set the original day as the previous day for the next
                            #  day to use.
                            prevDay = cmd

                    # Set the last day
                    dateDict[prevDay] = Day(-1, -1)

        return dateDict

    def createPreviousDuties(raList, prevDuties):

        lastDateAssigned = {}  # <- Dictionary of RA keys to lists of dates
        numDoubleDays = {}  # <- Dictionary of RA keys to int of the number of double duty days
        numFlagDuties = {}  # <- Dictionary of RA keys to int of the number of flagged duty days

        # Initialize lastDateAssigned and numDoubleDays for each RA
        for r in raList:
            numDoubleDays[r] = 0
            lastDateAssigned[r] = [0]
            numFlagDuties[r] = 0

        # Prime the lastDateAssigned and lastFlagDateAssigned from the prevDuties
        for ra, dDate, flagged in prevDuties:
            lastDateAssigned[ra] = [dDate]

            # If the duty was a flagged duty...
            if flagged:
                # Then add the duty to the lastFlagDateAssigned dictionary.
                numFlagDuties[ra] += 1

        return numDoubleDays, lastDateAssigned, numFlagDuties

    # Create and prime the numDoubleDays, lastDateAssigned, and lastFlagDateAssigned dicts with the
    #  data from the previous month's schedule.
    numDoubleDays, lastDateAssigned, numFlagDuties = createPreviousDuties(raList, prevDuties)

    # Create the calendar
    logging.debug(" Creating Calendar")
    cal = createDateDict(year, month, noDutyDates, doubleDays, doublePts, doubleNum,
                         doubleDates, doubleDateNum, doubleDatePts, breakDuties,
                         setDDFlag)

    logging.debug(" Finished Creating Calendar")

    logging.debug(" Initial numDoubleDays: {}".format(numDoubleDays))
    logging.debug(" Initial lastDateAssigned: {}".format(lastDateAssigned))
    logging.debug(" Initial numFlagDuties: {}".format(numFlagDuties))

    stateStack = Stack()  # Stack of memory states for traversing the dates
    # The stack contains tuples of the following objects:
    #       0: Date object for the given state
    #       1: The sorted, unvisited RA candidate list
    #       2: The lastDateAssigned dictionary
    #       3: The numDoubleDays dictionary
    #       4: The numFlagDuties dictionary

    logging.debug(" Initializing First Day")
    # Initialize the first day
    curDay = cal[Day(0, -1)]

    # Prime the stack with the first day and raList
    startState = State(curDay, raList, lastDateAssigned, numDoubleDays,
                       ldaTolerance, nddTolerance, numFlagDuties)

    stateStack.push(startState)

    # Set the internally used furthest state to the first state so that we
    #  can keep track of it.
    furthestState = startState

    # The RA assigned to the conflict state that got us the furthest through
    #  the month without running into another roadblocking state
    postConStateFurthestRA = None

    # Roadblocking state that exists after the provided conAssignState
    subConAssignState = None

    # Have we already seen the conAssignState?
    alreadySeenConAssignState = False   # TODO: Possibly startState == conAssignState and assignConflicts?

    logging.debug(" Finished Initializing First Day")

    logging.debug(" Beginning Scheduling")
    while not stateStack.isEmpty() and curDay.getDate() != -1:

        # Get the current working state off the stack
        curState = stateStack.pop()
        curDay, candList, lastDateAssigned, numDoubleDays, numFlagDuties = curState.restoreState()

        # logging.debug("--TOP OF SCHEDULE LOOP--\n" +
        #               "Current Day: {}\nCandidate List: {}\nlastDateAssigned: {}\nnumDoubleDays: {}"
        #               .format(curDay, candList, lastDateAssigned, numDoubleDays))
        # input("  Hit 'Enter' to continue ")

        # If there are no more candidate RAs for a given day...
        if curState.hasEmptyCandList():
            # logging.debug("   NO CANDIDATES")

            # Check to see if this run has been configured to override duty conflicts
            if assignConflicts:
                # If so, then check to see if we have reached the provided
                #  assign conflicts state
                if curState == conAssignState:
                    # logging.debug("   REACHED ASSIGN CONFLICTS STATE")
                    # If we have reached the Assign Conflicts State

                    # If we have NOT already seen this state before.
                    if not curState.returnedFromPreviousState():
                        # logging.debug("   OVERRIDING DUTY CONFLICT")
                        # Then this is the first time we have reached this state.

                        # Assign an RA for duty that has a conflict on this day.
                        postConStateFurthestRA = curState.assignNextConflictRA()

                        # This day is now the new furthest day.
                        furthestState = curState.deepcopy()

                        # Set the subConAssignState to the current state
                        subConAssignState = curState.deepcopy()

                        # Set the alreadySeenConAssignState to True
                        alreadySeenConAssignState = True

                    else:
                        # logging.debug("   REMOVING PREVIOUS CONFLICT OVERRIDE RA")
                        # Otherwise we have reached this state before and have come back
                        #  due to a roadblock on a future day.

                        #  In this implementation, we will keep track of how far we got
                        #  with the previously assigned conflict RA and try somebody new.
                        #  If we come to another roadblock that is impassable without
                        #  assigning over conflicts again, then we will pick the RA that
                        #  got us the furthest and repeat these steps on the next roadblock.

                        # Check to see if there are any other RAs with duty conflicts for
                        #  this day that can be overridden.
                        if not curState.hasEmptyConList():
                            # If there are, then check to see if the currently assigned RA
                            #  got us further through the month than the previous
                            #  postConStateFurthestRA
                            if furthestState == subConAssignState:
                                # If so, then we have a new furthest RA
                                postConStateFurthestRA = curDay.getLastDutySlotAssignment()

                            # Remove all previously assigned RAs from this day
                            curState.removeAssignedRAs()

                            # Select the next conflict RA to be assigned and try again
                            curState.assignNextConflictRA()

                        else:
                            # If there is not, then re-assign the RA that got us the furthest

                            # Remove all previously assigned RAs from this day
                            curState.removeAssignedRAs()

                            # Assign the RA that got us the furthest
                            curState.assignRA(postConStateFurthestRA)

                    # Regardless of which path above was taken, put the updated
                    #  current state back on the stateStack
                    curStateCopy = curState.copy()
                    stateStack.push(curStateCopy)

                    # Get the next Day
                    nextDay = cal[curDay]

                    # Generate the next State
                    nextState = State(nextDay, raList, lastDateAssigned, numDoubleDays,
                                      ldaTolerance, nddTolerance, numFlagDuties)

                elif curState == subConAssignState:
                    # logging.debug("   REACHED SUBSEQUENT ROADBLOCKING STATE")
                    # Else if we have reached a subsequent roadblocking state.

                    # Then assign an RA who has a conflict with this day
                    #  and keep going.

                    pass

                else:
                    # Otherwise, this run is configured to override duty conflicts,
                    #  however we have reached a day with no available duties per
                    #  the normal workflow.

                    # Check to see if we have reached a new furthest subsequent
                    #  conflict assignment state
                    if curState > subConAssignState:
                        # If so, then set this state as being a new furthest
                        #  subsequent conflict assignment state
                        subConAssignState = curState.deepcopy()

                    # Go back to the previous state.
                    continue

            else:
                # Otherwise, simply go back to the previous state.
                continue

        else:
            # Otherwise, this day is eligible to have an RA assigned for duty.

            # Check to see if we have come back from a subsequent state. This will
            #  be asserted if an RA has been assigned a duty for the current day.
            if curState.returnedFromPreviousState():
                # If we are returning from a subsequent day, then remove the RA(s)
                #  that were previously assigned.
                # logging.debug("   REVISTED DAY")
                curState.removeAssignedRAs()

            # Check to see if we have reached a new furthest state
            if curDay.getDate() > furthestState.curDay.getDate():
                # If so, set this state as the new furthest
                furthestState = curState.deepcopy()

            # Check to see if we have already seen the conAssignState and we have
            #  reached a new furthest subsequent conflict assignment state
            if alreadySeenConAssignState and curDay.getDate() > subConAssignState.curDay.getDate():
                # If so, set this state as the new furthest subConAssignState
                subConAssignState = curState.deepcopy()

            curState.assignNextRA()
            # logging.debug("   Chosen RA: {}".format(candRA))

            # Put the updated current state back on the stateStack
            curStateCopy = curState.copy()
            stateStack.push(curStateCopy)

            # Get the next Day
            nextDay = cal[curDay]

            # Generate the next State
            nextState = State(nextDay, raList, lastDateAssigned, numDoubleDays,
                              ldaTolerance, nddTolerance, numFlagDuties)

        # If there is at least one RA that can be scheduled for the next day,
        #  or the current day is the end of the month, then add the next day to
        #  the stateStack. Otherwise, we will need to try a different path on
        #  the current state
        if not (nextState.hasEmptyCandList()) or nextDay.getDate() == -1:
            # logging.debug("   MOVING TO NEXT DAY")
            # Add the next day on the stack
            stateStack.push(nextState)

        # input()

    logging.debug(" Finished Scheduling")

    # We've made it out of the scheduling loop meaning we either were not able to
    #  find a solution, or we were successful

    if stateStack.isEmpty():
        # If the stateStack is empty, then the algorithm could not create a
        #  schedule with zero conflicts.
        logging.info(" Could Not Generate Schedule")
        return [], furthestState

    def parseSchedule(cal):
        # logging.debug("Parsing Generated Schedule")
        # Generate and return the schedule object
        sched = []
        prev = Day(-1, -1)
        # logging.debug(" Calendar Length: {}".format(len(cal)))
        # logging.debug(" Calendar keys: {}".format(sorted(cal.keys())))
        for key in sorted(cal.keys()):

            day = cal[key]
            # logging.debug(" -- Top of Parsing Loop --\nPrev: {}\nKey: {}\nDay: {}".format(prev,key,day))
            d = day.getDate()

            # If the date is the same as the previous date, and the date is not -1
            if d == prev.getDate() and d != -1:
                # Then combine this day with the previous
                # logging.debug("   Same as previous")
                # Add a duty slot
                prev.addDutySlot()

                # Use the combineDay() method to simply append the
                #  current day's duty slots to the previous
                #  day's duty slots.
                prev.combineDay(day)

            else:
                # logging.debug("   New Day")
                # Add the previous day to the schedule
                sched.append(prev)

                #  and mark the current day as the new prev
                prev = day

            # input()

        logging.debug("Finished Parsing Schedule")

        # Return the completed schedule (minus the first entry as it was just
        #  a part of the loop-and-a-half)
        return sched[1:]

    logging.info("Finished Scheduling Process")

    return Schedule(year, month, noDutyDates, parseSchedule(cal), doubleDays, doubleDates), furthestState


if __name__ == "__main__":
    test = {0: 1, 1: 2, 2: 2.1, 2.1: 3, 3: 3.1, 3.1: 4,
            4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 9.1, 9.1: 10,
            10: 10.1, 10.1: 11, 11: 12, 12: 13, 13: 14,
            14: 15, 15: 16, 16: 16.1, 16.1: 17, 17: 17.1,
            17.1: 18, 18: 19, 19: 20, 20: 21, 21: 22, 22: 23, 23: 23.1,
            23.1: 24, 24: 24.1, 24.1: 25, 25: 26, 26: 27, 27: 28,
            28: 29, 29: 30, 30: 30.1, 30.1: 31, 31: 31.1, 31.1: -1}

    import random

    raList = []
    i = 0
    for name in "abcdefghijklmnop":
        upper = random.randint(0, 10)
        c = []
        while len(c) < upper:
            cnum = random.randint(1, 32)
            if cnum not in c:
                c.append(cnum)

        print(c)
        raList.append(RA(name, name, i, 1, None, conflicts=c, points=random.randint(0, 5)))

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

    r = schedule(raList, 2019, 9)

    for day in r:
        print(day)
        for ra in day.getRAs():
            print(" ", ra)
