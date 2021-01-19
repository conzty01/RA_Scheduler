from unittest.mock import MagicMock, patch
from scheduleServer import app
from flask import Response
import unittest

from helperFunctions.helperFunctions import stdRet


class TestIntegration_handleGCalAuthResponse(unittest.TestCase):
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
        self.patcher_getAuth = patch("integration.integrations.getAuth", autospec=True)

        # Start the patcher - mock returned
        self.mocked_getAuth = self.patcher_getAuth.start()

        # Configure the mocked_getAuth to return the helper_getAuth dictionary
        self.mocked_getAuth.return_value = self.helper_getAuth

        # -- Create a patcher for the appGlobals file --
        self.patcher_appGlobals = patch("integration.integrations.ag", autospec=True)

        # Start the patcher - mock returned
        self.mocked_appGlobals = self.patcher_appGlobals.start()

        # Configure the mocked appGlobals as desired
        self.mocked_appGlobals.baseOpts = {"HOST_URL": "https://localhost:5000"}
        self.mocked_appGlobals.conn = MagicMock()
        self.mocked_appGlobals.UPLOAD_FOLDER = "./static"
        self.mocked_appGlobals.ALLOWED_EXTENSIONS = {"txt", "csv"}

        # -- Create a patcher for the gCalIntegratinator object --
        self.patcher_integrationPart = patch("integration.integrations.gCalInterface", autospec=True)

        # Start the patcher - mock returned
        self.mocked_integrationPart = self.patcher_integrationPart.start()

        # -- Create a patcher for the BytesIO object --
        self.patcher_bytesIO = patch("integration.integrations.BytesIO")

        # Start the patcher - mock returned
        self.mocked_bytesIO = self.patcher_bytesIO.start()

        # -- Create a patcher for the pickle module --
        self.patcher_pickle = patch("integration.integrations.pickle")

        # Start the patcher - mock returned
        self.mocked_pickle = self.patcher_pickle.start()

    def tearDown(self):
        # Stop all of the patchers
        self.patcher_getAuth.stop()
        self.patcher_appGlobals.stop()
        self.patcher_osEnviron.stop()
        self.patcher_integrationPart.stop()
        self.patcher_bytesIO.stop()
        self.patcher_pickle.stop()

    def resetAuthLevel(self):
        # This function serves to reset the auth_level of the session
        #  to the default value which is 1.
        self.mocked_authLevel.return_value = 1

    def test_withoutAuthorizedUser_returnsNotAuthorizedResponse(self):
        # Test to ensure that when this method is called without an authorized
        #  user, a NOT AUTHORIZED response is returned. An authorized user is
        #  a user that has an auth_level of at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.resetAuthLevel()

        expectedResponse = stdRet(-1, "NOT AUTHORIZED")

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/GCalAuth",
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that the response we received is json
        self.assertTrue(resp.is_json)

        # Assert that we received the expected response
        self.assertDictEqual(expectedResponse, resp.json)

    def test_withAuthorizedUser_withNoStateInDB_returnsInvalidStateResponse(self):
        # Test to ensure that when this method is called with an authorized user,
        #  and there is no partial state already in the DB, this method returns
        #  an INVALID STATE response. An authorized user is a user that has an
        #  auth_level of at least 3 (HD).

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.resetAuthLevel()

        # Set the auth_level to be used for this test.
        self.mocked_authLevel.return_value = 3

        # Create the objects needed for this test
        desiredState = "Example State"
        expectedResponse = stdRet(-1, "Invalid State Received")

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            None,  # First call returns the auth state
        ]

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/GCalAuth",
                               query_string=dict(
                                   state=desiredState
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a SELECT statement.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_once_with(
            "SELECT id FROM google_calendar_info WHERE auth_state = %s",
            (desiredState,)
        )

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

        # Assert that the response we received is json
        self.assertTrue(resp.is_json)

        # Assert that we received the expected response
        self.assertDictEqual(expectedResponse, resp.json)

    @patch("integration.integrations.redirect", autospec=True)
    @patch("integration.integrations.url_for", autospec=True)
    @patch("integration.integrations.createGoogleCalendar", autospec=True)
    def test_withAuthorizedUser_withStateInDB_callsGCalIntegratinatorHandleAuthResponse(self,
                                                                                        mocked_createGoogleCalendar,
                                                                                        mocked_urlFor, mocked_redirect):
        # Test to ensure that when this method is called with an authorized user and
        #  a partial state already in the DB, this method calls the gCalIntegratinator's
        #  handleAuthResponse method.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.mocked_integrationPart.reset_mock()
        self.resetAuthLevel()

        # Set the auth_level to be used for this test.
        self.mocked_authLevel.return_value = 3

        # Create the objects needed for this test
        desiredState = "ExampleState"
        expectedInfoID = 12
        expectedRequestURL = self.mocked_appGlobals.baseOpts["HOST_URL"] + \
                             "/int/GCalAuth" + "?state={}".format(desiredState)
        expectedCreds = MagicMock()
        expectedResponse = Response(status=200)

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedInfoID,)  # First call returns the auth state
        ]

        # Configure the mocked gCalIntegratinator to behave as expected
        self.mocked_integrationPart.handleAuthResponse.return_value = expectedCreds

        # Configure the mocked createGoogleCalendar to behave as expected
        mocked_createGoogleCalendar.return_value = stdRet(1, "TEST RESULT")

        # Configure the mocked redirect object to return a Response object
        mocked_redirect.return_value = expectedResponse

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/GCalAuth",
                               query_string=dict(
                                   state=desiredState
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that this method called the gCalIntegratinator.handleAuthResponse() method
        self.mocked_integrationPart.handleAuthResponse.assert_called_once_with(
            expectedRequestURL,
            self.mocked_appGlobals.baseOpts["HOST_URL"] + "int/GCalAuth"
        )

    @patch("integration.integrations.redirect", autospec=True)
    @patch("integration.integrations.url_for", autospec=True)
    @patch("integration.integrations.createGoogleCalendar", autospec=True)
    def test_withAuthorizedUser_withStateInDB_savesCredentialsToDB(self, mocked_createGoogleCalendar, mocked_urlFor,
                                                                   mocked_redirect):
        # Test to ensure that when this method is called with an authorized user and
        #  a partial state already in the DB, this saves the credentials received from
        #  the gCalIntegratinator into the DB.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.mocked_integrationPart.reset_mock()
        self.mocked_bytesIO.reset_mock()
        self.mocked_pickle.reset_mock()
        self.resetAuthLevel()

        # Set the auth_level to be used for this test.
        self.mocked_authLevel.return_value = 3

        # Create the objects needed for this test
        desiredState = "ExampleState"
        expectedInfoID = 12
        expectedCreds = MagicMock()
        expectedResponse = Response(status=200)

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedInfoID,)  # First call returns the auth state
        ]

        # Configure the mocked gCalIntegratinator to behave as expected
        self.mocked_integrationPart.handleAuthResponse.return_value = expectedCreds

        # Configure the mocked createGoogleCalendar to behave as expected
        mocked_createGoogleCalendar.return_value = stdRet(1, "TEST RESULT")

        # Configure the mocked redirect object to return a Response object
        mocked_redirect.return_value = expectedResponse

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/GCalAuth",
                               query_string=dict(
                                   state=desiredState
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that a BytesIO object was created as expected
        self.mocked_bytesIO.assert_called_once()

        # Assert that the pickle module is used to dump the data into the BytesIO object
        self.mocked_pickle.dump.assert_called_once_with(expectedCreds, self.mocked_bytesIO())

        # Assert that the BytesIO object's reader head gets reset.
        self.mocked_bytesIO().seek.assert_called_once_with(0)

        # Assert that the BytesIO object was read to add it to the DB
        self.mocked_bytesIO().getvalue.assert_called_once()

        # Assert that the when the appGlobals.conn.cursor().execute was called,
        #  it was a UPDATE statement.
        self.mocked_appGlobals.conn.cursor().execute.assert_called_with(
            """UPDATE google_calendar_info
                   SET token = %s ,
                       auth_state = NULL
                   WHERE id = %s;""",
            (self.mocked_bytesIO().getvalue(), expectedInfoID)
        )

    @patch("integration.integrations.redirect", autospec=True)
    @patch("integration.integrations.url_for", autospec=True)
    @patch("integration.integrations.createGoogleCalendar", autospec=True)
    def test_withAuthorizedUser_withStateInDB_callsCreateGoogleCalendarFunction(self, mocked_createGoogleCalendar,
                                                                                mocked_urlFor, mocked_redirect):
        # Test to ensure that when this method is called with an authorized user and
        #  a partial state already in the DB, this method calls the createGoogleCalendar
        #  function.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.mocked_integrationPart.reset_mock()
        self.mocked_bytesIO.reset_mock()
        self.mocked_pickle.reset_mock()
        self.resetAuthLevel()

        # Set the auth_level to be used for this test.
        self.mocked_authLevel.return_value = 3

        # Create the objects needed for this test
        desiredState = "ExampleState"
        expectedInfoID = 12
        expectedCreds = MagicMock()
        expectedResponse = Response(status=200)

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedInfoID,)  # First call returns the auth state
        ]

        # Configure the mocked gCalIntegratinator to behave as expected
        self.mocked_integrationPart.handleAuthResponse.return_value = expectedCreds

        # Configure the mocked createGoogleCalendar to behave as expected
        mocked_createGoogleCalendar.return_value = stdRet(1, "TEST RESULT")

        # Configure the mocked redirect object to return a Response object
        mocked_redirect.return_value = expectedResponse

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/GCalAuth",
                               query_string=dict(
                                   state=desiredState
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that createGoogleCalendar() gets called once
        mocked_createGoogleCalendar.assert_called_once_with(expectedInfoID)

    @patch("integration.integrations.redirect", autospec=True)
    @patch("integration.integrations.url_for", autospec=True)
    @patch("integration.integrations.createGoogleCalendar", autospec=True)
    def test_withAuthorizedUser_withStateInDB_ifCalendarCreationFails_rollsBackDB(self, mocked_createGoogleCalendar,
                                                                                  mocked_urlFor, mocked_redirect):
        # Test to ensure that when this method is called with an authorized user and
        #  a partial state already in the DB, this method calls the createGoogleCalendar
        #  function and rolls back the DB if a failure state is received.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.mocked_integrationPart.reset_mock()
        self.mocked_bytesIO.reset_mock()
        self.mocked_pickle.reset_mock()
        self.resetAuthLevel()

        # Set the auth_level to be used for this test.
        self.mocked_authLevel.return_value = 3

        # Create the objects needed for this test
        desiredState = "ExampleState"
        expectedInfoID = 12
        expectedCreds = MagicMock()
        expectedResponse = Response(status=200)

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedInfoID,)  # First call returns the auth state
        ]

        # Configure the mocked gCalIntegratinator to behave as expected
        self.mocked_integrationPart.handleAuthResponse.return_value = expectedCreds

        # Configure the mocked createGoogleCalendar to behave as expected
        mocked_createGoogleCalendar.return_value = stdRet(-1, "NEGATIVE TEST RESULT")

        # Configure the mocked redirect object to return a Response object
        mocked_redirect.return_value = expectedResponse

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/GCalAuth",
                               query_string=dict(
                                   state=desiredState
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that createGoogleCalendar() gets called once
        mocked_createGoogleCalendar.assert_called_once_with(expectedInfoID)

        # Assert that the DB was rolled back
        self.mocked_appGlobals.conn.rollback.assert_called_once()

        # Assert that appGlobals.conn.commit was never called
        self.mocked_appGlobals.conn.commit.assert_not_called()

    @patch("integration.integrations.redirect", autospec=True)
    @patch("integration.integrations.url_for", autospec=True)
    @patch("integration.integrations.createGoogleCalendar", autospec=True)
    def test_withAuthorizedUser_withStateInDB_ifCalendarCreationPasses_commitsToDB(self, mocked_createGoogleCalendar,
                                                                                   mocked_urlFor, mocked_redirect):
        # Test to ensure that when this method is called with an authorized user and
        #  a partial state already in the DB, this method calls the createGoogleCalendar
        #  function and commits the changes to the DB if a success state is received.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.mocked_integrationPart.reset_mock()
        self.mocked_bytesIO.reset_mock()
        self.mocked_pickle.reset_mock()
        self.resetAuthLevel()

        # Set the auth_level to be used for this test.
        self.mocked_authLevel.return_value = 3

        # Create the objects needed for this test
        desiredState = "ExampleState"
        expectedInfoID = 12
        expectedCreds = MagicMock()
        expectedResponse = Response(status=200)

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedInfoID,)  # First call returns the auth state
        ]

        # Configure the mocked gCalIntegratinator to behave as expected
        self.mocked_integrationPart.handleAuthResponse.return_value = expectedCreds

        # Configure the mocked createGoogleCalendar to behave as expected
        mocked_createGoogleCalendar.return_value = stdRet(1, "SUCCESS TEST RESULT")

        # Configure the mocked redirect object to return a Response object
        mocked_redirect.return_value = expectedResponse

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/GCalAuth",
                               query_string=dict(
                                   state=desiredState
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that createGoogleCalendar() gets called once
        mocked_createGoogleCalendar.assert_called_once_with(expectedInfoID)

        # Assert that the DB was NOT rolled back
        self.mocked_appGlobals.conn.rollback.assert_not_called()

        # Assert that appGlobals.conn.commit was called
        self.mocked_appGlobals.conn.commit.assert_called_once()

    @patch("integration.integrations.redirect", autospec=True)
    @patch("integration.integrations.url_for", autospec=True)
    @patch("integration.integrations.createGoogleCalendar", autospec=True)
    def test_withAuthorizedUser_withStateInDB_returnsRedirectToManHallPage(self, mocked_createGoogleCalendar,
                                                                           mocked_urlFor, mocked_redirect):
        # Test to ensure that when this method is called with an authorized user and
        #  a partial state already in the DB, this method returns a redirect to the
        #  Manage Hall page.

        # -- Arrange --

        # Reset all of the mocked objects that will be used in this test
        self.mocked_authLevel.reset_mock()
        self.mocked_appGlobals.conn.reset_mock()
        self.mocked_integrationPart.reset_mock()
        self.mocked_bytesIO.reset_mock()
        self.mocked_pickle.reset_mock()
        self.resetAuthLevel()

        # Set the auth_level to be used for this test.
        self.mocked_authLevel.return_value = 3

        # Create the objects needed for this test
        desiredState = "ExampleState"
        expectedInfoID = 12
        expectedCreds = MagicMock()
        expectedResponse = Response(status=200)

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (expectedInfoID,)  # First call returns the auth state
        ]

        # Configure the mocked gCalIntegratinator to behave as expected
        self.mocked_integrationPart.handleAuthResponse.return_value = expectedCreds

        # Configure the mocked createGoogleCalendar to behave as expected
        mocked_createGoogleCalendar.return_value = stdRet(1, "SUCCESS TEST RESULT")

        # Configure the mocked redirect object to return a Response object
        mocked_redirect.return_value = expectedResponse

        # -- Act --

        # Make a request to the desired API endpoint
        resp = self.server.get("/int/GCalAuth",
                               query_string=dict(
                                   state=desiredState
                               ),
                               base_url=self.mocked_appGlobals.baseOpts["HOST_URL"])

        # -- Assert --

        # Assert that the url_for function was called with the appropriate parameters
        mocked_urlFor.assert_called_once_with("hall_bp.manHall")

        # Assert that the redirect function was called with the result of url_for()
        mocked_redirect.assert_called_once_with(mocked_urlFor(""))

        # Assert that we received the response we expected
        self.assertEqual(expectedResponse.status_code, resp.status_code)
