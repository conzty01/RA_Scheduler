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
        # Test to ensure that the __deepcopy__ magic method returns
        #  a pseudo deep copy of the State object.

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
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

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

        # -- Act --

        # Call the method being tested
        result = testState.__deepcopy__()

        # -- Assert --

        # Assert that we received a deep copy of the testState
        self.assertEqual(testState, result)
        # curDay
        self.assertEqual(testState.curDay, result.curDay)
        # candList
        self.assertListEqual(testState.candList, result.candList)
        self.assertIsNot(testState.candList, result.candList)
        # lda
        self.assertDictEqual(testState.lda, result.lda)
        self.assertIsNot(testState.lda, result.lda)
        # ndd
        self.assertDictEqual(testState.ndd, result.ndd)
        self.assertIsNot(testState.ndd, result.ndd)
        # ldaTol
        self.assertEqual(testState.ldaTol, result.ldaTol)
        # nddTol
        self.assertEqual(testState.nddTol, result.nddTol)
        # nfd
        self.assertDictEqual(testState.nfd, result.nfd)
        self.assertIsNot(testState.nfd, result.nfd)
        # predetermined
        self.assertEqual(testState.predetermined, result.predetermined)
        # overrideCons
        self.assertEqual(testState.overrideCons, result.overrideCons)

    def test_deepcopy_createsDeepcopyOfStateObject(self):
        # Test to ensure that the deepcopy method returns
        #  a pseudo deep copy of the State object.

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
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

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

        # -- Act --

        # Call the method being tested
        result = testState.deepcopy()

        # -- Assert --

        # Assert that we received a deep copy of the testState
        self.assertEqual(testState, result)
        # curDay
        self.assertEqual(testState.curDay, result.curDay)
        # candList
        self.assertListEqual(testState.candList, result.candList)
        self.assertIsNot(testState.candList, result.candList)
        # lda
        self.assertDictEqual(testState.lda, result.lda)
        self.assertIsNot(testState.lda, result.lda)
        # ndd
        self.assertDictEqual(testState.ndd, result.ndd)
        self.assertIsNot(testState.ndd, result.ndd)
        # ldaTol
        self.assertEqual(testState.ldaTol, result.ldaTol)
        # nddTol
        self.assertEqual(testState.nddTol, result.nddTol)
        # nfd
        self.assertDictEqual(testState.nfd, result.nfd)
        self.assertIsNot(testState.nfd, result.nfd)
        # predetermined
        self.assertEqual(testState.predetermined, result.predetermined)
        # overrideCons
        self.assertEqual(testState.overrideCons, result.overrideCons)

    def test_magicMethodCopy_createsShallowCopyOfStateObject(self):
        # Test to ensure that the __copy__ magic method returns
        #  a shallow copy of the State object.

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
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

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

        # -- Act --

        # Call the method being tested
        result = testState.__copy__()

        # -- Assert --

        # Assert that we received a deep copy of the testState
        self.assertEqual(testState, result)
        # curDay
        self.assertEqual(testState.curDay, result.curDay)
        self.assertIs(testState.curDay, result.curDay)
        # candList
        self.assertListEqual(testState.candList, result.candList)
        # lda
        self.assertDictEqual(testState.lda, result.lda)
        self.assertIs(testState.lda, result.lda)
        # ndd
        self.assertDictEqual(testState.ndd, result.ndd)
        self.assertIs(testState.ndd, result.ndd)
        # ldaTol
        self.assertEqual(testState.ldaTol, result.ldaTol)
        self.assertIs(testState.ldaTol, result.ldaTol)
        # nddTol
        self.assertEqual(testState.nddTol, result.nddTol)
        self.assertIs(testState.ldaTol, result.ldaTol)
        # nfd
        self.assertDictEqual(testState.nfd, result.nfd)
        self.assertIs(testState.nfd, result.nfd)
        # predetermined
        self.assertEqual(testState.predetermined, result.predetermined)
        self.assertIs(testState.predetermined, result.predetermined)
        # overrideCons
        self.assertEqual(testState.overrideCons, result.overrideCons)
        self.assertIs(testState.overrideCons, result.overrideCons)

    def test_copy_createsShallowCopyOfStateObject(self):
        # Test to ensure that the copy method returns
        #  a shallow deep copy of the State object.

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
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

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

        # -- Act --

        # Call the method being tested
        result = testState.copy()

        # -- Assert --

        # Assert that we received a deep copy of the testState
        self.assertEqual(testState, result)
        # curDay
        self.assertEqual(testState.curDay, result.curDay)
        self.assertIs(testState.curDay, result.curDay)
        # candList
        self.assertListEqual(testState.candList, result.candList)
        # lda
        self.assertDictEqual(testState.lda, result.lda)
        self.assertIs(testState.lda, result.lda)
        # ndd
        self.assertDictEqual(testState.ndd, result.ndd)
        self.assertIs(testState.ndd, result.ndd)
        # ldaTol
        self.assertEqual(testState.ldaTol, result.ldaTol)
        self.assertIs(testState.ldaTol, result.ldaTol)
        # nddTol
        self.assertEqual(testState.nddTol, result.nddTol)
        self.assertIs(testState.ldaTol, result.ldaTol)
        # nfd
        self.assertDictEqual(testState.nfd, result.nfd)
        self.assertIs(testState.nfd, result.nfd)
        # predetermined
        self.assertEqual(testState.predetermined, result.predetermined)
        self.assertIs(testState.predetermined, result.predetermined)
        # overrideCons
        self.assertEqual(testState.overrideCons, result.overrideCons)
        self.assertIs(testState.overrideCons, result.overrideCons)

    def test_magicMethodEq_raisesTypeErrorIfOtherObjectIsNotStateObject(self):
        # Test to ensure that when the __eq__ method is called with an object
        #  that is not of Type State, the method raises a TypeError.

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
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

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

        # -- Act --
        # -- Assert --

        # Assert that we see the expected behavior.
        self.assertRaises(TypeError, testState.__eq__, 1)                   # Integer
        self.assertRaises(TypeError, testState.__eq__, "Test")              # String
        self.assertRaises(TypeError, testState.__eq__, 1.0)                 # Floating Point
        self.assertRaises(TypeError, testState.__eq__, True)                # Boolean
        self.assertRaises(TypeError, testState.__eq__, desiredRAList[0])    # RA Object
        self.assertRaises(TypeError, testState.__eq__, desiredDay)          # Day Object

    def test_magicMethodEq_returnsTrueIfAndOnlyIfAllAttributesAreEqual(self):
        # Test to ensure that the __eq__ magic method returns True if and
        #  only if all attributes of the two State objects are equal.

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = 27
        desiredDay = Day(desiredDate, 1)
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredPredetermined = False
        desiredOverrideCons = False
        desiredLastDateAssigned = {}
        desiredNumDoubleDays = {}
        desiredNumFlagDuties = {}
        desiredRAList = []

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        diffDate = 26
        diffDay = Day(diffDate, 2)
        diffLDATolerance = 11
        diffNDDTolerance = .14
        diffPredetermined = True
        diffOverrideCons = True
        diffLastDateAssigned = {}
        diffNumDoubleDays = {}
        diffNumFlagDuties = {}
        diffRAList = [
            # Candidate RAs
            RA("Test", "RA1.2", 1, 1, "2021-08-27"),
            RA("Test", "RA2.2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in diffRAList:
            diffLastDateAssigned[ra] = 0
            diffNumDoubleDays[ra] = 0
            diffNumFlagDuties[ra] = 0

        # Create the State objects being tested
        origState = State(
            desiredDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined,
            overrideConflicts=desiredOverrideCons
        )

        diffDayState = State(
            diffDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined,
            overrideConflicts=desiredOverrideCons
        )

        diffRAListState = State(
            desiredDay,
            diffRAList,
            diffLastDateAssigned,
            diffNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            diffNumFlagDuties,
            predetermined=desiredPredetermined,
            overrideConflicts=desiredOverrideCons
        )

        diffLDATolState = State(
            desiredDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            diffLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined,
            overrideConflicts=desiredOverrideCons
        )

        diffNDDTolState = State(
            desiredDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            diffNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined,
            overrideConflicts=desiredOverrideCons
        )

        diffPredeterminedState = State(
            desiredDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=diffPredetermined,
            overrideConflicts=desiredOverrideCons
        )

        diffOverrideConflictsState = State(
            desiredDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined,
            overrideConflicts=diffOverrideCons
        )

        diffState = State(
            diffDay,
            diffRAList,
            diffLastDateAssigned,
            diffNumDoubleDays,
            diffLDATolerance,
            diffNDDTolerance,
            diffNumFlagDuties,
            predetermined=diffPredetermined,
            overrideConflicts=diffOverrideCons
        )

        # -- Act --

        # Call the method being tested in a variety of different scenarios.
        origOrigComparison = origState == origState
        origDiffDayComparison = origState == diffDayState
        origDiffRAListStateComparison = origState == diffRAListState
        origDiffLDATolStateComparison = origState == diffLDATolState
        origDiffNDDTolStateComparison = origState == diffNDDTolState
        origDiffPredeterminedComparision = origState == diffPredeterminedState
        origDiffOverrideConsComparison = origState == diffOverrideConflictsState
        diffDiffComparison = diffState == diffState

        # -- Assert --

        # Assert that we received the expected results

        # Expected True
        self.assertTrue(origOrigComparison)
        self.assertTrue(diffDiffComparison)

        # Expected False
        self.assertFalse(origDiffDayComparison)
        self.assertFalse(origDiffRAListStateComparison)
        self.assertFalse(origDiffLDATolStateComparison)
        self.assertFalse(origDiffNDDTolStateComparison)
        self.assertFalse(origDiffPredeterminedComparision)
        self.assertFalse(origDiffOverrideConsComparison)

    def test_magicMethodLt_raisesTypeErrorIfOtherObjectIsNotStateObject(self):
        # Test to ensure that when the __lt__ method is called with an object
        #  that is not of Type State, the method raises a TypeError.

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
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

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

        # -- Act --
        # -- Assert --

        # Assert that we see the expected behavior.
        self.assertRaises(TypeError, testState.__lt__, 1)                   # Integer
        self.assertRaises(TypeError, testState.__lt__, "Test")              # String
        self.assertRaises(TypeError, testState.__lt__, 1.0)                 # Floating Point
        self.assertRaises(TypeError, testState.__lt__, True)                # Boolean
        self.assertRaises(TypeError, testState.__lt__, desiredRAList[0])    # RA Object
        self.assertRaises(TypeError, testState.__lt__, desiredDay)          # Day Object

    def test_magicMethodLt_returnsTrueIfOtherObjectIsNone(self):
        # Test to ensure that when the __lt__ magic method is pass
        #  a None object, the method returns True.

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
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

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

        # -- Act --

        res = testState < None

        # -- Assert --

        # Assert that we received the expected result
        self.assertTrue(res)

    def test_magicMethodLt_returnsTrueIfAndOnlyIfTheCurDaysIdIsLessThanTheOtherStatesCurDay(self):
        # Test to ensure that the __gt__ magic method returns True if and only if the State
        #  object's curDay.id is less than the other State object's curDay.id.

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = 27
        desiredDay1 = Day(desiredDate, 1, dayID=1)
        desiredDay2 = Day(desiredDate, 1, dayID=2)
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredPredetermined = False
        desiredLastDateAssigned = {}
        desiredNumDoubleDays = {}
        desiredNumFlagDuties = {}
        desiredRAList = [
            # Candidate RAs
            RA("Test", "RA1", 1, 1, "2021-08-27"),
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        # Create the State object being tested
        testState1 = State(
            desiredDay1,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        testState2 = State(
            desiredDay2,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # -- Act --

        # Call the method being tested in a variety of scenarios
        res1_lt_2 = testState1 < testState2
        res2_lt_1 = testState2 < testState1
        res1_lt_1 = testState1 < testState1
        res2_lt_2 = testState2 < testState2

        # -- Assert --

        # Assert that we received the expected results
        self.assertTrue(res1_lt_2)
        self.assertFalse(res2_lt_1)
        self.assertFalse(res1_lt_1)
        self.assertFalse(res2_lt_2)

    def test_magicMethodGt_raisesTypeErrorIfOtherObjectIsNotStateObject(self):
        # Test to ensure that when the __gt__ method is called with an object
        #  that is not of Type State, the method raises a TypeError.

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
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

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

        # -- Act --
        # -- Assert --

        # Assert that we see the expected behavior.
        self.assertRaises(TypeError, testState.__gt__, 1)  # Integer
        self.assertRaises(TypeError, testState.__gt__, "Test")  # String
        self.assertRaises(TypeError, testState.__gt__, 1.0)  # Floating Point
        self.assertRaises(TypeError, testState.__gt__, True)  # Boolean
        self.assertRaises(TypeError, testState.__gt__, desiredRAList[0])  # RA Object
        self.assertRaises(TypeError, testState.__gt__, desiredDay)  # Day Object

    def test_magicMethodGt_returnsTrueIfOtherObjectIsNone(self):
        # Test to ensure that when the __gt__ magic method is pass
        #  a None object, the method returns True.

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
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

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

        # -- Act --

        res = testState > None

        # -- Assert --

        # Assert that we received the expected result
        self.assertTrue(res)

    def test_magicMethodGt_returnsTrueIfAndOnlyIfTheCurDaysIdIsLessThanTheOtherStatesCurDay(self):
        # Test to ensure that the __gt__ magic method returns True if and only if the State
        #  object's curDay.id is less than the other State object's curDay.id.

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = 27
        desiredDay1 = Day(desiredDate, 1, dayID=10)
        desiredDay2 = Day(desiredDate, 1, dayID=2)
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredPredetermined = False
        desiredLastDateAssigned = {}
        desiredNumDoubleDays = {}
        desiredNumFlagDuties = {}
        desiredRAList = [
            # Candidate RAs
            RA("Test", "RA1", 1, 1, "2021-08-27"),
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        # Create the State object being tested
        testState1 = State(
            desiredDay1,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        testState2 = State(
            desiredDay2,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # -- Act --

        # Call the method being tested in a variety of scenarios
        res1_gt_2 = testState1 > testState2
        res2_gt_1 = testState2 > testState1
        res1_gt_1 = testState1 > testState1
        res2_gt_2 = testState2 > testState2

        # -- Assert --

        # Assert that we received the expected results
        self.assertTrue(res1_gt_2)
        self.assertFalse(res2_gt_1)
        self.assertFalse(res1_gt_1)
        self.assertFalse(res2_gt_2)

    def test_restoreState_returnsExpectedInformation(self):
        # Test to ensure that the restoreState method returns
        #  the expected attributes of the State Object

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
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

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

        # -- Act --

        # Call the method being tested
        resCurDay, resCandList, resLDA, resNDD, resNFD = testState.restoreState()

        # -- Assert --

        # Assert that we received the expected values
        self.assertEqual(testState.curDay, resCurDay)
        self.assertEqual(testState.candList, resCandList)
        self.assertEqual(testState.lda, resLDA)
        self.assertEqual(testState.ndd, resNDD)
        self.assertEqual(testState.nfd, resNFD)

    def test_hasEmptyCandList_returnsTrueIfAndOnlyIfCandListIsEmpty(self):
        # Test to ensure that the hasEmptyCandList returns True if and only
        #  if the State Object's candList is empty

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
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        # Create the State object being tested
        populatedState = State(
            desiredDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        emptyState = State(
            desiredDay,
            [],
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # -- Act --

        # Call the method being tested in several permutations
        populatedResult = populatedState.hasEmptyCandList()
        emptyResult = emptyState.hasEmptyCandList()

        # -- Assert --

        # Assert that we received the desired result
        self.assertFalse(populatedResult)
        self.assertTrue(emptyResult)

    def test_hasEmptyConList_returnsTrueIfAndOnlyIfCandListIsEmpty(self):
        # Test to ensure that the hasEmptyConList returns True if and only
        #  if the State Object's conList is empty

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
        raList = [
            # Candidate RAs
            RA("Test", "RA1", 1, 1, "2021-08-27"),
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]
        conRAList = [
            # Candidate RAs
            RA("Test", "RA1", 1, 1, "2021-08-27", conflicts=[desiredDay.getDate()]),
            RA("Test", "RA2", 2, 1, "2021-08-27", conflicts=[desiredDay.getDate()])
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in raList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        # Create the State object being tested
        conState = State(
            desiredDay,
            conRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        noConState = State(
            desiredDay,
            raList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        emptyState = State(
            desiredDay,
            [],
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # -- Act --

        # Call the method being tested in several permutations
        conResult = conState.hasEmptyConList()
        noConResult = noConState.hasEmptyConList()
        emptyResult = emptyState.hasEmptyCandList()

        # -- Assert --

        # Assert that we received the desired result
        self.assertFalse(conResult)
        self.assertTrue(noConResult)
        self.assertTrue(emptyResult)

    def test_returnedFromPreviousState_returnsTrueIfRAIsAssignedForDutyOnCurDay(self):
        # Test to ensure that the returnedFromPreviousState method returns True if
        #  and only if at least one RA has been assigned for duty on the curDay.

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = 27
        unassignedDay = Day(desiredDate, 1)
        assignedDay = Day(desiredDate, 1, numDutySlots=2)
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredPredetermined = False
        desiredLastDateAssigned = {}
        desiredNumDoubleDays = {}
        desiredNumFlagDuties = {}
        desiredRAList = [
            # Candidate RAs
            RA("Test", "RA1", 1, 1, "2021-08-27"),
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Assign an RA to the assigned Day
        assignedDay.addRA(desiredRAList[0])
        assignedDay.addRA(desiredRAList[1])

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        # Create the State object being tested
        unassignedState = State(
            unassignedDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        assignedState = State(
            assignedDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # -- Act --

        # Test the method with a State object that has never been assigned an RA
        unassignedRes = unassignedState.returnedFromPreviousState()

        # Test the method with a State object that has been assigned an RA
        multipleAssignedRes = assignedState.returnedFromPreviousState()

        # Remove an RA assigned for duty
        assignedState.curDay.removeRA(desiredRAList[0])

        # Test the method with a State object that has been assigned an RA
        singleAssignedRes = assignedState.returnedFromPreviousState()

        # Remove all RAs assigned for duty
        assignedState.curDay.removeAllRAs()

        # Test the method with a State object that has had their RA removed from duty
        removedRes = assignedState.returnedFromPreviousState()

        # -- Assert --

        # Assert that we received the expected results
        self.assertFalse(unassignedRes)
        self.assertTrue(multipleAssignedRes)
        self.assertTrue(singleAssignedRes)
        self.assertFalse(removedRes)

    def test_isDoubleDay_returnsTrueIfAndOnlyIfCurDayIsDoubleDay(self):
        # Test to ensure that the isDoubleDay method returns True
        #  if and only if the State object's curDay is a double day.

        # -- Arrange --

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = 27
        singleDutyDay = Day(desiredDate, 1)
        doubleDutyDay = Day(desiredDate, 1, isDoubleDay=True)
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredPredetermined = False
        desiredLastDateAssigned = {}
        desiredNumDoubleDays = {}
        desiredNumFlagDuties = {}
        desiredRAList = [
            # Candidate RAs
            RA("Test", "RA1", 1, 1, "2021-08-27"),
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        # Create the State object being tested
        singleDutyState = State(
            singleDutyDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        doubleDutyState = State(
            doubleDutyDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # -- Act --

        # Test the method with a State object that is not a double duty day
        singleDutyRes = singleDutyState.isDoubleDay()

        # Test the method with a State object that is a double duty day
        doubleDutyRes = doubleDutyState.isDoubleDay()

        # -- Assert --

        # Assert that we received the expected results
        self.assertFalse(singleDutyRes)
        self.assertTrue(doubleDutyRes)

    def test_getNextCandidate_returnsFirstItemInCandList(self):
        # Test to ensure that the getNextCandidate method returns the
        #  first item in the candList and removes the item from the list

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = 27
        singleDutyDay = Day(desiredDate, 1)
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredPredetermined = False
        desiredLastDateAssigned = {}
        desiredNumDoubleDays = {}
        desiredNumFlagDuties = {}
        desiredRAList = [
            # Candidate RAs
            RA("Test", "RA1", 1, 1, "2021-08-27"),
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        # Create the State object being tested
        testState = State(
            singleDutyDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        preTestCandList = testState.candList.copy()

        # -- Act --

        # Call the method being tested
        res = testState.getNextCandidate()

        # -- Assert --

        # Assert that the result was the first item in the preTestCandList
        self.assertIn(res, preTestCandList)
        self.assertEqual(preTestCandList[0], res)

        # Assert that the result is no longer in the testState's candList
        self.assertNotIn(res, testState.candList)

    def test_assignNextRA_returnsAssignedRA(self):
        # Test to ensure that the assignNextRA method returns the RA
        #  that was assigned for duty to the calling method.

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = 27
        singleDutyDay = Day(desiredDate, 1)
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredPredetermined = False
        desiredLastDateAssigned = {}
        desiredNumDoubleDays = {}
        desiredNumFlagDuties = {}
        expectedAssignedRA = RA("Test", "RA1", 1, 1, "2021-08-27")
        desiredRAList = [expectedAssignedRA]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        # Create the State object being tested
        testState = State(
            singleDutyDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # -- Act --

        # Call the method being tested.
        res = testState.assignNextRA()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(expectedAssignedRA, res)

        # Assert that the returned RA was also assigned for duty
        self.assertEqual(res, testState.curDay.getRAs()[0])

    def test_assignNextRA_updatesLastDateAssignedAsNecessary(self):
        # Test to ensure that the assignNextRA updates the lastDateAssigned
        #  dictionary when assigning an RA for duty.

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = 27
        singleDutyDay = Day(desiredDate, 1)
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredPredetermined = False
        desiredLastDateAssigned = {}
        desiredNumDoubleDays = {}
        desiredNumFlagDuties = {}
        desiredRAList = [
            RA("Test", "RA1", 1, 1, "2021-08-27"),
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        # Create the State object being tested
        testState = State(
            singleDutyDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # Grab the RA that is expected to be assigned for duty
        expectedAssignedRA = testState.candList[0]

        # -- Act --

        # Call the method being tested.
        res = testState.assignNextRA()

        # -- Assert --

        # Assert that the lastDateAssigned dictionary was updated as expected.
        self.assertEqual(desiredLastDateAssigned[expectedAssignedRA], desiredDate)
        self.assertEqual(desiredLastDateAssigned[testState.candList[0]], 0)

    def test_assignNextRA_ifDoubleDay_incrementsNumDoubleDaysAsNecessary(self):
        # Test to ensure that the assignNextRA updates the numDoubleDays
        #  dictionary when assigning an RA for duty if the curDay is a
        #  doubleDay.

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = 27
        singleDutyDay = Day(desiredDate, 1, isDoubleDay=True)
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredPredetermined = False
        desiredLastDateAssigned = {}
        desiredNumDoubleDays = {}
        desiredNumFlagDuties = {}
        desiredRAList = [
            RA("Test", "RA1", 1, 1, "2021-08-27"),
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        # Create the State object being tested
        testState = State(
            singleDutyDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # Grab the RA that is expected to be assigned for duty
        expectedAssignedRA = testState.candList[0]

        # -- Act --

        # Call the method being tested.
        res = testState.assignNextRA()

        # -- Assert --

        # Assert that the lastDateAssigned dictionary was updated as expected.
        self.assertEqual(desiredNumDoubleDays[expectedAssignedRA], 1)
        self.assertEqual(desiredNumDoubleDays[testState.candList[0]], 0)

    def test_assignNextRA_ifFlaggedDuty_incrementsNumFlagDutiesAsNecessary(self):
        # Test to ensure that the assignNextRA updates the numFlagDuties
        #  dictionary when assigning an RA for duty if the next duty slot
        #  is a flagged duty.

        # -- Arrange --

        # Create the objects used in this test
        desiredDate = 27
        singleDutyDay = Day(desiredDate, 1, flagDutySlot=True)
        desiredLDATolerance = 15
        desiredNDDTolerance = .141
        desiredPredetermined = False
        desiredLastDateAssigned = {}
        desiredNumDoubleDays = {}
        desiredNumFlagDuties = {}
        desiredRAList = [
            RA("Test", "RA1", 1, 1, "2021-08-27"),
            RA("Test", "RA2", 2, 1, "2021-08-27")
        ]

        # Populate the lda, ndd, and nfd dictionaries
        for ra in desiredRAList:
            desiredLastDateAssigned[ra] = 0
            desiredNumDoubleDays[ra] = 0
            desiredNumFlagDuties[ra] = 0

        # Create the State object being tested
        testState = State(
            singleDutyDay,
            desiredRAList,
            desiredLastDateAssigned,
            desiredNumDoubleDays,
            desiredLDATolerance,
            desiredNDDTolerance,
            desiredNumFlagDuties,
            predetermined=desiredPredetermined
        )

        # Grab the RA that is expected to be assigned for duty
        expectedAssignedRA = testState.candList[0]

        # -- Act --

        # Call the method being tested.
        res = testState.assignNextRA()

        # -- Assert --

        # Assert that the lastDateAssigned dictionary was updated as expected.
        self.assertEqual(desiredNumFlagDuties[expectedAssignedRA], 1)
        self.assertEqual(desiredNumFlagDuties[testState.candList[0]], 0)

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
