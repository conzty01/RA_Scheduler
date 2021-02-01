from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest

from helperFunctions.helperFunctions import stdRet


class TestSchedule_addNewDuty(unittest.TestCase):
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

        # Assemble all of the desired values into a dict object.
        self.helper_getAuth = {
            "uEmail": "test@email.com",
            "ra_id": self.user_ra_id,
            "name": "Test User",
            "hall_id": self.user_hall_id,
            "auth_level": self.mocked_authLevel,
            "hall_name": "Test Hall"
        }

        # Create the patcher for the getAuth() method
        self.patcher_getAuth = patch("schedule.schedule.getAuth", autospec=True)

        # Start the patcher - mock returned
        self.mocked_getAuth = self.patcher_getAuth.start()

        # Configure the mocked_getAuth to return the helper_getAuth dictionary
        self.mocked_getAuth.return_value = self.helper_getAuth

        # -- Create a patcher for the appGlobals file --
        self.patcher_appGlobals = patch("schedule.schedule.ag", autospec=True)

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

        # Stop all of the logging patchers
        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

    def resetAuthLevel(self):
        # This function serves to reset the auth_level of the session
        #  to the default value which is 1.
        self.mocked_authLevel.return_value = 1

    def test_withoutAuthorizedUser_returnsNotAuthorizedResponse(self):
        # Test to ensure that when an unauthorized user attempts to reach this API
        #  endpoint, a NOT AUTHORIZED response is returned to the user. An authorized
        #  user is one whose auth_level is at least 2 (AHD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Reset the auth_level to 1
        self.resetAuthLevel()

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/schedule/api/addNewDuty",
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

    def test_withAuthorizedUser_withoutValidRA_returnsInvalidRASelectionResponse(self):
        # Test to ensure that when an authorized user attempts to use this API,
        #  if an invalid RA is provided, this method will return an Invalid RA
        #  Selection response.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Generate the various objects that will be used in this test
        desiredRAID = 8
        desiredDateStr = "2021-01-26"
        desiredPointVal = 1

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            None,   # First query is for the RA ID
            None,   # Second query is for the day info
            None    # Third query is for the schedule
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/schedule/api/addNewDuty",
                                json=dict(
                                    id=desiredRAID,
                                    pts=desiredPointVal,
                                    dateStr=desiredDateStr
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the last time appGlobals.conn.cursor().execute was called,
        #  it was a query for the RA.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            "SELECT id FROM ra WHERE id = %s AND hall_id = %s;",
            (desiredRAID, self.user_hall_id)
        )

        # Assert that we received the expected response
        self.assertEqual(resp.json, stdRet(-1, "Chosen RA is not a Valid Selection"))

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

    def test_withAuthorizedUser_withoutValidDay_returnsInvalidDayResponse(self):
        # Test to ensure that when an authorized user attempts to use this API,
        #  if an invalid Day is provided, this method will return an Invalid Day
        #  Selection response.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Generate the various objects that will be used in this test
        desiredRAID = 15
        desiredDateStr = "2021-01-26"
        desiredPointVal = 4

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (desiredRAID,),  # First query is for the RA ID
            None,  # Second query is for the day info
            None  # Third query is for the schedule
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/schedule/api/addNewDuty",
                                json=dict(
                                    id=desiredRAID,
                                    pts=desiredPointVal,
                                    dateStr=desiredDateStr
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the last time appGlobals.conn.cursor().execute was called,
        #  it was a query for the RA.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            "SELECT id, month_id FROM day WHERE date = TO_DATE(%s, 'YYYY-MM-DD');",
            (desiredDateStr,)
        )

        # Assert that we received the expected response
        self.assertEqual(resp.json, stdRet(0, "Invalid Date"))

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

    def test_withAuthorizedUser_withoutValidSchedule_returnsInvalidScheduleResponse(self):
        # Test to ensure that when an authorized user attempts to use this API,
        #  if no schedule is available, this method will return an Invalid
        #  Schedule response.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Generate the various objects that will be used in this test
        desiredRAID = 1
        desiredDateStr = "2021-01-26"
        desiredPointVal = 3
        expectedMonthID = 9
        expectedDayID = 17

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (desiredRAID,),                     # First query is for the RA ID
            (expectedDayID, expectedMonthID),   # Second query is for the day info
            None                                # Third query is for the schedule
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/schedule/api/addNewDuty",
                                json=dict(
                                    id=desiredRAID,
                                    pts=desiredPointVal,
                                    dateStr=desiredDateStr
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the last time appGlobals.conn.cursor().execute was called,
        #  it was a query for the RA.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            "SELECT id FROM schedule WHERE hall_id = %s AND month_id = %s ORDER BY created DESC, id DESC;",
            (self.user_hall_id, expectedMonthID)
        )

        # Assert that we received the expected response
        self.assertEqual(resp.json, stdRet(0, "Unable to validate schedule."))

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

    def test_withAuthorizedUser_withValidParameters_addsNewDutyIntoDB(self):
        # Test to ensure that when an authorized user attempts to reach this
        #  API and provides valid parameters, that a new duty is created in
        #  the DB

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Generate the various objects that will be used in this test
        desiredRAID = 89
        desiredDateStr = "2021-01-26"
        desiredPointVal = 44
        expectedMonthID = 25
        expectedDayID = 81
        expectedScheduleID = 100

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (desiredRAID,),                     # First query is for the RA ID
            (expectedDayID, expectedMonthID),   # Second query is for the day info
            (expectedScheduleID,)               # Third query is for the schedule
        ]

        # Configure the flag that should be passed in
        desiredFlagState = True

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/schedule/api/addNewDuty",
                                json=dict(
                                    id=desiredRAID,
                                    pts=desiredPointVal,
                                    dateStr=desiredDateStr,
                                    flag=desiredFlagState
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the last time appGlobals.conn.cursor().execute was called,
        #  it was a query for the RA.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            """INSERT INTO duties (hall_id, ra_id, day_id, sched_id, point_val, flagged)
                    VALUES (%s, %s, %s, %s, %s, %s);""",
            (self.user_hall_id, desiredRAID, expectedDayID,
             expectedScheduleID, desiredPointVal, desiredFlagState)
        )

        # Assert that we received the expected response
        self.assertEqual(resp.json, stdRet(1, "successful"))

        # Assert that the appGlobals.conn.commit was called
        self.mocked_appGlobals.conn.commit.assert_called_once()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()
