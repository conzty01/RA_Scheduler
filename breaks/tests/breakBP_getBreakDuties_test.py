from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest


from breaks.breaks import getBreakDuties


class TestBreakBP_getBreakDuties(unittest.TestCase):
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
    def test_whenCalledFromClient_returnScheduleInExpectedJSONFormat(self):
        # Test to ensure that when this API is called from a remote client
        #  it accepts the below parameters and returns a schedule in the
        #  expected JSON format.
        #
        #   start      <str>  -  a string representing the first day that should be included
        #                         for the returned duty schedule.
        #   end        <str>  -  a string representing the last day that should be included
        #                         for the returned duty schedule.
        #   allColors  <bool> -  a boolean value representing whether the returned duty
        #                         schedule should include the RA's ra.color value or if
        #                         the generic value '#2C3E50' should be returned. Setting
        #                         this value to True will return the RA's ra.color value.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Set the passed arguments
        desiredStartStr = "2021-01-01T00:00:00.000"
        desiredEndStr = "2022-02-01T00:00:00.000"
        desiredColors = "false"  # <- Must be set as it would appear coming across from JSON

        # Create some dummy duties that will be returned from the DB.
        breakDutySchedule = []
        for i in range(31):
            breakDutySchedule.append((
                "Test" + str(i),
                "User" + str(i),
                "#{:06}".format(i),
                i,
                "2021-01-{:02}".format(i)
            ))

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            # First call returns the break duty schedule
            tuple(breakDutySchedule)
        ]

        # Generate the expected result based on the results from the DB
        expectedScheduleResult = []
        for row in breakDutySchedule:
            # Set the default color value since we set desiredColors to False
            color = "#2C3E50"

            # If the RA's id matches our own
            if row[3] == self.user_ra_id:
                # Then we need to set our id to the expected value
                color = "#{:06}".format(row[3])

            # Append the duty to the list
            expectedScheduleResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": color,
                "extendedProps": {"dutyType": "brk"}
            })

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/breaks/api/getBreakDuties",
                               query_string=dict(
                                   start=desiredStartStr,
                                   end=desiredEndStr,
                                   allColors=desiredColors
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with("""
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD')
        FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                          JOIN month ON (month.id=break_duties.month_id)
                          JOIN ra ON (ra.id=break_duties.ra_id)
        WHERE break_duties.hall_id = %s
        AND month.year >= TO_DATE(%s,'YYYY-MM')
        AND month.year <= TO_DATE(%s,'YYYY-MM')
    """, (self.user_hall_id, desiredStartStr.split("T")[0], desiredEndStr.split("T")[0])
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertListEqual(expectedScheduleResult, resp.json)

    def test_whenCalledFromClientAndShowAllColorsIsTrue_returnsScheduleWithAllColors(self):
        # Test to ensure that if the remote client specifies that they would like
        #  to receive a schedule with all of the unique RAs' colors, then they
        #  do, in fact, receive this result. This is requested by setting allColors
        #  to True.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Set the passed arguments
        desiredStartStr = "2021-01-01T00:00:00.000"
        desiredEndStr = "2022-02-01T00:00:00.000"
        desiredColors = "true"  # <- Must be set as it would appear coming across from JSON

        # Create some dummy duties that will be returned from the DB.
        breakDutySchedule = []
        for i in range(1):
            breakDutySchedule.append((
                "Test" + str(i),
                "User" + str(i),
                "#{:06}".format(i),
                i,
                "2021-01-{:02}".format(i)
            ))

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            # First call returns the break duty schedule
            tuple(breakDutySchedule)
        ]

        # Generate the expected result based on the results from the DB
        expectedScheduleResult = []
        for row in breakDutySchedule:
            # Append the duty to the list
            expectedScheduleResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": row[2],
                "extendedProps": {"dutyType": "brk"}
            })

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/breaks/api/getBreakDuties",
                               query_string=dict(
                                   start=desiredStartStr,
                                   end=desiredEndStr,
                                   allColors=desiredColors
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received our expected result
        self.assertEqual(expectedScheduleResult, resp.json)

    def test_whenCalledFromClientAndShowAllColorsIsFalse_returnsScheduleWithDefaultColor(self):
        # Test to ensure that if the remote client specifies that they would NOT like
        #  to receive a schedule with all of the unique RAs' colors, then they
        #  do, in fact, receive this result. This is requested by setting allColors
        #  to False. This does not include the requesting user's id, which will always
        #  return their unique color.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 2

        # Set the passed arguments
        desiredStartStr = "2021-01-01T00:00:00.000"
        desiredEndStr = "2022-02-01T00:00:00.000"
        desiredColors = "false"  # <- Must be set as it would appear coming across from JSON

        # Create some dummy duties that will be returned from the DB.
        breakDutySchedule = []
        for i in range(31):
            breakDutySchedule.append((
                "Test" + str(i),
                "User" + str(i),
                "#{:06}".format(i),
                i,
                "2021-01-{:02}".format(i)
            ))

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            # First call returns the break duty schedule
            tuple(breakDutySchedule)
        ]

        # Generate the expected result based on the results from the DB
        expectedScheduleResult = []
        for row in breakDutySchedule:
            # Set the default color value since we set desiredColors to False
            color = "#2C3E50"

            # If the RA's id matches our own
            if row[3] == self.user_ra_id:
                # Then we need to set our id to the expected value
                color = "#{:06}".format(row[3])

            # Append the duty to the list
            expectedScheduleResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": color,
                "extendedProps": {"dutyType": "brk"}
            })

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/breaks/api/getBreakDuties",
                               query_string=dict(
                                   start=desiredStartStr,
                                   end=desiredEndStr,
                                   allColors=desiredColors
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that we received our expected result
        self.assertListEqual(expectedScheduleResult, resp.json)

    # ------------------------------
    # -- Called from Server Tests --
    # ------------------------------
    def test_whenCalledFromServer_returnsScheduleInExpectedFormat(self):
        # Test to ensure that when this API is called from the server
        #  it accepts the below parameters and returns a schedule in the
        #  expected JSON format.
        #
        #   hallId         <int>  -  an integer representing the id of the desired residence
        #                             hall in the res_hall table.
        #   start          <str>  -  a string representing the first day that should be included
        #                             for the returned duty schedule.
        #   end            <str>  -  a string representing the last day that should be included
        #                             for the returned duty schedule.
        #   showAllColors  <bool> -  a boolean value representing whether the returned duty
        #                             schedule should include the RA's ra.color value or if
        #                             the generic value '#2C3E50' should be returned. Setting
        #                             this value to True will return the RA's ra.color value.
        #                             By default this parameter is set to False.
        #
        #   raId           <int>  -  an integer representing the id of the RA that should be
        #                             considered the requesting user. By default this value is
        #                             set to -1 which indicates that no RA should be considered
        #                              the requesting user.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set the passed arguments
        desiredStartStr = "2021-01-01"
        desiredEndStr = "2022-02-01"

        # Create some dummy duties that will be returned from the DB.
        breakDutySchedule = []
        for i in range(31):
            breakDutySchedule.append((
                "Test" + str(i),
                "User" + str(i),
                "#{:06}".format(i),
                i,
                "2021-01-{:02}".format(i)
            ))

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            # First call returns the break duty schedule
            tuple(breakDutySchedule)
        ]

        # Generate the expected result based on the results from the DB
        expectedScheduleResult = []
        for row in breakDutySchedule:
            # Append the duty to the list
            expectedScheduleResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": "#2C3E50",
                "extendedProps": {"dutyType": "brk"}
            })

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/breaks/api/getBreakDuties",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):

            # Make our call to the function
            result = getBreakDuties(self.user_hall_id, desiredStartStr, desiredEndStr)

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with("""
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD')
        FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                          JOIN month ON (month.id=break_duties.month_id)
                          JOIN ra ON (ra.id=break_duties.ra_id)
        WHERE break_duties.hall_id = %s
        AND month.year >= TO_DATE(%s,'YYYY-MM')
        AND month.year <= TO_DATE(%s,'YYYY-MM')
    """, (self.user_hall_id, desiredStartStr, desiredEndStr)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertIsInstance(result, list)

        # Assert that we received our expected result
        self.assertListEqual(expectedScheduleResult, result)

    def test_whenCalledFromServer_whenShowAllColorsIsTrue_returnsScheduleWithAllColors(self):
        # Test to ensure that if the server specifies that they would like
        #  to receive a schedule with all of the unique RAs' colors, then they
        #  do, in fact, receive this result. This is requested by setting allColors
        #  to True.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set the passed arguments
        desiredStartStr = "2021-01-01"
        desiredEndStr = "2022-02-01"

        # Create some dummy duties that will be returned from the DB.
        breakDutySchedule = []
        for i in range(31):
            breakDutySchedule.append((
                "Test" + str(i),
                "User" + str(i),
                "#{:06}".format(i),
                i,
                "2021-01-{:02}".format(i)
            ))

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            # First call returns the break duty schedule
            tuple(breakDutySchedule)
        ]

        # Generate the expected result based on the results from the DB
        expectedScheduleResult = []
        for row in breakDutySchedule:
            # Append the duty to the list
            expectedScheduleResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": row[2],
                "extendedProps": {"dutyType": "brk"}
            })

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/breaks/api/getBreakDuties",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):

            # Make our call to the function
            result = getBreakDuties(self.user_hall_id, desiredStartStr,
                                    desiredEndStr, True)

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with("""
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD')
        FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                          JOIN month ON (month.id=break_duties.month_id)
                          JOIN ra ON (ra.id=break_duties.ra_id)
        WHERE break_duties.hall_id = %s
        AND month.year >= TO_DATE(%s,'YYYY-MM')
        AND month.year <= TO_DATE(%s,'YYYY-MM')
    """, (self.user_hall_id, desiredStartStr, desiredEndStr)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertIsInstance(result, list)

        # Assert that we received our expected result
        self.assertListEqual(expectedScheduleResult, result)

    def test_whenCalledFromServer_whenRAidIsNotSpecifiedAndShowAllColorsIsFalse_returnsScheduleWithDefaultColor(self):
        # Test to ensure that if the server specifies that they would NOT like
        #  to receive a schedule with all of the unique RAs' colors, and they have
        #  NOT provided an ra that should be considered as the user, then they
        #  do, in fact, receive this result. This is requested by setting allColors
        #  to False and not providing an raId.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set the passed arguments
        desiredStartStr = "2021-01-01"
        desiredEndStr = "2022-02-01"

        # Create some dummy duties that will be returned from the DB.
        breakDutySchedule = []
        for i in range(31):
            breakDutySchedule.append((
                "Test" + str(i),
                "User" + str(i),
                "#{:06}".format(i),
                i,
                "2021-01-{:02}".format(i)
            ))

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            # First call returns the break duty schedule
            tuple(breakDutySchedule)
        ]

        # Generate the expected result based on the results from the DB
        expectedScheduleResult = []
        for row in breakDutySchedule:
            # Append the duty to the list
            expectedScheduleResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": "#2C3E50",
                "extendedProps": {"dutyType": "brk"}
            })

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/breaks/api/getBreakDuties",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):

            # Make our call to the function
            result = getBreakDuties(self.user_hall_id, desiredStartStr,
                                    desiredEndStr, False)

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with("""
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD')
        FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                          JOIN month ON (month.id=break_duties.month_id)
                          JOIN ra ON (ra.id=break_duties.ra_id)
        WHERE break_duties.hall_id = %s
        AND month.year >= TO_DATE(%s,'YYYY-MM')
        AND month.year <= TO_DATE(%s,'YYYY-MM')
    """, (self.user_hall_id, desiredStartStr, desiredEndStr)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertIsInstance(result, list)

        # Assert that we received our expected result
        self.assertListEqual(expectedScheduleResult, result)

    def test_whenCalledFromServer_whenRAidIsSpecifiedAndShowAllColorsIsFalse_returnsScheduleWithDefaultColorExceptRA(self):
        # Test to ensure that if the server specifies that they would NOT like
        #  to receive a schedule with all of the unique RAs' colors, and it does
        #  specify an ra that should be considered as the user, then they
        #  do, in fact, receive this result except for the user provided. This is
        #  requested by setting allColors to False and providing an raId.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set the passed arguments
        desiredStartStr = "2021-01-01"
        desiredEndStr = "2022-02-01"

        # Create some dummy duties that will be returned from the DB.
        breakDutySchedule = []
        for i in range(31):
            breakDutySchedule.append((
                "Test" + str(i),
                "User" + str(i),
                "#{:06}".format(i),
                i,
                "2021-01-{:02}".format(i)
            ))

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            # First call returns the break duty schedule
            tuple(breakDutySchedule)
        ]

        # Generate the expected result based on the results from the DB
        expectedScheduleResult = []
        for row in breakDutySchedule:
            # Set the default color value since we set desiredColors to False
            color = "#2C3E50"

            # If the RA's id matches our own
            if row[3] == self.user_ra_id:
                # Then we need to set our id to the expected value
                color = "#{:06}".format(row[3])

            # Append the duty to the list
            expectedScheduleResult.append({
                "id": row[3],
                "title": row[0] + " " + row[1],
                "start": row[4],
                "color": color,
                "extendedProps": {"dutyType": "brk"}
            })

        # -- Act --

        # Bundle the call up in a test_request_context so that we can test
        #  the function as if we were calling it from the server.

        with app.test_request_context("/breaks/api/getBreakDuties",
                                      base_url=self.mocked_appGlobals.baseOpts["HOST_URL"]):

            # Make our call to the function
            result = getBreakDuties(self.user_hall_id, desiredStartStr,
                                    desiredEndStr, False, self.user_hall_id)

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a select statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with("""
        SELECT ra.first_name, ra.last_name, ra.color, ra.id, TO_CHAR(day.date, 'YYYY-MM-DD')
        FROM break_duties JOIN day ON (day.id=break_duties.day_id)
                          JOIN month ON (month.id=break_duties.month_id)
                          JOIN ra ON (ra.id=break_duties.ra_id)
        WHERE break_duties.hall_id = %s
        AND month.year >= TO_DATE(%s,'YYYY-MM')
        AND month.year <= TO_DATE(%s,'YYYY-MM')
    """, (self.user_hall_id, desiredStartStr, desiredEndStr)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertIsInstance(result, list)

        # Assert that we received our expected result
        self.assertListEqual(expectedScheduleResult, result)
