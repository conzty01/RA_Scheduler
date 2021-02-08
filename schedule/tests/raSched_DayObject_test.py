from schedule.ra_sched import Day, RA
from unittest.mock import patch
from datetime import date
import unittest


class TestDayObject(unittest.TestCase):
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

        # LEGACY TEST DATA - TO BE REMOVED
        s = []
        n = 5
        for i in range(n):
            ra = RA("T", "C", i, 1, date(2017, 1, 1))
            s.append(ra)

        self.day = Day(date(2018, 5, 24), 3, numDutySlots=n+1, ras=s)

    def tearDown(self):
        # Stop all of the patchers
        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

    # --------------------------
    # -- Tests for Day Object --
    # --------------------------
    def test_hasExpectedMethods(self):
        # Test to ensure the Day Object has the following methods:
        #  - addRA
        #  - addRaWithoutPoints
        #  - removeRA
        #  - removeAllRAs
        #  - numberDutySlots
        #  - addDutySlot
        #  - getPoints
        #  - getDate
        #  - getDoW
        #  - getId
        #  - numberOnDuty
        #  - isDoubleDay
        #  - getRAs
        #  - setReview
        #  - review
        #  - combineDay
        #  - iterDutySlots
        
        # -- Arrange --
        # -- Act --
        # -- Assert --

        self.assertTrue(hasattr(Day, "addRA"))
        self.assertTrue(hasattr(Day, "addRaWithoutPoints"))
        self.assertTrue(hasattr(Day, "removeRA"))
        self.assertTrue(hasattr(Day, "removeAllRAs"))
        self.assertTrue(hasattr(Day, "numberDutySlots"))
        self.assertTrue(hasattr(Day, "addDutySlot"))
        self.assertTrue(hasattr(Day, "getPoints"))
        self.assertTrue(hasattr(Day, "getDate"))
        self.assertTrue(hasattr(Day, "getDoW"))
        self.assertTrue(hasattr(Day, "getId"))
        self.assertTrue(hasattr(Day, "numberOnDuty"))
        self.assertTrue(hasattr(Day, "isDoubleDay"))
        self.assertTrue(hasattr(Day, "getRAs"))
        self.assertTrue(hasattr(Day, "setReview"))
        self.assertTrue(hasattr(Day, "getReview"))
        self.assertTrue(hasattr(Day, "combineDay"))
        self.assertTrue(hasattr(Day, "iterDutySlots"))

    def test_DayObject_hasExpectedProperties(self):
        # Test to ensure that the Day object has the following properties:
        # - date
        # - dow
        # - isdd
        # - id
        # - review
        # - flagDutySlot
        # - ras
        # - numDutySlots
        # - pointVal

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = date(2021, 2, 7)
        desiredDOW = 6

        # Create the Day object being tested
        testDayObject = Day(
            desiredDate,
            desiredDOW
        )

        # -- Act --
        # -- Assert --

        # Assert that the above properties exist and are as we expect
        self.assertIsInstance(testDayObject.date, date)
        self.assertIsInstance(testDayObject.dow, int)
        self.assertIsInstance(testDayObject.isdd, bool)
        self.assertIsInstance(testDayObject.id, int)
        self.assertIsInstance(testDayObject.review, bool)
        self.assertIsInstance(testDayObject.flagDutySlot, bool)
        self.assertIsInstance(testDayObject.ras, list)
        self.assertIsInstance(testDayObject.numDutySlots, int)
        self.assertIsInstance(testDayObject.pointVal, int)

    def test_DayObject_hasExpectedDefaultValues(self):
        # Test to ensure that when omitting non-required parameters
        #  when constructing a Day object, the default values are as
        #  we would expect.

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = date(2021, 2, 7)
        desiredDOW = 6
        expectedNumDutySlots = 1
        expectedRAs = []
        expectedPointVal = 1
        expectedDayID = 0
        expectedIsDoubleDay = False
        expectedFlagDutySlot = False
        expectedReview = False

        # -- Act --

        # Create the Day object being tested
        testDayObject = Day(
            desiredDate,
            desiredDOW
        )

        # -- Assert --

        # Assert that the values that weren't provided are set to the
        #  expected default.
        self.assertEqual(expectedIsDoubleDay, testDayObject.isdd)
        self.assertEqual(expectedDayID, testDayObject.id)
        self.assertEqual(expectedReview, testDayObject.review)
        self.assertEqual(expectedFlagDutySlot, testDayObject.flagDutySlot)
        self.assertEqual(expectedNumDutySlots, testDayObject.numDutySlots)
        self.assertEqual(expectedRAs, testDayObject.ras)
        self.assertEqual(expectedPointVal, testDayObject.pointVal)

    def test_whenProvidedRAList_setsNumDutySlotsToLengthOfProvidedList(self):
        # Test to ensure that when a list is provided as the ras parameter,
        #  the Day object sets the number of duty slots to be the length of
        #  the ra list.

        # -- Arrange --

        # The date to be used for this test
        desiredDate = date(2021, 1, 25)

        # Create RA lists for multiple Day Objects
        raList1 = [1]
        raList2 = [1, 2]
        raList3 = [1, 2, 3]
        raList4 = [i for i in range(43)]

        # -- Act --

        # Create the Day objects used for this test
        testDay1 = Day(desiredDate, 0, ras=raList1)
        testDay2 = Day(desiredDate, 0, ras=raList2)
        testDay3 = Day(desiredDate, 0, ras=raList3)
        testDay4 = Day(desiredDate, 0, ras=raList4)

        # -- Assert --

        # Assert that the numDutySlots attribute is updated to be the length
        #  of the provided RA list.
        self.assertEqual(testDay1.numDutySlots, len(raList1))
        self.assertEqual(testDay2.numDutySlots, len(raList2))
        self.assertEqual(testDay3.numDutySlots, len(raList3))
        self.assertEqual(testDay4.numDutySlots, len(raList4))

    def test_DayObject_whenRAListProvided_whenFlagDutySlotIsTrue_setsLastDutyAsFlagged(self):
        # Test to ensure that when an RA list list is provided to a Day object, if the
        #  flagDutySlot parameter is set to True, the constructor sets flag on the last
        #  duty slot.

        # -- Arrange --

        # Create the objects to be used in this test
        iterations = 5 + 1

        # Create a list of RA objects that will be passed in to the Day objects
        desiredRAList = []
        for i in range(1, iterations):
            desiredRAList.append(RA("Test", "User", i, 2019, date(2017, 1, 1)))

        # -- Act --

        # Create Day objects that are passed in lists of RA objects at various lengths
        testDayList = []
        for i in range(1, iterations):
            testDayList.append(Day(date(2021, 2, 2), 1, ras=desiredRAList[:i], flagDutySlot=True))

        # -- Assert --

        # Assert that each of the Day objects have flagged the appropriate duty slot

        # Iterate over all of the Day objects
        for day in testDayList:

            # Iterate over all of the duty slots in the day object
            for i, slot in enumerate(day.ras):

                # If this is the last duty slot of the day
                if i == len(day.ras) - 1:
                    # Then check to make sure the flag is set
                    self.assertTrue(slot.getFlag())

                else:
                    # Otherwise make sure the flag is NOT set
                    self.assertFalse(slot.getFlag())

    def test_withCustomPointVal_usesCustomPointValue(self):
        # Test to ensure that when a customPointVal is provided, the constructor
        #  will use that value regardless of the number of duty slots provided.

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = date(2021, 2, 7)
        desiredDOW = 6
        desiredCustomPointVal = 99

        # -- Act --

        # Create the Day Objects to be tested
        testDay1 = Day(desiredDate, desiredDOW,
                       customPointVal=desiredCustomPointVal,
                       numDutySlots=1)
        testDay2 = Day(desiredDate, desiredDOW,
                       customPointVal=desiredCustomPointVal,
                       numDutySlots=2)

        # -- Assert --

        # Assert that the pointVal is set as we would expect
        self.assertEqual(desiredCustomPointVal, testDay1.pointVal)
        self.assertEqual(desiredCustomPointVal, testDay2.pointVal)

    def test_withoutCustomPointVal_setsPointValueBasedOnNumDutySlots(self):
        # Test to ensure that when a customPointVal is not provided, the constructor
        #  will set a point value based on the number of duty slots provided

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = date(2021, 2, 7)
        desiredDOW = 6

        # -- Act --

        # Create the Day Objects to be tested
        testDay1 = Day(desiredDate, desiredDOW, numDutySlots=0)
        testDay2 = Day(desiredDate, desiredDOW, numDutySlots=1)
        testDay3 = Day(desiredDate, desiredDOW, numDutySlots=2)
        testDay4 = Day(desiredDate, desiredDOW, numDutySlots=3)

        # -- Assert --

        # Assert that the pointVal is set as we would expect
        self.assertEqual(1, testDay1.pointVal)
        self.assertEqual(1, testDay2.pointVal)
        self.assertEqual(2, testDay3.pointVal)
        self.assertEqual(2, testDay4.pointVal)

    def test_magicMethodStr_returnsExpectedStr(self):
        # Test to ensure that the __str__ magic method returns the expected result.

        # -- Arrange --

        # Create the Day Object being tested
        dateObj = date(2021, 2, 7)
        dow = 6
        testDayObject1 = Day(dateObj, dow, dayID=9)
        testDayObject2 = Day(dateObj, dow)

        expectedResult1 = "Day({}.{})".format(dateObj, 9)
        expectedResult2 = "Day({}.{})".format(dateObj, 0)

        # -- Act --

        # Call the method being tested
        result1 = testDayObject1.__str__()
        result2 = testDayObject2.__str__()

        # -- Assert --

        # Assert that the results are as we would expect
        self.assertEqual(expectedResult1, result1)
        self.assertEqual(expectedResult2, result2)

    def test_magicMethodRepr_returnsExpectedStr(self):
        # Test to ensure that the __repr__ magic method returns the expected result.

        # -- Arrange --

        # Create the Day Object being tested
        dateObj = date(2021, 2, 7)
        dow = 6
        testDayObject1 = Day(dateObj, dow, dayID=9)
        testDayObject2 = Day(dateObj, dow)

        expectedResult1 = "Day({}.{})".format(dateObj, 9)
        expectedResult2 = "Day({}.{})".format(dateObj, 0)

        # -- Act --

        # Call the method being tested
        result1 = testDayObject1.__repr__()
        result2 = testDayObject2.__repr__()

        # -- Assert --

        # Assert that the results are as we would expect
        self.assertEqual(expectedResult1, result1)
        self.assertEqual(expectedResult2, result2)

    def test_magicMethodIter_iteratesOverRAsOnDuty(self):
        # Test to ensure that the __iter__ method of the Day Object
        #  iterates over the RAs that are assigned for duty on that
        #  day.

        # -- Arrange --

        # The date to be used for this test
        desiredDate = date(2021, 1, 25)

        # Create the expected RA list
        expectedRAList = []
        for i in range(25):
            expectedRAList.append(
                RA(
                    "{}".format(i),
                    "{}".format(i),
                    i,
                    1,
                    desiredDate
                )
            )

        # Create the Day object used for this test
        testDay = Day(desiredDate, 0, ras=expectedRAList)

        # -- Act/Assert --

        # Iterate over the Day object
        for i, ra in enumerate(testDay):
            # Assert that we received an RA object
            self.assertIsInstance(ra, RA)

            # Assert that the RA object that we received
            #  is the expected RA object
            self.assertEqual(expectedRAList[i], ra)

    def test_magicMethodLt_isTrueIfAndOnlyIfThisDateIsLessThanOtherDate(self):
        # Test to ensure that the __lt__ magic method returns True when this Day
        #  Object's date is less than the other Day Object's date.

        # -- Arrange --

        # Create the objets used in this test.

        # Testing with Date Objects
        desiredDate1 = date(2021, 2, 8)
        desiredDOW1 = 0
        desiredDate2 = date(2021, 2, 14)
        desiredDOW2 = 6

        # Testing with Int Objects
        desiredDate3 = 12
        desiredDOW3 = 0
        desiredDate4 = 30
        desiredDOW4 = 1

        # Create the Day Objects
        testDayObject1 = Day(desiredDate1, desiredDOW1)
        testDayObject2 = Day(desiredDate2, desiredDOW2)

        testDayObject3 = Day(desiredDate3, desiredDOW3)
        testDayObject4 = Day(desiredDate4, desiredDOW4)

        # -- Act --

        # Call the method being tested
        dateResult1 = testDayObject1 < testDayObject2
        dateResult2 = testDayObject2 < testDayObject1

        intResult1 = testDayObject3 < testDayObject4
        intResult2 = testDayObject4 < testDayObject3

        # -- Assert --

        # Assert that the first result of each set is True
        self.assertTrue(dateResult1)
        self.assertTrue(intResult1)

        # Assert that the second result of each set is False
        self.assertFalse(dateResult2)
        self.assertFalse(intResult2)

    def test_magicMethodHash_returnsCombinationOfDateAndIDHashes(self):
        # Test to ensure that the __hash__ magic method returns a hash that is the
        #  combination of the Day Object's date and ID.

        # -- Arrange --

        # Create the objets used in this test.
        desiredDate1 = date(2021, 2, 8)
        desiredDOW1 = 0
        dayID1 = 14
        desiredDate2 = date(2021, 2, 14)
        desiredDOW2 = 6
        dayID2 = 2

        # Create the Day Objects
        testDayObject1 = Day(desiredDate1, desiredDOW1, dayID=dayID1)
        testDayObject2 = Day(desiredDate2, desiredDOW2, dayID=dayID2)
        testDayObject3 = Day(desiredDate1, desiredDOW1, dayID=dayID1)

        # -- Act --

        # Call the method being tested
        result1 = hash(testDayObject1)
        result2 = hash(testDayObject2)
        result3 = hash(testDayObject3)

        # -- Assert --

        # Assert that result1 and result2 are different hashes
        self.assertNotEqual(result1, result2)

        # Assert that result1 and result3 are the same hash despite being different objects
        self.assertEqual(result1, result3)

    def test_magicMethodEq_isTrueIfAndOnlyIfDateIsEqual(self):
        # Test to ensure that the __eq__ magic method returns True if and only
        #  if this Day Object's date is equal to the other Day Object's date.

        # -- Arrange --

        # Create the objets used in this test.

        # Testing with Date Objects
        desiredDate1 = date(2021, 2, 8)
        desiredDOW1 = 0
        desiredDate2 = date(2021, 2, 14)
        desiredDOW2 = 6

        # Testing with Int Objects
        desiredDate3 = 12
        desiredDOW3 = 0
        desiredDate4 = 12
        desiredDOW4 = 0

        # Create the Day Objects
        testDayObject1 = Day(desiredDate1, desiredDOW1)
        testDayObject2 = Day(desiredDate2, desiredDOW2)

        testDayObject3 = Day(desiredDate3, desiredDOW3)
        testDayObject4 = Day(desiredDate4, desiredDOW4)

        # -- Act --

        # Call the method being tested
        dateResult1 = testDayObject1 == testDayObject2
        dateResult2 = testDayObject2 == testDayObject1

        intResult1 = testDayObject3 == testDayObject4
        intResult2 = testDayObject4 == testDayObject3

        # -- Assert --

        # Assert that the if and only if conditional applies
        self.assertFalse(dateResult1)
        self.assertFalse(dateResult2)
        self.assertTrue(intResult2)
        self.assertTrue(intResult1)

    def test_magicMethodContains_isTrueIfAndOnlyIfRAIsAssignedForDuty(self):
        # Test to ensure that the __contains__ method returns True if and only
        #  if the provided RA object hass been assigned for duty on that day.

        # -- Arrange --

        # Create the objects to be used in this test
        assignedRA = RA("Test1", "User1", 1, 2019, date(2017, 1, 1))
        notAssignedRA = RA("Test2", "User2", 2, 2019, date(2017, 1, 1))
        testDayObject = Day(date(2021, 2, 1), 0, ras=[assignedRA])

        # -- Act --

        # Execute the __contains__ method for each scenario
        result1 = assignedRA in testDayObject
        result2 = notAssignedRA in testDayObject

        # -- Assert --

        # Assert that when the RA is assigned for duty, the method returns True
        self.assertTrue(result1)

        # Assert that when the RA is NOT assigned for duty, the method returns False
        self.assertFalse(result2)

    def test_addRA_withDutySlotsLeft_addsRAToDutySlots(self):
        # Test to ensure that when the addRA method is called with an open duty
        #  slot left, the method adds the RA to the Duty Slots.

        # -- Arrange --

        # Create the objects used in this test
        ra1 = RA("R", "E", 99, 1, date(2017, 2, 2))
        ra2 = RA("C", "K", 98, 1, date(2017, 3, 3))
        desiredDate = date(2021, 2, 8)
        desiredDOW = 0

        # Create the Day object to be used in this test
        testDayObject = Day(desiredDate, desiredDOW, numDutySlots=1, flagDutySlot=True)

        # Verify the number on duty
        numOnDuty = testDayObject.numDutySlots

        # -- Act --

        # Add an RA to the duty slot
        testDayObject.addRA(ra1)

        # -- Assert --

        # Assert that we were able to add the RA to the duty slots
        self.assertIn(ra1, testDayObject.getRAs())

        # Assert that we have filled up the duty slots
        self.assertEqual(numOnDuty, len(testDayObject.getRAs()))

    def test_addRA_withDutySlotsLeft_callsRaAddPointsMethod(self):
        # Test to ensure that when the addRA method is called with an open duty
        #  slot left, the method adds the appropriate number of points to the
        #  RA object.

        # -- Arrange --

        # Create the objects used in this test
        ra1 = RA("R", "E", 99, 1, date(2017, 2, 2), points=0)
        desiredDate = date(2021, 2, 8)
        desiredDOW = 0
        desiredDayPoints = 12

        # Create the Day object to be used in this test
        testDayObject = Day(desiredDate, desiredDOW, numDutySlots=1, customPointVal=desiredDayPoints)

        # -- Act --

        # Add an RA to the duty slot
        testDayObject.addRA(ra1)

        # -- Assert --

        # Assert that we were able to add the RA to the duty slots
        self.assertIn(ra1, testDayObject.getRAs())

        # Assert that we have filled up the duty slots
        self.assertEqual(ra1.getPoints(), desiredDayPoints)

    def test_addRA_withNoDutySlotsLeft_throwsOverflowError(self):
        # Test to ensure that when the addRA method is called with no open
        #  duty slots, the method raises an OverflowError.

        # -- Arrange --

        # Create the objects used in this test
        ra1 = RA("R", "E", 99, 1, date(2017, 2, 2))
        ra2 = RA("C", "K", 98, 1, date(2017, 3, 3))
        desiredDate = date(2021, 2, 8)
        desiredDOW = 0

        # Create the Day object to be used in this test
        testDayObject = Day(desiredDate, desiredDOW, numDutySlots=1)

        # -- Act --

        # Add an RA to the duty slot
        testDayObject.addRA(ra1)

        # -- Assert --

        # Assert that attempting to add another RA object results in
        #  an OverflowError being raised.
        self.assertRaises(OverflowError, testDayObject.addRA, ra2)

        # Assert that attempting to add yet another RA object results in
        #  an OverflowError being raised.
        self.assertRaises(OverflowError, testDayObject.addRA, ra2)

    def test_addRAWithoutPoints_withDutySlotsLeft_addsRAToDutySlots(self):
        # Test to ensure that when the addRaWithoutPoints is called with an
        #  open duty slots left, the method adds the provided RA to the
        #  duty slot.

        # -- Arrange --

        # Create the objects used in this test
        ra1 = RA("R", "E", 99, 1, date(2017, 2, 2))
        ra2 = RA("C", "K", 98, 1, date(2017, 3, 3))
        desiredDate = date(2021, 2, 8)
        desiredDOW = 0

        # Create the Day object to be used in this test
        testDayObject = Day(desiredDate, desiredDOW, numDutySlots=1, flagDutySlot=True)

        # Verify the number on duty
        numOnDuty = testDayObject.numDutySlots

        # -- Act --

        # Add an RA to the duty slot
        testDayObject.addRaWithoutPoints(ra1)

        # -- Assert --

        # Assert that we were able to add the RA to the duty slots
        self.assertIn(ra1, testDayObject.getRAs())

        # Assert that we have filled up the duty slots
        self.assertEqual(numOnDuty, len(testDayObject.getRAs()))

    def test_addRAWithoutPoints_withDutySlotsLeft_doesNotCallRAAddPointsMethod(self):
        # Test to ensure that when the addRaWithoutPoints method is called with an open duty
        #  slot left, the method does NOT add any number of points to the RA object.

        # -- Arrange --

        # Create the objects used in this test
        ra1 = RA("R", "E", 99, 1, date(2017, 2, 2), points=0)
        desiredDate = date(2021, 2, 8)
        desiredDOW = 0
        desiredDayPoints = 12

        # Create the Day object to be used in this test
        testDayObject = Day(desiredDate, desiredDOW, numDutySlots=1, customPointVal=desiredDayPoints)

        # -- Act --

        # Add an RA to the duty slot
        testDayObject.addRaWithoutPoints(ra1)

        # -- Assert --

        # Assert that we were able to add the RA to the duty slots
        self.assertIn(ra1, testDayObject.getRAs())

        # Assert that we have filled up the duty slots
        self.assertNotEqual(ra1.getPoints(), desiredDayPoints)

    def test_addRAWithoutPoints_withNoDutySlotsLeft_throwsOverflowError(self):
        # Test to ensure that when the addRaWithoutPoints method is called with no open
        #  duty slots, the method raises an OverflowError.

        # -- Arrange --

        # Create the objects used in this test
        ra1 = RA("R", "E", 99, 1, date(2017, 2, 2))
        ra2 = RA("C", "K", 98, 1, date(2017, 3, 3))
        desiredDate = date(2021, 2, 8)
        desiredDOW = 0

        # Create the Day object to be used in this test
        testDayObject = Day(desiredDate, desiredDOW, numDutySlots=1)

        # -- Act --

        # Add an RA to the duty slot
        testDayObject.addRaWithoutPoints(ra1)

        # -- Assert --

        # Assert that attempting to add another RA object results in
        #  an OverflowError being raised.
        self.assertRaises(OverflowError, testDayObject.addRA, ra2)

        # Assert that attempting to add yet another RA object results in
        #  an OverflowError being raised.
        self.assertRaises(OverflowError, testDayObject.addRA, ra2)

    def test_removeRA_removesAndReturnsRAFromDutySlots(self):
        # Test to ensure that when the removeRA method is called, the method removes
        #  and returns the provided RA from the duty slot.

        # -- Arrange --

        # Create the objects being used in this test
        ra1 = RA("D", "B", 97, 1, date(2017, 4, 4))
        ra2 = RA("T", "C", 40, 1, date(2017, 4, 4))
        testDayObject = Day(date(2021, 2, 8), 0, ras=[ra1, ra2])

        # -- Act --

        # Call the method being tested
        removedRA = testDayObject.removeRA(ra1)

        # -- Assert --

        # Assert that the RA object has been removed
        self.assertNotIn(ra1, testDayObject.getRAs())

        # Assert that the correct RA was returned
        self.assertEqual(ra1, removedRA)

        # Assert that the other RA still remains assigned to the duty slot
        self.assertIn(ra2, testDayObject.getRAs())

    def test_removeRA_whenUnableToFindRA_returnsNoneObject(self):
        # Test to ensure that when the removeRA method is called and the provided RA
        #  has not been assigned to the Day's duty slots, the method returns a None
        #  object.

        # -- Arrange --

        # Create the objects being used in this test
        ra1 = RA("D", "B", 97, 1, date(2017, 4, 4))
        ra2 = RA("T", "C", 40, 1, date(2017, 4, 4))
        ra3 = RA("A", "C", 0, 1, date(2017, 4, 5))
        testDayObject = Day(date(2021, 2, 8), 0, ras=[ra1, ra2])

        # -- Act --

        # Call the method being tested
        removedRA = testDayObject.removeRA(ra3)

        # -- Assert --

        # Assert that the RAs assigned to duty on this day have
        #  not changed from this operation.
        self.assertListEqual([ra1, ra2], testDayObject.getRAs())

        # Assert that the result is None
        self.assertIsNone(removedRA)

    def test_removeRA_callsRARemovePointsMethod(self):
        # Test to ensure that when the removeRA method is called, the method
        #  calls the RA.removePoints() method passing it the pointVal of the
        #  Day Object.

        # -- Arrange --

        # Create the objects being used in this test
        raPoints = 12
        dayPoints = 10
        expectedRemainingRAPoints = raPoints - dayPoints
        ra1 = RA("D", "B", 97, 1, date(2017, 4, 4), points=raPoints)
        ra2 = RA("T", "C", 40, 1, date(2017, 4, 4), points=raPoints)
        testDayObject = Day(date(2021, 2, 8), 0, ras=[ra1, ra2], customPointVal=dayPoints)

        # -- Act --

        # Call the method being tested
        removedRA = testDayObject.removeRA(ra1)

        # -- Assert --

        # Assert that the RA object has been removed
        self.assertNotIn(ra1, testDayObject.getRAs())

        # Assert that the correct RA was returned
        self.assertEqual(ra1, removedRA)

        # Assert that the other RA still remains assigned to the duty slot
        self.assertIn(ra2, testDayObject.getRAs())

        # Assert that the returned RA has fewer points now
        self.assertEqual(ra1.getPoints(), expectedRemainingRAPoints)

    def test_removeAllRAs_removesAndReturnsAllRAsFromDutySlots(self):
        # Test to ensure that when the removeAllRAs method is called, the method removes
        #  and returns all RAs assigned from the duty slot.

        # -- Arrange --

        # Create the objects being used in this test
        ra1 = RA("D", "B", 97, 1, date(2017, 4, 4))
        ra2 = RA("T", "C", 40, 1, date(2017, 4, 4))
        raList = [ra1, ra2]
        testDayObject = Day(date(2021, 2, 8), 0, ras=raList)

        # -- Act --

        # Call the method being tested
        removedRAs = testDayObject.removeAllRAs()

        # -- Assert --

        # Assert that the RAs were removed as expected
        self.assertListEqual(raList, removedRAs)

        # Assert that no RAs remain assigned for duty
        self.assertListEqual([], testDayObject.getRAs())

    def test_removeAllRAs_callsRARemovePointsMethod(self):
        # Test to ensure that when the removeAllRAs method is called, the method
        #  calls the RA.removePoints() method passing it the pointVal of the
        #  Day Object.

        # -- Arrange --

        # Create the objects being used in this test
        raPoints = 12
        dayPoints = 10
        expectedRemainingRAPoints = raPoints - dayPoints
        ra1 = RA("D", "B", 97, 1, date(2017, 4, 4), points=raPoints)
        ra2 = RA("T", "C", 40, 1, date(2017, 4, 4), points=raPoints)
        raList = [ra1, ra2]
        testDayObject = Day(date(2021, 2, 8), 0, ras=raList, customPointVal=dayPoints)

        # -- Act --

        # Call the method being tested
        removedRAs = testDayObject.removeAllRAs()

        # -- Assert --

        # Assert that the RAs were removed as expected
        self.assertListEqual(raList, removedRAs)

        # Assert that no RAs remain assigned for duty
        self.assertListEqual([], testDayObject.getRAs())

        # Assert that each RA's points have been reduced by the expected amount.
        for ra in removedRAs:
            self.assertEqual(expectedRemainingRAPoints, ra.getPoints())

    def test_removeAllRAs_whenNoRAsAssigned_returnsEmptyList(self):
        # Test to ensure that when the removeAllRAs method is called and no RAs
        #  are assigned for duty, the method returns an empty list

        # -- Arrange --

        # Create the objects being used in this test
        testDayObject = Day(date(2021, 2, 8), 0)

        # -- Act --

        # Call the method being tested
        removedRAs = testDayObject.removeAllRAs()

        # -- Assert --

        # Assert that the RAs were removed as expected
        self.assertListEqual([], removedRAs)

    def test_numberDutySlots_returnsNumberDutySlotsAttribute(self):
        # Test to ensure that when the numberDutySlots method is called,
        #  the method returns the number of duty slots the Day Object has.

        # -- Arrange --

        # Create the objects being used in this test
        testDayObject0 = Day(date(2021, 2, 8), 0, numDutySlots=0)
        testDayObject1 = Day(date(2021, 2, 8), 0, numDutySlots=1)
        testDayObject2 = Day(date(2021, 2, 8), 0, numDutySlots=2)
        testDayObject3 = Day(date(2021, 2, 8), 0, numDutySlots=3)

        # -- Act --

        # Call the method being tested
        result0 = testDayObject0.numberDutySlots()
        result1 = testDayObject1.numberDutySlots()
        result2 = testDayObject2.numberDutySlots()
        result3 = testDayObject3.numberDutySlots()

        # -- Assert --

        # Assert that we received the expected value
        self.assertEqual(testDayObject0.numDutySlots, result0)
        self.assertEqual(testDayObject1.numDutySlots, result1)
        self.assertEqual(testDayObject2.numDutySlots, result2)
        self.assertEqual(testDayObject3.numDutySlots, result3)

    def test_addDutySlot_addsProvidedNumberOfDutySlotsToNumDutySlots(self):
        # Test to ensure that when the addDutySlot method is called, the method
        #  increases the number of duty slots by the amount provided.

        # -- Arrange --

        # Create the objects used in this test
        startSlotNum = 0
        incrementAmount = 3
        expectedResultingNumSlots = startSlotNum + incrementAmount
        testDayObject = Day(date(2021, 2, 8), 0, numDutySlots=startSlotNum)

        # -- Act --

        # Call the method being tested
        testDayObject.addDutySlot(incrementAmount)

        # -- Assert --

        # Assert that the Day Object has the expected number of duty slots
        self.assertEqual(expectedResultingNumSlots, testDayObject.numberDutySlots())

    def test_getPoints_returnsPointValAttribute(self):
        # Test to ensure that when the getPoints method is called, the method
        #  returns the pointVal of the Day Object.

        # -- Arrange --

        # Create the objects used in this test.
        testDayObject0 = Day(date(2021, 2, 8), 0, customPointVal=1)
        testDayObject1 = Day(date(2021, 2, 8), 0, customPointVal=2)
        testDayObject2 = Day(date(2021, 2, 8), 0, customPointVal=3)
        testDayObject3 = Day(date(2021, 2, 8), 0, customPointVal=50)

        # -- Act --

        # Call the method being tested
        result0 = testDayObject0.getPoints()
        result1 = testDayObject1.getPoints()
        result2 = testDayObject2.getPoints()
        result3 = testDayObject3.getPoints()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(1, result0)
        self.assertEqual(2, result1)
        self.assertEqual(3, result2)
        self.assertEqual(50, result3)

    def test_getDate_returnsDateAttribute(self):
        # Test to ensure that when the getDate method is called, the method
        #  returns the date of the Day Object.

        # -- Arrange --

        # Create the objects used in this test.
        desiredDate1 = date(2021, 2, 8)
        desiredDate2 = date(2021, 2, 9)
        desiredDate3 = date(2021, 2, 3)
        desiredDate4 = date(1996, 12, 3)

        testDayObject0 = Day(desiredDate1, 0)
        testDayObject1 = Day(desiredDate2, 1)
        testDayObject2 = Day(desiredDate3, 2)
        testDayObject3 = Day(desiredDate4, 1)

        # -- Act --

        # Call the method being tested
        result0 = testDayObject0.getDate()
        result1 = testDayObject1.getDate()
        result2 = testDayObject2.getDate()
        result3 = testDayObject3.getDate()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredDate1, result0)
        self.assertEqual(desiredDate2, result1)
        self.assertEqual(desiredDate3, result2)
        self.assertEqual(desiredDate4, result3)

    def test_getDoW_returnsDOWAttribute(self):
        # Test to ensure that when the getDoW method is called, the method
        #  returns the dow of the Day Object.

        # -- Arrange --

        # Create the objects used in this test.
        desiredDoW1 = 0
        desiredDoW2 = 1
        desiredDoW3 = 2
        desiredDoW4 = 1

        testDayObject0 = Day(date(2021, 2, 8), desiredDoW1)
        testDayObject1 = Day(date(2021, 2, 9), desiredDoW2)
        testDayObject2 = Day(date(2021, 2, 3), desiredDoW3)
        testDayObject3 = Day(date(1996, 12, 3), desiredDoW4)

        # -- Act --

        # Call the method being tested
        result0 = testDayObject0.getDoW()
        result1 = testDayObject1.getDoW()
        result2 = testDayObject2.getDoW()
        result3 = testDayObject3.getDoW()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredDoW1, result0)
        self.assertEqual(desiredDoW2, result1)
        self.assertEqual(desiredDoW3, result2)
        self.assertEqual(desiredDoW4, result3)

    def test_getId_returnsIDAttribute(self):
        # Test to ensure that when the getId method is called, the method
        #  returns the ID of the Day Object.

        # -- Arrange --

        # Create the objects used in this test
        desiredID0 = 0
        desiredID1 = 1
        desiredID2 = 2
        desiredID3 = 3

        testDayObject0 = Day(date(2021, 2, 8), 0)
        testDayObject1 = Day(date(2021, 2, 9), 1, dayID=desiredID1)
        testDayObject2 = Day(date(2021, 2, 3), 2, dayID=desiredID2)
        testDayObject3 = Day(date(1996, 12, 3), 1, dayID=desiredID3)

        # -- Act --

        # Call the method being tested
        result0 = testDayObject0.getId()
        result1 = testDayObject1.getId()
        result2 = testDayObject2.getId()
        result3 = testDayObject3.getId()

        # -- Assert --

        # Assert that we received the expected results
        self.assertEqual(desiredID0, result0)
        self.assertEqual(desiredID1, result1)
        self.assertEqual(desiredID2, result2)
        self.assertEqual(desiredID3, result3)

    def test_numberOnDuty_returnsNumberOfRAsOnDuty(self):
        # Test to ensure that when the numberOnDuty method is called, the method
        #  returns the number of RAs that have already been assigned for duty.

        # -- Arrange --

        # Create the objects being used in this test.
        testDayObject = Day(date(2021, 2, 8), 0, numDutySlots=100)
        ra = RA("D", "B", 97, 1, date(2017, 4, 4))

        # -- Act --
        # -- Assert --

        # Begin going through a loop to test multiple results
        for expectedNumberOnDuty in range(10):

            # Assert that we have the expected number of RAs on Duty
            self.assertEqual(expectedNumberOnDuty, testDayObject.numberOnDuty())

            # Assign another RA for duty
            testDayObject.addRA(ra)

    def test_isDoubleDay_returnsIsDDAttribute(self):
        # Test to ensure that when the isDoubleDay method is called, the method
        #  returns the isdd attribute for the Day Object.

        # -- Arrange --

        # Create the objects being used in this test.
        testDayObject1 = Day(date(2021, 2, 8), 0, isDoubleDay=True)
        testDayObject2 = Day(date(2021, 2, 8), 0, isDoubleDay=False)

        # -- Act --

        # Call the method being tested
        result1 = testDayObject1.isDoubleDay()
        result2 = testDayObject2.isDoubleDay()

        # -- Assert --

        # Assert that we received the expected results
        self.assertTrue(result1)
        self.assertFalse(result2)

    def test_setReview_setsReviewAttribute(self):
        # Test to ensure that when the setReview method is called, the method
        #  sets the Day's review attribute to the provided value.

        # -- Arrange --

        # Create the objects being used in this test.
        testDayObject = Day(date(2021, 2, 8), 0)

        # -- Act --

        # Set the review attribute to True
        testDayObject.setReview()

        # Get the value of review
        review1 = testDayObject.review

        # Set the review attribute to False
        testDayObject.setReview(False)

        # Get the value of review
        review2 = testDayObject.review

        # -- Assert --

        # Assert that we received the expected results
        self.assertTrue(review1)
        self.assertFalse(review2)

    def test_getReview_returnsReviewAttribute(self):
        # Test to ensure that when the getReview method is called, the method
        #  returns the value of the review attribute.

        # -- Arrange --

        # Create the objects being used in this test.
        testDayObject = Day(date(2021, 2, 8), 0)

        # -- Act --

        # Set the review attribute to True
        testDayObject.setReview()

        # Get the value of review
        review1 = testDayObject.getReview()

        # Set the review attribute to False
        testDayObject.setReview(False)

        # Get the value of review
        review2 = testDayObject.getReview()

        # -- Assert --

        # Assert that we received the expected results
        self.assertTrue(review1)
        self.assertFalse(review2)

    def test_getRAs_returnsRAsOnDuty(self):
        # Test to ensure that the getRAs function returns a list of
        #  the RAs that are assigned for duty.

        # -- Arrange --

        # Create the objects that will be used in this test
        testRAObject = RA("Test", "User", 1, 2019, date(2017, 1, 1))
        testDayObject = Day(date(2021, 2, 1), 0, ras=[testRAObject])

        # Create the expected result
        expectedResult = [slot.getAssignment() for slot in testDayObject.ras]

        # -- Act --

        # Call the appropriate method
        result = testDayObject.getRAs()

        # -- Assert --

        # Assert that the RAs were returned
        self.assertEqual(expectedResult, result)

    def test_DayObject_iterDutySlots_iteratesThroughDutySlots(self):
        # Test to ensure that the iterDutySlots method iterates over the Day's duty slots.

        # -- Arrange --

        # Create the objects ot be used in this test

        # Create a list of RA objects that will be passed in to the Day objects
        desiredRAList = []
        for i in range(5):
            desiredRAList.append(RA("Test", "User", i, 2019, date(2017, 1, 1)))

        testDayObject = Day(date(2021, 2, 2), 1, ras=desiredRAList)

        # -- Act --

        # Execute the iterDutySlots method and save the result
        results = []
        for slot in testDayObject.iterDutySlots():
            results.append(slot)

        # -- Assert --

        # Assert that we iterated over the DutySlot objects
        #  At this time, the DutySlot objects do not have the __eq__ method defined,
        #  so we can really only check to make sure we iterated over instances of the
        #  DutySlot class.
        for slotCandidate in results:
            self.assertIsInstance(slotCandidate, Day.DutySlot)

    def test_DayObject_combineDay_ensuresOtherObjectIsDayObject(self):
        # Test to ensure that then the combineDay method is called, the Day object
        #  checks to ensure that the other object it is combining with is a Day object.
        #  If not, a TypeError is thrown.

        # -- Arrange --

        # Create the objects that are to be used in this test
        testDay1 = Day(date(2021, 2, 2), 1, numDutySlots=5)
        testDay2 = Day(date(2021, 2, 2), 1, numDutySlots=1)
        testFalseDay = set()

        # -- Act --
        # -- Assert --

        # Assert that calling combineDay with another Day object does not throw an error
        testDay1.combineDay(testDay2)

        # Assert that calling combineDay with a non-Day object throws a TypeError
        with self.assertRaises(TypeError):
            testDay1.combineDay(testFalseDay)

    def test_DayObject_combineDay_throwsOverflowErrorWhenTooManyDutiesAreAdded(self):
        # Test to ensure that when the combineDay method is called, the Day object
        #  checks to ensure that its duty slot limit has not already been reached.
        #  If the limit could be exceeded by adding another duty slot, then the Day
        #  object should raise an overflow error.

        # -- Arrange --

        # Create the objects used in this test
        desiredRAList = [
            RA("Test", "User", 1, 2019, date(2017, 1, 1)),
            RA("Test", "User", 2, 2019, date(2017, 1, 1))
        ]
        testDay1 = Day(date(2021, 2, 2), 1, numDutySlots=0)
        testDay2 = Day(date(2021, 2, 2), 1, ras=desiredRAList)

        # -- Act --
        # -- Assert --

        # Assert that calling combineDay with another Day object that would exceed
        #  the first day's number of available duty slots throws an OverflowError
        with self.assertRaises(OverflowError):
            testDay1.combineDay(testDay2)

    def test_DayObject_combineDay_appendsOtherDayToOwnDutySlotList(self):
        # Test to ensure that when the combineDay method is called with another
        #  Day object, the other Day object's duty slots are appended to the first
        #  Day object's duty slot list.

        # -- Arrange --

        # Create the objects that are to be used in this test
        desiredRAList = [
            RA("Test", "User", 1, 2019, date(2017, 1, 1)),
            RA("Test", "User", 2, 2019, date(2017, 1, 1)),
            RA("Test", "User", 3, 2019, date(2017, 1, 1))
        ]
        testDay1 = Day(date(2021, 2, 2), 1, numDutySlots=3)
        # Add an RA to the first day
        testDay1.addRA(desiredRAList[-1])
        testDay2 = Day(date(2021, 2, 2), 1, ras=desiredRAList[:-1])

        # -- Act --

        # Execute the combineDay method
        testDay1.combineDay(testDay2)

        # -- Assert --

        # Test to ensure that the duty slots were added as expected
        for ra in testDay1:
            self.assertIn(ra, desiredRAList)

        self.assertEqual(len(desiredRAList), len(testDay1.ras))

    # -------------------------------
    # -- Tests for DutySlot Object --
    # -------------------------------
    def test_DutySlotObject_hasExpectedProperties(self):
        # Test to ensure that the DutySlot Object has the following properties:
        #  - slot  :: RA
        #  - flag  :: boolean

        # -- Arrange --

        # Create the RA object to pass in
        testRA = RA("Test", "User", 1, 2019, date(2017, 1, 1))

        # Create the DutySlot Object
        testDutySlot = Day.DutySlot(testRA)

        # -- Act --
        # -- Assert --

        # Assert that all of the properties are as we would expect
        self.assertIsInstance(testDutySlot.slot, RA)
        self.assertIsInstance(testDutySlot.flagged, bool)

    def test_DutySlotObject_hasExpectedDefaultValues(self):
        # Test to ensure that the DutySlot Object has the expected default values

        # -- Arrange --

        # Create the DutySlot Object
        testDutySlot = Day.DutySlot()

        # -- Act --
        # -- Assert --

        # Assert that all of the default properties are as we expect
        self.assertFalse(testDutySlot.flagged)
        self.assertIsNone(testDutySlot.slot)

    def test_DutySlotObject_hasExpectedMethods(self):
        # Test to make sure the DutySlot Object has the following methods:
        #  - isAssigned
        #  - assignRA
        #  - setFlag
        #  - getFlag
        #  - getAssignment
        #  - removeAssignment

        #  -- ARRANGE --
        #  --   ACT   --
        #  -- ASSERT  --

        self.assertTrue(hasattr(Day.DutySlot, "isAssigned"))
        self.assertTrue(hasattr(Day.DutySlot, "assignRA"))
        self.assertTrue(hasattr(Day.DutySlot, "setFlag"))
        self.assertTrue(hasattr(Day.DutySlot, "getFlag"))
        self.assertTrue(hasattr(Day.DutySlot, "getAssignment"))
        self.assertTrue(hasattr(Day.DutySlot, "removeAssignment"))

    def test_DutySlotObject_isAssigned_returnsTrueIfAndOnlyIfDutyIsAssigned(self):
        # Test to ensure that the isAssigned method returns True if and only if
        #  the duty has been assigned.

        # -- Arrange --

        # Create the DutySlot object
        testDutySlot = Day.DutySlot()

        # Create a test RA Object
        testRAObject = RA("Test", "User", 1, 2019, date(2017, 1, 1))

        # -- Act --

        # Get the result of the method when there is nothing assigned
        notAssignedRes = testDutySlot.isAssigned()

        # Assign an RA to the duty slot and get the method result
        testDutySlot.assignRA(testRAObject)
        assignedRes = testDutySlot.isAssigned()

        # Remove the duty assignment and get the method result
        testDutySlot.slot = None
        removedAssignedRes = testDutySlot.isAssigned()

        # -- Assert --

        # Assert that the isAssigned method returns True if and only if
        #  the duty has been assigned
        self.assertFalse(notAssignedRes)
        self.assertTrue(assignedRes)
        self.assertFalse(removedAssignedRes)

    def test_DutySlotObject_assignRA_setsRAToDutySlot(self):
        # Test to ensure that the assignRA method sets the slot attribute
        #  to object passed in.

        # -- Arrange --

        # Create the objects to be used in this test
        testDutySlot = Day.DutySlot()
        testRAObject = RA("Test", "User", 1, 2019, date(2017, 1, 1))

        # -- Act --

        # Execute the assignRA method
        testDutySlot.assignRA(testRAObject)

        # -- Assert --

        # Assert that the DutySlot's slot attribute has been set as expected
        self.assertEqual(testRAObject, testDutySlot.slot)

    def test_DutySlotObject_setFlag_setsTheFlaggedAttribute(self):
        # Test to ensure that the setFlag method sets the flag attribute
        #  to the provided object.

        # -- Arrange --

        # Create the objects to be used in this test
        testDutySlot1 = Day.DutySlot()
        desiredBoolFlag = True

        # -- Act --

        # Execute the setFlag method
        testDutySlot1.setFlag(desiredBoolFlag)

        # -- Assert --

        # Assert that the flag attribute is set as expected
        self.assertTrue(testDutySlot1.flagged)

    def test_DutySlotObject_getFlag_returnsTheValueOfTheFlaggedAttribute(self):
        # Test to ensure that the getFlag method returns the flagged attribute

        # -- Arrange --

        # Create the objects to be used in this test
        desiredBoolFlag1 = True
        desiredBoolFlag2 = False
        testDutySlot1 = Day.DutySlot(flagged=desiredBoolFlag1)
        testDutySlot2 = Day.DutySlot(flagged=desiredBoolFlag2)

        # -- Act --

        # Execute the getFlag method
        result1 = testDutySlot1.getFlag()
        result2 = testDutySlot2.getFlag()

        # -- Assert --

        # Assert that we received the expected result
        self.assertTrue(result1)
        self.assertFalse(result2)

    def test_DutySlotObject_getAssignment_returnsRAObjectAssignedToDutySlot(self):
        # Test to ensure that the getAssignment method returns the slot attribute

        # -- Arrange --

        # Create the objects to be used in this test
        testRAObject = RA("Test", "User", 1, 2019, date(2017, 1, 1))
        testDutySlot = Day.DutySlot(assignee=testRAObject)

        # -- Act --

        # Execute the getAssignment method
        result = testDutySlot.getAssignment()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(testRAObject, result)

    def test_DutySlotObject_removeAssignment_removesAndReturnsRAObjectAssignedToDuty(self):
        # Test to ensure that the removeAssignment method removes and returns the slot
        #  attribute.

        # -- Arrange --

        # Create the objects to be used in this test
        testRAObject = RA("Test", "User", 1, 2019, date(2017, 1, 1))
        testDutySlot = Day.DutySlot(assignee=testRAObject)

        # -- Act --

        # Execute the removeAssignment method
        result = testDutySlot.removeAssignment()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(testRAObject, result)

        # Assert that the slot attribute is no longer set
        self.assertIsNone(testDutySlot.slot)


if __name__ == "__main__":
    unittest.main()
