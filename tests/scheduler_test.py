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
        self.noDutyDates = set()
        self.doubleDays = set()
        self.doublePts = 2
        self.doubleNum = 2
        self.doubleDates = set()
        self.doubleDateNum = 2
        self.doubleDatePts = 2

    def testCreateDateDict(self):
        rList = []
        sList = [6,7,8,9,0]
        raList, schedList = resetRAList(rList,sList)

        self.assertEqual(raList,sList)
        self.assertEqual(schedList,[])

        self.assertNotEqual(raList,rList)
        self.assertNotEqual(schedList,sList)



if __name__ == "__main__":
    unittest.main()
