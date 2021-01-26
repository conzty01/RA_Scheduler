from schedule.scheduler4_0 import schedule
from schedule.ra_sched import Schedule, RA
from unittest.mock import MagicMock, patch
from datetime import date
import unittest
import random


class TestScheduler(unittest.TestCase):
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
        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

    def test_scheduler_whenUnableToGenerateSchedule_returnsEmptyList(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_scheduler_whenAbleToGenerateSchedule_returnsScheduleObject(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_scheduler_returnsExpectedSchedule(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_createDateDict_buildsExpectedDateDictionary(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_createPreviousDuties_returnsLastDateAssignedDictionary(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_createPreviousDuties_returnsNumDoubleDaysDictionary(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass


if __name__ == "__main__":
    unittest.main()
