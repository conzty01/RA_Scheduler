from unittest.mock import MagicMock, patch
from scheduleServer import app
from flask import Response
import unittest
import datetime

from helperFunctions.helperFunctions import AuthenticatedUser


class TestConflictBP_conflicts(unittest.TestCase):
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
        self.user_school_id = 1
        self.associatedResHalls = [
            {
                "id": self.user_hall_id,
                "auth_level": self.mocked_authLevel,
                "name": "Test Hall",
                "school_id": self.user_school_id,
                "school_name": "Test School"
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
        self.patcher_getAuth = patch("conflicts.conflicts.getAuth", autospec=True)

        # Start the patcher - mock returned
        self.mocked_getAuth = self.patcher_getAuth.start()

        # Configure the mocked_getAuth to return the helper_getAuth dictionary
        self.mocked_getAuth.return_value = self.helper_getAuth

        # -- Create a patcher for the appGlobals file --
        self.patcher_appGlobals = patch("conflicts.conflicts.ag", autospec=True)

        # Start the patcher - mock returned
        self.mocked_appGlobals = self.patcher_appGlobals.start()

        # Configure the mocked appGlobals as desired
        self.mocked_appGlobals.baseOpts = {"HOST_URL": "https://localhost:5000"}
        self.mocked_appGlobals.conn = MagicMock()
        self.mocked_appGlobals.UPLOAD_FOLDER = "./static"
        self.mocked_appGlobals.ALLOWED_EXTENSIONS = {"txt", "csv"}

        # Create a patcher for the getCurSchoolYear method
        self.patcher_getCurSchoolYear = patch("breaks.breaks.getCurSchoolYear", autospec=True)

        # Start the patcher - mock returned
        self.mocked_getCurSchoolYear = self.patcher_getCurSchoolYear.start()

        # Configure the mocked getCurSchoolYear
        self.helper_schoolYearStart = datetime.date(2021, 8, 1)
        self.helper_schoolYearEnd = datetime.date(2022, 7, 31)
        self.mocked_getCurSchoolYear.return_value = (self.helper_schoolYearStart, self.helper_schoolYearEnd)

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
        self.patcher_getCurSchoolYear.stop()

        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

    def resetAuthLevel(self):
        # This function serves to reset the auth_level of the session
        #  to the default value which is 1.
        self.mocked_authLevel.return_value = 1

    def test_withLoggedInUser_RendersAppropriateTemplate(self):
        # Test to ensure that when a user that is logged in
        #  navigates to the page, they are able to see a rendered
        #  template of the conflicts. Users that are not logged in
        #  are handled by the helperFunction getAuth() which is not
        #  not being tested in this test Class.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Reset the auth_level
        self.resetAuthLevel()

        # -- Act --

        # Request the desired page.
        resp = self.server.get("/conflicts/",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received a 200 status code
        self.assertEqual(resp.status_code, 200)

        # Assert that the response is not JSON
        self.assertFalse(resp.is_json)

    @patch("conflicts.conflicts.render_template", autospec=True)
    def test_withLoggedInUser_PassesExpectedDataToRenderer(self, mocked_renderTemplate):
        # Test to ensure that when a user that is logged in navigates
        #  to the page, the expected information is being passed to
        #  the render_template function.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Reset the auth_level
        self.resetAuthLevel()

        # Configure the mocked render_template function to return a valid response object
        mocked_renderTemplate.return_value = Response(status=200)

        # Create a custom settings dict for the options
        custSettings = {
            "yearStart": self.helper_schoolYearStart,
            "yearEnd": self.helper_schoolYearEnd
        }

        # Merge the base options into the custom settings dictionary to simplify passing
        #  settings into the template renderer.
        custSettings.update(self.mocked_appGlobals.baseOpts)

        # -- Act --

        # Request the desired page.
        resp = self.server.get("/conflicts/",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received a 200 status code
        self.assertEqual(resp.status_code, 200)

        # Assert that the response is not JSON
        self.assertFalse(resp.is_json)

        # Assert that render_template was called with the expected data
        mocked_renderTemplate.assert_called_once_with(
            "conflicts/conflicts.html",
            auth_level=self.mocked_authLevel,
            curView=2,
            opts=custSettings,
            hall_name=self.helper_getAuth.hall_name(),
            linkedHalls=self.helper_getAuth.getAllAssociatedResHalls()
        )
