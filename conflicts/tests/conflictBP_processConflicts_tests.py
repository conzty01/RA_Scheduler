from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest

from helperFunctions.helperFunctions import stdRet


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

    def tearDown(self):
        # Stop all of the patchers
        self.patcher_getAuth.stop()
        self.patcher_appGlobals.stop()
        self.patcher_osEnviron.stop()

    def resetAuthLevel(self):
        # This function serves to reset the auth_level of the session
        #  to the default value which is 1.
        self.mocked_authLevel.return_value = 1

    def test_whenGivenNewConflicts_addsNewConflictsToDB(self):
        # When a user calls the API and provides a set of conflicts
        #  that are not already registered in the DB, the method
        #  will add the new conflicts into the DB.
        #
        #   monthNum   <int>       -  an integer representing the numeric month number for
        #                              the desired month using the standard gregorian
        #                              calendar convention.
        #   year       <int>       -  an integer denoting the year for the desired time period
        #                              using the standard gregorian calendar convention.
        #   conflicts  <lst<str>>  -  a list containing strings representing dates that the
        #                              user has a duty conflict with.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        desiredMonthNum = 3
        desiredYear = 2021
        desiredNewConflicts = []
        for i in range(13):
            desiredNewConflicts.append("2021-01-{:02}".format(i))

        expectedPrevConflicts = []

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            tuple(expectedPrevConflicts)  # First call returns the Previous conflicts
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/conflicts/api/enterConflicts/",
                                json=dict(
                                    monthNum=desiredMonthNum,
                                    year=desiredYear,
                                    conflicts=desiredNewConflicts
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was last called,
        #  it was an INSERT statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            """INSERT INTO conflicts (ra_id, day_id)
                        SELECT %s, day.id FROM day
                        WHERE TO_CHAR(day.date, 'YYYY-MM-DD') IN %s
                        """, (self.user_ra_id, tuple(set(desiredNewConflicts))))

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_called_once()

        # Assert that appGlobals.conn.cursor().close was called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(1, "successful"), resp.json)

    def test_whenGivenConflictsAlreadyInDB_returnsSuccessResponse(self):
        # When a user calls the API and provides a set of conflicts that ARE
        #  already registered in the DB, the method will not modify the conflicts.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        desiredMonthNum = 3
        desiredYear = 2021
        desiredNewConflicts = ["2021-01-{:02}".format(i) for i in range(10)]

        # Create the expected previous conflicts that should be returned
        #  from the DB.
        expectedPrevConflicts = []
        for i in desiredNewConflicts:
            expectedPrevConflicts.append((i,))

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            tuple(expectedPrevConflicts)  # First call returns the Previous conflicts
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/conflicts/api/enterConflicts/",
                                json=dict(
                                    monthNum=desiredMonthNum,
                                    year=desiredYear,
                                    conflicts=desiredNewConflicts
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was last called,
        #  it was an INSERT statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once()

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that appGlobals.conn.cursor().close was NOT called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(1, "successful"), resp.json)

    def test_whenNotGivenPreviouslyEnteredConflicts_removesPreviouslyEnteredConflictsFromDB(self):
        # When a user calls the API and excludes a set of conflicts that are
        #  already registered in the DB, the method will remove the excluded
        #  conflicts.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        desiredMonthNum = 3
        desiredYear = 2021
        desiredNewConflicts = ["2021-01-{:02}".format(i) for i in range(20)]

        # Create the expected previous conflicts that should be returned
        #  from the DB.
        expectedPrevConflicts = []
        for i in desiredNewConflicts:
            expectedPrevConflicts.append((i,))

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            tuple(expectedPrevConflicts)  # First call returns the Previous conflicts
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/conflicts/api/enterConflicts/",
                                json=dict(
                                    monthNum=desiredMonthNum,
                                    year=desiredYear,
                                    # In this test, we will exclude several of the
                                    #  conflicts that we have in the expectedPrevConflicts
                                    #  so that these are removed from the DB.
                                    conflicts=desiredNewConflicts[:15]
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was last called,
        #  it was an Delete statement. Since this line is using triple-quote strings,
        #  the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            """DELETE FROM conflicts
                       WHERE conflicts.day_id IN (
                            SELECT conflicts.day_id
                            FROM conflicts
                                JOIN day ON (conflicts.day_id = day.id)
                            WHERE TO_CHAR(day.date, 'YYYY-MM-DD') IN %s
                            AND conflicts.ra_id = %s
                        );""", (tuple(set(desiredNewConflicts[15:])), self.user_ra_id))

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_called_once()

        # Assert that appGlobals.conn.cursor().close was NOT called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(1, "successful"), resp.json)

    def test_ableToAddAndRemoveConflictsInSingleCall(self):
        # Essentially, is the method able to add new conflicts and remove no longer needed
        #  conflicts at the same time.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()

        desiredMonthNum = 3
        desiredYear = 2021
        desiredNewConflicts = ["2021-01-{:02}".format(i) for i in range(5)]
        expectedPrevConflicts = ["2021-01-{:02}".format(i) for i in range(10, 20)]

        # Create a list of conflict dates to be sent to the server. It comprises of
        #  "new" dates as well as some of the dates that were already in the DB.
        sentConflicts = desiredNewConflicts + expectedPrevConflicts[:5]

        # Create the expected previous conflicts that should be returned
        #  from the DB.
        for index, date in enumerate(expectedPrevConflicts):
            expectedPrevConflicts[index] = tuple(date)

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.

        # Fetchall() config
        self.mocked_appGlobals.conn.cursor().fetchall.side_effect = [
            tuple(expectedPrevConflicts)  # First call returns the Previous conflicts
        ]

        # Create the sets that the API will use to determine what needs to be added
        #  and removed.
        prevSet = set([i[0] for i in expectedPrevConflicts])
        newSet = set(sentConflicts)
        deleteSet = prevSet.difference(newSet)
        addSet = newSet.difference(prevSet)

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.post("/conflicts/api/enterConflicts/",
                                json=dict(
                                    monthNum=desiredMonthNum,
                                    year=desiredYear,
                                    conflicts=sentConflicts
                                ),
                                base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  one of the calls was the following. Since this line is using triple-
        #  quote strings, the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            """DELETE FROM conflicts
                       WHERE conflicts.day_id IN (
                            SELECT conflicts.day_id
                            FROM conflicts
                                JOIN day ON (conflicts.day_id = day.id)
                            WHERE TO_CHAR(day.date, 'YYYY-MM-DD') IN %s
                            AND conflicts.ra_id = %s
                        );""", (tuple(deleteSet), self.user_ra_id)
        )

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  one of the calls was the following. Since this line is using triple-
        #  quote strings, the whitespace must match exactly.
        self.mocked_appGlobals.conn.cursor().execute.assert_any_call(
            """INSERT INTO conflicts (ra_id, day_id)
                        SELECT %s, day.id FROM day
                        WHERE TO_CHAR(day.date, 'YYYY-MM-DD') IN %s
                        """, (self.user_ra_id, tuple(addSet))
        )

        # Assert that the execute() method was called 3 times.
        self.assertEqual(self.mocked_appGlobals.conn.cursor().execute.call_count, 3)

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_called_once()

        # Assert that appGlobals.conn.cursor().close was NOT called
        self.mocked_appGlobals.conn.cursor().close.assert_called_once()

        # Assert that we received a json response
        self.assertTrue(resp.is_json)

        # Assert that we received our expected result
        self.assertEqual(stdRet(1, "successful"), resp.json)
