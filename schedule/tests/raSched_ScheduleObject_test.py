from schedule.ra_sched import Schedule, RA
from unittest.mock import patch
from datetime import date
import unittest


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

    def test_withNoProvidedSchedule_generatesScheduleUsingDoubleDaysAndDates(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

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
        ra = RA("T", "C", 1234, 4321, date(2017, 1, 1))
        d = 1
        preAdd = self.sched.getDate(d).getRAs()
        self.sched.addRA(d, ra)
        postAdd = self.sched.getDate(d).getRAs()

        self.assertEqual(preAdd, postAdd)
        self.assertRaises(IndexError, self.sched.addRA, 0, ra)
        self.assertRaises(IndexError, self.sched.addRA, 100, ra)

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
