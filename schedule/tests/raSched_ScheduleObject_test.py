from schedule.ra_sched import Schedule, RA, Day
from unittest.mock import patch
from datetime import date
import unittest
import calendar


class TestScheduleObject(unittest.TestCase):
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

    def tearDown(self):
        # Stop all of the patchers
        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

    def test_ScheduleObject_hasExpectedMethods(self):
        # Test to ensure the Schedule Object has the following methods:
        #  - sort
        #  - numDays
        #  - getDate
        #  - addRA
        #  - removeRA
        #  - setReview
        #  - addReviewDay
        #  - getReivewDay
        #  - shouldReview
        #  - getStatus
        #  - addNote
        #  - getNotes

        # -- Arrange --
        # -- Act --
        # -- Assert --

        self.assertTrue(hasattr(Schedule, "sort"))
        self.assertTrue(hasattr(Schedule, "numDays"))
        self.assertTrue(hasattr(Schedule, "getDate"))
        self.assertTrue(hasattr(Schedule, "addRA"))
        self.assertTrue(hasattr(Schedule, "removeRA"))
        self.assertTrue(hasattr(Schedule, "setReview"))
        self.assertTrue(hasattr(Schedule, "addReviewDay"))
        self.assertTrue(hasattr(Schedule, "getReviewDays"))
        self.assertTrue(hasattr(Schedule, "shouldReview"))
        self.assertTrue(hasattr(Schedule, "getStatus"))
        self.assertTrue(hasattr(Schedule, "addNote"))
        self.assertTrue(hasattr(Schedule, "getNotes"))

    def test_ScheduleObject_hasExpectedProperties(self):
        # Test to ensure that the Schedule Object has the following properties:
        #  - review
        #  - reviewDays
        #  - noDutyDates
        #  - doubleDays
        #  - doubleDates
        #  - schedule
        #  - schedNotes
        #  - status
        #  - ERROR
        #  - FAIL
        #  - WARNING
        #  - DEFAULT
        #  - SUCCESS

        # -- Arrange --

        # Create the objects used in this test
        testSchedule = Schedule(2021, 8)

        # -- Act --
        # -- Assert --

        # Assert that the above properties exist and are as we expect
        self.assertIsInstance(testSchedule.review, bool)
        self.assertIsInstance(testSchedule.reviewDays, set)
        self.assertIsInstance(testSchedule.noDutyDates, list)
        self.assertIsInstance(testSchedule.doubleDays, tuple)
        self.assertIsInstance(testSchedule.doubleDates, list)
        self.assertIsInstance(testSchedule.schedule, list)
        self.assertIsInstance(testSchedule.schedNotes, list)
        self.assertIsInstance(testSchedule.status, int)
        self.assertIsInstance(testSchedule.ERROR, int)
        self.assertIsInstance(testSchedule.FAIL, int)
        self.assertIsInstance(testSchedule.WARNING, int)
        self.assertIsInstance(testSchedule.DEFAULT, int)
        self.assertIsInstance(testSchedule.SUCCESS, int)

    def test_ScheduleObject_hasExpectedDefaultValues(self):
        # Test to ensure that when omitting non-required parameters
        #  when constructing a Schedule object, the default values are
        #  as we would expect. This test will not deal with the schedule
        #  property.

        # -- Arrange --

        # Create the objects used in this test
        expectedReview = False
        expectedReviewDays = set()
        expectedNoDutyDates = []
        expectedDoubleDays = (4, 5)

        # -- Act --

        # Create the Schedule object being tested
        testScheduleObject = Schedule(2021, 8)

        # -- Assert --

        # Assert that the values that weren't provided are set to the
        #  expected default.
        self.assertEqual(expectedReview, testScheduleObject.review)
        self.assertEqual(expectedReviewDays, testScheduleObject.reviewDays)
        self.assertEqual(expectedNoDutyDates, testScheduleObject.noDutyDates)
        self.assertEqual(expectedDoubleDays, testScheduleObject.doubleDays)

    def test_ScheduleObject_withProvidedSchedule_doesNotGenerateNewSchedule(self):
        # Test to ensure that when providing a schedule parameter, the object
        #  does not regenerate a new schedule.

        # -- Arrange --

        # Create a dummy schedule
        desiredSchedule = [i for i in range(10)]

        # -- Act --

        # Create the Schedule object being tested
        testScheduleObject = Schedule(2021, 8, sched=desiredSchedule)

        # -- Assert --

        # Assert that the schedule is set to the one passed to the constructor
        self.assertListEqual(desiredSchedule, testScheduleObject.schedule)

    def test_ScheduleObject_withNoProvidedSchedule_generatesScheduleUsingDoubleDays(self):
        # Test to ensure that when a schedule parameter is not provided, the object
        #  generates its own schedule using the provided doubleDays and doubleDates

        # -- Arrange --

        # Create the objects to be used in this test
        desiredYear = 2021
        desiredMonth = 8
        desiredDoubleDays = (1, 4, 5)
        expectedSchedule = []

        # Generate the expected schedule
        for d, dow in calendar.Calendar().itermonthdays2(desiredYear, desiredMonth):
            if d != 0:
                if dow in desiredDoubleDays:
                    expectedSchedule.append(
                        Day(date(desiredYear, desiredMonth, d), dow, numDutySlots=2)
                    )

                else:
                    expectedSchedule.append(
                        Day(date(desiredYear, desiredMonth, d), dow, numDutySlots=1)
                    )

        # -- Act --

        # Create the Schedule Object
        testScheduleObject = Schedule(desiredYear, desiredMonth, doubleDays=desiredDoubleDays)

        # -- Assert --

        # Assert that the generated schedule is as we expected
        self.assertListEqual(expectedSchedule, testScheduleObject.schedule)

    def test_ScheduleObject_withNoProvidedSchedule_generatesScheduleExcludingNoDutyDates(self):
        # Test to ensure that when a schedule parameter is not provided, the object
        #  generates its own schedule excluding the noDutyDates.

        # -- Arrange --

        # Create the objects being used in this test
        desiredYear = 2021
        desiredMonth = 8
        desiredNoDutyDates = [17, 18, 19, 20]
        expectedSchedule = []

        # Generate the expected schedule
        for d, dow in calendar.Calendar().itermonthdays2(desiredYear, desiredMonth):
            if d != 0:
                if d in desiredNoDutyDates:
                    expectedSchedule.append(
                        Day(date(desiredYear, desiredMonth, d), dow, numDutySlots=0)
                    )

                else:
                    expectedSchedule.append(
                        Day(date(desiredYear, desiredMonth, d), dow)
                    )

        # -- Act --

        # Create the Schedule Object
        testScheduleObject = Schedule(desiredYear, desiredMonth, noDutyDates=desiredNoDutyDates)

        # -- Assert --

        # Assert that the generated schedule is as we expected
        self.assertListEqual(expectedSchedule, testScheduleObject.schedule)

    def test_ScheduleObject_magicMethodIter_iteratesOverSchedule(self):
        # Test to ensure that the __iter__ magic method iterates over the schedule.

        # -- Arrange --

        # Create the objects to be used in this test
        testSchedule = Schedule(2021, 8)

        # -- Act --
        # -- Assert --

        # Iterate over the schedule and ensure that we are receiving the expected
        #  day object
        for pos, day in enumerate(testSchedule):
            self.assertEqual(testSchedule.schedule[pos], day)

    def test_ScheduleObject_magicMethodLen_returnsLengthOfSchedule(self):
        # Test to ensure that the __len__ magic method returns the length
        #  of the Schedule Object's schedule.

        # -- Arrange --

        # Create the objects used in this test
        janSchedule = Schedule(2021, 1)  # 31 days
        febSchedule = Schedule(2021, 2)  # 28 days
        novSchedule = Schedule(2021, 11)  # 30 days

        # -- Act --

        # Call the method being tested
        janResult = janSchedule.numDays()
        febResult = febSchedule.numDays()
        novResult = novSchedule.numDays()

        # -- Assert --

        # Assert that we received the expected results
        self.assertEqual(len(janSchedule), janResult)
        self.assertEqual(len(febSchedule), febResult)
        self.assertEqual(len(novSchedule), novResult)

    def test_ScheduleObject_sort_sortsScheduleInDescendingOrder(self):
        # Test to ensure that the Schedule object's sort method sorts the schedule
        #  so that the days are in reverse order.

        # -- Arrange --

        # Create the objects to be used in this test
        desiredYear = 2021
        desiredMonth = 8
        testSchedule = Schedule(desiredYear, desiredMonth)
        expectedResult = testSchedule.schedule.copy()
        expectedResult.sort(reverse=True)

        # -- Act --

        # Call the method being tested
        testSchedule.sort()

        # -- Assert --

        # Assert that the method acted as expected
        self.assertListEqual(expectedResult, testSchedule.schedule)

    def test_ScheduleObject_numDays_returnsNumberOfDaysInSchedule(self):
        # Test to ensure that the numDays method returns the length of the
        #  Schedule Object's schedule

        # -- Arrange --

        # Create the objects used in this test
        janSchedule = Schedule(2021, 1)     # 31 days
        febSchedule = Schedule(2021, 2)     # 28 days
        novSchedule = Schedule(2021, 11)    # 30 days

        # -- Act --

        # Call the method being tested
        janResult = janSchedule.numDays()
        febResult = febSchedule.numDays()
        novResult = novSchedule.numDays()

        # -- Assert --

        # Assert that we received the expected results
        self.assertEqual(len(janSchedule.schedule), janResult)
        self.assertEqual(len(febSchedule.schedule), febResult)
        self.assertEqual(len(novSchedule.schedule), novResult)

    def test_ScheduleObject_getDate_withValidIndex_returnsExpectedDayObject(self):
        # Test to ensure that when the getDate method is provided an index that
        #  is within bounds of the schedule, the appropriate Day Object is returned.

        # -- Arrange --

        # Create objects that will be used in this test
        testSchedule = Schedule(2021, 2)
        desiredIndex1 = 1
        desiredIndex2 = 15
        desiredIndex3 = 28

        # -- Act --

        # Call the method being tested
        result1 = testSchedule.getDate(desiredIndex1)
        result2 = testSchedule.getDate(desiredIndex2)
        result3 = testSchedule.getDate(desiredIndex3)

        # -- Assert --

        # Assert that we received the expected results
        self.assertEqual(result1, testSchedule.schedule[desiredIndex1 - 1])
        self.assertEqual(result2, testSchedule.schedule[desiredIndex2 - 1])
        self.assertEqual(result3, testSchedule.schedule[desiredIndex3 - 1])

    def test_ScheduleObject_getDateWithInvalidIndex_throwsIndexError(self):
        # Test to ensure that when the getDate method is provided an index that
        #  is out of bounds of the schedule, an IndexError is raised.

        # -- Arrange --

        # Create objects that will be used in this test
        testSchedule = Schedule(2021, 2)
        desiredLowerBound = 0
        desiredUpperBound = 32

        # -- Act --
        # -- Assert --

        # Assert that providing indexes that are out of bounds raises an IndexError
        self.assertRaises(IndexError, testSchedule.getDate, desiredLowerBound)
        self.assertRaises(IndexError, testSchedule.getDate, desiredUpperBound)

    def test_ScheduleObject_addRA_assignsProvidedRAToDutyOnProvidedDate(self):
        # Test to ensure that the addRA function assigns the provided
        #  RA for duty on the provided date.

        # -- Arrange --

        # Create the objects that will be used in this test
        desiredYear = 2021
        desiredMonth = 2
        testScheduleObject = Schedule(desiredYear, desiredMonth)
        desiredRAObject = RA("Test", "User", 1, 2019, date(2017, 1, 1))
        desiredUpperBound = 5

        # -- Act --

        # Run through this process a few times
        for dateIndex in range(1, desiredUpperBound):
            # Execute the addRA function
            testScheduleObject.addRA(dateIndex, desiredRAObject)

        # -- Assert --

        # Assert that the RA was added to the appropriate days
        totalPoints = 0
        for dateIndex in range(1, desiredUpperBound):
            # Load the date from the Schedule Object
            d = testScheduleObject.getDate(dateIndex)

            # Add the points to the total
            totalPoints += d.getPoints()

            # Ensure that the RA was added to the duty
            self.assertIn(desiredRAObject, d.getRAs())

        # Assert that the appropriate number of points have
        #  been added to the RA Object
        self.assertEqual(totalPoints, desiredRAObject.getPoints())

        # Also assert that index errors are raised if inappropriate indexes
        #  are used.
        self.assertRaises(IndexError, testScheduleObject.addRA, -40, desiredRAObject)
        self.assertRaises(IndexError, testScheduleObject.addRA, 0, desiredRAObject)
        self.assertRaises(IndexError, testScheduleObject.addRA, 100, desiredRAObject)

    def test_ScheduleObject_removeRA_removesProvidedRAFromProvidedDuty(self):
        # Test to ensure that the removeRA method removes the provided RA
        #  from the provided duty.

        # -- Arrange --

        # Create the objects used in this test
        testSchedule = Schedule(2021, 8)
        desiredRA = RA("R", "K", 5, 1, date(2017, 2, 2))
        desiredDate = 1

        # Add the RA into the desired duty slot
        testSchedule.addRA(desiredDate, desiredRA)

        # -- Act --

        # Call the method being tested
        testSchedule.removeRA(desiredDate, desiredRA)

        # -- Assert --

        # Assert that the method behaved as expected
        self.assertNotIn(desiredRA, testSchedule.getDate(desiredDate).getRAs())

    def test_ScheduleObject_setReview_setsReviewAttributeToTrue(self):
        # Test to ensure that the setReview method marks the Schedule Object's
        #  review attribute to true.

        # -- Arrange --

        # Create the objects used in this test
        testSchedule = Schedule(2021, 8)
        defaultReviewAttribute = testSchedule.review

        # -- Act --

        # Call the method being tested
        testSchedule.setReview()

        # -- Assert --

        # Assert that the review attribute started as False
        self.assertFalse(defaultReviewAttribute)

        # Assert that the method behaved as expected
        self.assertTrue(testSchedule.review)

    def test_ScheduleObject_addReviewDay_addsProvidedDayToReviewDaysAttribute(self):
        # Test to ensure that the addReviewDay method adds the provided Day object
        #  to the reviewDays collection.

        # -- Arrange --

        # Create the objects used in this test
        testSchedule = Schedule(2021, 8)
        desiredDay = Day(date(2021, 8, 19), 3)
        blankReviewDays = testSchedule.reviewDays.copy()

        # -- Act --

        # Call the method being tested
        testSchedule.addReviewDay(desiredDay)

        # -- Assert --

        # Assert that there was originally nothing in the review days collection
        self.assertEqual(len(blankReviewDays), 0)

        # Assert that the addReviewDay method behaved as expected
        self.assertIn(desiredDay, testSchedule.reviewDays)
        self.assertEqual(len(testSchedule.reviewDays), 1)

    def test_ScheduleObject_getReviewDays_returnsReviewDaysAttribute(self):
        # Test to ensure that the getReviewDays returns the Schedule Object's
        #  reviewDays collection.

        # -- Arrange --

        # Create the objects used in this test
        testSchedule = Schedule(2021, 8)
        desiredDay1 = Day(date(2021, 8, 19), 3)
        desiredDay2 = Day(date(2021, 8, 20), 4)
        blankReviewDays = testSchedule.reviewDays.copy()
        expectedReviewDays = set([desiredDay1, desiredDay2])

        testSchedule.addReviewDay(desiredDay1)
        testSchedule.addReviewDay(desiredDay2)

        # -- Act --

        # Call the method being tested
        result = testSchedule.getReviewDays()

        # -- Assert --

        # Assert that the test started with no entries in the collection
        self.assertEqual(len(blankReviewDays), 0)

        # Assert that we received the expected result
        self.assertSetEqual(result, expectedReviewDays)

    def test_ScheduleObject_shouldReview_returnsValueOfReviewAttribute(self):
        # Test to ensure that the shouldReview method returns the value of the
        #  Schedule Object's review attribute

        # -- Arrange --

        # Create the objects used in this test
        testSchedule = Schedule(2021, 8)
        defaultReviewAttribute = testSchedule.review

        # -- Act --

        # Call the method being tested
        defaultResult = testSchedule.shouldReview()

        # Set the review attribute
        testSchedule.review = True

        # Call the method being tested
        setResult = testSchedule.shouldReview()

        # -- Assert --

        # Assert that the default value is returned
        self.assertEqual(defaultReviewAttribute, defaultResult)

        # Assert that the set value is returned
        self.assertEqual(testSchedule.review, setResult)

    def test_ScheduleObject_getStatus_returnsValueOfStatusAttribute(self):
        # Test to ensure that the getStatus method returns the value of the
        #  Schedule Object's status attribute.

        # -- Arrange --

        # Create the objects used in this test
        desiredStatus1 = Schedule.ERROR
        desiredStatus2 = Schedule.DEFAULT
        desiredStatus3 = Schedule.SUCCESS

        testSchedule1 = Schedule(2021, 8, status=desiredStatus1)
        testSchedule2 = Schedule(2021, 8, status=desiredStatus2)
        testSchedule3 = Schedule(2021, 8, status=desiredStatus3)

        # -- Act --

        # Call the method being tested
        result1 = testSchedule1.getStatus()
        result2 = testSchedule2.getStatus()
        result3 = testSchedule3.getStatus()

        # -- Assert --

        # Assert that we received the expected results
        self.assertEqual(result1, desiredStatus1)
        self.assertEqual(result2, desiredStatus2)
        self.assertEqual(result3, desiredStatus3)

    def test_ScheduleObject_addNote_addsNewNoteObjectToSchedNotes(self):
        # Test to ensure that the addNote method adds a Note Object to the
        #  Schedule Object's schedNotes collection with the provided message
        #  and status.

        # -- Arrange --

        # Create the objects used in this test
        testSchedule = Schedule(2021, 8)
        desiredMsg = "Test Message\n"
        desiredStatus = Schedule.SUCCESS
        expectedSchedNotes = [Schedule.Note(desiredMsg, Schedule.DEFAULT), Schedule.Note(desiredMsg, desiredStatus)]

        # -- Act --

        # Call the method being tested with no provided status
        testSchedule.addNote(desiredMsg)

        # Call the method being tested with a provided status
        testSchedule.addNote(desiredMsg, desiredStatus)

        # -- Assert --

        # Assert that the method added the notes to the
        self.assertListEqual(testSchedule.schedNotes, expectedSchedNotes)

        # Assert that the first Note has a status of DEFAULT
        self.assertEqual(testSchedule.schedNotes[0].status, Schedule.DEFAULT)

        # Assert that the second Note has the provided status
        self.assertEqual(testSchedule.schedNotes[1].status, desiredStatus)

    def test_ScheduleObject_getNotes_returnsSchedNotesCollection(self):
        # Test to ensure that the getNotes method returns the Schedule Object's
        #  schedNotes collection.

        # Create the objects used in this test
        testSchedule = Schedule(2021, 8)
        desiredMsg = "Test Message"
        desiredStatus = Schedule.SUCCESS

        testSchedule.addNote(desiredMsg, desiredStatus)

        # -- Act --

        # Call the method being tested
        result = testSchedule.getNotes()

        # -- Assert --

        # Assert that the method added the notes to the
        self.assertListEqual(testSchedule.schedNotes, result)

    # ---------------------------
    # -- Tests for Note Object --
    # ---------------------------
    def test_NoteObject_hasExpectedMethods(self):
        # Test to ensure the Note Object has the following methods:
        #  - __repr__
        #  - __str__

        # -- Arrange --
        # -- Act --
        # -- Assert --

        self.assertTrue(hasattr(Schedule.Note, "__repr__"))
        self.assertTrue(hasattr(Schedule.Note, "__str__"))

    def test_NoteObject_hasExpectedProperties(self):
        # Test to ensure that the Note Object has the following properties:
        #  - msg
        #  - status

        # -- Arrange --

        # Create the objects used in this test
        testNote = Schedule.Note("Test", 1)

        # -- Act --
        # -- Assert --

        # Assert that the above properties exist and are as we expect
        self.assertIsInstance(testNote.msg, str)
        self.assertIsInstance(testNote.status, int)

    def test_NoteObject_magicMethodEQ_returnsTrueIfAndOnlyIfMsgAndStatusAttrsAreEqual(self):
        # Test to ensure that the Note Object's __eq__ magic method returns True if and only if
        #  the other Note object's msg and status attributes are the same.

        # -- Arrange --

        # Create the objects used in this test
        testMsg1 = "Test Message 1"
        testMsg2 = "Another Test Message"
        testStatus1 = Schedule.DEFAULT
        testStatus2 = Schedule.ERROR

        # -- Act --
        # -- Assert --

        # Assert that the method behaves as we expect
        self.assertTrue(
            Schedule.Note(testMsg1, testStatus1) ==
            Schedule.Note(testMsg1, testStatus1)
        )
        self.assertFalse(
            Schedule.Note(testMsg1, testStatus1) ==
            Schedule.Note(testMsg1, testStatus2)
        )
        self.assertFalse(
            Schedule.Note(testMsg1, testStatus1) ==
            Schedule.Note(testMsg2, testStatus1)
        )
        self.assertFalse(
            Schedule.Note(testMsg1, testStatus1) ==
            Schedule.Note(testMsg2, testStatus2)
        )

    def test_NoteObject_addsNewLineMessageWhenNotPresent(self):
        # Test to ensure that the Note Object adds the "\n" character is added to the end
        #  of the provided message if it is not already present at the end of the message.

        # -- Arrange --

        # Create the objects used in this test
        desiredMsg = "Test"
        expectedMsg = desiredMsg + "\n"

        # -- Act --

        # Create a Note Object with the desired message (without newline)
        testNote_noNewline = Schedule.Note(desiredMsg, 1)

        # Create a Note Object with the desired message (with newline)
        testNote_withNewline = Schedule.Note(expectedMsg, 1)

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(expectedMsg, testNote_noNewline.msg)
        self.assertEqual(expectedMsg, testNote_withNewline.msg)


if __name__ == "__main__":
    unittest.main()
