from datetime import date
from ra_sched import Schedule, Day
import random
import calendar                                                                 # Only needed for oldScheduling()

def scheduling(raList,year,month,noDutyDates=[],doubleDays=(4,5)):
    # This algorithm will schedule RAs for duties based on ...
    #
    # The algorithm returns a Schedule object that contains Day objects which, in
    #  turn, contain RA objects that have been scheduled for that day.
    #
    # The breakdown of the parameters that this algorithm accepts is as follows:
    #
    #     raList      = list containing RA objects that are to be scheduled
    #     year        = year for scheduling
    #     month       = month for scheduling
    #     noDutyDates = list of Date objects that represent dates where no RAs
    #                    should be on duty.
    #     doubleDays  = set containing integers denoting the day of the week
    #                    where two RAs should be scheduled these integers line
    #                    up with the representation that is in the datetime
    #                    module. The mapping is as follows:
    #
    #                       Mon, Tues, Wed, Thurs, Fri, Sat, Sun
    #                        0    1     2     3     4    5    6
    #
    def resetRAList(raList,schedList):
        raList = schedList                                                      # Switch the two lists
        return (raList, [])                                                     # Reset schedList to []

    def assignRA(day,raList,schedList,cand_index):
        cand_ra = raList[cand_index]                                            # Candidate RA
        day.addRA(cand_ra)                                                      # Assign candidate RA for duty
        schedList.append(raList.pop(cand_index))                                # Add RA to scheduledList
        return (raList,schedList,0)

    def checkReset(raList,scheduledList):
        if len(raList) < 1 and len(scheduledList) > 0:                          # If all RAs have been assigned
            raList, scheduledList = resetRAList(raList, scheduledList)          # Reset lists
            raList.sort()                                                       # Re-sort the RA lists
        return (raList,scheduledList)

    scheduledList = [] # A list that contains RAs that have been scheduled already
    schedule = Schedule(year,month,noDutyDates,doubleDays=doubleDays)

    raList.sort()
    # Prioritize RAs by the number of points they have accumulated -> [least points...most points]
    schedule.sort()
    # Prioritize the days by the number of duty slots they have as well as the
    #  calendar date
    #  -> [most # duty slots...least # duty slots]
    #  -> [earlier date...later date]

    # DEBUGING PRINT STATEMENTS
    #print("raList: ",raList)
    #print("schedule: ",schedule)
    #print("scheduledList: ",scheduledList)

    for day in schedule:                                                        # Iterate through days in the month
        if day.numberDutySlots() > 0:                                           # If there are duty slots available for a given day (Otherwise skip)

            # If there should be at least 1 RA scheduled for duty on this day,
            #  then while the number of RAs assigned for duty on this day is
            #  less than the number of duty slots for this day, iterate through
            #  the RAs until one is found that does not have a conflict with
            #  this day. If all RAs have a conflict with this day, then assign
            #  an RA and add the day to the schedule's review set and mark the
            #  schedule for review.

            cand_index = 0                                                      # Index of Candidate RA

            while day.numberOnDuty() < day.numberDutySlots():

                if cand_index >= len(raList):
                    # If the candidate RA index exceeds the length of the raList,
                    #  then assign an RA and add the day to the schedule's review
                    #  set and mark the schedule for review.
                    raList, scheduledList, cand_index = assignRA(day,raList,    # Assign the first RA for duty
                                                            scheduledList,0)
                    schedule.addReviewDay(day)                                  # Add day to schedule's review days
                    schedule.setReview()                                        # Mark schedule for review
                    raList, scheduledList = checkReset(raList,scheduledList)    # Check if the lists should be reset

                else:
                    cand_ra = raList[cand_index]                                # Candidate RA

                    if day.getDate() not in cand_ra.getConflicts():
                        raList, scheduledList, cand_index = assignRA(day, raList,  # Assign RA
                                                                     scheduledList,
                                                                     cand_index)

                    else:
                        cand_index += 1                                         # Move to next candidate

                    raList, scheduledList = checkReset(raList, scheduledList)   # Check if the lists should be reset

    return schedule

