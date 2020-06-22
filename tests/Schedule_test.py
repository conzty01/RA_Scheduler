import unittest
from datetime import date
from ra_sched import Schedule, RA

class TestScheduleObject(unittest.TestCase):
    def setUp(self):
        self.sched = Schedule(2018,5,
        noDutyDates=[date(2018,5,24),date(2018,5,25),date(2018,5,26)],
        doubleDays=(4,5),
        doubleDates=[date(2018,5,21),date(2018,5,22),date(2018,5,23)])

    def testIter(self):
        for pos,day in enumerate(self.sched):
            self.assertEqual(self.sched.schedule[pos],day)

    def testNumDays(self):
        self.assertEqual(len(self.sched.schedule),self.sched.numDays())

    def testGetDate(self):
        self.assertEqual(self.sched.getDate(1),self.sched.schedule[0])
        self.assertEqual(self.sched.getDate(self.sched.numDays()),self.sched.schedule[self.sched.numDays()-1])
        self.assertRaises(IndexError,self.sched.getDate,0)
        self.assertRaises(IndexError,self.sched.getDate,100)

    def testAddRA(self):
        ra = RA("T","C",1234,4321,date(2017,1,1))
        d = 1
        preAdd = self.sched.getDate(d).getRAs()
        self.sched.addRA(d,ra)
        postAdd = self.sched.getDate(d).getRAs()

        self.assertEqual(preAdd,postAdd)
        self.assertRaises(IndexError,self.sched.addRA,0,ra)
        self.assertRaises(IndexError,self.sched.addRA,100,ra)

    def testRemoveRA(self):
        ra = RA("R","K",5,1,date(2017,2,2))
        d = 1

        preRem = self.sched.getDate(d).getRAs()
        self.sched.addRA(d,ra)
        self.sched.removeRA(d,ra)
        postRem = self.sched.getDate(d).getRAs()

        self.assertEqual(preRem,postRem)


if __name__ == "__main__":
    unittest.main()
