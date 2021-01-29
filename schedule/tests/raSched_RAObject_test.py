from schedule.ra_sched import RA
from unittest.mock import patch
from datetime import date
import unittest
import random


class TestRAObject(unittest.TestCase):
    def setUp(self):

        # -- Create a patchers for the logging --
        self.patcher_loggingDEBUG = patch("logging.debug", autospec=True)
        self.patcher_loggingINFO = patch("logging.info", autospec=True)
        self.patcher_loggingWARNING = patch("logging.warning", autospec=True)
        self.patcher_loggingCRITICAL = patch("logging.critical", autospec=True)
        self.patcher_loggingERROR = patch("logging.error", autospec=True)

        # Start the patcher - mock returned
        self.mocked_loggingDEBUG = self.patcher_loggingDEBUG.start()
        self.mocked_loggingINFO = self.patcher_loggingINFO.start()
        self.mocked_loggingWARNING = self.patcher_loggingWARNING.start()
        self.mocked_loggingCRITICAL = self.patcher_loggingCRITICAL.start()
        self.mocked_loggingERROR = self.patcher_loggingERROR.start()

        self.ra = RA("Tyler", "Conzett", 1234, 4321, date(2017, 1, 1),
                     [date(2018, 5, 3), date(2018, 5, 7), date(2018, 5, 22)])

    def tearDown(self):
        # Stop all of the patchers
        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

    def test_hasExpectedMethods(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_hasExpectedProperties(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_hasExpectedDefaultValues(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodStr_returnsExpectedString(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodRepr_returnsExpectedRepr(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodIter_iteratesOverConflicts(self):
        for pos, conflict in enumerate(self.ra):
            self.assertEqual(self.ra.conflicts[pos], conflict)

    def test_magicMethodEq_returnsTrueIfAndOnlyIfAllDesiredAttributesMatch(self):
        ra1 = RA("1","1",1,0,date(2017,1,1))
        ra2 = RA("1","1",1,0,date(2017,1,1))
        ra3 = RA("2","2",3,0,date(2017,1,1))

        self.assertEqual(ra1,ra2)
        self.assertNotEqual(ra1,ra3)

    def test_magicMethodHash_returnsHashOfTupleOfAttributes(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodLt_ifRAObjectsHaveUnequalPoints_evaluatesAppropriately(self):
        ra1 = RA("1", "1", 1, 0, date(2017, 1, 1))
        ra2 = RA("2", "2", 2, 0, date(2017, 1, 1))
        ra3 = RA("3", "3", 3, 0, date(2017, 1, 1))
        ra4 = RA("4", "4", 3, 0, date(2017, 1, 1))
        ra5 = RA("5", "5", 3, 0, date(2017, 1, 1))

        # By default, all RAs have 0 points.
        ra1.addPoints(1)
        ra2.addPoints(1)
        ra3.addPoints(5)
        ra4.addPoints(3)
        # The general, expected outcome is:
        #     ra5, ra1 or ra2, ra4, ra3

        lst = [ra4, ra2, ra5, ra3, ra1]  # Initialize the list

        random.seed(4)  # Set random number generation seed

        lst.sort()
        self.assertEqual(lst, [ra5, ra2, ra1, ra4, ra3])
        lst.sort()
        self.assertEqual(lst, [ra5, ra2, ra1, ra4, ra3])
        lst.sort()
        self.assertEqual(lst, [ra5, ra1, ra2, ra4, ra3])

    def test_magicMethodLt_ifRAObjectsHaveEqualPoints_evaluatesRandomly(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodDeepcopy_returnsDeepCopyOfRAObject(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_getConflicts_returnsConflictsAttribute(self):
        self.assertEqual(self.ra.getConflicts(), self.ra.conflicts)

    def test_getId_returnsIDAttribute(self):
        self.assertEqual(self.ra.getId(), self.ra.id)

    def test_getStartDate_returnsStartDateAttribute(self):
        self.assertEqual(self.ra.getStartDate(), self.ra.dateStarted)

    def test_getPoints_returnsPointsAttribute(self):
        self.assertEqual(self.ra.getPoints(), self.ra.points)

    def test_addPoints_addsProvidedNumberOfPointsToPointsAttribute(self):
        prevPoints = self.ra.getPoints()
        self.ra.addPoints(1)
        newPoints = self.ra.getPoints()

        self.assertEqual(newPoints, prevPoints + 1)

    def test_removePoints_decreasesPointsAttributeByProvidedAmount(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_getName_returnsFullNameAttribute(self):
        self.assertEqual(self.ra.getName(), self.ra.fullName)

    def test_getHallId_returnsHallIDAttribute(self):
        self.assertEqual(self.ra.getHallId(), self.ra.hallId)


if __name__ == '__main__':
    unittest.main()
