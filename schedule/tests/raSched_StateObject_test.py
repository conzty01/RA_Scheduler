from schedule.ra_sched import State, Day, RA
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
        # Test to ensure that the State Object has the following methods:
        #  - deepcopy
        #  - copy
        #  - restoreState
        #  - hasEmptyCandList
        #  - hasEmptyConList
        #  - returnedFromPreviousState
        #  - isDoubleDay
        #  - getNextCandidate
        #  - assignNextRA
        #  - getSortedWorkableRAs
        #  - getNextConflictCandidate
        #  - assignNextConflictRA
        #  - assignRA

        # -- Arrange --
        # -- Act --
        # -- Assert --

        self.assertTrue(hasattr(State, "deepcopy"))
        self.assertTrue(hasattr(State, "copy"))
        self.assertTrue(hasattr(State, "restoreState"))
        self.assertTrue(hasattr(State, "hasEmptyCandList"))
        self.assertTrue(hasattr(State, "hasEmptyConList"))
        self.assertTrue(hasattr(State, "returnedFromPreviousState"))
        self.assertTrue(hasattr(State, "isDoubleDay"))
        self.assertTrue(hasattr(State, "getNextCandidate"))
        self.assertTrue(hasattr(State, "assignNextRA"))
        self.assertTrue(hasattr(State, "getSortedWorkableRAs"))
        self.assertTrue(hasattr(State, "getNextConflictCandidate"))
        self.assertTrue(hasattr(State, "assignNextConflictRA"))
        self.assertTrue(hasattr(State, "assignRA"))

    def test_hasExpectedProperties(self):
        # Test to ensure that the State Object has the following properties:
        #  - curDay
        #  - lda
        #  - ndd
        #  - ldaTol
        #  - nddTol
        #  - nfd
        #  - predetermined
        #  - overrideCons
        #  - candList
        #  - conList

        # -- Arrange --

        # Create the objects used in this test
        desiredDay = Day(27, 1)
        desiredRAList = []
        desiredLastDateAssigned = {"LDA": "TEST"}
        desiredNumDoubleDays = {"NDD": "TEST"}
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredNumFlagDuties = {"NFD": "TEST"}
        desiredPredetermined = False
        desiredOverrideConflicts = False

        # Create the State object being tested
        testState = State(
            desiredDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            desiredPredetermined,
            desiredOverrideConflicts
        )

        # -- Act --
        # -- Assert --

        # Assert that the above properties exist and are as we expect
        self.assertIsInstance(testState.curDay, type(desiredDay))
        self.assertIsInstance(testState.lda, type(desiredLastDateAssigned))
        self.assertIsInstance(testState.ndd, type(desiredNumDoubleDays))
        self.assertIsInstance(testState.ldaTol, type(desiredLDATolerance))
        self.assertIsInstance(testState.nddTol, type(desiredNDDTolerance))
        self.assertIsInstance(testState.nfd, type(desiredNumFlagDuties))
        self.assertIsInstance(testState.predetermined, type(desiredPredetermined))
        self.assertIsInstance(testState.overrideCons, type(desiredOverrideConflicts))
        self.assertIsInstance(testState.candList, type(desiredRAList))
        self.assertIsInstance(testState.conList, type(desiredRAList))

    def test_hasExpectedDefaultValues(self):
        # Test to ensure that when omitting non-required parameters
        #  when constructing a State object, the default values are as
        #  we would expect.

        # -- Arrange --

        # Create the objects used in this test
        desiredDay = Day(27, 1)
        desiredRAList = []
        desiredLastDateAssigned = {"LDA": "TEST"}
        desiredNumDoubleDays = {"NDD": "TEST"}
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredNumFlagDuties = {"NFD": "TEST"}

        expectedPredetermined = False
        expectedOverrideConflicts = False

        # -- Act --

        # Create the State object being tested
        testState = State(
            desiredDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties
        )

        # -- Assert --

        # Assert that the values that weren't provided are set to the
        #  expected default.
        self.assertEqual(testState.predetermined, expectedPredetermined)
        self.assertEqual(testState.overrideCons, expectedOverrideConflicts)

    def test_whenPredeterminedIsTrue_setsRaListAsCandList(self):
        # Test to ensure that when the 'predetermined' parameter is set to True,
        #  the provided raList is set to the State Object's candList.

        # -- Arrange --

        # Create the objects used in this test
        desiredDay = Day(27, 1)
        desiredRAList = [9, 8, 7, 6]
        desiredLastDateAssigned = {"LDA": "TEST"}
        desiredNumDoubleDays = {"NDD": "TEST"}
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredNumFlagDuties = {"NFD": "TEST"}
        desiredPredetermined = True

        # -- Act --

        # Create the State object being tested
        testState = State(
            desiredDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # -- Assert --

        # Assert that the provided raList is set to the State Object's candList.
        self.assertListEqual(testState.candList, desiredRAList)

    def test_whenPredeterminedIsFalse_andRaListHasNoItems_setsCandListAndConListToEmptyLists(self):
        # Test to ensure that when the 'predetermined' parameter is set to False and
        #  the provided RA List is empty, then the State Object constructor sets its
        #  candList and conList to empty lists.

        # -- Arrange --

        # Create the objects used in this test
        desiredDay = Day(27, 1)
        desiredRAList = []
        desiredLastDateAssigned = {"LDA": "TEST"}
        desiredNumDoubleDays = {"NDD": "TEST"}
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredNumFlagDuties = {"NFD": "TEST"}
        desiredPredetermined = False

        # -- Act --

        # Create the State object being tested
        testState = State(
            desiredDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # -- Assert --

        # Test to ensure that the State Object is as we expect
        self.assertListEqual(testState.candList, [])
        self.assertListEqual(testState.conList, [])

    def test_whenPredeterminedIsFalse_andRaListHasItems_createsCandAndConListsFromRAList(self):
        # Test to ensure that when the 'predetermined' parameter is set to False, and
        #  the provided RA List is NOT empty, the State Object's constructor creates
        #  a candList and conList from the provided raList.

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = 27
        desiredDay = Day(desiredDate, 1)
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredPredetermined = False
        desiredLastDateAssigned = {}
        desiredNumDoubleDays = {}
        desiredNumFlagDuties = {}
        desiredRAList = [
            # Candidate RAs
            RA("Test", "RA1", 1, 1, "2021-08-27"),
            RA("Test", "RA2", 2, 1, "2021-08-27"),
            # Conflict RAs
            RA("Test", "RA3", 3, 1, "2021-08-27", conflicts=[desiredDate]),
            RA("Test", "RA4", 4, 1, "2021-08-27", conflicts=[desiredDate])
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        # Generate the candList and conList
        expectedCandList = desiredRAList[:2]
        expectedConList = desiredRAList[2:]

        # -- Act --

        # Create the State object being tested
        testState = State(
            desiredDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # -- Assert --

        # Test to ensure that the candList and conList objects were
        #  generated as we expect.
        self.assertListEqual(testState.candList, expectedCandList)
        self.assertListEqual(testState.conList, expectedConList)

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
