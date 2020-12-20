from schedule.scheduler4_0 import schedule
from schedule.ra_sched import Schedule, RA
from datetime import date
import unittest
import random

class TestScheduler(unittest.TestCase):
    def setUp(self):
        random.seed(12345)

        self.year = 2020
        self.month = 8
        self.conflictList = [date(self.year, self.month,  1),
                             date(self.year, self.month,  2),
                             date(self.year, self.month,  3),
                             date(self.year, self.month,  4),
                             date(self.year, self.month,  5),
                             date(self.year, self.month, 10),
                             date(self.year, self.month, 11),
                             date(self.year, self.month, 12),
                             date(self.year, self.month, 13),
                             date(self.year, self.month, 14),
                             date(self.year, self.month, 22),
                             date(self.year, self.month, 30)]

        self.raList = [RA("R", "E", 1, 1, date(2017, 8, 22)),
                       RA("J", "L", 1, 2, date(2017, 8, 22)),
                       RA("S", "B", 1, 3, date(2017, 8, 22)),
                       RA("T", "C", 1, 4, date(2017, 8, 22)),
                       RA("C", "K", 1, 5, date(2017, 8, 22))]

        self.noDutyDates = list()
        self.doubleDays = (4,5)
        self.doublePts = 2
        self.doubleNum = 2
        self.doubleDates = set()
        self.doubleDateNum = 2
        self.doubleDatePts = 1

    def testScheduler_ReturnsListObjectWhenUnableToGenerateSchedule(self):
        # Arrange

        sched = schedule(self.raList,self.year,self.month,
                         self.noDutyDates,self.doubleDays,
                         self.doublePts,self.doubleNum,
                         self.doubleDates,self.doubleDateNum,
                         self.doubleDatePts)

        # Act
        # Assert

        self.assertIsInstance(sched, list)

    def testScheduler_ReturnsScheduleObject(self):
        # Arrange

        additionalRAs = [RA("A", "K", 1, 6, date(2017, 8, 22)),
                         RA("A", "Z", 1, 7, date(2017, 8, 22)),
                         RA("F", "P", 1, 8, date(2017, 8, 22)),
                         RA("I", "O", 1, 9, date(2017, 8, 22)),
                         RA("Y", "E", 1, 10, date(2017, 8, 22)),
                         RA("W", "A", 1, 11, date(2017, 8, 22)),
                         RA("Z", "A", 1, 12, date(2017, 8, 22)),
                         RA("R", "S", 1, 13, date(2017, 8, 22))]

        # Act

        self.raList += additionalRAs

        sched = schedule(self.raList,self.year,self.month,
                         self.noDutyDates,self.doubleDays,
                         self.doublePts,self.doubleNum,
                         self.doubleDates,self.doubleDateNum,
                         self.doubleDatePts)

        # Assert

        self.assertIsInstance(sched, Schedule)



if __name__ == "__main__":
    unittest.main()
