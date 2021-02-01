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
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_DayObject_hasExpectedProperties(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_DayObject_hasExpectedDefaultValues(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_whenProvidedRAList_setsNumDutySlotsToLengthOfProvidedList(self):
        # Test to ensure that when a list is provided as the ras parameter,
        #  the Day object sets the number of duty slots to be the length of
        #  the ra list.

        # -- Arrange --

        # The date to be used for this test
        desiredDate = date(2021, 1, 25)

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

    def test_withCustomPointVal_usesCustomPointValue(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_withoutCustomPointVal_setsPointValueBasedOnNumDutySlots(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodStr_returnsExpectedStr(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodRepr_returnsExpectedStr(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

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

    def test_magicMethodLt_isTrueWhenThisDayIsLessThanOtherDay(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodLt_isFalseWhenThisDayIsNotLessThanOtherDay(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodHash_returnsCombinationOfDateAndIDHashes(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodEq_isTrueIfAndOnlyIfDateIsEqual(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodContains_isTrueIfAndOnlyIfRAIsAssignedForDuty(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        self.fail("Incomplete test")

    def test_addRA_withDutySlotsLeft_addsRAToDutySlots(self):
        ra1 = RA("R","E",99,1,date(2017,2,2))
        ra2 = RA("C","K",98,1,date(2017,3,3))
        self.day.addDutySlot()
        preNum = self.day.numberOnDuty()

        self.day.addRA(ra1)
        self.assertEqual(self.day.numberOnDuty(),preNum+1)
        self.assertRaises(OverflowError,self.day.addRA,ra2)

    def test_addRA_withDutySlotsLeft_callsRaAddPointsMethod(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_addRA_withNoDutySlotsLeft_throwsOveflowError(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_addRAWithoutPoints_withDutySlotsLeft_addsRAToDutySlots(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_addRAWithoutPoints_withDutySlotsLeft_doesNotCallRAAddPointsMethod(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_addRAWithoutPoints_withNoDutySlotsLeft_throwsOverflowError(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_removeRA_removesRAFromDutySlots(self):
        ra = RA("D", "B", 97, 1, date(2017, 4, 4))
        self.day.addDutySlot()
        self.day.addRA(ra)
        self.day.removeRA(ra)

        self.assertNotIn(ra, self.day.getRAs())

    def test_removeRA_callsRARemovePointsMethod(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_removeAllRAs_removesAllRAsFromDutySlots(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_numberdutySlots_returnsNumberDutySlotsAttribute(self):
        self.assertEqual(self.day.numberDutySlots(), self.day.numDutySlots)

    def test_addDutySlot_addsProvidedNumberOfDutySlotsToNumDutySlots(self):
        numSlots = self.day.numberDutySlots()
        addNum = 2
        self.day.addDutySlot(addNum)
        self.assertEqual(self.day.numberDutySlots(),numSlots + addNum)

    def test_getPoints_returnsPointValAttribute(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_getDate_returnsDateAttribute(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_getDoW_returnsDOWAttribute(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_getId_returnsIDAttribute(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_numberOnDuty_returnsNumberOfRAsOnDuty(self):
        num = self.day.numberOnDuty()
        self.assertEqual(num, len(self.day.ras))

    def test_isDoubleDay_returnsIsDDAttribute(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_setReview_setsReviewAttributeToTrue(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_review_returnsReviewAttribute(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

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
        # -- Arrange --
        # -- Act --
        # -- Assert --
        self.fail("Incomplete test")

    def test_DutySlotObject_setFlag_setsTheFlaggedAttribute(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        self.fail("Incomplete test")

    def test_DutySlotObject_getFlag_returnsTheValueOfTheFlaggedAttribute(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        self.fail("Incomplete test")

    def test_DutySlotObject_getAssignment_returnsRAObjectAssignedToDutySlot(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        self.fail("Incomplete test")

    def test_DutySlotObject_removeAssignment_removesAndReturnsRAObjectAssignedToDuty(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        self.fail("Incomplete test")

    def test_DayObject_whenRAListProvided_whenFlagDutySlotIsTrue_setsLastDutyAsFlagged(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        self.fail("Incomplete test")

    def test_DayObject_iterDutySlots_iteratesThroughDutySlots(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        self.fail("Incomplete test")

    def test_DayObject_combineDay_ensuresOtherObjectIsDayObject(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        self.fail("Incomplete test")

    def test_DayObject_combineDay_throwsOverflowErrorWhenTooManyDutiesAreAdded(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        self.fail("Incomplete test")

    def test_DayObject_combineDay_appendsOtherDayToOwnDutySlotList(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        self.fail("Incomplete test")


if __name__ == "__main__":
    unittest.main()
