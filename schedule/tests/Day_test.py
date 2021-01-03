from schedule.ra_sched import Day, RA
from datetime import date
import unittest

class TestDayObject(unittest.TestCase):
    def setUp(self):
        s = []
        n = 5
        for i in range(n):
            ra = RA("T","C",i,1,date(2017,1,1))
            s.append(ra)

        self.day = Day(date(2018,5,24),3,numDutySlots=n+1,ras=s)

    def testIter(self):
        for ra in self.day:
            self.assertIsInstance(ra,RA)

    def testAddRA(self):
        ra1 = RA("R","E",99,1,date(2017,2,2))
        ra2 = RA("C","K",98,1,date(2017,3,3))
        self.day.addDutySlot()
        preNum = self.day.numberOnDuty()

        self.day.addRA(ra1)
        self.assertEqual(self.day.numberOnDuty(),preNum+1)
        self.assertRaises(OverflowError,self.day.addRA,ra2)

    def testRemoveRA(self):
        ra = RA("D","B",97,1,date(2017,4,4))
        self.day.addDutySlot()
        self.day.addRA(ra)
        self.day.removeRA(ra)

        self.assertNotIn(ra,self.day.getRAs())

    def testNumberdutySlots(self):
        self.assertEqual(self.day.numberDutySlots(),self.day.numDutySlots)

    def testAddDutySlot(self):
        numSlots = self.day.numberDutySlots()
        addNum = 2
        self.day.addDutySlot(addNum)
        self.assertEqual(self.day.numberDutySlots(),numSlots + addNum)

    def testNumberOnDuty(self):
        num = self.day.numberOnDuty()
        self.assertEqual(num,len(self.day.ras))

    def testGetRAs(self):
        ras = self.day.getRAs()
        self.assertEqual(ras,self.day.ras)

if __name__ == "__main__":
    unittest.main()
