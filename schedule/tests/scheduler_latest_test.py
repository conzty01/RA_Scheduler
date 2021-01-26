from schedule.scheduler4_0 import schedule
from schedule.ra_sched import Schedule, RA
from unittest.mock import MagicMock, patch
from datetime import date
import unittest
import random

class TestScheduler(unittest.TestCase):
    def setUp(self):
        random.seed(12345)

        self.year = 2020
        self.month = 8
        self.conflictList = [date(self.year, self.month,  1),
                             date(self.year, self.month,  2),
                             date(self.year, self.month,  3),
                             date(self.year, self.month,  4),
                             date(self.year, self.month,  5),
                             date(self.year, self.month, 10),
                             date(self.year, self.month, 11),
                             date(self.year, self.month, 12),
                             date(self.year, self.month, 13),
                             date(self.year, self.month, 14),
                             date(self.year, self.month, 22),
                             date(self.year, self.month, 30)]

        self.raList = [RA("R", "E", 1, 1, date(2017, 8, 22)),
                       RA("J", "L", 1, 2, date(2017, 8, 22)),
                       RA("S", "B", 1, 3, date(2017, 8, 22)),
                       RA("T", "C", 1, 4, date(2017, 8, 22)),
                       RA("C", "K", 1, 5, date(2017, 8, 22))]

        self.noDutyDates = list()
        self.doubleDays = (4,5)
        self.doublePts = 2
        self.doubleNum = 2
        self.doubleDates = set()
        self.doubleDateNum = 2
        self.doubleDatePts = 1

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

    def testScheduler_ReturnsListObjectWhenUnableToGenerateSchedule(self):
        # Arrange

        sched = schedule(self.raList,self.year,self.month,
                         self.noDutyDates,self.doubleDays,
                         self.doublePts,self.doubleNum,
                         self.doubleDates,self.doubleDateNum,
                         self.doubleDatePts)

        # Act
        # Assert

        self.assertIsInstance(sched, list)

    def testScheduler_ReturnsScheduleObject(self):
        # Arrange

        additionalRAs = [RA("A", "K", 1, 6, date(2017, 8, 22)),
                         RA("A", "Z", 1, 7, date(2017, 8, 22)),
                         RA("F", "P", 1, 8, date(2017, 8, 22)),
                         RA("I", "O", 1, 9, date(2017, 8, 22)),
                         RA("Y", "E", 1, 10, date(2017, 8, 22)),
                         RA("W", "A", 1, 11, date(2017, 8, 22)),
                         RA("Z", "A", 1, 12, date(2017, 8, 22)),
                         RA("R", "S", 1, 13, date(2017, 8, 22))]

        # Act

        self.raList += additionalRAs

        sched = schedule(self.raList,self.year,self.month,
                         self.noDutyDates,self.doubleDays,
                         self.doublePts,self.doubleNum,
                         self.doubleDates,self.doubleDateNum,
                         self.doubleDatePts)

        # Assert

        self.assertIsInstance(sched, Schedule)



if __name__ == "__main__":
    unittest.main()
