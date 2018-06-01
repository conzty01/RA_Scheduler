import unittest
import random
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

    def testEqual(self):
        ra1 = RA("1","1",1,0,date(2017,1,1))
        ra2 = RA("1","1",1,0,date(2017,1,1))
        ra3 = RA("2","2",3,0,date(2017,1,1))

        self.assertEqual(ra1,ra2)
        self.assertNotEqual(ra1,ra3)

    def testLessThan(self):
        ra1 = RA("1","1",1,0,date(2017,1,1))
        ra2 = RA("2","2",2,0,date(2017,1,1))
        ra3 = RA("3","3",3,0,date(2017,1,1))
        ra4 = RA("4","4",3,0,date(2017,1,1))
        ra5 = RA("5","5",3,0,date(2017,1,1))

        # By default, all RAs have 0 points.
        ra1.addPoints(1)
        ra2.addPoints(1)
        ra3.addPoints(5)
        ra4.addPoints(3)
        # The general, expected outcome is:
        #     ra5, ra1 or ra2, ra4, ra3

        lst = [ra4,ra2,ra5,ra3,ra1]     # Initialize the list

        random.seed(4)                  # Set random number generation seed

        lst.sort()
        self.assertEqual(lst,[ra5,ra2,ra1,ra4,ra3])
        lst.sort()
        self.assertEqual(lst,[ra5,ra2,ra1,ra4,ra3])
        lst.sort()
        self.assertEqual(lst,[ra5,ra1,ra2,ra4,ra3])

if __name__ == '__main__':
    unittest.main()
