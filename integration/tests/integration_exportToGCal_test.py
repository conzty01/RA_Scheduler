from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest

from helperFunctions.helperFunctions import stdRet


class TestIntegration_exportToGCal(unittest.TestCase):
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
        self.patcher_getAuth = patch("integration.integrations.getAuth", autospec=True)

        # Start the patcher - mock returned
        self.mocked_getAuth = self.patcher_getAuth.start()

        # Configure the mocked_getAuth to return the helper_getAuth dictionary
        self.mocked_getAuth.return_value = self.helper_getAuth

        # -- Create a patcher for the appGlobals file --
        self.patcher_appGlobals = patch("integration.integrations.ag", autospec=True)

        # Start the patcher - mock returned
        self.mocked_appGlobals = self.patcher_appGlobals.start()

        # Configure the mocked appGlobals as desired
        self.mocked_appGlobals.baseOpts = {"HOST_URL": "https://localhost:5000"}
        self.mocked_appGlobals.conn = MagicMock()
        self.mocked_appGlobals.UPLOAD_FOLDER = "./static"
        self.mocked_appGlobals.ALLOWED_EXTENSIONS = {"txt", "csv"}

        # -- Create a patcher for the gCalIntegratinator object --
        self.patcher_integrationPart = patch("integration.integrations.gCalInterface", autospec=True)

        # Start the patcher - mock returned
        self.mocked_integrationPart = self.patcher_integrationPart.start()

        # -- Create a patcher for the BytesIO object --
        self.patcher_bytesIO = patch("integration.integrations.BytesIO")

        # Start the patcher - mock returned
        self.mocked_bytesIO = self.patcher_bytesIO.start()

        # -- Create a patcher for the pickle module --
        self.patcher_pickle = patch("integration.integrations.pickle")

        # Start the patcher - mock returned
        self.mocked_pickle = self.patcher_pickle.start()

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
        self.patcher_integrationPart.stop()
        self.patcher_bytesIO.stop()
        self.patcher_pickle.stop()

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
        # Test to ensure that when this method is called without an authorized user
        #  a NOT AUTHORIZED response is returned. An authorized user is a user that
        #  has an auth_level of at least 2 (AHD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.resetAuthLevel()

        expectedResponse = stdRet(-1, "NOT AUTHORIZED")

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/api/exportToGCal",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that the response we received is json
        self.assertTrue(resp.is_json)

        # Assert that we received the expected response
        self.assertDictEqual(expectedResponse, resp.json)

    def test_withAuthorizedUser_withNOTokenInDB_returnsNoTokenResponse(self):
        # Test to ensure that when this method is called with an authorized user,
        #  but without a token already registered in the DB, this method returns
        #  a No Token Found response. An authorized user is a user that has an
        #  auth_level of at least 2 (AHD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.resetAuthLevel()

        # Set the auth_level to be used for this test.
        self.mocked_authLevel.return_value = 2

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            None,  # First call returns the token
        ]

        # Create the expected response
        expectedResponse = stdRet(0, "No Token Found")

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/api/exportToGCal",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was an UPDATE statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with(
            "SELECT calendar_id, token FROM google_calendar_info WHERE res_hall_id = %s",
            (self.user_hall_id,)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that the response we received is json
        self.assertTrue(resp.is_json)

        # Assert that we received the expected response
        self.assertDictEqual(expectedResponse, resp.json)

    @patch("integration.integrations.getSchedule2", autospec=True)
    @patch("integration.integrations.getBreakDuties", autospec=True)
    def test_withAuthorizedUser_withTokenInDB_callsGetScheduleAPI(self, mocked_getBreakDuties, mocked_getSchedule2):
        # Test to ensure that when this method is called with an authorized user,
        #  and a token has already been added in the DB, this method calls the
        #  appropriate methods to get the full schedule for the given month. This
        #  involves gathering both the regular duties as well as the break duties.
        #  An authorized user is a user that has an  auth_level of at least 2 (AHD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.resetAuthLevel()

        # Set the auth_level to be used for this test.
        self.mocked_authLevel.return_value = 2

        # Configure the result of the gCalIntegratinator.exportScheduleToGoogleCalendar method
        self.mocked_integrationPart.exportScheduleToGoogleCalendar.return_value = 1

        # Create the objects needed for this test
        desiredMonthNum = 3
        desiredYear = 1997
        expectedStartDate = "1997-03-01"
        expectedEndDate = "1997-03-31"
        expectedToken = MagicMock()
        expectedID = "longCalendarID@calendar.google.com"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedID, expectedToken),  # First call returns the token
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/api/exportToGCal",
                               query_string=dict(
                                   monthNum=desiredMonthNum,
                                   year=desiredYear,
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that the getBreakDuties API was called
        mocked_getBreakDuties.assert_called_once_with(
            start=expectedStartDate,
            end=expectedEndDate,
            hallId=self.user_hall_id,
            showAllColors=True
        )

        # Assert that the getSchedule2 API was called
        mocked_getSchedule2.assert_called_once_with(
            start=expectedStartDate,
            end=expectedEndDate,
            hallId=self.user_hall_id,
            showAllColors=True
        )

    @patch("integration.integrations.getSchedule2", autospec=True)
    @patch("integration.integrations.getBreakDuties", autospec=True)
    def test_withAuthorizedUser_withTokenInDB_callsGCalIntegratinatorExportFunction(self, mocked_getBreakDuties,
                                                                                    mocked_getSchedule2):
        # Test to ensure that when this method is called with an authorized user,
        #  and a token has already been added in the DB, this method calls the
        #  exportScheduleToGoogleCalendar method for the gCalIntegratinator.
        #  An authorized user is a user that has an  auth_level of at least 2 (AHD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.mocked_integrationPart.reset_mock()
        self.mocked_bytesIO.reset_mock()
        self.mocked_pickle.reset_mock()
        self.resetAuthLevel()

        # Set the auth_level to be used for this test.
        self.mocked_authLevel.return_value = 2

        # Configure the result of the gCalIntegratinator.exportScheduleToGoogleCalendar method
        self.mocked_integrationPart.exportScheduleToGoogleCalendar.return_value = 1

        # Create the objects needed for this test
        desiredMonthNum = 3
        desiredYear = 1997
        expectedToken = MagicMock()
        expectedID = "longCalendarID@calendar.google.com"
        expectedRegularDutyDict = [1, 2, 3, 4, 5]
        expectedBreakDutyDict = [6, 7, 8, 9, 10]

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedID, expectedToken),  # First call returns the token
        ]

        # Configure the results of the mocked_getBreakDuties and mocked_getSchedule2 functions
        mocked_getBreakDuties.return_value = expectedBreakDutyDict
        mocked_getSchedule2.return_value = expectedRegularDutyDict

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/api/exportToGCal",
                               query_string=dict(
                                   monthNum=desiredMonthNum,
                                   year=desiredYear,
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that a BytesIO object was created from the token's memview
        self.mocked_bytesIO.assert_called_once_with(expectedToken)

        # Assert that pickle.load was called as expected
        self.mocked_pickle.load.assert_called_once_with(self.mocked_bytesIO())

        # Assert that the gCalIntegratinator.exportScheduleToGoogleCalendar method was called
        self.mocked_integrationPart.exportScheduleToGoogleCalendar.assert_called_once_with(
            self.mocked_pickle.load(),
            expectedID,
            expectedRegularDutyDict + expectedBreakDutyDict
        )

    @patch("integration.integrations.getSchedule2", autospec=True)
    @patch("integration.integrations.getBreakDuties", autospec=True)
    def test_withAuthorizedUser_withTokenInDB_ifExportFails_returnsReconnectResponse(self, mocked_getBreakDuties,
                                                                                     mocked_getSchedule2):
        # Test to ensure that when this method is called with an authorized user,
        #  and a token has already been added in the DB and the export fails, this
        #  method returns a response to the user indicating that they should reconnect
        #  their Google Calendar account. An authorized user is a user that has an
        #  auth_level of at least 2 (AHD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.mocked_integrationPart.reset_mock()
        self.mocked_bytesIO.reset_mock()
        self.mocked_pickle.reset_mock()
        self.resetAuthLevel()

        # Set the auth_level to be used for this test.
        self.mocked_authLevel.return_value = 2

        # Configure the result of the gCalIntegratinator.exportScheduleToGoogleCalendar method
        self.mocked_integrationPart.exportScheduleToGoogleCalendar.return_value = -1

        # Create the objects needed for this test
        desiredMonthNum = 3
        desiredYear = 1997
        expectedToken = MagicMock()
        expectedID = "longCalendarID@calendar.google.com"
        expectedRegularDutyDict = [1, 2, 3, 4, 5]
        expectedBreakDutyDict = [6, 7, 8, 9, 10]
        expectedResponse = stdRet(0, "Reconnect Google Calendar Account")

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedID, expectedToken),  # First call returns the token
        ]

        # Configure the results of the mocked_getBreakDuties and mocked_getSchedule2 functions
        mocked_getBreakDuties.return_value = expectedBreakDutyDict
        mocked_getSchedule2.return_value = expectedRegularDutyDict

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/api/exportToGCal",
                               query_string=dict(
                                   monthNum=desiredMonthNum,
                                   year=desiredYear,
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that the response we received is json
        self.assertTrue(resp.is_json)

        # Assert that we received the expected response
        self.assertDictEqual(expectedResponse, resp.json)

    @patch("integration.integrations.getSchedule2", autospec=True)
    @patch("integration.integrations.getBreakDuties", autospec=True)
    def test_withAuthorizedUser_withTokenInDB_whenSuccessful_returnsSuccessfulResponse(self, mocked_getBreakDuties,
                                                                                     mocked_getSchedule2):
        # Test to ensure that when this method is called with an authorized user,
        #  and a token has already been added in the DB, when the export succeeds, this
        #  method returns a response to the user indicating that the export was successful.
        #  An authorized user is a user that has an auth_level of at least 2 (AHD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.mocked_integrationPart.reset_mock()
        self.mocked_bytesIO.reset_mock()
        self.mocked_pickle.reset_mock()
        self.resetAuthLevel()

        # Set the auth_level to be used for this test.
        self.mocked_authLevel.return_value = 2

        # Configure the result of the gCalIntegratinator.exportScheduleToGoogleCalendar method
        self.mocked_integrationPart.exportScheduleToGoogleCalendar.return_value = 1

        # Create the objects needed for this test
        desiredMonthNum = 3
        desiredYear = 1997
        expectedToken = MagicMock()
        expectedID = "longCalendarID@calendar.google.com"
        expectedRegularDutyDict = [1, 2, 3, 4, 5]
        expectedBreakDutyDict = [6, 7, 8, 9, 10]
        expectedResponse = stdRet(1, "successful")

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedID, expectedToken),  # First call returns the token
        ]

        # Configure the results of the mocked_getBreakDuties and mocked_getSchedule2 functions
        mocked_getBreakDuties.return_value = expectedBreakDutyDict
        mocked_getSchedule2.return_value = expectedRegularDutyDict

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/api/exportToGCal",
                               query_string=dict(
                                   monthNum=desiredMonthNum,
                                   year=desiredYear,
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that the response we received is json
        self.assertTrue(resp.is_json)

        # Assert that we received the expected response
        self.assertDictEqual(expectedResponse, resp.json)
