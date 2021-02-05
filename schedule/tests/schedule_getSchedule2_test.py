from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest

from schedule.schedule import getSchedule2
from helperFunctions.helperFunctions import AuthenticatedUser


class TestSchedule_getSchedule2(unittest.TestCase):
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

    # ------------------------------
    # -- Called from Client Tests --
    # ------------------------------
    def test_whenCalledFromClient_returnsScheduleInExpectedJSONFormat(self):
        # Test to ensure that when called from a remote client, the function
        #  returns the appropriate schedule in the expected JSON format.
        #
        #     [
        #        {
        #           "id": <ra.id>,
        #           "title": <ra.first_name> + " " + <ra.last_name>,
        #           "start": <day.date>,
        #           "color": <ra.color or "#2C3E50">,
        #           "extendedProps": {
        #               "dutyType": "std",
        #               "flagged": <duties.flagged>,
        #               "pts": <duties.point_val>
        #           }
        #        }
        #     ]

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Create the schedule information that will be returned by the query call
        expectedScheduleInfoList = []
        for i in range(1, 7):
            expectedScheduleInfoList.append(
                (
                    "Test {}".format(i),
                    "User {}".format(i),
                    "#{:06}".format(i),
                    i,
                    '2021-02-{:02}'.format(i),
                    False,
                    1
                )
            )

        # Create the expected result
        expectedResult = []
        for row in expectedScheduleInfoList:
            expectedResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": row[2],
                "extendedProps": {
                    "dutyType": "std",
                    "flagged": row[5],
                    "pts": row[6]
                }
            })

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            expectedScheduleInfoList,  # First query returns the schedule information
        ]

        desiredStartStr = '2021-02-01T00:00:00-05:00'
        desiredEndStr = '2021-03-01T00:00:00-05:00'
        desiredShowAllColors = "true"

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/schedule/api/getSchedule",
                               query_string=dict(
                                   start=desiredStartStr,
                                   end=desiredEndStr,
                                   allColors=desiredShowAllColors
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the last time appGlobals.conn.cursor().execute was called,
        #  it was a query for the RA.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with(
            """
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD'),
               duties.flagged, duties.point_val
        FROM duties JOIN day ON (day.id=duties.day_id)
                    JOIN RA ON (ra.id=duties.ra_id)
        WHERE duties.hall_id = %s
        AND duties.sched_id IN
                (
                SELECT DISTINCT ON (schedule.month_id) schedule.id
                FROM schedule
                WHERE schedule.hall_id = %s
                AND schedule.month_id IN
                    (
                        SELECT month.id
                        FROM month
                        WHERE month.year >= TO_DATE(%s,'YYYY-MM')
                        AND month.year <= TO_DATE(%s,'YYYY-MM')
                    )
                ORDER BY schedule.month_id, schedule.created DESC, schedule.id DESC
                )
        AND day.date >= TO_DATE(%s,'YYYY-MM-DD')
        AND day.date <= TO_DATE(%s,'YYYY-MM-DD')
        ORDER BY day.date ASC;
    """, (self.user_hall_id, self.user_hall_id, desiredStartStr[:7], desiredEndStr[:7],
          desiredStartStr[:10], desiredEndStr[:10])
        )

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received the expected response
        self.assertListEqual(expectedResult, resp.json)

    def test_whenCalledFromClient_whenAllColorsIsTrue_returnsScheduleWithAllColors(self):
        # Test to ensure that when this method is called from a remote client and the showColors
        #  parameter is set to "true", the result will provide the unique colors for the RAs.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Create the schedule information that will be returned by the query call
        expectedScheduleInfoList = []
        for i in range(1, 7):
            expectedScheduleInfoList.append(
                (
                    "Test {}".format(i),
                    "User {}".format(i),
                    "#{:06}".format(i),
                    i,
                    '2021-02-{:02}'.format(i),
                    False,
                    1
                )
            )

        # Create the expected result
        expectedResult = []
        for row in expectedScheduleInfoList:
            expectedResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": row[2],
                "extendedProps": {
                    "dutyType": "std",
                    "flagged": row[5],
                    "pts": row[6]
                }
            })

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            expectedScheduleInfoList,  # First query returns the schedule information
        ]

        desiredStartStr = '2021-02-01T00:00:00-05:00'
        desiredEndStr = '2021-03-01T00:00:00-05:00'
        desiredShowAllColors = "true"

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/schedule/api/getSchedule",
                               query_string=dict(
                                   start=desiredStartStr,
                                   end=desiredEndStr,
                                   allColors=desiredShowAllColors
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received the expected response
        self.assertListEqual(expectedResult, resp.json)

    def test_whenCalledFromClient_whenShowAllColorsIsFalse_returnsScheduleWithDefaultColor(self):
        # Test to ensure that when this method is called from a remote client and the showColors
        #  parameter is set to False, the result will provide the unique color for only the
        #  requesting user. Otherwise the default will be used for all other RAs.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Create the schedule information that will be returned by the query call
        expectedScheduleInfoList = []
        for i in range(1, 7):
            expectedScheduleInfoList.append(
                (
                    "Test {}".format(i),
                    "User {}".format(i),
                    "#{:06}".format(i),
                    i,
                    '2021-02-{:02}'.format(i),
                    False,
                    1
                )
            )

        # Create the expected result
        expectedResult = []
        for row in expectedScheduleInfoList:
            if row[3] == self.user_ra_id:
                c = "#{:06}".format(self.user_ra_id)
            else:
                c = "#2C3E50"

            expectedResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": c,
                "extendedProps": {
                    "dutyType": "std",
                    "flagged": row[5],
                    "pts": row[6]
                }
            })

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            expectedScheduleInfoList,  # First query returns the schedule information
        ]

        desiredStartStr = '2021-02-01T00:00:00-05:00'
        desiredEndStr = '2021-03-01T00:00:00-05:00'
        desiredShowAllColors = "false"

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/schedule/api/getSchedule",
                               query_string=dict(
                                   start=desiredStartStr,
                                   end=desiredEndStr,
                                   allColors=desiredShowAllColors
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received the expected response
        self.assertListEqual(expectedResult, resp.json)

    # ------------------------------
    # -- Called from Server Tests --
    # ------------------------------
    def test_whenCalledFromServer_returnsScheduleInExpectedFormat(self):
        # Test to ensure that when called from the server, the function
        #  returns the appropriate schedule in the expected format.
        #
        #     [
        #        {
        #           "id": <ra.id>,
        #           "title": <ra.first_name> + " " + <ra.last_name>,
        #           "start": <day.date>,
        #           "color": <ra.color or "#2C3E50">,
        #           "extendedProps": {
        #               "dutyType": "std",
        #               "flagged": <duties.flagged>,
        #               "pts": <duties.point_val>
        #           }
        #        }
        #     ]

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Create the schedule information that will be returned by the query call
        expectedScheduleInfoList = []
        for i in range(1, 7):
            expectedScheduleInfoList.append(
                (
                    "Test {}".format(i),
                    "User {}".format(i),
                    "#{:06}".format(i),
                    i,
                    '2021-02-{:02}'.format(i),
                    False,
                    1
                )
            )

        # Create the expected result
        expectedResult = []
        for row in expectedScheduleInfoList:
            expectedResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": row[2],
                "extendedProps": {
                    "dutyType": "std",
                    "flagged": row[5],
                    "pts": row[6]
                }
            })

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            expectedScheduleInfoList,  # First query returns the schedule information
        ]

        desiredStartStr = '2021-02-01'
        desiredEndStr = '2021-03-01'
        desiredShowAllColors = True

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/schedule/api/getSchedule",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):

            # Make our call to the function
            result = getSchedule2(
                start=desiredStartStr,
                end=desiredEndStr,
                hallId=self.user_hall_id,
                showAllColors=desiredShowAllColors
            )

        # -- Assert --

        # Assert that the last time appGlobals.conn.cursor().execute was called,
        #  it was a query for the RA.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with(
            """
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD'),
               duties.flagged, duties.point_val
        FROM duties JOIN day ON (day.id=duties.day_id)
                    JOIN RA ON (ra.id=duties.ra_id)
        WHERE duties.hall_id = %s
        AND duties.sched_id IN
                (
                SELECT DISTINCT ON (schedule.month_id) schedule.id
                FROM schedule
                WHERE schedule.hall_id = %s
                AND schedule.month_id IN
                    (
                        SELECT month.id
                        FROM month
                        WHERE month.year >= TO_DATE(%s,'YYYY-MM')
                        AND month.year <= TO_DATE(%s,'YYYY-MM')
                    )
                ORDER BY schedule.month_id, schedule.created DESC, schedule.id DESC
                )
        AND day.date >= TO_DATE(%s,'YYYY-MM-DD')
        AND day.date <= TO_DATE(%s,'YYYY-MM-DD')
        ORDER BY day.date ASC;
    """, (self.user_hall_id, self.user_hall_id, desiredStartStr[:7], desiredEndStr[:7],
          desiredStartStr[:10], desiredEndStr[:10])
        )

        # Assert that we received the expected response
        self.assertListEqual(expectedResult, result)

    def test_whenCalledFromServer_whenShowAllColorsIsTrue_returnsScheduleWithAllColors(self):
        # Test to ensure that when this method is called from the server and the showAllColors
        #  parameter is set to True, the result will provide the unique colors for the RAs.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Create the schedule information that will be returned by the query call
        expectedScheduleInfoList = []
        for i in range(1, 7):
            expectedScheduleInfoList.append(
                (
                    "Test {}".format(i),
                    "User {}".format(i),
                    "#{:06}".format(i),
                    i,
                    '2021-02-{:02}'.format(i),
                    False,
                    1
                )
            )

        # Create the expected result
        expectedResult = []
        for row in expectedScheduleInfoList:
            expectedResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": row[2],
                "extendedProps": {
                    "dutyType": "std",
                    "flagged": row[5],
                    "pts": row[6]
                }
            })

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            expectedScheduleInfoList,  # First query returns the schedule information
        ]

        desiredStartStr = '2021-02-01'
        desiredEndStr = '2021-03-01'
        desiredShowAllColors = True

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/schedule/api/getSchedule",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):

            # Make our call to the function
            result = getSchedule2(
                start=desiredStartStr,
                end=desiredEndStr,
                hallId=self.user_hall_id,
                showAllColors=desiredShowAllColors
            )

        # -- Assert --

        # Assert that we received the expected response
        self.assertListEqual(expectedResult, result)

    def test_whenCalledFromServer_whenShowAllColorsIsFalse_returnsScheduleWithDefaultColor(self):
        # Test to ensure that when this method is called from the server and the showAllColors
        #  parameter is set to False, the result will provide the default color for all RAs.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Create the schedule information that will be returned by the query call
        expectedScheduleInfoList = []
        for i in range(1, 7):
            expectedScheduleInfoList.append(
                (
                    "Test {}".format(i),
                    "User {}".format(i),
                    "#{:06}".format(i),
                    i,
                    '2021-02-{:02}'.format(i),
                    False,
                    1
                )
            )

        # Create the expected result
        expectedResult = []
        for row in expectedScheduleInfoList:
            expectedResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": "#2C3E50",
                "extendedProps": {
                    "dutyType": "std",
                    "flagged": row[5],
                    "pts": row[6]
                }
            })

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            expectedScheduleInfoList,  # First query returns the schedule information
        ]

        desiredStartStr = '2021-02-01'
        desiredEndStr = '2021-03-01'
        desiredShowAllColors = False

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/schedule/api/getSchedule",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):

            # Make our call to the function
            result = getSchedule2(
                start=desiredStartStr,
                end=desiredEndStr,
                hallId=self.user_hall_id,
                showAllColors=desiredShowAllColors
            )

        # -- Assert --

        # Assert that we received the expected response
        self.assertListEqual(expectedResult, result)