import unittest
from scheduler import resetRAList, assignRA, checkReset, scheduling
from ra_sched import Schedule, Day, RA
from datetime import date
import random
import calendar

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.year = 2018
        self.month = 5
        self.raList = [RA("Ryan", "E", 1, 1, date(2017, 8, 22), [date(self.year, self.month, 1),
                                                                 date(self.year, self.month, 10),
                                                                 date(self.year, self.month, 11)]),
                       RA("Jeff", "L", 1, 2, date(2017, 8, 22), [date(self.year, self.month, 2),
                                                                 date(self.year, self.month, 12),
                                                                 date(self.year, self.month, 22)]),
                       RA("Steve", "B", 1, 3, date(2017, 8, 22),[date(self.year, self.month, 3),
                                                                 date(self.year, self.month, 13),
                                                                 date(self.year, self.month, 30)]),
                       RA("Tyler", "C", 1, 4, date(2017, 8, 22),[date(self.year, self.month, 4), 
                                                                 date(self.year, self.month, 14)]),
                       RA("Casey", "K", 1, 5, date(2017, 8, 22),[date(self.year, self.month, 5)])]

    def testResetRAList(self):
        rList = []
        sList = [6,7,8,9,0]
        raList, schedList = resetRAList(rList,sList)

        self.assertEqual(raList,sList)
        self.assertEqual(schedList,[])

        self.assertNotEqual(raList,rList)
        self.assertNotEqual(schedList,sList)

    def testCheckReset(self):
        # Should Reset
        rList = []
        sList = [7,0,3,8,9,6,]
        raList, schedList = checkReset(rList,sList)

        self.assertEqual(raList,sList)
        self.assertEqual(schedList,[])

        # Should not reset raList !< 1
        rList = [1]
        sList = [5,6,7]
        raList, schedList = checkReset(rList,sList)

        self.assertEqual(raList,rList)
        self.assertEqual(schedList,sList)

        # Should not reset, but both should be []
        rList = []
        sList = []
        raList, schedList = checkReset(rList,sList)

        self.assertEqual(raList,rList)
        self.assertEqual(schedList,sList)

if __name__ == "__main__":
    unittest.main()
