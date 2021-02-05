from unittest.mock import MagicMock, patch
from scheduleServer import app
from flask import Response
import unittest

from helperFunctions.helperFunctions import stdRet, getCurSchoolYear, AuthenticatedUser


class TestSchedule_editSched(unittest.TestCase):
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
        # Test to ensure that when a user that is NOT authorized to view
        #  the Edit Schedule Portal navigates to the page, they receive a
        #  JSON response that indicates that they are not authorized. An
        #  authorized user is a user that has an auth_level of at least
        #  2 (AHD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()

        # Reset the auth_level to 1
        self.resetAuthLevel()

        # -- Act --

        # Request the desired page.
        resp = self.server.get("/schedule/editSched",
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

    @patch("schedule.schedule.getRAStats", autospec=True)
    def test_withAuthorizedUser_callsGetRAStatsFunction(self, mocked_getRAStats):
        # Test to ensure that when an AHD that is authorized to view the
        #  Edit Schedule Portal navigates to the page, this method calls
        #  the getRAStats API.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Generate the various objects that will be used in this test
        # Configure the getRAStats mock to behave as expected. This function
        #  will be thoroughly tested in another test class.
        mocked_getRAStats.return_value = {
            1: {
                "name": "Test UserA",
                "pts": 19
            },
            2: {
                "name": "Test User",
                "pts": 1
            }
        }

        # Get the values for the start and end dates of the current school year
        start, end = getCurSchoolYear()

        # -- Act --

        # Request the desired page.
        resp = self.server.get("/schedule/editSched",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received a 200 status code
        self.assertEqual(resp.status_code, 200)

        # Assert that the response is not JSON
        self.assertFalse(resp.is_json)

        # Assert that the getRABreakStats Function was called as expected
        mocked_getRAStats.assert_called_once_with(self.helper_getAuth["hall_id"], start, end)

        # Assert that the last call to the DB was queried as expected.
        #  In this instance, we are unable to use the assert_called_once_with
        #  method as this function calls out to
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            "SELECT id, first_name, last_name, color FROM ra WHERE hall_id = %s ORDER BY first_name ASC;",
            (self.helper_getAuth["hall_id"],)
        )

        # Assert that at least one call to the DB was queried as expected.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            "SELECT duty_flag_label FROM hall_settings WHERE res_hall_id = %s",
            (self.user_hall_id,)
        )

    @patch("schedule.schedule.getRAStats", autospec=True)
    @patch("schedule.schedule.render_template", autospec=True)
    def test_withAuthorizedUser_passesExpectedDataToRenderer(self, mocked_renderTemplate, mocked_getRAStats):
        # Test to ensure that when a user that is authorized to view the
        #  Edit Schedule Portal navigates to the page, the expected information
        #  is being passed to the render_template function. An authorized user
        #  is a user that has an auth_level of at least 2 (AHD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Create some of the objects used in this test
        expectedDutyFlagLabel = "Test Label"
        expectedCustomSettingsDict = {"dutyFlagLabel": expectedDutyFlagLabel}

        # Configure the expectedCustomSettingsDict so that it is as it would
        #  appear to the renderer
        expectedCustomSettingsDict.update(self.mocked_appGlobals.baseOpts)

        # Generate the various objects that will be used in this test
        expectedRAList = []
        for i in range(10):
            expectedRAList.append((i, "User{}".format(i), "Test", "#{i}"))

        # Configure the getRAStats mock to behave as expected. This function
        #  will be thoroughly tested in another test class.
        mocked_getRAStats.return_value = {
            1: {
                "name": "Test UserA",
                "pts": 19
            },
            2: {
                "name": "Test User",
                "pts": 1
            }
        }

        # Sort alphabetically by last name of RA
        ptDictSorted = sorted(
            mocked_getRAStats.return_value.items(),
            key=lambda kv: kv[1]["name"].split(" ")[1]
        )

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedDutyFlagLabel, )   # First query is for the call to hall_settings
        ]

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            expectedRAList  # First query is for the list of all RAs
        ]

        # Configure the mocked render_template function to return a valid response object
        mocked_renderTemplate.return_value = Response(status=200)

        # -- Act --

        # Request the desired page.
        resp = self.server.get("/schedule/editSched",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received a 200 status code
        self.assertEqual(resp.status_code, 200)

        # Assert that the response is not JSON
        self.assertFalse(resp.is_json)

        # Assert that the last call to the DB was queried as expected.
        #  In this instance, we are unable to use the assert_called_once_with
        #  method as this function calls out to
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            "SELECT id, first_name, last_name, color FROM ra WHERE hall_id = %s ORDER BY first_name ASC;",
            (self.helper_getAuth["hall_id"],)
        )

        # Assert that at least one call to the DB was queried as expected.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            "SELECT duty_flag_label FROM hall_settings WHERE res_hall_id = %s",
            (self.user_hall_id,)
        )

        # Assert that the appropriate information was passed to the render_template function
        mocked_renderTemplate.assert_called_once_with(
            "schedule/editSched.html",
            raList=expectedRAList,
            auth_level=self.mocked_authLevel,
            ptDict=ptDictSorted,
            curView=3,
            opts=expectedCustomSettingsDict,
            hall_name=self.helper_getAuth["hall_name"]
        )