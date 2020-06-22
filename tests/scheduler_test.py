import unittest
from scheduler3_0 import schedule
from ra_sched import Schedule, Day, RA
from datetime import date
import random
import calendar

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.year = 2020
        self.month = 8
        self.raList = [RA("R", "E", 1, 1, date(2017, 8, 22), [date(self.year, self.month, 1),
                                                                 date(self.year, self.month, 10),
                                                                 date(self.year, self.month, 11)]),
                       RA("J", "L", 1, 2, date(2017, 8, 22), [date(self.year, self.month, 2),
                                                                 date(self.year, self.month, 12),
                                                                 date(self.year, self.month, 22)]),
                       RA("S", "B", 1, 3, date(2017, 8, 22),[date(self.year, self.month, 3),
                                                                 date(self.year, self.month, 13),
                                                                 date(self.year, self.month, 30)]),
                       RA("T", "C", 1, 4, date(2017, 8, 22),[date(self.year, self.month, 4),
                                                                 date(self.year, self.month, 14)]),
                       RA("C", "K", 1, 5, date(2017, 8, 22),[date(self.year, self.month, 5)])
                       ]
        self.noDutyDates = list()
        self.doubleDays = (4,5)
        self.doublePts = 2
        self.doubleNum = 2
        self.doubleDates = set()
        self.doubleDateNum = 2
        self.doubleDatePts = 1

    def testCreateDateDict_ReturnsDict(self):
        # Arrange #


        # Act #
        # 31 Days; 4,5 doubleDays; no DoubleDates
        dateDict = schedule.createDateDict(self.year,self.month,self.noDutyDates,
                                            self.doubleDays,self.doublePts,
                                            self.doubleNum,self.doubleDates,
                                            self.doubleDateNum,self.doubleDatePts)

        # Assert #

    def testCreateDateDict_ReturnsTraversableDict(self):
        pass

    def testCreateDateDict_CreateMultipleDaysForDoubleDays(self):
        pass

    def testCreateDateDict_CreateMultipleDaysForDoubleDates(self):
        pass

    def testCreateDateDict_SetCorrectPointsForDay(self):
        pass

    def testGetSortedWorkableRAs_RespectsLDATolerance(self):
        pass

    def testGetSortedWorkableRAs_RespectsNDDTolerance(self):
        pass

    def testGetSortedWorkableRAs_ReturnsList(self):
        pass

    def testGenCandScore_ReturnsInt(self):
        pass

    def testParseSchedule_ReturnsList(self):
        pass

    def testParseSchedule_CombinesSameDates(self):
        pass

    def testScheduler3_0_CalculatesRAPoints(self):
        pass


if __name__ == "__main__":
    unittest.main()
