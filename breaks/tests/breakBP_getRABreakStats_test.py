from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest

from breaks.breaks import getRABreakStats


class TestBreakBP_getRABreakStats(unittest.TestCase):
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
        self.patcher_getAuth = patch("breaks.breaks.getAuth", autospec=True)

        # Start the patcher - mock returned
        self.mocked_getAuth = self.patcher_getAuth.start()

        # Configure the mocked_getAuth to return the helper_getAuth dictionary
        self.mocked_getAuth.return_value = self.helper_getAuth

        # -- Create a patcher for the appGlobals file --
        self.patcher_appGlobals = patch("breaks.breaks.ag", autospec=True)

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

    # ------------------------------
    # -- Called from Client Tests --
    # ------------------------------
    def test_whenCalledFromClient_returnsStatsInExpectedJSONFormat(self):
        # Test to ensure that when this API is called from a remote client
        #  it accepts the below parameters and returns the statistics in
        #  the expected JSON format.
        #
        #   start  <str>  -  a string representing the first day that should be included
        #                     for the break duty count calculation.
        #   end    <str>  -  a string representing the last day that should be included
        #                     for the duty count calculation.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Reset the auth_level
        self.resetAuthLevel()

        # Create some dummy break statistics to be returned by the DB
        breakDutyStatistics = []
        for i in range(20):
            breakDutyStatistics.append((
                i,                      # ra.id
                "Test{}".format(i),     # ra.first_name
                "User{}".format(i),     # ra.last_name
                20 - i                  # Number of Break Duties
            ))

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            # First call returns the break duty statistics
            tuple(breakDutyStatistics)
        ]

        # Set the start and end strings
        desiredStartStr = "2020-08-01"
        desiredEndStr = "2021-07-31"

        # Create a dictionary that represents the expected result from this API
        expectedBreakStatisticResult = {}
        for ra in breakDutyStatistics:
            # The keys for the dictionary need to be strings as that is the datatype
            #  that jsonify converts them to.
            expectedBreakStatisticResult[str(ra[0])] = {
                "name": ra[1] + " " + ra[2],
                "count": ra[3]
            }

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/breaks/api/getRABreakStats",
                               query_string=dict(
                                   start=desiredStartStr,
                                   end=desiredEndStr
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with(
            """SELECT ra.id, ra.first_name, ra.last_name, COALESCE(numQuery.count, 0)
                   FROM (SELECT ra.id AS rid, COUNT(break_duties.id) AS count
                         FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                                           JOIN ra ON (ra.id=break_duties.ra_id)
                         WHERE break_duties.hall_id = %s
                         AND day.date BETWEEN TO_DATE(%s, 'YYYY-MM-DD')
                                          AND TO_DATE(%s, 'YYYY-MM-DD')
                        GROUP BY rid) AS numQuery
                   RIGHT JOIN ra ON (numQuery.rid = ra.id)
                   WHERE ra.hall_id = %s;""",
            (self.user_hall_id, desiredStartStr, desiredEndStr, self.user_hall_id)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertDictEqual(expectedBreakStatisticResult, resp.json)

    # ------------------------------
    # -- Called from Server Tests --
    # ------------------------------
    def test_whenCalledFromServer_returnsStatsInExpectedFormat(self):
        # Test to ensure that when this API is called from the server
        #  it accepts the below parameters and returns the statistics in
        #  the expected format.
        #
        #   hallId        <int>  -  an integer representing the id of the desired residence
        #                            hall in the res_hall table.
        #   startDateStr  <str>  -  a string representing the first day that should be included
        #                            for the duty points calculation.
        #   endDateStr    <str>  -  a string representing the last day that should be included
        #                            for the duty points calculation.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Create some dummy break statistics to be returned by the DB
        breakDutyStatistics = []
        for i in range(30):
            breakDutyStatistics.append((
                i,  # ra.id
                "Test{}".format(i),  # ra.first_name
                "User{}".format(i),  # ra.last_name
                30 - i  # Number of Break Duties
            ))

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            # First call returns the break duty statistics
            tuple(breakDutyStatistics)
        ]

        # Set the start and end strings
        desiredStartStr = "2020-08-01"
        desiredEndStr = "2021-07-31"

        # Create a dictionary that represents the expected result from this API
        expectedBreakStatisticResult = {}
        for ra in breakDutyStatistics:
            expectedBreakStatisticResult[ra[0]] = {
                "name": ra[1] + " " + ra[2],
                "count": ra[3]
            }

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/breaks/api/getRABreakStats",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):

            # Make our call to the function
            result = getRABreakStats(self.user_hall_id, desiredStartStr, desiredEndStr)

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with(
            """SELECT ra.id, ra.first_name, ra.last_name, COALESCE(numQuery.count, 0)
                   FROM (SELECT ra.id AS rid, COUNT(break_duties.id) AS count
                         FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                                           JOIN ra ON (ra.id=break_duties.ra_id)
                         WHERE break_duties.hall_id = %s
                         AND day.date BETWEEN TO_DATE(%s, 'YYYY-MM-DD')
                                          AND TO_DATE(%s, 'YYYY-MM-DD')
                        GROUP BY rid) AS numQuery
                   RIGHT JOIN ra ON (numQuery.rid = ra.id)
                   WHERE ra.hall_id = %s;""",
            (self.user_hall_id, desiredStartStr, desiredEndStr, self.user_hall_id)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received our expected result
        self.assertDictEqual(expectedBreakStatisticResult, result)
