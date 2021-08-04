from unittest.mock import MagicMock, patch
from werkzeug.exceptions import Unauthorized
import unittest

from helperFunctions.helperFunctions import getAuth


class TestHallBP_getAuth(unittest.TestCase):
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
        self.patcher_flaskLoginCurrentUser.stop()
        self.patcher_appGlobals.stop()
        self.patcher_osEnviron.stop()

        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

    def test_whenCurrentUsernameIsInDB_returnsExpectedAuthenticatedUserObject(self):
        # Test to ensure that when this method is called with a username that
        #  is in the DB, the method returns the expected Authenticated User Object.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_currentUser.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Configure the results that should be returned by the DB lookup
        expectedRAID = 1
        expectedFirstName = "Trumpets"
        expectedLastName = "Are Cool"
        expectedHallID = 42
        expectedAuthLevel = 68
        expectedResHallName = "Test Hall"
        expectedSchoolID = 46
        expectedSchoolName = "Test School"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            # First call returns the desired information which has one row
            ((expectedRAID, expectedFirstName, expectedLastName,
             expectedHallID, expectedAuthLevel, expectedResHallName,
             expectedSchoolID, expectedSchoolName),)
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
            SELECT ra.id, ra.first_name, ra.last_name, 
                   sm.res_hall_id, sm.auth_level, res_hall.name,
                   school.id, school.name
            FROM "user" JOIN ra ON ("user".ra_id = ra.id)
                        JOIN staff_membership AS sm ON (ra.id = sm.ra_id)
                        JOIN res_hall ON (sm.res_hall_id = res_hall.id)
                        JOIN school ON (school.id = res_hall.school_id)
            WHERE username = %s
            ORDER BY sm.selected DESC""", (self.username,)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that the result has the correctly selected default res hall
        self.assertEqual(result.hall_name(), expectedResHallName)
        self.assertEqual(result.hall_id(), expectedHallID)
        self.assertEqual(result.auth_level(), expectedAuthLevel)

    def test_whenCurrentUsernameIsNotInDB_returnsRedirectForErrorPage(self):
        # Test to ensure that when this method is called with a username that
        #  is NOT in the DB, the method aborts with a 401 HTTP Error.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_currentUser.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            # First call returns the desired information
            []
        ]

        # -- Act --
        # -- Assert --

        self.assertRaises(Unauthorized, getAuth)

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with(
            """
            SELECT ra.id, ra.first_name, ra.last_name, 
                   sm.res_hall_id, sm.auth_level, res_hall.name,
                   school.id, school.name
            FROM "user" JOIN ra ON ("user".ra_id = ra.id)
                        JOIN staff_membership AS sm ON (ra.id = sm.ra_id)
                        JOIN res_hall ON (sm.res_hall_id = res_hall.id)
                        JOIN school ON (school.id = res_hall.school_id)
            WHERE username = %s
            ORDER BY sm.selected DESC""", (self.username,)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

    def test_whenCurrentUsernameIsInDB_ifAssociatedWithMultipleHalls_returnsExpectedAuthenticatedUser(self):
        # Test to ensure that when this method is called with a username that
        #  is in the DB, and the ra record has multiple Res Halls that it is
        #  associated with, the method returns an Authenticated User Object
        #  with all of those halls in it and the expected one as the selected
        #  default hall.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_currentUser.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Configure the results that should be returned by the DB lookup
        expectedRAID = 1
        expectedFirstName = "Trumpets"
        expectedLastName = "Are Cool"
        expectedSchoolID = 99
        expectedSchoolName = "Test School"
        expectedHallID1 = 42
        expectedAuthLevel1 = 68
        expectedResHallName1 = "Test Hall 1"
        expectedHallID2 = 43
        expectedAuthLevel2 = 1
        expectedResHallName2 = "Test Hall 2"


        expectedResHallList = [
            {
                "id": expectedHallID1,
                "auth_level": expectedAuthLevel1,
                "name": expectedResHallName1,
                "school_id": expectedSchoolID,
                "school_name": expectedSchoolName
            },
            {
                "id": expectedHallID2,
                "auth_level": expectedAuthLevel2,
                "name": expectedResHallName2,
                "school_id": expectedSchoolID,
                "school_name": expectedSchoolName
            },
        ]

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            # First call returns the desired information which will have two rows
            ((expectedRAID, expectedFirstName, expectedLastName, expectedHallID1,
              expectedAuthLevel1, expectedResHallName1, expectedSchoolID, expectedSchoolName),
             (expectedRAID, expectedFirstName, expectedLastName, expectedHallID2,
              expectedAuthLevel2, expectedResHallName2, expectedSchoolID, expectedSchoolName)
             )
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
            SELECT ra.id, ra.first_name, ra.last_name, 
                   sm.res_hall_id, sm.auth_level, res_hall.name,
                   school.id, school.name
            FROM "user" JOIN ra ON ("user".ra_id = ra.id)
                        JOIN staff_membership AS sm ON (ra.id = sm.ra_id)
                        JOIN res_hall ON (sm.res_hall_id = res_hall.id)
                        JOIN school ON (school.id = res_hall.school_id)
            WHERE username = %s
            ORDER BY sm.selected DESC""", (self.username,)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that the result has the correctly selected default res hall
        self.assertEqual(result.hall_name(), expectedResHallName1)
        self.assertEqual(result.hall_id(), expectedHallID1)
        self.assertEqual(result.auth_level(), expectedAuthLevel1)

        # Assert that all of the res hall associations were returned
        self.assertListEqual(expectedResHallList, result.getAllAssociatedResHalls())
