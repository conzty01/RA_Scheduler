from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest

from helperFunctions.helperFunctions import stdRet, AuthenticatedUser
from conflicts.conflicts import getRAConflicts


class TestConflictBP_getRAConflicts(unittest.TestCase):
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

    # ------------------------------
    # -- Called from Client Tests --
    # ------------------------------
    def test_whenCalledFromClient_whenPassedRAID_returnsGivenRAConflictsInExpectedJSONFormat(self):
        # Test to ensure that when called from an Authorized remote client and provided an
        #  RA ID, the API returns the given RA's conflicts in a JSON format. An authorized
        #  user is considered a user whose "auth_level" is at least 2 (AHD).
        #
        #   start      <str>  -  a string representing the first day that should be included
        #                         for the returned RA conflicts.
        #   end        <str>  -  a string representing the last day that should be included
        #                         for the returned RA conflicts.
        #   raID      <int>  -  an integer denoting the row id for the RA in the
        #                        ra table whose conflicts should be returned.
        #                        If a value of -1 is passed, then all conflicts for the
        #                        user's staff will be returned.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        desiredRAID = 18
        desiredStartDate = "2021-01-01T00:00:00.000"
        desiredEndDate = "2021-02-01T00:00:00.000"

        expectedConflicts = [(i, "Test", "User", "2021-01-{:02}".format(i), "#OD1E76") for i in range(16)]

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            tuple(expectedConflicts)  # First call returns the conflicts
        ]

        expectedConflictsResult = []
        for row in expectedConflicts:
            expectedConflictsResult.append({
                "id": row[0],
                "title": row[1] + " " + row[2],
                "start": row[3],
                "color": row[4]
            })

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/conflicts/api/getRAConflicts",
                               query_string=dict(
                                   raID=desiredRAID,
                                   start=desiredStartDate,
                                   end=desiredEndDate
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with("""
        SELECT conflicts.id, ra.first_name, ra.last_name, TO_CHAR(day.date, 'YYYY-MM-DD'), ra.color
        FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                       JOIN month ON (month.id=day.month_id) 
                       JOIN ra ON (ra.id = conflicts.ra_id)
                       JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE sm.res_hall_id = %s
        AND month.year >= TO_DATE(%s, 'YYYY-MM')
        AND month.year <= TO_DATE(%s, 'YYYY-MM') 
        AND conflicts.ra_id = {};""".format(desiredRAID), (self.user_hall_id, desiredStartDate[:10], desiredEndDate[:10]))

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertListEqual(expectedConflictsResult, resp.json)

    def test_whenCalledFromClient_whenPassedNegativeRAID_returnsAllRAConflictsForHallInExpectedJSONFormat(self):
        # Test to ensure that when called from an Authorized remote client and provided a
        #  negative RA ID, the API returns the conflicts for all of the RA's on the
        #  requesting user's staff in a JSON format. An authorized user is considered a
        #  user whose "auth_level" is at least 2 (AHD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        desiredRAID = -1
        desiredStartDate = "2021-01-01T00:00:00.000"
        desiredEndDate = "2021-02-01T00:00:00.000"

        expectedConflicts = []
        for i in range(15):
            expectedConflicts.append(
                (i, "Test{}".format(i), "User{}".format(i), "2021-01-{:02}".format(i), "#OD1E76")
            )

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            tuple(expectedConflicts)  # First call returns the conflicts
        ]

        expectedConflictsResult = []
        for row in expectedConflicts:
            expectedConflictsResult.append({
                "id": row[0],
                "title": row[1] + " " + row[2],
                "start": row[3],
                "color": row[4]
            })

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/conflicts/api/getRAConflicts",
                               query_string=dict(
                                   raID=desiredRAID,
                                   start=desiredStartDate,
                                   end=desiredEndDate
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with("""
        SELECT conflicts.id, ra.first_name, ra.last_name, TO_CHAR(day.date, 'YYYY-MM-DD'), ra.color
        FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                       JOIN month ON (month.id=day.month_id) 
                       JOIN ra ON (ra.id = conflicts.ra_id)
                       JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE sm.res_hall_id = %s
        AND month.year >= TO_DATE(%s, 'YYYY-MM')
        AND month.year <= TO_DATE(%s, 'YYYY-MM') 
        ;""", (self.user_hall_id, desiredStartDate[:10], desiredEndDate[:10]))

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertListEqual(expectedConflictsResult, resp.json)

    def test_whenCalledFromClient_withUnauthorizedUser_returnsNotAuthorizedResponse(self):
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
        resp = self.server.get("/conflicts/api/getRAConflicts",
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

    # ------------------------------
    # -- Called from Server Tests --
    # ------------------------------
    def test_whenCalledFromServer_whenPassedRAID_returnsGivenRAConflictsInExpectedFormat(self):
        # Test to ensure that when called from the server and provided an RA ID, the API returns
        #  the given RA's conflicts in the expected format.
        #
        #    startDateStr  <str>  -  a string representing the first day that should be included
        #                             for the returned RA conflicts.
        #    endDateStr    <str>  -  a string representing the last day that should be included
        #                             for the returned RA conflicts.
        #    raID          <int>  -  an integer denoting the row id for the RA in the
        #                             ra table whose conflicts should be returned.
        #                             If a value of -1 is passed, then all conflicts for the
        #                             user's staff will be returned.
        #    hallID        <int>  -  an integer denoting the row id for the Res Hall
        #                             in the res_hall table whose staff conflicts should
        #                             be returned.
        #
        #  NOTE: If both the raID and hallID are provided, preference will be given
        #         to the raID with the hallID being used to verify that the user
        #         belongs to the provided Res Hall. If the user does not belong to
        #         the provided hall, then an empty list is returned.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        desiredStartDateStr = "2021-01-01"
        desiredEndDateStr = "2021-02-01"
        desiredRAID = 15
        desiredHallID = 2

        expectedConflicts = []
        for i in range(15):
            expectedConflicts.append(
                (i, "Test", "User", "2021-01-{:02}".format(i), "#OD1E76")
            )

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            tuple(expectedConflicts)  # First call returns the conflicts
        ]

        expectedConflictsResult = []
        for row in expectedConflicts:
            expectedConflictsResult.append({
                "id": row[0],
                "title": row[1] + " " + row[2],
                "start": row[3],
                "color": row[4]
            })

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/conflicts/api/getRAConflicts",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):
            # Make our call to the function
            result = getRAConflicts(desiredStartDateStr, desiredEndDateStr, desiredRAID, desiredHallID)

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with("""
        SELECT conflicts.id, ra.first_name, ra.last_name, TO_CHAR(day.date, 'YYYY-MM-DD'), ra.color
        FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                       JOIN month ON (month.id=day.month_id) 
                       JOIN ra ON (ra.id = conflicts.ra_id)
                       JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE sm.res_hall_id = %s
        AND month.year >= TO_DATE(%s, 'YYYY-MM')
        AND month.year <= TO_DATE(%s, 'YYYY-MM') 
        AND conflicts.ra_id = {};""".format(desiredRAID), (desiredHallID, desiredStartDateStr, desiredEndDateStr))

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertIsInstance(result, list)

        # Assert that we received our expected result
        self.assertListEqual(expectedConflictsResult, result)

    def test_whenCalledFromServer_whenPassedNegativeRAID_returnsAllRAConflictsForHallInExpectedFormat(self):
        # Test to ensure that when called from the server and provided a negative RA ID, the API
        #  returns the conflicts for the given HallID.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        desiredStartDateStr = "2021-01-01"
        desiredEndDateStr = "2021-02-01"
        desiredRAID = -1
        desiredHallID = 2

        expectedConflicts = []
        for i in range(15):
            expectedConflicts.append(
                (i, "Test{}".format(i), "User{}".format(i), "2021-01-{:02}".format(i), "#OD1E76")
            )

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            tuple(expectedConflicts)  # First call returns the conflicts
        ]

        expectedConflictsResult = []
        for row in expectedConflicts:
            expectedConflictsResult.append({
                "id": row[0],
                "title": row[1] + " " + row[2],
                "start": row[3],
                "color": row[4]
            })

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/conflicts/api/getRAConflicts",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):
            # Make our call to the function
            result = getRAConflicts(desiredStartDateStr, desiredEndDateStr, desiredRAID, desiredHallID)

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with("""
        SELECT conflicts.id, ra.first_name, ra.last_name, TO_CHAR(day.date, 'YYYY-MM-DD'), ra.color
        FROM conflicts JOIN day ON (conflicts.day_id = day.id)
                       JOIN month ON (month.id=day.month_id) 
                       JOIN ra ON (ra.id = conflicts.ra_id)
                       JOIN staff_membership AS sm ON (sm.ra_id = ra.id)
        WHERE sm.res_hall_id = %s
        AND month.year >= TO_DATE(%s, 'YYYY-MM')
        AND month.year <= TO_DATE(%s, 'YYYY-MM') 
        ;""", (desiredHallID, desiredStartDateStr, desiredEndDateStr))

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertIsInstance(result, list)

        # Assert that we received our expected result
        self.assertListEqual(expectedConflictsResult, result)
