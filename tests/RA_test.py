import unittest
from datetime import date
from ra_sched import RA

class TestRAObject(unittest.TestCase):
    def setUp(self):
        self.ra = RA("Tyler","Conzett",1234,4321,date(2017,1,1),
                     [date(2018,5,3),date(2018,5,7),date(2018,5,22)])

    def testIter(self):
        for pos,conflict in enumerate(self.ra):
            self.assertEqual(self.ra.conflicts[pos],conflict)

    def testGetConflicts(self):
        self.assertEqual(self.ra.getConflicts(),self.ra.conflicts)

    def testGetId(self):
        self.assertEqual(self.ra.getId(),self.ra.id)

    def testGetStartDate(self):
        self.assertEqual(self.ra.getStartDate(),self.ra.dateStarted)

    def testGetPoints(self):
        self.assertEqual(self.ra.getPoints(),self.ra.points)

    def testAddPoints(self):
        prevPoints = self.ra.getPoints()
        self.ra.addPoints(1)
        newPoints = self.ra.getPoints()

        self.assertEqual(newPoints,prevPoints + 1)

    def testGetName(self):
        self.assertEqual(self.ra.getName(),self.ra.fullName)

    def testGetHallId(self):
        self.assertEqual(self.ra.getHallId(),self.ra.hallId)

if __name__ == '__main__':
    unittest.main()
