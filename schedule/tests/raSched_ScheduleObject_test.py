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

        self.sched = Schedule(
            2018,
            5,
            noDutyDates=[24, 25, 26],
            doubleDays=(4, 5),
            doubleDates=[21, 22, 23]
        )

    def tearDown(self):
        # Stop all of the patchers
        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

    def test_hasExpectedMethods(self):
        # Test to ensure the Schedule Object has the following methods:
        #  - sort
        #  - numDays
        #  - getDate
        #  - addRA
        #  - removeRA
        #  - setReview
        #  - addReviewDay
        #  - shouldReview

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
        self.assertTrue(hasattr(Schedule, "shouldReview"))

    def test_hasExpectedProperties(self):
        # Test to ensure that the Schedule Object has the following properties:
        #  - review
        #  - reviewDays
        #  - noDutyDates
        #  - doubleDays
        #  - doubleDates
        #  - schedule

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

    def test_hasExpectedDefaultValues(self):
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

    def test_withProvidedSchedule_doesNotGenerateNewSchedule(self):
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

    def test_withNoProvidedSchedule_generatesScheduleUsingDoubleDays(self):
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
                expectedSchedule.append(
                    Day(date(desiredYear, desiredMonth, d), dow)
                )
                

        # -- Act --

        # Create the Schedule Object
        testScheduleObject = Schedule(desiredYear, desiredMonth, doubleDays=desiredDoubleDays)

        # -- Assert --

        # Assert that the generated schedule is as we expected
        self.assertListEqual(expectedSchedule, testScheduleObject.schedule)

    def test_withNoProvidedSchedule_generatesScheduleExcludingNoDutyDates(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodRepr_returnsExpectedString(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodIter_iteratesOverSchedule(self):
        for pos, day in enumerate(self.sched):
            self.assertEqual(self.sched.schedule[pos], day)

    def test_magicMethodLen_returnsLengthOfSchedule(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_sort_sortsScheduleInDescendingOrder(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_numDays_returnsNumberOfDaysInSchedule(self):
        self.assertEqual(len(self.sched.schedule),self.sched.numDays())

    def test_getDate_withValidIndex_returnsExpectedDayObject(self):
        self.assertEqual(self.sched.getDate(1), self.sched.schedule[0])
        self.assertEqual(self.sched.getDate(self.sched.numDays()), self.sched.schedule[self.sched.numDays() - 1])
        self.assertRaises(IndexError, self.sched.getDate, 0)
        self.assertRaises(IndexError, self.sched.getDate, 100)

    def test_getDateWithInvalidIndex_throwsIndexError(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_addRA_assignsProvidedRAToDutyOnProvidedDate(self):
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
        self.assertRaises(IndexError, self.sched.addRA, -40, desiredRAObject)
        self.assertRaises(IndexError, self.sched.addRA, 0, desiredRAObject)
        self.assertRaises(IndexError, self.sched.addRA, 100, desiredRAObject)

    def test_removeRA_removesProvidedRAFromProvidedDuty(self):
        ra = RA("R", "K", 5, 1, date(2017, 2, 2))
        d = 1

        preRem = self.sched.getDate(d).getRAs()
        self.sched.addRA(d, ra)
        self.sched.removeRA(d, ra)
        postRem = self.sched.getDate(d).getRAs()

        self.assertEqual(preRem, postRem)

    def test_setReview_setsReviewAttributeToTrue(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_addReviewDay_addsProvidedDayToReviewDaysAttribute(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_getReviewDays_returnsReviewDaysAttribute(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_shouldReview_returnsValueOfReviewAttribute(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass


if __name__ == "__main__":
    unittest.main()
