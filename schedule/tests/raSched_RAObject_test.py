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
            desiredFirstName + str(3),
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            desiredConflicts
        )
        # -- Act --
        # -- Assert --

        self.assertEqual(testRAObject1, testRAObject2)
        self.assertNotEqual(testRAObject1, testRAObject3)

    def test_magicMethodHash_returnsHashOfTupleOfAttributes(self):
        # Test to ensure that the __hash__ magic method returns the hash
        #  of the expected tuple of information from the RA Object.

        # -- Arrange --

        # Create the objects used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 99
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 12)
        desiredConflicts = [i for i in range(20)]
        expectedHash = hash(
            (desiredFirstName + " " + desiredLastName, desiredID, desiredHallID, str(desiredDateStarted))
        )

        # Create the RA Object being tested
        testRAObject1 = RA(
            desiredFirstName,
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

        # -- Act --

        # Get the hash value of the RA Object
        result1 = hash(testRAObject1)
        result2 = hash(testRAObject2)

        # -- Assert --

        # Assert that we received the expected results
        self.assertEqual(expectedHash, result1)
        self.assertNotEqual(expectedHash, result2)

    def test_magicMethodLt_ifRAObjectsHaveUnequalPoints_evaluatesAppropriately(self):
        # Test to ensure that that __let__ magic method, when the two RA Objects have
        #  a different number of points, will return True if and only if the first Object
        #  has fewer points than the second Object.

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 99
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 12)
        desiredPoints = 25

        # Create the RA Object being tested
        testRAObject1 = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints
        )
        testRAObject2 = RA(
            desiredFirstName + str(1),
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints
        )

        # -- Act --

        # Call the method being tested
        resultEqual = testRAObject1.getPoints() == testRAObject2.getPoints()

        # Give testRAObject1 more points
        testRAObject1.addPoints(10)

        # Call the method being tested
        resultFalse = testRAObject1 < testRAObject2

        # Give testRAObject2 more points
        testRAObject2.addPoints(100)

        # Call the method being tested
        resultTrue = testRAObject1 < testRAObject2

        # -- Assert --

        # Assert that we received the expected results
        self.assertTrue(resultEqual)
        self.assertFalse(resultFalse)
        self.assertTrue(resultTrue)

    def test_magicMethodLt_ifRAObjectsHaveEqualPoints_evaluatesRandomly(self):
        # Test to ensure that the __lt__ magic method, when the two RA Objects have the
        #  same number of points, the method will randomly assign one over the other.

        # -- Arrange --

        # Seed the random number generator so that we have the same consecutive results
        #  between each test run.
        random.seed(11072020)

        # With this seed, we expect to see the following consecutive results:
        #  True, False, True, False, True, False, True, False, True, True, True

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 99
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 12)
        desiredPoints = 25

        # Create the RA Object being tested
        testRAObject1 = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints
        )
        testRAObject2 = RA(
            desiredFirstName + str(1),
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints
        )

        # -- Act --
        # -- Assert --

        # Assert that we receive the expected results
        self.assertTrue(testRAObject1 < testRAObject2)
        self.assertFalse(testRAObject1 < testRAObject2)
        self.assertTrue(testRAObject1 < testRAObject2)
        self.assertFalse(testRAObject1 < testRAObject2)
        self.assertTrue(testRAObject1 < testRAObject2)
        self.assertFalse(testRAObject1 < testRAObject2)
        self.assertTrue(testRAObject1 < testRAObject2)
        self.assertFalse(testRAObject1 < testRAObject2)
        self.assertTrue(testRAObject1 < testRAObject2)
        self.assertTrue(testRAObject1 < testRAObject2)
        self.assertTrue(testRAObject1 < testRAObject2)

    def test_magicMethodDeepcopy_returnsDeepCopyOfRAObject(self):
        # Test to ensure that the __deepcopy__ magic method returns a
        #  deep copy of the RA Object.

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 99
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 12)
        desiredPoints = 25

        # Create the RA Object being tested
        testRAObject = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints
        )

        # -- Act --

        # Call the method being tested
        resultRAObject = testRAObject.__deepcopy__("")

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(testRAObject.firstName, resultRAObject.firstName)
        self.assertEqual(testRAObject.lastName, resultRAObject.lastName)
        self.assertEqual(testRAObject.id, resultRAObject.id)
        self.assertEqual(testRAObject.hallId, resultRAObject.hallId)
        self.assertEqual(testRAObject.dateStarted, resultRAObject.dateStarted)
        self.assertEqual(testRAObject.conflicts, resultRAObject.conflicts)
        self.assertEqual(testRAObject.points, resultRAObject.points)

    def test_getConflicts_returnsConflictsAttribute(self):
        # Test to ensure that the getConflicts method returns the RA
        #  Object's conflicts.

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 99
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 17)
        desiredPoints = 25
        desiredConflicts = [i for i in range(100)]

        # Create the RA Object being tested
        testRAObject = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints,
            conflicts=desiredConflicts
        )

        # -- Act --

        # Call the method being tested
        result = testRAObject.getConflicts()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredConflicts, result)

    def test_getId_returnsIDAttribute(self):
        # Test to ensure that the getId method returns the RA Object's
        #  ID attribute

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 4
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 17)
        desiredPoints = 25
        desiredConflicts = [i for i in range(100)]

        # Create the RA Object being tested
        testRAObject = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints,
            conflicts=desiredConflicts
        )

        # -- Act --

        # Call the method being tested
        result = testRAObject.getId()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredID, result)

    def test_getStartDate_returnsStartDateAttribute(self):
        # Test to ensure that the getStartDate method returns the
        #  RA Object's start date

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 4
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 17)
        desiredPoints = 25
        desiredConflicts = [i for i in range(100)]

        # Create the RA Object being tested
        testRAObject = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints,
            conflicts=desiredConflicts
        )

        # -- Act --

        # Call the method being tested
        result = testRAObject.getStartDate()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredDateStarted, result)

    def test_getPoints_returnsPointsAttribute(self):
        # Test to ensure that the getPoints method returns the
        #  RA Object's start date

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 4
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 17)
        desiredPoints = 25
        desiredConflicts = [i for i in range(100)]

        # Create the RA Object being tested
        testRAObject = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints,
            conflicts=desiredConflicts
        )

        # -- Act --

        # Call the method being tested
        result = testRAObject.getPoints()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredPoints, result)

    def test_addPoints_addsProvidedNumberOfPointsToPointsAttribute(self):
        # Test to ensure that the addPoints method adds the value
        #  provided to the RA Object's points attribute

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 4
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 17)
        desiredPoints = 25
        desiredConflicts = [i for i in range(100)]

        desiredAdditionalPoints = 1264254

        # Create the RA Object being tested
        testRAObject = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints,
            conflicts=desiredConflicts
        )

        # -- Act --

        # Call the method being tested
        testRAObject.addPoints(desiredAdditionalPoints)

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(testRAObject.getPoints(), desiredPoints + desiredAdditionalPoints)

    def test_removePoints_decreasesPointsAttributeByProvidedAmount(self):
        # Test to ensure that the removePoints method subtracts the value
        #  provided from the RA Object's points attribute

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 4
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 17)
        desiredPoints = 25
        desiredConflicts = [i for i in range(100)]

        desiredPointDifference = 11

        # Create the RA Object being tested
        testRAObject = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints,
            conflicts=desiredConflicts
        )

        # -- Act --

        # Call the method being tested
        testRAObject.removePoints(desiredPointDifference)

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(testRAObject.getPoints(), desiredPoints - desiredPointDifference)

    def test_getName_returnsFullNameAttribute(self):
        # Test to ensure that the getName method returns the
        #  RA Object's Full Name

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 4
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 17)
        desiredPoints = 25
        desiredConflicts = [i for i in range(100)]

        # Create the RA Object being tested
        testRAObject = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints,
            conflicts=desiredConflicts
        )

        # -- Act --

        # Call the method being tested
        result = testRAObject.getName()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredFirstName + " " + desiredLastName, result)

    def test_getHallId_returnsHallIDAttribute(self):
        # Test to ensure that the getHallId method returns the
        #  RA Object's Hall ID

        # -- Arrange --

        # Create the objects to be used in this test
        desiredFirstName = "User"
        desiredLastName = "Test"
        desiredID = 4
        desiredHallID = 12
        desiredDateStarted = date(2021, 2, 17)
        desiredPoints = 25
        desiredConflicts = [i for i in range(100)]

        # Create the RA Object being tested
        testRAObject = RA(
            desiredFirstName,
            desiredLastName,
            desiredID,
            desiredHallID,
            desiredDateStarted,
            points=desiredPoints,
            conflicts=desiredConflicts
        )

        # -- Act --

        # Call the method being tested
        result = testRAObject.getHallId()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredHallID, result)


if __name__ == '__main__':
    unittest.main()
