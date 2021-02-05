from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest

from helperFunctions.helperFunctions import stdRet


class TestHallBP_saveHallSettings(unittest.TestCase):
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

    def test_withAuthorizedUser_SavesResHallName(self):
        # Test to ensure that when an authorized user passes valid
        #  Hall Setting data to this API, the method saves the
        #  data to the DB. An authorized user is considered a user
        #  whose "auth_level" at least 3 (HD).
        #
        #   name   <str>  -  The name of the Hall Setting that has been changed.
        #   value  <ukn>  -  The new value for the setting that has been altered.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        desiredSettingName = "Residence Hall Name"
        desiredSettingValue = "Test Hall"

        expectedHallID = 14

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallID,)  # First call returns a Hall ID if the user belongs
                               #  to the appropriate hall.
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/hall/api/saveHallSettings",
                                json=dict(
                                    name=desiredSettingName,
                                    value=desiredSettingValue
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was last called,
        #  it was an UPDATE statement.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            "UPDATE res_hall SET name = %s WHERE id = %s",
            (desiredSettingValue, self.user_hall_id)
        )

        # Assert that the API method checked to ensure that the user belonged
        #  to the hall that whose settings they are manipulating.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            """SELECT res_hall.id
                   FROM res_hall JOIN ra ON (ra.hall_id = res_hall.id)
                   WHERE ra.id = %s;""", (self.user_ra_id,)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_called_once()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(1, "successful"), resp.json)

    def test_withAuthorizedUser_withMismatchedHallID_returnsNotAuthorizedResponse(self):
        # Test to ensure that when a user that is authorized to make
        #  changes to Hall Settings attempts to do so but an issue
        #  occurs in the DB so that there is no res_hall.id value
        #  associated with them, the API returns a not authorized
        #  JSON response.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        desiredSettingName = "Residence Hall Name"
        desiredSettingValue = "Test Hall"

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            None  # First call returns a Hall ID if the user belongs
            #  to the appropriate hall.
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/hall/api/saveHallSettings",
                                json=dict(
                                    name=desiredSettingName,
                                    value=desiredSettingValue
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the API method checked to ensure that the user belonged
        #  to the hall that whose settings they are manipulating.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            """SELECT res_hall.id
                   FROM res_hall JOIN ra ON (ra.hall_id = res_hall.id)
                   WHERE ra.id = %s;""", (self.user_ra_id,)
        )

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(0, "NOT AUTHORIZED"), resp.json)

    def test_withUnauthorizedUser_returnsNotAuthorizedResponse(self):
        # Test to ensure that when a user that is not authorized to
        #  make changes to Hall Settings attempts to call this API,
        #  they receive a JSON response that indicates that they are
        #  not authorized. An authorized user is considered a user
        #  whose "auth_level" at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/hall/api/saveHallSettings",
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(-1, "NOT AUTHORIZED"), resp.json)

    @patch("hall.hall.Json", autospec=True)
    def test_withAuthorizedUser_SavesDutyConfig(self, mocked_psycopg2Json):
        # Test to ensure that when an authorized user passes valid
        #  Hall Setting data to this API, the method saves the
        #  data to the DB. An authorized user is considered a user
        #  whose "auth_level" at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        desiredSettingName = "Duty Configuration"
        desiredSettingValue = {
            "reg_duty_num_assigned": 1,     # Number of RAs to be assigned on regular duty days.
            "multi_duty_num_assigned": 2,   # Number of RAs to be assigned on multi-duty days.
            "brk_duty_num_assigned": 1,     # Number of RAs to be assigned on break duty days.
            "reg_duty_pts": 1,              # Number of points to be awarded for regular duties.
            "multi_duty_pts": 2,            # Number of points to be awarded for multi-day duties.
            "brk_duty_pts": 3,              # Number of points to be awarded for break duties.
            "multi_duty_days": [4, 5]       # Days of the week which are considered multi-duty days.
                                            #    Mon, Tues, Wed, Thurs, Fri, Sat, Sun
                                            #     0    1     2     3     4    5    6
        }

        expectedHallID = 14

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallID,)  # First call returns a Hall ID if the user belongs
            #  to the appropriate hall.
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/hall/api/saveHallSettings",
                                json=dict(
                                    name=desiredSettingName,
                                    value=desiredSettingValue
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the Json constructor was called once
        mocked_psycopg2Json.assert_called_once_with(desiredSettingValue)

        # Assert that the when the appGlobals.conn.cursor().execute was last called,
        #  it was an UPDATE statement.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            "UPDATE hall_settings SET duty_config = %s WHERE res_hall_id = %s;",
            (mocked_psycopg2Json(mocked_psycopg2Json), self.user_hall_id)
        )

        # Assert that the API method checked to ensure that the user belonged
        #  to the hall that whose settings they are manipulating.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            """SELECT res_hall.id
                   FROM res_hall JOIN ra ON (ra.hall_id = res_hall.id)
                   WHERE ra.id = %s;""", (self.user_ra_id,)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_called_once()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(1, "successful"), resp.json)

    def test_withAuthorizedUser_SavesSchoolYear(self):
        # Test to ensure that when an authorized user passes valid
        #  Hall Setting data to this API, the method saves the
        #  data to the DB. An authorized user is considered a user
        #  whose "auth_level" at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        desiredSettingName = "Defined School Year"
        desiredSettingValue = {
            "start": 1,
            "end": 12
        }

        expectedHallID = 14

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallID,)  # First call returns a Hall ID if the user belongs
            #  to the appropriate hall.
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/hall/api/saveHallSettings",
                                json=dict(
                                    name=desiredSettingName,
                                    value=desiredSettingValue
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was last called,
        #  it was an UPDATE statement.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            """UPDATE hall_settings 
                       SET year_start_mon = %s, year_end_mon = %s
                       WHERE res_hall_id = %s;""",
            (desiredSettingValue["start"], desiredSettingValue["end"], self.user_hall_id)
        )

        # Assert that the API method checked to ensure that the user belonged
        #  to the hall that whose settings they are manipulating.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            """SELECT res_hall.id
                   FROM res_hall JOIN ra ON (ra.hall_id = res_hall.id)
                   WHERE ra.id = %s;""", (self.user_ra_id,)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_called_once()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(1, "successful"), resp.json)

    def test_withAuthorizedUser_SavesMultiDutyFlag(self):
        # Test to ensure that when an authorized user passes valid
        #  Hall Setting data to this API, the method saves the
        #  data to the DB. An authorized user is considered a user
        #  whose "auth_level" at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        desiredSettingName = "Multi-Duty Day Flag"
        desiredSettingValue = {
            "flag": True,
            "label": "Secondary"
        }

        expectedHallID = 14

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallID,)  # First call returns a Hall ID if the user belongs
            #  to the appropriate hall.
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/hall/api/saveHallSettings",
                                json=dict(
                                    name=desiredSettingName,
                                    value=desiredSettingValue
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was last called,
        #  it was an UPDATE statement.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            """UPDATE hall_settings 
                       SET flag_multi_duty = %s, duty_flag_label = %s
                       WHERE res_hall_id = %s;""",
            (desiredSettingValue["flag"], desiredSettingValue["label"], self.user_hall_id)
        )

        # Assert that the API method checked to ensure that the user belonged
        #  to the hall that whose settings they are manipulating.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            """SELECT res_hall.id
                   FROM res_hall JOIN ra ON (ra.hall_id = res_hall.id)
                   WHERE ra.id = %s;""", (self.user_ra_id,)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_called_once()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(1, "successful"), resp.json)

    def test_withAuthorizedUser_SavesAutoAdjRAPts(self):
        # Test to ensure that when an authorized user passes valid
        #  Hall Setting data to this API, the method saves the
        #  data to the DB. An authorized user is considered a user
        #  whose "auth_level" at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        desiredSettingName = "Automatic RA Point Adjustment"
        desiredSettingValue = False

        expectedHallID = 14

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallID,)  # First call returns a Hall ID if the user belongs
            #  to the appropriate hall.
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/hall/api/saveHallSettings",
                                json=dict(
                                    name=desiredSettingName,
                                    value=desiredSettingValue
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was last called,
        #  it was an UPDATE statement.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            "UPDATE hall_settings SET auto_adj_excl_ra_pts = %s WHERE res_hall_id = %s;",
            (desiredSettingValue, self.user_hall_id)
        )

        # Assert that the API method checked to ensure that the user belonged
        #  to the hall that whose settings they are manipulating.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            """SELECT res_hall.id
                   FROM res_hall JOIN ra ON (ra.hall_id = res_hall.id)
                   WHERE ra.id = %s;""", (self.user_ra_id,)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_called_once()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(1, "successful"), resp.json)

    def test_withAuthorizedUser_withUnknownSetting_returnsAppropriateResponse(self):
        # Test to ensure that when an authorized user passes an unknown
        #  Hall Setting to this API, the method logs a warning and returns
        #  an "Unknown Setting Provided" response. An authorized user is
        #  considered a user whose "auth_level" at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.mocked_loggingWARNING.reset_mock()

        # Set the auth_level of this session to 2
        self.mocked_authLevel.return_value = 3

        desiredSettingName = "Unknown Setting Name48"
        desiredSettingValue = "Unknown Setting Value"

        expectedHallID = 14

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedHallID,)  # First call returns a Hall ID if the user belongs
            #  to the appropriate hall.
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/hall/api/saveHallSettings",
                                json=dict(
                                    name=desiredSettingName,
                                    value=desiredSettingValue
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the API method checked to ensure that the user belonged
        #  to the hall that whose settings they are manipulating.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            """SELECT res_hall.id
                   FROM res_hall JOIN ra ON (ra.hall_id = res_hall.id)
                   WHERE ra.id = %s;""", (self.user_ra_id,)
        )

        # Assert that the event was logged
        self.mocked_loggingWARNING.assert_called_once_with(
            "Unable to handle Hall Setting: {}".format(desiredSettingName)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(0, "Unknown Setting Provided"), resp.json)