def oldScheduling(raConflicts, year, month):
    # Depreciated
    #this will take conflicts eventually
    daysInMonth = calendar.monthrange(year,month)[1]
    days = [0,1,2,3,4,5,6] # Mon,Tues,Wed,Thurs,Fri,,Sat,Sun
    weekDays = [0,1,2,3,6] # Mon,Tues,Wed,Thurs,Sun
    startDay = calendar.monthrange(year,month)[0]
    raNames = []
    schedule = {}
    conflictchecker = []
    pos = 0
    for key in raConflicts:
        raNames.append(key)
        schedule[key]=[]
    for day in range(1,daysInMonth+1):
        #checks to shcedule one RA vs two depending on weekday/weekend

        if startDay in weekDays:
            #checks to see if there is a conflict, if there isn't we schedule
            if day not in raConflicts[raNames[pos]]:

                schedule[raNames[pos]].append(day)
                #next RA checks to see if we are at the end of the list of their names
                #uses accumulator pattern.
                if pos == len(raNames)-1:
                    random.shuffle(raNames)
                    pos = 0
                else:
                    pos = pos+1
                if startDay == 6:
                    startDay = 0
                else:
                    startDay = startDay+1



            #we have a conflict!  it adds the ra's name to a list of conflicts
            #to keep track of ra's with conflicts on that date
            else:
                conflictchecker.append(raNames[pos])
                if pos == len(raNames)-1:
                    random.shuffle(raNames)
                    pos = 0
                else:
                    pos = pos+1
                while len(conflictchecker) != len(raNames):
                    if day not in raConflicts[raNames[pos]]:
                        schedule[raNames[pos]].append(day)
                        #next RA checks to see if we are at the end of the list of their names
                        #uses accumulator pattern.
                        if pos == len(raNames)-1:
                            random.shuffle(raNames)
                            pos = 0
                        else:
                            pos = pos+1
                        if startDay == 6:
                            startDay = 0
                        else:
                            startDay = startDay+1
                        #refresh the list to save for conflicts on a different day
                        conflictchecker = []
                        break
                    else:
                        conflictchecker.append(raNames[pos])
                        if pos == len(raNames)-1:
                            random.shuffle(raNames)
                            pos = 0
                        else:
                            pos = pos+1
                        continue
                #worst case scenario where everyone remaining has a conflict on
                #this day we schedule someone at random and move on.
                if len(conflictchecker) == len(raNames):
                    random.shuffle(raNames)
                    schedule[raNames[pos]].append(day)
                    if pos == len(raNames)-1:
                        random.shuffle(raNames)
                        pos = 0
                    else:
                        pos = pos+1
                    if startDay == 6:
                        startDay = 0
                    else:
                        startDay = startDay+1
                    conflictchecker = []


        #we have a weekend so with most staff's we schedule 2
        else:
            if day not in raConflicts[raNames[pos]]:
                schedule[raNames[pos]].append(day)
                #next RA checks to see if we are at the end of the list of their names
                #uses accumulator pattern.
                if pos == len(raNames)-1:
                    random.shuffle(raNames)
                    pos = 0
                else:
                    pos = pos + 1
                if day not in raConflicts[raNames[pos]]:
                    schedule[raNames[pos]].append(day)
                    if pos == len(raNames)-1:
                        random.shuffle(raNames)
                        pos = 0
                    else:
                        pos = pos + 1
                    if startDay == 6:
                        startDay= 0
                    else:
                        startDay = startDay+1
                else:
                    conflictchecker.append(raNames[pos])
                    if pos == len(raNames)-1:
                        random.shuffle(raNames)
                        pos = 0
                    else:
                        pos = pos + 1
                    while len(conflictchecker) != len(raNames):
                        if day not in raConflicts[raNames[pos]]:
                            schedule[raNames[pos]].append(day)

                            if pos == len(raNames)-1:
                                random.shuffle(raNames)
                                pos = 0
                            else:
                                pos = pos+1

                            if startDay == 6:
                                startDay= 0
                            else:
                                startDay = startDay+1
                            conflictchecker = []
                            break
                        else:
                            conflictchecker.append(raNames[pos])
                            if pos == len(raNames) - 1:
                                random.shuffle(raNames)
                                pos = 0
                            else:
                                pos = pos + 1
                            continue
                    if len(conflictchecker) == len(raNames):
                        random.shuffle(raNames)
                        schedule[raNames[pos]].append(day)
                        if pos == len(raNames)-1:
                            random.shuffle(raNames)
                            pos = 0
                        else:
                            pos = pos+1
                        if startDay == 6:
                            startDay = 0
                        else:
                            startDay = startDay+1
                        conflictchecker = []

            else:
                conflictchecker.append(raNames[pos])
                if pos == len(raNames)-1:
                    random.shuffle(raNames)
                    pos = 0
                else:
                    pos = pos+1
                while len(conflictchecker) != len(raNames):
                    if day not in raConflicts[raNames[pos]]:
                        schedule[raNames[pos]].append(day)

                        if pos == len(raNames)-1:
                            random.shuffle(raNames)
                            pos = 0
                        else:
                            pos = pos+1

                        if startDay == 6:
                            startDay= 0
                        else:
                            startDay = startDay+1
                        conflictchecker = []
                        break
                    else:
                        conflictchecker.append(raNames[pos])
                        if pos == len(raNames) - 1:
                            random.shuffle(raNames)
                            pos = 0
                        else:
                            pos = pos + 1
                        continue
                if len(conflictchecker) == len(raNames):
                    random.shuffle(raNames)
                    schedule[raNames[pos]].append(day)
                    if pos == len(raNames)-1:
                        random.shuffle(raNames)
                        pos = 0
                    else:
                        pos = pos+1
                    if startDay == 6:
                        startDay = 0
                    else:
                        startDay = startDay+1
                    conflictchecker = []
    #print(schedule)
    return schedule

