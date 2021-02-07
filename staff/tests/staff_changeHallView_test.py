from unittest.mock import MagicMock, patch
from scheduleServer import app
from flask import Response
import unittest

from helperFunctions.helperFunctions import AuthenticatedUser


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
        self.user_hall_id2 = 2
        self.associatedResHalls = [
            {
                "id": self.user_hall_id,
                "auth_level": self.mocked_authLevel,
                "name": "Test Hall"
            },
            {
                "id": self.user_hall_id2,
                "auth_level": self.mocked_authLevel,
                "name": "Test Hall 2"
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
        self.patcher_getAuth = patch("staff.staff.getAuth", autospec=True)

        # Start the patcher - mock returned
        self.mocked_getAuth = self.patcher_getAuth.start()

        # Configure the mocked_getAuth to return the helper_getAuth dictionary
        self.mocked_getAuth.return_value = self.helper_getAuth

        # -- Create a patcher for the appGlobals file --
        self.patcher_appGlobals = patch("staff.staff.ag", autospec=True)

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

    @patch("staff.staff.redirect", autospec=True)
    @patch("staff.staff.url_for", autospec=True)
    def test_whenProvidedHallUserIsAssociatedWith_setsProvidedHallAsSelected(self, mocked_urlFor, mocked_redirect):
        # Test to ensure that when the method is provided a hall that the user is
        #  associated with, the method sets the provided hall as the selected hall.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set the various items to be used in this test
        desiredHallID = self.user_hall_id2

        # Configure the mocked redirect function to return a valid response object
        mocked_redirect.return_value = Response(status=200)

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/staff/api/changeHallView/{}".format(desiredHallID),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was an UPDATE statement to clear out the selected halls for the user.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            """
                UPDATE staff_membership
                SET selected = false
                WHERE ra_id = %s
            """
            , (self.user_ra_id, )
        )

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was an UPDATE statement to mark the desired hall as selected.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            """
                UPDATE staff_membership
                SET selected = true
                WHERE ra_id = %s
                AND res_hall_id = %s
            """
            , (self.user_ra_id, desiredHallID)
        )

        # Assert that appGlobals.conn.commit was called
        self.mocked_appGlobals.conn.commit.assert_called_once()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that the url_for was called for the index page
        mocked_urlFor.assert_called_once_with("index")

        # Assert that a redirect was created for the index page
        mocked_redirect.assert_called_once_with(mocked_urlFor("index"))

    @patch("staff.staff.redirect", autospec=True)
    @patch("staff.staff.url_for", autospec=True)
    def test_whenProvidedHallUserIsAssociatedWith_returnsRedirectToIndex(self, mocked_urlFor, mocked_redirect):
        # Test to ensure that when provided a hall ID that the user is associated
        #  with, the method returns a redirect to the index page.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set the various items to be used in this test
        desiredHallID = self.user_hall_id2

        # Configure the mocked redirect function to return a valid response object
        mocked_redirect.return_value = Response(status=200)

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/staff/api/changeHallView/{}".format(desiredHallID),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was an UPDATE statement to clear out the selected halls for the user.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            """
                UPDATE staff_membership
                SET selected = false
                WHERE ra_id = %s
            """
            , (self.user_ra_id,)
        )

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was an UPDATE statement to mark the desired hall as selected.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            """
                UPDATE staff_membership
                SET selected = true
                WHERE ra_id = %s
                AND res_hall_id = %s
            """
            , (self.user_ra_id, desiredHallID)
        )

        # Assert that appGlobals.conn.commit was called
        self.mocked_appGlobals.conn.commit.assert_called_once()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that the url_for was called for the index page
        mocked_urlFor.assert_called_once_with("index")

        # Assert that a redirect was created for the index page
        mocked_redirect.assert_called_once_with(mocked_urlFor("index"))

    @patch("staff.staff.redirect", autospec=True)
    @patch("staff.staff.url_for", autospec=True)
    def test_whenProvidedHallUserIsNOTAssociatedWith_doesNotInteractWithDB(self, mocked_urlFor, mocked_redirect):
        # Test to ensure that when the provided hall id is not associated with the user,
        #  the method does not interact with the DB.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set the various items to be used in this test
        desiredHallID = 999

        # Configure the mocked redirect function to return a valid response object
        mocked_redirect.return_value = Response(status=200)

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/staff/api/changeHallView/{}".format(desiredHallID),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.cursor.execute was never called
        self.mocked_appGlobals.conn.cursor().execute.assert_not_called()

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

    @patch("staff.staff.redirect", autospec=True)
    @patch("staff.staff.url_for", autospec=True)
    def test_whenProvidedHallUserIsNOTAssociatedWith_returnsRedirectToIndex(self, mocked_urlFor, mocked_redirect):
        # Test to ensure that when the provided hall id is not associated with the user,
        #  the method returns a redirect to the index page.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set the various items to be used in this test
        desiredHallID = 999

        # Configure the mocked redirect function to return a valid response object
        mocked_redirect.return_value = Response(status=200)

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/staff/api/changeHallView/{}".format(desiredHallID),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.cursor.execute was never called
        self.mocked_appGlobals.conn.cursor().execute.assert_not_called()

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that the url_for was called for the index page
        mocked_urlFor.assert_called_once_with("index")

        # Assert that a redirect was created for the index page
        mocked_redirect.assert_called_once_with(mocked_urlFor("index"))
