from unittest.mock import MagicMock, patch
from calendar import month_name
from scheduleServer import app
import unittest

from helperFunctions.helperFunctions import stdRet, AuthenticatedUser
from hall.hall import getHallSettings


class TestHallBP_getHallSettings(unittest.TestCase):
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
        self.patcher_getAuth = patch("hall.hall.getAuth", autospec=True)

        # Start the patcher - mock returned
        self.mocked_getAuth = self.patcher_getAuth.start()

        # Configure the mocked_getAuth to return the helper_getAuth dictionary
        self.mocked_getAuth.return_value = self.helper_getAuth

        # -- Create a patcher for the appGlobals file --
        self.patcher_appGlobals = patch("hall.hall.ag", autospec=True)

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

    def buildExpectedHallSettingsDict(self, expectedHallName, expectedGCalTokenSetup, expectedStartMon, expectedEndMon,
                                      expectedDutyConfig, expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag):
        # This function will build and return the expected settings list
        #  that can be used throughout this test.
        return [
            {
                "settingName": "Residence Hall Name",
                "settingDesc": "The name of the Residence Hall.",
                "settingVal": expectedHallName,
                "settingData": expectedHallName
            },
            {
                "settingName": "Google Calendar Integration",
                "settingDesc": "Connecting a Google Calendar account allows AHDs and " +
                               "HDs to export a given month's duty schedule to Google Calendar.",
                "settingVal": "Connected" if expectedGCalTokenSetup else "Not Connected",
                "settingData": "Connected" if expectedGCalTokenSetup else "Not Connected"
            },
            {
                "settingName": "Defined School Year",
                "settingDesc": "The start and end dates that outline the beginning and end of " +
                               "the school year.",
                "settingVal": "{} - {}".format(month_name[expectedStartMon], month_name[expectedEndMon]),
                "settingData": {"start": expectedStartMon, "end": expectedEndMon}
            },
            {
                "settingName": "Duty Configuration",
                "settingDesc": "The configuration for how the duty scheduler should schedule a given " +
                               "month's duties.",
                "settingVal": "Configured",
                "settingData": expectedDutyConfig
            },
            {
                "settingName": "Automatic RA Point Adjustment",
                "settingDesc": "Automatically create point modifiers for RAs that have been excluded " +
                               "from being scheduled for duty for a given month. If enabled, the point " +
                               "modifier will be equal to the average number of points that were awarded " +
                               "for the month.",
                "settingVal": "Enabled" if expectedAutoAdjPts else "Disabled",
                "settingData": expectedAutoAdjPts
            },
            {
                "settingName": "Multi-Duty Day Flag",
                "settingDesc": "On days with multiple duties, automatically flag one duty slot with a " +
                               "customized label.",
                "settingVal": "'{}' label {}".format(expectedMDDLabel, "Enabled" if expectedMDDFlag else "Disabled"),
                "settingData": {"flag": expectedMDDFlag, "label": expectedMDDLabel}
            }
        ]

    # ------------------------------
    # -- Called from Client Tests --
    # ------------------------------
    def test_whenCalledFromClient_withAuthorizedUser_withGCalSetup_returnsSettingListInExpectedJSONFormat(self):
        # Test to ensure that when this API is called from a remote client with an
        #  authorized user, it returns the settings list in the expected JSON format.
        #  In this test, the Google Calendar Integration is being marked as being set up.
        #  An authorized user is considered a user whose "auth_level" is at least 3 (HD).
        #
        #   [
        #      {
        #         "settingName": ""
        #         "settingDesc": ""
        #         "settingVal": ""
        #      },
        #      ...
        #   ]

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        # Set various items to be used in this test
        expectedHallName = "Test Hall"
        expectedGCalTokenSetup = True
        expectedStartMon = 8
        expectedEndMon = 5
        expectedDutyConfig = {
            "test1": 1
        }
        expectedAutoAdjPts = True
        expectedMDDFlag = False
        expectedMDDLabel = "Secondary"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallName,),  # First call returns the Res Hall name
            (expectedGCalTokenSetup,),  # Second call returns whether GCal Integration
                                        #  has been set up.
            (expectedStartMon, expectedEndMon, expectedDutyConfig, expectedAutoAdjPts,
             expectedMDDFlag, expectedMDDLabel)     # Third call is for the hall_setting items
        ]

        # Build the expected returned Settings List
        expectedSettingsList = self.buildExpectedHallSettingsDict(expectedHallName, expectedGCalTokenSetup,
                                                                  expectedStartMon, expectedEndMon, expectedDutyConfig,
                                                                  expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag)

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/hall/api/getHallSettings",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertListEqual(expectedSettingsList, resp.json)

    def test_whenCalledFromClient_withAuthorizedUser_withoutGCalSetup_returnsSettingListInExpectedJSONFormat(self):
        # Test to ensure that when this API is called from a remote client with an
        #  authorized user, it returns the settings list in the expected JSON format.
        #  In this test, the Google Calendar Integration is being marked as NOT
        #  being set up. An authorized user is considered a user whose "auth_level"
        #  is at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        # Set various items to be used in this test
        expectedHallName = "Test Hall"
        expectedGCalTokenSetup = False
        expectedStartMon = 8
        expectedEndMon = 5
        expectedDutyConfig = {
            "test1": 1
        }
        expectedAutoAdjPts = True
        expectedMDDFlag = False
        expectedMDDLabel = "Secondary"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallName,),  # First call returns the Res Hall name
            (expectedGCalTokenSetup,),  # Second call returns whether GCal Integration
            #  has been set up.
            (expectedStartMon, expectedEndMon, expectedDutyConfig, expectedAutoAdjPts,
             expectedMDDFlag, expectedMDDLabel)  # Third call is for the hall_setting items
        ]

        # Build the expected returned Settings List
        expectedSettingsList = self.buildExpectedHallSettingsDict(expectedHallName, expectedGCalTokenSetup,
                                                                  expectedStartMon, expectedEndMon, expectedDutyConfig,
                                                                  expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag)

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/hall/api/getHallSettings",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertListEqual(expectedSettingsList, resp.json)

    def test_whenCalledFromClient_withUnAuthorizedUser_returnsNotAuthorizedResponse(self):
        # Test to ensure that when a user that is NOT authorized to view
        #  the Manage Hall page, they receive a JSON response that indicates
        #  that they are not authorized. An authorized user is a user that
        #  has an auth_level of at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/hall/api/getHallSettings",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(-1, "NOT AUTHORIZED"), resp.json)

    def test_whenCalledFromClient_withAuthorizedUser_withAutoAdjRAPts_returnsSettingListInExpectedJSONFormat(self):
        # Test to ensure that when this API is called from a remote client with an
        #  authorized user, it returns the settings list in the expected JSON format.
        #  In this test, the Auto Adjust RA Pts setting is being marked as enabled.
        #  An authorized user is considered a user whose "auth_level" is at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        # Set various items to be used in this test
        expectedHallName = "Test Hall"
        expectedGCalTokenSetup = False
        expectedStartMon = 8
        expectedEndMon = 5
        expectedDutyConfig = {
            "test1": 1
        }
        expectedAutoAdjPts = True
        expectedMDDFlag = False
        expectedMDDLabel = "Secondary"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallName,),  # First call returns the Res Hall name
            (expectedGCalTokenSetup,),  # Second call returns whether GCal Integration
            #  has been set up.
            (expectedStartMon, expectedEndMon, expectedDutyConfig, expectedAutoAdjPts,
             expectedMDDFlag, expectedMDDLabel)  # Third call is for the hall_setting items
        ]

        # Build the expected returned Settings List
        expectedSettingsList = self.buildExpectedHallSettingsDict(expectedHallName, expectedGCalTokenSetup,
                                                                  expectedStartMon, expectedEndMon, expectedDutyConfig,
                                                                  expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag)

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/hall/api/getHallSettings",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertListEqual(expectedSettingsList, resp.json)

    def test_whenCalledFromClient_withAuthorizedUser_withoutAutoAdjRAPts_returnsSettingListInExpectedJSONFormat(self):
        # Test to ensure that when this API is called from a remote client with an
        #  authorized user, it returns the settings list in the expected JSON format.
        #  In this test, the Auto Adjust RA Pts setting is being marked as disabled.
        #  An authorized user is considered a user whose "auth_level" is at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        # Set various items to be used in this test
        expectedHallName = "Test Hall"
        expectedGCalTokenSetup = False
        expectedStartMon = 8
        expectedEndMon = 5
        expectedDutyConfig = {
            "test1": 1
        }
        expectedAutoAdjPts = False
        expectedMDDFlag = False
        expectedMDDLabel = "Secondary"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallName,),  # First call returns the Res Hall name
            (expectedGCalTokenSetup,),  # Second call returns whether GCal Integration
            #  has been set up.
            (expectedStartMon, expectedEndMon, expectedDutyConfig, expectedAutoAdjPts,
             expectedMDDFlag, expectedMDDLabel)  # Third call is for the hall_setting items
        ]

        # Build the expected returned Settings List
        expectedSettingsList = self.buildExpectedHallSettingsDict(expectedHallName, expectedGCalTokenSetup,
                                                                  expectedStartMon, expectedEndMon, expectedDutyConfig,
                                                                  expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag)

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/hall/api/getHallSettings",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertListEqual(expectedSettingsList, resp.json)

    def test_whenCalledFromClient_withAuthorizedUser_withMultiDutyFlags_returnsSettingListInExpectedJSONFormat(self):
        # Test to ensure that when this API is called from a remote client with an
        #  authorized user, it returns the settings list in the expected JSON format.
        #  In this test, the Multi-Duty Day Flag setting is being marked as enabled.
        #  An authorized user is considered a user whose "auth_level" is at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        # Set various items to be used in this test
        expectedHallName = "Test Hall"
        expectedGCalTokenSetup = False
        expectedStartMon = 8
        expectedEndMon = 5
        expectedDutyConfig = {
            "test1": 1
        }
        expectedAutoAdjPts = True
        expectedMDDFlag = True
        expectedMDDLabel = "Secondary"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallName,),  # First call returns the Res Hall name
            (expectedGCalTokenSetup,),  # Second call returns whether GCal Integration
            #  has been set up.
            (expectedStartMon, expectedEndMon, expectedDutyConfig, expectedAutoAdjPts,
             expectedMDDFlag, expectedMDDLabel)  # Third call is for the hall_setting items
        ]

        # Build the expected returned Settings List
        expectedSettingsList = self.buildExpectedHallSettingsDict(expectedHallName, expectedGCalTokenSetup,
                                                                  expectedStartMon, expectedEndMon, expectedDutyConfig,
                                                                  expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag)

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/hall/api/getHallSettings",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertListEqual(expectedSettingsList, resp.json)

    def test_whenCalledFromClient_withAuthorizedUser_withoutMultiDutyFlags_returnsSettingListInExpectedJSONFormat(self):
        # Test to ensure that when this API is called from a remote client with an
        #  authorized user, it returns the settings list in the expected JSON format.
        #  In this test, the Multi-Duty Day Flag setting is being marked as disabled.
        #  An authorized user is considered a user whose "auth_level" is at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        # Set various items to be used in this test
        expectedHallName = "Test Hall"
        expectedGCalTokenSetup = False
        expectedStartMon = 8
        expectedEndMon = 5
        expectedDutyConfig = {
            "test1": 1
        }
        expectedAutoAdjPts = True
        expectedMDDFlag = False
        expectedMDDLabel = "On Call"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallName,),  # First call returns the Res Hall name
            (expectedGCalTokenSetup,),  # Second call returns whether GCal Integration
            #  has been set up.
            (expectedStartMon, expectedEndMon, expectedDutyConfig, expectedAutoAdjPts,
             expectedMDDFlag, expectedMDDLabel)  # Third call is for the hall_setting items
        ]

        # Build the expected returned Settings List
        expectedSettingsList = self.buildExpectedHallSettingsDict(expectedHallName, expectedGCalTokenSetup,
                                                                  expectedStartMon, expectedEndMon, expectedDutyConfig,
                                                                  expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag)

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/hall/api/getHallSettings",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertListEqual(expectedSettingsList, resp.json)

    # ------------------------------
    # -- Called from Server Tests --
    # ------------------------------
    def test_whenCalledFromServer_withoutGCalSetup_returnsSettingListInExpectedFormat(self):
        # Test to ensure that when this API is called from a remote client with an
        #  authorized user, it returns the settings list in the expected JSON format.
        #  In this test, the Google Calendar Integration is being marked as NOT
        #  being set up. An authorized user is considered a user whose "auth_level"
        #  is at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set various items to be used in this test
        expectedHallName = "Test Hall"
        expectedGCalTokenSetup = False
        expectedStartMon = 8
        expectedEndMon = 5
        expectedDutyConfig = {
            "test1": 1
        }
        expectedAutoAdjPts = True
        expectedMDDFlag = False
        expectedMDDLabel = "Secondary"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallName,),  # First call returns the Res Hall name
            (expectedGCalTokenSetup,),  # Second call returns whether GCal Integration
            #  has been set up.
            (expectedStartMon, expectedEndMon, expectedDutyConfig, expectedAutoAdjPts,
             expectedMDDFlag, expectedMDDLabel)  # Third call is for the hall_setting items
        ]

        # Build the expected returned Settings List
        expectedSettingsList = self.buildExpectedHallSettingsDict(expectedHallName, expectedGCalTokenSetup,
                                                                  expectedStartMon, expectedEndMon, expectedDutyConfig,
                                                                  expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag)

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/conflicts/api/getRAConflicts",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):
            # Make our call to the function
            result = getHallSettings(self.user_hall_id)

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received our expected result
        self.assertListEqual(expectedSettingsList, result)

    def test_whenCalledFromServer_withGCalSetup_returnsSettingListInExpectedFormat(self):
        # Test to ensure that when this API is called from a remote client with an
        #  authorized user, it returns the settings list in the expected JSON format.
        #  In this test, the Google Calendar Integration is being marked as being set
        #  up. An authorized user is considered a user whose "auth_level"  is at least
        #  3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set various items to be used in this test
        expectedHallName = "Test Hall"
        expectedGCalTokenSetup = True
        expectedStartMon = 8
        expectedEndMon = 5
        expectedDutyConfig = {
            "test1": 1
        }
        expectedAutoAdjPts = True
        expectedMDDFlag = False
        expectedMDDLabel = "Secondary"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallName,),  # First call returns the Res Hall name
            (expectedGCalTokenSetup,),  # Second call returns whether GCal Integration
            #  has been set up.
            (expectedStartMon, expectedEndMon, expectedDutyConfig, expectedAutoAdjPts,
             expectedMDDFlag, expectedMDDLabel)  # Third call is for the hall_setting items
        ]

        # Build the expected returned Settings List
        expectedSettingsList = self.buildExpectedHallSettingsDict(expectedHallName, expectedGCalTokenSetup,
                                                                  expectedStartMon, expectedEndMon, expectedDutyConfig,
                                                                  expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag)

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/conflicts/api/getRAConflicts",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):
            # Make our call to the function
            result = getHallSettings(self.user_hall_id)

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received our expected result
        self.assertListEqual(expectedSettingsList, result)

    def test_whenCalledFromServer_withAutoAdjRAPts_returnsSettingListInExpectedFormat(self):
        # Test to ensure that when this API is called from the server it returns the
        #  settings list in the expected JSON format. In this test, the Auto Adjust RA
        #  Pts Flag setting is being marked as enabled.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set various items to be used in this test
        expectedHallName = "Test Hall"
        expectedGCalTokenSetup = True
        expectedStartMon = 8
        expectedEndMon = 5
        expectedDutyConfig = {
            "test1": 1
        }
        expectedAutoAdjPts = True
        expectedMDDFlag = False
        expectedMDDLabel = "Primary"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallName,),  # First call returns the Res Hall name
            (expectedGCalTokenSetup,),  # Second call returns whether GCal Integration
            #  has been set up.
            (expectedStartMon, expectedEndMon, expectedDutyConfig, expectedAutoAdjPts,
             expectedMDDFlag, expectedMDDLabel)  # Third call is for the hall_setting items
        ]

        # Build the expected returned Settings List
        expectedSettingsList = self.buildExpectedHallSettingsDict(expectedHallName, expectedGCalTokenSetup,
                                                                  expectedStartMon, expectedEndMon, expectedDutyConfig,
                                                                  expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag)

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/conflicts/api/getRAConflicts",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):
            # Make our call to the function
            result = getHallSettings(self.user_hall_id)

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received our expected result
        self.assertListEqual(expectedSettingsList, result)

    def test_whenCalledFromServer_withoutAutoAdjRAPts_returnsSettingListInExpectedFormat(self):
        # Test to ensure that when this API is called from the server it returns the
        #  settings list in the expected JSON format. In this test, the Auto Adjust RA
        #  Pts Flag setting is being marked as disabled.
        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set various items to be used in this test
        expectedHallName = "Test Hall"
        expectedGCalTokenSetup = True
        expectedStartMon = 8
        expectedEndMon = 5
        expectedDutyConfig = {
            "test1": 1
        }
        expectedAutoAdjPts = False
        expectedMDDFlag = False
        expectedMDDLabel = "Primary"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallName,),  # First call returns the Res Hall name
            (expectedGCalTokenSetup,),  # Second call returns whether GCal Integration
            #  has been set up.
            (expectedStartMon, expectedEndMon, expectedDutyConfig, expectedAutoAdjPts,
             expectedMDDFlag, expectedMDDLabel)  # Third call is for the hall_setting items
        ]

        # Build the expected returned Settings List
        expectedSettingsList = self.buildExpectedHallSettingsDict(expectedHallName, expectedGCalTokenSetup,
                                                                  expectedStartMon, expectedEndMon, expectedDutyConfig,
                                                                  expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag)

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/conflicts/api/getRAConflicts",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):
            # Make our call to the function
            result = getHallSettings(self.user_hall_id)

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received our expected result
        self.assertListEqual(expectedSettingsList, result)

    def test_whenCalledFromServer_withMultiDutyFlags_returnsSettingListInExpectedFormat(self):
        # Test to ensure that when this API is called from the server it returns the
        #  settings list in the expected JSON format. In this test, the Multi-Duty Day
        #  Flag setting is being marked as enabled.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set various items to be used in this test
        expectedHallName = "Test Hall"
        expectedGCalTokenSetup = True
        expectedStartMon = 8
        expectedEndMon = 5
        expectedDutyConfig = {
            "test1": 1
        }
        expectedAutoAdjPts = True
        expectedMDDFlag = True
        expectedMDDLabel = "At Desk"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallName,),  # First call returns the Res Hall name
            (expectedGCalTokenSetup,),  # Second call returns whether GCal Integration
            #  has been set up.
            (expectedStartMon, expectedEndMon, expectedDutyConfig, expectedAutoAdjPts,
             expectedMDDFlag, expectedMDDLabel)  # Third call is for the hall_setting items
        ]

        # Build the expected returned Settings List
        expectedSettingsList = self.buildExpectedHallSettingsDict(expectedHallName, expectedGCalTokenSetup,
                                                                  expectedStartMon, expectedEndMon, expectedDutyConfig,
                                                                  expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag)

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/conflicts/api/getRAConflicts",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):
            # Make our call to the function
            result = getHallSettings(self.user_hall_id)

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received our expected result
        self.assertListEqual(expectedSettingsList, result)

    def test_whenCalledFromServer_withoutMultiDutyFlags_returnsSettingListInExpectedFormat(self):
        # Test to ensure that when this API is called from the server it returns the
        #  settings list in the expected JSON format. In this test, the Multi-Duty Day
        #  Flag setting is being marked as disabled.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set various items to be used in this test
        expectedHallName = "Test Hall"
        expectedGCalTokenSetup = True
        expectedStartMon = 8
        expectedEndMon = 5
        expectedDutyConfig = {
            "test1": 1
        }
        expectedAutoAdjPts = True
        expectedMDDFlag = False
        expectedMDDLabel = "Primary"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallName,),  # First call returns the Res Hall name
            (expectedGCalTokenSetup,),  # Second call returns whether GCal Integration
            #  has been set up.
            (expectedStartMon, expectedEndMon, expectedDutyConfig, expectedAutoAdjPts,
             expectedMDDFlag, expectedMDDLabel)  # Third call is for the hall_setting items
        ]

        # Build the expected returned Settings List
        expectedSettingsList = self.buildExpectedHallSettingsDict(expectedHallName, expectedGCalTokenSetup,
                                                                  expectedStartMon, expectedEndMon, expectedDutyConfig,
                                                                  expectedAutoAdjPts, expectedMDDLabel, expectedMDDFlag)

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/conflicts/api/getRAConflicts",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):
            # Make our call to the function
            result = getHallSettings(self.user_hall_id)

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received our expected result
        self.assertListEqual(expectedSettingsList, result)
