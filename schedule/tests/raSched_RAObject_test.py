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
        # Test to ensure that the RA Object has the following methods:
        #  - getConflicts
        #  - getId
        #  - getStartDate
        #  - getPoints
        #  - addPoints
        #  - removePoints
        #  - getName
        #  - getHallId

        # -- Arrange --
        # -- Act --
        # -- Assert --

        self.assertTrue(hasattr(RA, "getConflicts"))
        self.assertTrue(hasattr(RA, "getId"))
        self.assertTrue(hasattr(RA, "getStartDate"))
        self.assertTrue(hasattr(RA, "getPoints"))
        self.assertTrue(hasattr(RA, "addPoints"))
        self.assertTrue(hasattr(RA, "removePoints"))
        self.assertTrue(hasattr(RA, "getName"))
        self.assertTrue(hasattr(RA, "getHallId"))

    def test_hasExpectedProperties(self):
        # Test to ensure that the RA Object has the following properties:
        #  - firstName
        #  - lastName
        #  - fullName
        #  - id
        #  - hallId
        #  - conflicts
        #  - dateStarted
        #  - points

        # -- Arrange --

        # Create the objects used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 99
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 12)
        desiredConflicts = [1, 2, 3]
        desiredPoints = 1234

        # Create the RA Object being tested
        testRAObject = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            desiredConflicts,
            desiredPoints
        )

        # -- Act --
        # -- Assert --

        # Assert that the above properties exist and are as we expect
        self.assertIsInstance(testRAObject.firstName, str)
        self.assertIsInstance(testRAObject.lastName, str)
        self.assertIsInstance(testRAObject.fullName, str)
        self.assertIsInstance(testRAObject.id, int)
        self.assertIsInstance(testRAObject.hallId, int)
        self.assertIsInstance(testRAObject.dateStarted, date)
        self.assertIsInstance(testRAObject.conflicts, list)
        self.assertIsInstance(testRAObject.points, int)

    def test_hasExpectedDefaultValues(self):
        # Test to ensure that when omitting non-required parameters
        #  when constructing an RA Object, the default values are
        #  as we would expect.

        # -- Arrange --

        # Create the objects used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 99
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 12)
        expectedConflicts = []
        expectedPoints = 0

        # -- Act --

        # Create the RA Object being tested
        testRAObject = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted
        )

        # -- Assert --

        # Assert that the values that weren't provided are set to the expected defaults
        self.assertEqual(expectedConflicts, testRAObject.conflicts)
        self.assertEqual(expectedPoints, testRAObject.points)

    def test_magicMethodStr_returnsExpectedString(self):
        # Test to ensure that the __str__ magic method returns the expected result

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 99
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 12)
        desiredPoints=14

        expectedResult1 = "User1 Test has 0 points"
        expectedResult2 = "User2 Test has {} points".format(desiredPoints)

        # Create the RA Object being tested
        testRAObject1 = RA(
            desiredFirstName + str(1),
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted
        )
        testRAObject2 = RA(
            desiredFirstName + str(2),
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints
        )

        # -- Act --

        # Call the method being tested
        result1 = testRAObject1.__str__()
        result2 = testRAObject2.__str__()

        # -- Assert --

        # Assert that we received the expected results
        self.assertEqual(expectedResult1, result1)
        self.assertEqual(expectedResult2, result2)

    def test_magicMethodRepr_returnsExpectedRepr(self):
        # Test to ensure that the __repr__ magic method returns
        #  the expected result

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 99
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 12)
        desiredPoints = 14

        expectedResult1 = "RA(Id: {}, Name: {})".format(desiredID, desiredFirstName + "1")
        expectedResult2 = "RA(Id: {}, Name: {})".format(desiredID, desiredFirstName + "2")

        # Create the RA Object being tested
        testRAObject1 = RA(
            desiredFirstName + str(1),
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted
        )
        testRAObject2 = RA(
            desiredFirstName + str(2),
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints
        )

        # -- Act --

        # Call the method being tested
        result1 = testRAObject1.__repr__()
        result2 = testRAObject2.__repr__()

        # -- Assert --

        # Assert that we received the expected results
        self.assertEqual(expectedResult1, result1)
        self.assertEqual(expectedResult2, result2)

    def test_magicMethodIter_iteratesOverConflicts(self):
        # Test to ensure that the __iter__ magic method iterates over the RA
        #  Object's conflicts.

        # -- Arrange --
        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 99
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 12)
        desiredConflicts = [i for i in range(20)]

        # Create the RA Object being tested
        testRAObject = RA(
            desiredFirstName + str(1),
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            desiredConflicts
        )

        # -- Act --
        # -- Assert --

        # Iterate using the __iter__ method
        for pos, conflict in enumerate(testRAObject.__iter__()):
            # Assert that we are seeing the expected value.
            self.assertEqual(testRAObject.conflicts[pos], conflict)

    def test_magicMethodEq_returnsTrueIfAndOnlyIfAllDesiredAttributesMatch(self):
        # Test to ensure that the magic method __eq__ returns True if and
        #  only if all of the following attributes are the same.

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 99
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 12)
        desiredConflicts = [i for i in range(20)]

        # Create the RA Object being tested
        testRAObject1 = RA(
            desiredFirstName + str(1),
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            desiredConflicts
        )
        testRAObject2 = RA(
            desiredFirstName + str(1),
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            desiredConflicts
        )
        testRAObject3 = RA(
            desiredFirstName + str(1),
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            desiredConflicts
        )
        # -- Act --
        # -- Assert --

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
