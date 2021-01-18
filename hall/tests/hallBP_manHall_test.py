from unittest.mock import MagicMock, patch
from scheduleServer import app
from flask import Response
import unittest

from helperFunctions.helperFunctions import stdRet


class TestHallBP_manHall(unittest.TestCase):
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

    def tearDown(self):
        # Stop all of the patchers
        self.patcher_getAuth.stop()
        self.patcher_appGlobals.stop()
        self.patcher_osEnviron.stop()

    def resetAuthLevel(self):
        # This function serves to reset the auth_level of the session
        #  to the default value which is 1.
        self.mocked_authLevel.return_value = 1

    @patch("hall.hall.render_template", autospec=True)
    @patch("hall.hall.getHallSettings", autospec=True)
    def test_withAuthorizedHDUser_rendersAppropriateTemplate(self, mocked_hallSettings, mocked_renderTemplate):
        # Test to ensure that when an HD that is authorized to view
        #  the Manage Hall page navigates to the page, they are able
        #  to see a rendered template of the page. An authorized user
        #  is a user that has an auth_level of at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 3
        self.mocked_authLevel.return_value = 3

        # Configure the mocked render_template function to return a valid response object
        mocked_renderTemplate.return_value = Response(status=200)

        # -- Act --

        # Request the desired page.
        resp = self.server.get("/hall/", base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received a 200 status code
        self.assertEqual(resp.status_code, 200)

        # Assert that the response is not JSON
        self.assertFalse(resp.is_json)

    @patch("hall.hall.render_template", autospec=True)
    @patch("hall.hall.getHallSettings", autospec=True)
    def test_withUnauthorizedHDUser_returnsNotAuthorizedResponse(self, mocked_hallSettings, mocked_renderTemplate):
        # Test to ensure that when a user that is NOT authorized to view
        #  the Manage Hall page, they receive a JSON response that indicates
        #  that they are not authorized. An authorized user is a user that
        #  has an auth_level of at least 2 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # -- Act --

        # Request the desired page.
        resp = self.server.get("/hall/", base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received a 200 status code
        self.assertEqual(resp.status_code, 200)

        # Assert that the response is not JSON
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(-1, "NOT AUTHORIZED"), resp.json)

    @patch("hall.hall.render_template", autospec=True)
    @patch("hall.hall.getHallSettings", autospec=True)
    def test_withAuthorizedHDUser_PassesExpectedDataToRenderer(self, mocked_hallSettings, mocked_renderTemplate):
        # Test to ensure that when an HD that is authorized to view the
        #  Manage Hall page navigates to the page, the expected information
        #  is being passed to the render_template function. An authorized user
        #  is a user that has an auth_level of at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 3
        self.mocked_authLevel.return_value = 3

        # Configure the mocked render_template function to return a valid response object
        mocked_renderTemplate.return_value = Response(status=200)

        # -- Act --

        # Request the desired page.
        resp = self.server.get("/hall/", base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received a 200 status code
        self.assertEqual(resp.status_code, 200)

        # Assert that the response is not JSON
        self.assertFalse(resp.is_json)

        # Assert that render_template was called with the expected data
        mocked_renderTemplate.assert_called_once_with(
            "hall/hall.html",
            opts=self.mocked_appGlobals.baseOpts,
            curView=4,
            settingList=mocked_hallSettings(),
            auth_level=self.mocked_authLevel,
            hall_name=self.helper_getAuth["hall_name"]
        )