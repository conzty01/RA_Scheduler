from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest

from helperFunctions.helperFunctions import stdRet, AuthenticatedUser


class TestBreakBP_changeBreakDuty(unittest.TestCase):
    def setUp(self):
        # Set up a number of items that will be used for these tests.

        # -- Mock the os.environ method so that we can create the server. --

        # Helper Dict for holding the os.environ configuration
        self.helper_osEnviron = {
            "CLIENT_ID": "TEST CLIENT_ID",
            "PROJECT_ID": "TEST PROJECT_ID",
            "AUTH_URI": "TEST AUTH_URI",
            "TOKEN_URI": "TEST TOKEN_URI",
            "AUTH_PROVIDER_X509_CERT_URL": "TEST AUTH_PROVIDER_X509_CERT_URL",
            "CLIENT_SECRET": "TEST CLIENT_SECRET",
            "REDIRECT_URIS": "TEST1,TEST2,TEST3,TEST4",
            "JAVASCRIPT_ORIGINS": "TEST5,TEST6",
            "EXPLAIN_TEMPLATE_LOADING": "FALSE",
            "LOG_LEVEL": "WARNING",
            "USE_ADHOC": "FALSE",
            "SECRET_KEY": "TEST SECRET KEY",
            "OAUTHLIB_RELAX_TOKEN_SCOPE": "1",
            "OAUTHLIB_INSECURE_TRANSPORT": "1",
            "HOST_URL": "https://localhost:5000",
            "DATABASE_URL": "postgres://ra_sched"
        }

        # Create a dictionary patcher for the os.environ method
        self.patcher_osEnviron = patch.dict("os.environ",
                                            self.helper_osEnviron)

        # Start the os patchers (No mock object is returned since we used patch.dict())
        self.patcher_osEnviron.start()

        # -- Create an instance of ScheduleServer that we may test against. --

        # Mark the application as being tested
        app.config["TESTING"] = True
        # Disable the login_required decorator
        app.config["LOGIN_DISABLED"] = True
        # Reinitialize the Login Manager to accept the new configuration
        app.login_manager.init_app(app)
        # Create the test server
        self.server = app.test_client()

        # -- Create a patcher for the getAuth() method from helperFunctions --
        #     since we have disabled the login manager for testing

        # First we must create an object for the auth_level that we can manipulate
        #  as needed for the tests. By default, the auth_level is set to 1.
        self.mocked_authLevel = MagicMock(return_value=1)

        # In order for the authLevel to respond to __lt__, __gt__, and __eq__ calls,
        #  we need to create lambda functions that can effectively implement the
        #  respective magic methods.
        self.mocked_authLevel_ltMock = lambda me, other: me.return_value < other
        self.mocked_authLevel_gtMock = lambda me, other: me.return_value > other
        self.mocked_authLevel_eqMock = lambda me, other: me.return_value == other

        # We then set the auth_level mock to return the __lt__ Mock
        self.mocked_authLevel.__lt__ = self.mocked_authLevel_ltMock
        # We then set the auth_level mock to return the __gt__ Mock
        self.mocked_authLevel.__gt__ = self.mocked_authLevel_ltMock
        # We then set the auth_level mock to return the __eq__ Mock
        self.mocked_authLevel.__eq__ = self.mocked_authLevel_ltMock

        # Set the ra_id and hall_id to values that can be used throughout
        self.user_ra_id = 1
        self.user_hall_id = 1
        self.associatedResHalls = [
            {
                "id": self.user_hall_id,
                "auth_level": self.mocked_authLevel,
                "name": "Test Hall"
            }
        ]

        # Assemble all of the desired values into an Authenticated User Object
        self.helper_getAuth = AuthenticatedUser(
            "test@email.com",
            self.user_ra_id,
            "Test",
            "User",
            self.associatedResHalls
        )

        # Create the patcher for the getAuth() method
        self.patcher_getAuth = patch("breaks.breaks.getAuth", autospec=True)

        # Start the patcher - mock returned
        self.mocked_getAuth = self.patcher_getAuth.start()

        # Configure the mocked_getAuth to return the helper_getAuth dictionary
        self.mocked_getAuth.return_value = self.helper_getAuth

        # -- Create a patcher for the appGlobals file --
        self.patcher_appGlobals = patch("breaks.breaks.ag", autospec=True)

        # Start the patcher - mock returned
        self.mocked_appGlobals = self.patcher_appGlobals.start()

        # Configure the mocked appGlobals as desired
        self.mocked_appGlobals.baseOpts = {"HOST_URL": "https://localhost:5000"}
        self.mocked_appGlobals.conn = MagicMock()
        self.mocked_appGlobals.UPLOAD_FOLDER = "./static"
        self.mocked_appGlobals.ALLOWED_EXTENSIONS = {"txt", "csv"}

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
        self.patcher_getAuth.stop()
        self.patcher_appGlobals.stop()
        self.patcher_osEnviron.stop()

        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

    def resetAuthLevel(self):
        # This function serves to reset the auth_level of the session
        #  to the default value which is 1.
        self.mocked_authLevel.return_value = 1

    def test_whenPassedValidParams_returnsSuccessfulResponse(self):
        # Test to ensure that when an authorized remote client reaches this API
        #  endpoint that endpoint accepts the following parameters and returns a
        #  successful result:
        #
        #   oldName  <str> -  a string denoting the full name of the RA associated with
        #                      the break duty that should be changed.
        #   newId    <int> -  an integer representing the ra.id for the RA that should be
        #                      assigned for the break duty.
        #   dateStr  <str> -  a string representing the date of the break duty.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        desiredNewID = 68

        desiredOldName = "Test User"
        desiredOldID = 3

        desiredDateStr = "2021-01-06"
        desiredDayID = 9
        desiredMonthID = 10

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            # First call returns ra table record data for the new RA
            (desiredNewID, ),
            # Second call returns ra table record data for the old RA
            (desiredOldID,),
            # Third call returns the dayID and monthID for the date string
            (desiredDayID, desiredMonthID)
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/breaks/api/changeBreakDuty",
                                json=dict(
                                    oldName=desiredOldName,
                                    newId=desiredNewID,
                                    dateStr=desiredDateStr
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.cursor().execute was called four times
        self.assertEqual(self.mocked_appGlobals.conn.cursor().execute.call_count, 4)

        # Assert that the last time appGlobals.conn.cursor().execute was called,
        #  it was an update statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            """UPDATE break_duties
                   SET ra_id = %s
                   WHERE hall_id = %s
                   AND day_id = %s
                   AND month_id = %s
                   AND ra_id = %s
                """,
            (desiredNewID, self.user_hall_id, desiredDayID, desiredMonthID, desiredOldID)
        )

        # Assert that appGlobals.conn.commit was called once
        self.mocked_appGlobals.conn.commit.assert_called_once()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we got a successful response
        self.assertEqual(resp.json, stdRet(1, "successful"))

    def test_WithUnauthorizedUser_returnsNotAuthorizedResponse(self):
        # Test to ensure that when a user that is NOT authorized to reach this
        #  endpoint, they receive a JSON response that indicates that they are
        #  not authorized. An authorized user is a user that has an auth_level
        #  of at least 2 (AHD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()

        # Reset the auth_level to 1
        self.resetAuthLevel()

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/breaks/api/changeBreakDuty",
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that the json is formatted as expected
        self.assertEqual(resp.json, stdRet(-1, "NOT AUTHORIZED"))

        # Assert that we received a 200 status code
        self.assertEqual(resp.status_code, 200)

        # Assert that no additional call to the DB was made
        self.mocked_appGlobals.conn.cursor().execute.assert_not_called()

    def test_whenPassedInvalidDay_returnsInvalidParamsResponse(self):
        # Test to ensure that when a date is provided to the endpoint,
        #  a check is done to ensure that a day record exists for that
        #  date. If one does not exist, then we would expect to receive
        #  an "Unable to find all necessary Break Duty parameters in
        #  database." result.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        desiredNewID = 68

        desiredOldName = "Test User"
        desiredOldID = 3

        desiredDateStr = "2021-01-06"
        desiredMonthID = 10

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            # First call returns ra table record data for the new RA
            (desiredNewID, ),
            # Second call returns ra table record data for the old RA
            (desiredOldID,),
            # Third call returns the dayID and monthID for the date string
            (None, desiredMonthID)
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/breaks/api/changeBreakDuty",
                                json=dict(
                                    oldName=desiredOldName,
                                    newId=desiredNewID,
                                    dateStr=desiredDateStr
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received the expected response
        self.assertEqual(resp.json, stdRet(0, "Unable to find all necessary Break Duty parameters in database."))

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

    def test_whenPassedInvalidMonth_returnsInvalidParamsResponse(self):
        # Test to ensure that when a date is provided to the endpoint,
        #  a check is done to ensure that a month record exists for that
        #  date. If one does not exist, then we would expect to receive
        #  an "Unable to find all necessary Break Duty parameters in
        #  database." result.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        desiredNewID = 68

        desiredOldName = "Test User"
        desiredOldID = 3

        desiredDateStr = "2021-01-06"
        desiredDayID = 9

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            # First call returns ra table record data for the new RA
            (desiredNewID,),
            # Second call returns ra table record data for the old RA
            (desiredOldID,),
            # Third call returns the dayID and monthID for the date string
            (desiredDayID, None)
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/breaks/api/changeBreakDuty",
                                json=dict(
                                    oldName=desiredOldName,
                                    newId=desiredNewID,
                                    dateStr=desiredDateStr
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received the expected response
        self.assertEqual(resp.json, stdRet(0, "Unable to find all necessary Break Duty parameters in database."))

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

    def test_whenPassedInvalidNewRA_returnsInvalidParamsResponse(self):
        # Test to ensure that when the new RA's id is provided to the endpoint,
        #  a check is done to ensure that a ra record exists and that it belongs
        #  to the same hall as the user. If at least one of these criteria are not
        #  met, then we expect to receive an "Unable to find all necessary Break
        #  Duty parameters in database." result.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        desiredNewID = 68

        desiredOldName = "Test User"
        desiredOldID = 3

        desiredDateStr = "2021-01-06"
        desiredDayID = 9
        desiredMonthID = 10

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            # First call returns ra table record data for the new RA
            None,
            # Second call returns ra table record data for the old RA
            (desiredOldID,),
            # Third call returns the dayID and monthID for the date string
            (desiredDayID, desiredMonthID)
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/breaks/api/changeBreakDuty",
                                json=dict(
                                    oldName=desiredOldName,
                                    newId=desiredNewID,
                                    dateStr=desiredDateStr
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received the expected response
        self.assertEqual(resp.json, stdRet(0, "Unable to find all necessary Break Duty parameters in database."))

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

    def test_whenPassedInvalidOldRA_returnsInvalidParamResponse(self):
        # Test to ensure that when the old RA's name is provided to the endpoint,
        #  a check is done to ensure that a ra record exists and that it belongs
        #  to the same hall as the user. If at least one of these criteria are not
        #  met, then we expect to receive an "Unable to find all necessary Break
        #  Duty parameters in database." result.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        desiredNewID = 68
        desiredNewFName = "Test2"
        desiredNewLName = "User2"
        desiredNewColor = "Test Color"

        desiredOldName = "Test User"

        desiredDateStr = "2021-01-06"
        desiredDayID = 9
        desiredMonthID = 10

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            # First call returns ra table record data for the new RA
            (desiredNewID, desiredNewFName, desiredNewLName, desiredNewColor),
            # Second call returns ra table record data for the old RA
            None,
            # Third call returns the dayID and monthID for the date string
            (desiredDayID, desiredMonthID)
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/breaks/api/changeBreakDuty",
                                json=dict(
                                    oldName=desiredOldName,
                                    newId=desiredNewID,
                                    dateStr=desiredDateStr
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received the expected response
        self.assertEqual(resp.json, stdRet(0, "Unable to find all necessary Break Duty parameters in database."))

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()
