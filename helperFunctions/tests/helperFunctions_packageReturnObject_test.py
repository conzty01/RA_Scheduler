from unittest.mock import MagicMock, patch, call
import unittest

from helperFunctions.helperFunctions import packageReturnObject


class TestHelperFunctions_getSchoolYear(unittest.TestCase):
    def setUp(self):
        # Set up a number of items that will be used for these tests.

        # -- Create a patcher for the appGlobals file --
        self.patcher_appGlobals = patch("helperFunctions.helperFunctions.ag", autospec=True)

        # Start the patcher - mock returned
        self.mocked_appGlobals = self.patcher_appGlobals.start()

        # Configure the mocked appGlobals as desired
        self.mocked_appGlobals.baseOpts = {"HOST_URL": "https://localhost:5000"}
        self.mocked_appGlobals.conn = MagicMock()
        self.mocked_appGlobals.UPLOAD_FOLDER = "./static"

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

        # -- Create a patcher for flask.jsonify --
        self.patcher_flaskJSONIFY = patch("helperFunctions.helperFunctions.jsonify")

        # Start the patcher - mock returned
        self.mocked_flaskJSONIFY = self.patcher_flaskJSONIFY.start()

        # Create a side effect function for the jsonify mock
        def jsonifySideEffect(obj):
            return obj

        # Set the side effect on the jsonify mock
        self.mocked_flaskJSONIFY.side_effect = jsonifySideEffect

    def tearDown(self):
        # Stop all of the patchers
        self.patcher_appGlobals.stop()

        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

        self.patcher_flaskJSONIFY.stop()

    def test_ensureFromServerDefaultsToFalse(self):
        # Test to ensure that when the provided fromServer parameter is
        #  set to False, the method returns the object as it was provided.

        # -- Arrange --

        # Reset the mocks used in this test
        self.mocked_flaskJSONIFY.reset_mock()

        # Create the objects for this test
        testList = [1, 2, 3]
        testTuple = (1, 2, 3)
        testString = "Test String"
        testInt = 20210820

        # -- Act --

        # Call the method being tested
        listRes = packageReturnObject(testList)
        tupleRes = packageReturnObject(testTuple)
        stringRes = packageReturnObject(testString)
        intRes = packageReturnObject(testInt)

        # -- Assert --

        # Assert that the jsonify method was called on each of the test objects
        self.mocked_flaskJSONIFY.assert_has_calls(
            [call(testList), call(testTuple), call(testString), call(testInt)],
            any_order=True
        )

        # Assert that we received the expected result
        self.assertListEqual(testList, listRes)
        self.assertTupleEqual(testTuple, tupleRes)
        self.assertEqual(testString, stringRes)
        self.assertEqual(testInt, intRes)

    def test_whenFromServerParameterIsFalse_returnsSerializedObject(self):
        # Test to ensure that when the provided fromServer parameter is
        #  set to False, the method returns the object as it was provided.

        # -- Arrange --

        # Reset the mocks used in this test
        self.mocked_flaskJSONIFY.reset_mock()

        # Create the objects for this test
        testList = [1, 2, 3]
        testTuple = (1, 2, 3)
        testString = "Test String"
        testInt = 20210820

        # -- Act --

        # Call the method being tested
        listRes = packageReturnObject(testList, False)
        tupleRes = packageReturnObject(testTuple, False)
        stringRes = packageReturnObject(testString, False)
        intRes = packageReturnObject(testInt, False)

        # -- Assert --

        # Assert that the jsonify method was called on each of the test objects
        self.mocked_flaskJSONIFY.assert_has_calls(
            [call(testList), call(testTuple), call(testString), call(testInt)],
            any_order=True
        )

        # Assert that we received the expected result
        self.assertListEqual(testList, listRes)
        self.assertTupleEqual(testTuple, tupleRes)
        self.assertEqual(testString, stringRes)
        self.assertEqual(testInt, intRes)

    def test_whenFromServerParameterIsTrue_returnsObjectProvided(self):
        # Test to ensure that when the provided fromServer parameter is
        #  set to True, the method returns a serialized version of the object.

        # -- Arrange --

        # Reset the mocks used in this test
        self.mocked_flaskJSONIFY.reset_mock()

        # Create the objects for this test
        testList = [1, 2, 3]
        testTuple = (1, 2, 3)
        testString = "Test String"
        testInt = 20210820

        # -- Act --

        # Call the method being tested
        listRes = packageReturnObject(testList, True)
        tupleRes = packageReturnObject(testTuple, True)
        stringRes = packageReturnObject(testString, True)
        intRes = packageReturnObject(testInt, True)

        # -- Assert --

        # Assert that the flask.jsonify method was not called
        self.mocked_flaskJSONIFY.assert_not_called()

        # Assert that we received the expected result
        self.assertListEqual(testList, listRes)
        self.assertTupleEqual(testTuple, tupleRes)
        self.assertEqual(testString, stringRes)
        self.assertEqual(testInt, intRes)