if __name__ == "__main__":
    s = oldScheduling({'Ryan': [1,3,5,9,10],'Sarah':[4,5,6,20,25],
                    'Steve': [1,2,5,15, 25],'Tyler': [15,16,19,20,28],
                    'Casey': [1,13,14,15,16],'Steven':[7,11],
                    'Rob': [20,25]
                    },2017,5)

    from ra_sched import RA
    year = 2018
    month = 5
    reviewed = 0
    times = 1#00000
    for t in range(times):
        ra_list = [RA("Ryan", "E", 1, 1, date(2017, 8, 22),
                      [date(year, month, 1), date(year, month, 10), date(year, month, 11)]),
                   RA("Jeff", "L", 1, 2, date(2017, 8, 22),
                      [date(year, month, 2), date(year, month, 12), date(year, month, 22)]),
                   RA("Steve", "B", 1, 3, date(2017, 8, 22),
                      [date(year, month, 3), date(year, month, 13), date(year, month, 30)]),
                   RA("Tyler", "C", 1, 4, date(2017, 8, 22), [date(year, month, 4), date(year, month, 14)]),
                   RA("Casey", "K", 1, 5, date(2017, 8, 22), [date(year, month, 5)])]
        s2 = scheduling(ra_list,year,month,[date(year,month,14),date(year,month,15),date(year,month,16),date(year,month,17)])

        print(s)
        print(s2)
        print("Should review: ", s2.shouldReview())
        print("Review days: ", s2.getReviewDays())
        print("-----")
        if s2.shouldReview():
            reviewed += 1

    print("Review Avg: ",reviewed/times)
    print("Point Breakdown: ")

    for d in s2:
        for r in d:
            print(r.getName(),r.getPoints())
