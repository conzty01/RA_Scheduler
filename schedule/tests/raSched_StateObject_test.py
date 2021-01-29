from schedule.ra_sched import Schedule, RA
from unittest.mock import patch
import unittest


class TestStateObject(unittest.TestCase):
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

    def test_whenPredeterminedIsTrue_setsRaListAsCandList(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_whenPredeterminedIsFalse_andRaListHasNoItems_setsRAListAsCandList(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_whenPredeterminedIsFalse_callsGetSortedWorkableRAsMethod(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_magicMethodDeepcopy_createsDeepcopyOfStateObject(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_deepcopy_calls_deepcopyMagicMethod(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_restoreState_returnsExpectedInformation(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_hasEmptyCandList_returnsTrueIfCandListIsEmpty(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_hasEmptyCandList_returnsFalseIfCandListIsNOTEmpty(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_returnedFromPreviousState_returnsTrueIfRAIsAssignedForDutyOnCurDay(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_returnedFromPreviousState_returnsFalseIfRAIsNOTAssignedForDutyOnCurDay(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_isDoubleDay_callsDayIsDoubleDayMethod(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_getNextCandidate_returnsFirstItemInCandList(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_assignNextRA_returnsAssignedRA(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_assignNextRA_ifDoubleDay_incrementsNumDoubleDaysAsNecessary(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_assignNextRA_assignsNextRAToCurDay(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_getSortedWorkableRAs_discardsCandidate_ifRAHasAConflict(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_getSortedWorkableRAs_discardsCandidate_ifLastDateAssignedIsTooSoon(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_getSortedWorkableRAs_ifDoubleDay_discardsCandidate_ifDoubleDayAssignmentIsTooSoon(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_getSortedWorkableRAs_sortsCandidateListOnGeneratedCandidateScore(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_genCandScore_callsRAGetPointsMethod(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_genCandScore_ifDoubleDay_addsAdditionalWeight(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_genCandScore_ifRAPointsWouldBeAbovePtsAvg_addsAdditionalWeight(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_genCandScore_ifRAPointsWouldNOTBeAbovePtsAvg_subtractsAdditionalWeight(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass

    def test_genCandScore_returnsCalculatedWeight(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        pass
