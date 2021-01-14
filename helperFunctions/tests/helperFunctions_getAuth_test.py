from unittest.mock import MagicMock, patch
import unittest

from helperFunctions.helperFunctions import getAuth


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

        # -- Create a patcher for the appGlobals file --
        self.patcher_appGlobals = patch("helperFunctions.helperFunctions.ag", autospec=True)

        # Start the patcher - mock returned
        self.mocked_appGlobals = self.patcher_appGlobals.start()

        # Configure the mocked appGlobals as desired
        self.mocked_appGlobals.baseOpts = {"HOST_URL": "https://localhost:5000"}
        self.mocked_appGlobals.conn = MagicMock()
        self.mocked_appGlobals.UPLOAD_FOLDER = "./static"
        self.mocked_appGlobals.ALLOWED_EXTENSIONS = {"txt", "csv"}

        # -- Create a patcher for the flask_login.current_user object --
        self.patcher_flaskLoginCurrentUser = patch("helperFunctions.helperFunctions.current_user", autospec=True)

        # Start the patcher - mock returned
        self.mocked_currentUser = self.patcher_flaskLoginCurrentUser.start()

        # Configure the mocked current_user as desired
        self.username = "Test User"
        self.mocked_currentUser.username = self.username

        # -- Create a patcher for the flask.url_for function --
        self.patcher_flaskURLFor = patch("helperFunctions.helperFunctions.url_for", autospec=True)

        # Start the patcher - mock returned
        self.mocked_urlFor = self.patcher_flaskURLFor.start()

        # -- Create a patcher for the flask.redirect function --
        self.patcher_flaskRedirect = patch("helperFunctions.helperFunctions.redirect", autospec=True)

        # Start the patcher - mock returned
        self.mocked_redirect = self.patcher_flaskRedirect.start()

    def tearDown(self):
        # Stop all of the patchers
        self.patcher_flaskLoginCurrentUser.stop()
        self.patcher_flaskRedirect.stop()
        self.patcher_flaskURLFor.stop()
        self.patcher_appGlobals.stop()
        self.patcher_osEnviron.stop()

    def test_whenCurrentUsernameIsInDB_returnsExpectedDictionary(self):
        # Test to ensure that when this method is called with a username that
        #  is in the DB, the method returns the expected dictionary

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_currentUser.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Configure the results that should be returned by the DB lookup
        expectedRAID = 1
        expectedUsername = self.username
        expectedFirstName = "Trumpets"
        expectedLastName = "Are Cool"
        expectedHallID = 42
        expectedAuthLevel = 68
        expectedResHallName = "Test Hall"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            # First call returns the desired information
            (expectedRAID, expectedUsername, expectedFirstName,
             expectedLastName, expectedHallID, expectedAuthLevel, expectedResHallName)
        ]

        # Create the expected result
        expectedResult = {
            "uEmail": expectedUsername,
            "ra_id": expectedRAID,
            "name": expectedFirstName + " " + expectedLastName,
            "hall_id": expectedHallID,
            "auth_level": expectedAuthLevel,
            "hall_name": expectedResHallName
        }

        # -- Act --

        # Call getAuth()
        result = getAuth()

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with(
            """
            SELECT ra.id, username, first_name, last_name, hall_id, auth_level, res_hall.name
            FROM "user" JOIN ra ON ("user".ra_id = ra.id)
                        JOIN res_hall ON (ra.hall_id = res_hall.id)
            WHERE username = %s;""", (self.username,)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that the result is as expected
        self.assertDictEqual(expectedResult, result)

    def test_whenCurrentUsernameIsNotInDB_returnsRedirectForErrorPage(self):
        # Test to ensure that when this method is called with a username that
        #  is NOT in the DB, the method returns a redirect for the Error page.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_currentUser.reset_mock()
        self.mocked_urlFor.reset_mock()
        self.mocked_redirect.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            # First call returns the desired information
            None
        ]

        # -- Act --

        # Call getAuth()
        result = getAuth()

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with(
            """
            SELECT ra.id, username, first_name, last_name, hall_id, auth_level, res_hall.name
            FROM "user" JOIN ra ON ("user".ra_id = ra.id)
                        JOIN res_hall ON (ra.hall_id = res_hall.id)
            WHERE username = %s;""", (self.username,)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that the url for the error page was looked up
        self.mocked_urlFor.assert_called_once_with(
            "err",
            msg="No user found with email: {}".format(self.username)
        )

        # Assert that a redirect for the error page was created
        self.mocked_redirect.assert_called_once_with(self.mocked_urlFor(""))

        # Assert that the redirect that was created was returned by the method
        self.assertEqual(self.mocked_redirect(""), result)
