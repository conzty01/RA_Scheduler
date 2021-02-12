from integration.gCalIntegration import gCalIntegratinator, Event
from googleapiclient.errors import HttpError
from unittest.mock import MagicMock, patch
import unittest


class TestGCalIntegratinatorObject(unittest.TestCase):
    def setUp(self):

        # Mock the os.environ method

        # Helper Dict for holding the os.environ configuration
        self.helper_osEnviron = {"CLIENT_ID": "TEST CLIENT_ID",
                                      "PROJECT_ID": "TEST PROJECT_ID",
                                      "AUTH_URI": "TEST AUTH_URI",
                                      "TOKEN_URI": "TEST TOKEN_URI",
                                      "AUTH_PROVIDER_X509_CERT_URL": "TEST AUTH_PROVIDER_X509_CERT_URL",
                                      "CLIENT_SECRET": "TEST CLIENT_SECRET",
                                      "REDIRECT_URIS": "TEST1,TEST2,TEST3,TEST4",
                                      "JAVASCRIPT_ORIGINS": "TEST5,TEST6"}

        # Create a dictionary patcher for the os.environ method
        self.patcher_os = patch.dict("integration.gCalIntegration.os.environ", self.helper_osEnviron)

        self.patcher_flow = patch("integration.gCalIntegration.google_auth_oauthlib.flow.Flow", autospec=True)

        # Create the patcher for the googleapiclient
        self.patcher_build = patch("integration.gCalIntegration.build", autospec=True)

        # Start the os patcher (No mock object is returned since we used patch.dict()
        self.patcher_os.start()

        # Start the flow patcher
        self.mocked_flow = self.patcher_flow.start()

        # Create the mocked .from_client_config.return_value object
        self.authorizationURL = "TEST AUTH URL"
        self.credentials = "TEST CREDENTIALS"

        mocked_flowInstance_Config = {
            "redirect_uri": "",
            "authorization_url.return_value": self.authorizationURL,
            "fetch_token.return_value": None,
            "credentials": self.credentials
        }
        self.mocked_flowInstance = MagicMock(**mocked_flowInstance_Config)

        # Mock the google_auth_oauthlib.flow.Flow module
        mocked_flow_config = {
            "from_client_config": MagicMock(return_value=self.mocked_flowInstance),
            "redirect_uri": "",
            "authorization_url": MagicMock(return_value=self.authorizationURL),
            "fetch_token": MagicMock(return_value=None),
            "credentials": MagicMock(return_value=self.credentials)}

        self.mocked_flow.configure_mock(**mocked_flow_config)

        # Start the googleapiclient patcher
        self.mocked_build = self.patcher_build.start()

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
        self.patcher_build.stop()
        self.patcher_flow.stop()
        self.patcher_os.stop()

        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

    def test_HasExpectedMethods(self):
        # Test to make sure the Integration Object has the following methods:
        #  - generateAuthURL
        #  - handleAuthResponse
        #  - createGoogleCalendar
        #  - exportScheduleToGoogleCalendar
        #  - _checkIfValidCreds

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        #  --   ACT   --
        #  -- ASSERT  --

        self.assertTrue(hasattr(gCalIntegratinator, "_getCredsFromEnv"))
        self.assertTrue(hasattr(gCalIntegratinator, "_validateCredentials"))
        self.assertTrue(hasattr(gCalIntegratinator, "generateAuthURL"))
        self.assertTrue(hasattr(gCalIntegratinator, "handleAuthResponse"))
        self.assertTrue(hasattr(gCalIntegratinator, "createGoogleCalendar"))
        self.assertTrue(hasattr(gCalIntegratinator, "BaseGCalIntegratinatorException"))
        self.assertTrue(hasattr(gCalIntegratinator, "CalendarCreationError"))
        self.assertTrue(hasattr(gCalIntegratinator, "InvalidCalendarIdError"))
        self.assertTrue(hasattr(gCalIntegratinator, "InvalidCalendarCredentialsError"))
        self.assertTrue(hasattr(gCalIntegratinator, "ExpiredCalendarCredentialsError"))
        self.assertTrue(hasattr(gCalIntegratinator, "ScheduleExportError"))
        self.assertTrue(hasattr(gCalIntegratinator, "UnexpectedError"))

    def test_HasExpectedProperties(self):
        # Test to make sure the Integration Object has the following properties:
        #  - flow            :: Flow
        #  - serviceName     :: str
        #  - serviceVersion  :: str
        #  - scopes          :: list<str>

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()

        # Create a gCalIntegratinator
        gCalIntObj = gCalIntegratinator()

        #  --   ACT   --
        #  -- ASSERT  --

        self.assertIsInstance(gCalIntObj.serviceName, str)
        self.assertIsInstance(gCalIntObj.serviceVersion, str)
        self.assertIsInstance(gCalIntObj.scopes, list)
        # The following asserts that the .flow attribute is a Mock object instead of a true Flow
        #  object. This is because we mock the Flow object from a module level for these tests.
        #  As a result, if the .flow attribute is a Mock object, then we know it was created
        #  through the module as we would expect.
        self.assertIsInstance(gCalIntObj.flow, MagicMock)

    def test_HasExpectedDefaultScopes(self):
        # Test to make sure the Integration Object has the default scopes:
        #  - https://www.googleapis.com/auth/calendar.app.created
        #  - https://www.googleapis.com/auth/calendar.calendarlist.readonly

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()

        # The default scopes we would expect to use
        defaultScopes = ['https://www.googleapis.com/auth/calendar.app.created',
                         'https://www.googleapis.com/auth/calendar.calendarlist.readonly']

        gCalIntObj = gCalIntegratinator()

        #  --   ACT   --
        #  -- ASSERT  --
        self.assertEqual(gCalIntObj.scopes, defaultScopes)

    def test_UsesProvidedScopes(self):
        # Test to make sure the Integration Object uses the scopes passed
        #  in to it
        #  - https://www.googleapis.com/auth/calendar.app.created
        #  - https://www.googleapis.com/auth/calendar.calendarlist.readonly

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()

        # The "scopes" we are passing in
        newScopes = ['TEST SCOPE 1', 'TEST SCOPE 1']

        gCalIntObj = gCalIntegratinator(newScopes)

        #  --   ACT   --
        #  -- ASSERT  --
        self.assertEqual(gCalIntObj.scopes, newScopes)

    def test_HasExpectedFlow(self):
        # Test to ensure that the Google API Flow is created
        #  as expected

        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()

        # Configure the mocked_os to return results as we would expect

        # The mocked_os object has been created via the @patch decorator.

        # The expected .__appCreds that should be passed into the flow upon construction
        expectedConfigFormat = {
            "web": {
                "client_id": self.helper_osEnviron["CLIENT_ID"],
                "project_id": self.helper_osEnviron["PROJECT_ID"],
                "auth_uri": self.helper_osEnviron["AUTH_URI"],
                "token_uri": self.helper_osEnviron["TOKEN_URI"],
                "auth_provider_x509_cert_url": self.helper_osEnviron["AUTH_PROVIDER_X509_CERT_URL"],
                "client_secret": self.helper_osEnviron["CLIENT_SECRET"],
                "redirect_uris": [entry for entry in self.helper_osEnviron["REDIRECT_URIS"].split(",")],
                "javascript_origins": [entry for entry in self.helper_osEnviron["JAVASCRIPT_ORIGINS"].split(",")]
            }
        }

        # The following are the default scopes which we also expect to be passed into the
        #  flow upon construction.
        expectedScopes = ['https://www.googleapis.com/auth/calendar.app.created',
                          'https://www.googleapis.com/auth/calendar.calendarlist.readonly']

        #  -- ACT --

        # Build the gCaleIntegratinator that will have the mocked Flow and os
        gCalIntObj = gCalIntegratinator()

        #  -- ASSERT --

        self.mocked_flow.from_client_config.assert_called_once_with(
                                    expectedConfigFormat, scopes=expectedScopes)

    def test_UsesCalendarService(self):
        # Test to make sure the Integration Object has a serviceName of 'calendar'

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  --   ACT   --
        #  -- ASSERT  --

        self.assertEqual(gCalIntObj.serviceName, "calendar")

    def test_UsesCalendarVersion3(self):
        # Test to make sure the Integration Object has a serviceVersion of 'v3':

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  --   ACT   --
        #  -- ASSERT  --

        self.assertEqual(gCalIntObj.serviceVersion, "v3")

    def test_checkIfValidCreds_AcceptsValidCreds(self):
        # Test to make sure _checkIfValidCreds accepts valid credentials

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()

        # Create the Mocked objects
        mockedClientCreds = MagicMock()
        mocked_ExpiredMethod = MagicMock()
        mocked_RefreshTokenMethod = MagicMock()
        mocked_RefreshMethod = MagicMock()

        # Mock the client credentials
        credsMockAttrs = {
            "valid.return_value": True,
            "expired.return_value": mocked_ExpiredMethod,
            "refresh_token.return_value": mocked_RefreshTokenMethod,
            "refresh.return_value": mocked_RefreshMethod
        }

        # Configure the Mocked Client Creds
        mockedClientCreds.configure_mock(**credsMockAttrs)

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  -- ACT --

        validCreds = gCalIntObj._validateCredentials(mockedClientCreds)

        #  -- ASSERT --

        # Assert that we received a validation status of 1
        self.assertEqual(mockedClientCreds, validCreds)

        # Assert that the .expired .refresh_token properties
        #  and .refresh method were not called
        mocked_RefreshMethod.assert_not_called()
        mocked_ExpiredMethod.assert_not_called()
        mocked_RefreshTokenMethod.assert_not_called()

    def test_checkIfValidCreds_RefreshesExpiredCredentials_WithRefreshToken(self):
        # Test to make sure _checkIfValidCreds attempts to refresh credentials
        #  that have expired but do have a refresh token associated with them.

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        # Create the Mocked objects
        mockedClientCreds = MagicMock()
        mocked_RefreshMethod = MagicMock()

        # Mock the client credentials
        credsMockAttrs = {
            "valid": False,
            "expired": True,
            "refresh_token": True,
            "refresh": mocked_RefreshMethod
        }

        # Configure the Mocked Client Creds
        mockedClientCreds.configure_mock(**credsMockAttrs)

        #  -- ACT --

        validCreds = gCalIntObj._validateCredentials(mockedClientCreds)

        #  -- ASSERT --

        # Assert that we received a validation status of 0
        self.assertEqual(mockedClientCreds, validCreds)

        # Assert that .refresh was called passing it a Request() Object
        mocked_RefreshMethod.assert_called_once()

    def test_checkIfValidCreds_ReturnsExpectedStatus_WithoutRefreshToken(self):
        # Test to make sure _checkIfValidCreds returns the appropriate validation
        #  status if it is passed expired credentials that do not have a refresh
        #  token associated with them.

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        # Create the Mocked objects
        mockedClientCreds = MagicMock()
        mocked_RefreshMethod = MagicMock()

        # Mock the client credentials
        credsMockAttrs = {
            "valid": False,
            "expired": True,
            "refresh_token": False,
            "refresh": mocked_RefreshMethod
        }

        # Configure the Mocked Client Creds
        mockedClientCreds.configure_mock(**credsMockAttrs)

        #  -- ACT --
        #  -- ASSERT --

        # Call the method being tested and assert that we received an ExpiredCalendarCredentialsError
        self.assertRaises(
            gCalIntegratinator.ExpiredCalendarCredentialsError,     # Expected Exception
            gCalIntObj._validateCredentials,                        # Method to be called
            mockedClientCreds                                       # Parameters to pass to method
        )

        # Assert that .refresh was not called
        mocked_RefreshMethod.assert_not_called()

    def test_checkIfValidCreds_HandlesInvalidCredentials(self):
        # Test to make sure _checkIfValidCreds handles a scenario where it
        #  receives an object that is not a Google Credential

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        # Create the Mocked objects
        #  In this test, when the credentials are used, they should raise
        #   an AttributeError
        mockedClientCreds = MagicMock()
        mocked_RefreshMethod = MagicMock(side_effect=AttributeError)

        # Mock the client credentials
        credsMockAttrs = {
            "valid": False,
            "expired": True,
            "refresh_token": True,
            "refresh": mocked_RefreshMethod
        }

        # Configure the Mocked Client Creds
        mockedClientCreds.configure_mock(**credsMockAttrs)

        #  -- ACT --
        #  -- ASSERT --

        # Call the method being tested and assert that we received an InvalidCalendarCredentialsError
        self.assertRaises(
            gCalIntegratinator.InvalidCalendarCredentialsError,     # Expected Exception
            gCalIntObj._validateCredentials,                        # Method to be called
            mockedClientCreds                                       # Parameters to pass to method
        )

        # Assert that .refresh was called once
        mocked_RefreshMethod.assert_called_once()

    def test_checkIfValidCreds_HandlesUnknownError(self):
        # Test to make sure _checkIfValidCreds handles if an unknown error
        #  occurs when attempting to validate credentials

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        # Create the Mocked objects
        #  In this test, when the credentials are called, they should raise
        #   an AttributeError
        mockedClientCreds = MagicMock()
        mocked_RefreshMethod = MagicMock(side_effect=KeyError("Test Error"))

        # Mock the client credentials
        credsMockAttrs = {
            "valid": False,
            "expired": True,
            "refresh_token": True,
            "refresh": mocked_RefreshMethod
        }

        # Configure the Mocked Client Creds
        mockedClientCreds.configure_mock(**credsMockAttrs)

        #  -- ACT --
        #  -- ASSERT --

        # Call the method being tested and assert that we received an UnexpectedError
        self.assertRaises(
            gCalIntegratinator.UnexpectedError,     # Expected Exception
            gCalIntObj._validateCredentials,        # Method to be called
            mockedClientCreds                       # Parameters to pass to method
        )

    def test_getCredsFromEnv_ReturnsConfigurationInExpectedFormat(self):
        # Test to ensure that the proper values get imported from
        #  the environment.

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()

        # Create the Mocked objects

        # The expected dictionary to be returned
        expectedConfigFormat = {
            "web": {
                "client_id": self.helper_osEnviron["CLIENT_ID"],
                "project_id": self.helper_osEnviron["PROJECT_ID"],
                "auth_uri": self.helper_osEnviron["AUTH_URI"],
                "token_uri": self.helper_osEnviron["TOKEN_URI"],
                "auth_provider_x509_cert_url": self.helper_osEnviron["AUTH_PROVIDER_X509_CERT_URL"],
                "client_secret": self.helper_osEnviron["CLIENT_SECRET"],
                "redirect_uris": [entry for entry in self.helper_osEnviron["REDIRECT_URIS"].split(",")],
                "javascript_origins": [entry for entry in self.helper_osEnviron["JAVASCRIPT_ORIGINS"].split(",")]
            }
        }

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  -- ACT --

        returnConfigurationDict = gCalIntObj._getCredsFromEnv()

        #  -- ASSERT --

        # Ensure that the return dict is in the format the Flow expects
        self.assertEqual(returnConfigurationDict, expectedConfigFormat)

    def test_generateAuthURL_SetsRedirectURI(self):
        # Test to ensure that generateAuthURL sets the redirect_uri
        #  of the flow

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        testAuthURI = self.authorizationURL

        #  -- ACT --

        # Build the gCaleIntegratinator that will have use the mocked Flow
        gCalIntObj = gCalIntegratinator()

        # Run the auth url generation process
        gCalIntObj.generateAuthURL(testAuthURI)

        #  -- ASSERT --

        # Make sure that the redirect_uri has been set
        self.assertEqual(self.mocked_flowInstance.redirect_uri, testAuthURI)

    def test_generateAuthURL_PassesExpectedParametersToFlowAuthorizationUrl(self):
        # Test to ensure that generateAuthURL passes the expected parameters into
        #  flow.authorization_url()

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        #  -- ACT --

        # Build the gCaleIntegratinator that will have use the mocked Flow
        gCalIntObj = gCalIntegratinator()

        # Run the auth url generation process
        gCalIntObj.generateAuthURL("TEST")

        #  -- ASSERT --

        # Make sure that the expected parameters were passed to the authorization_url
        #  method within the mocked Flow
        self.mocked_flowInstance.authorization_url.assert_called_once_with(access_type="offline",
                                                                           include_granted_scopes="true",
                                                                           prompt="select_account")

    def test_generateAuthURL_ReturnsAuthorizationURL(self):
        # Test to ensure that generateAuthURL returns an authorization url

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        #  -- ACT --

        # Build the gCaleIntegratinator that will have use the mocked Flow
        gCalIntObj = gCalIntegratinator()

        # Run the auth url generation process
        result = gCalIntObj.generateAuthURL("TEST")

        #  -- ASSERT --
        self.mocked_flowInstance.authorization_url.assert_called_once()
        self.assertEqual(self.authorizationURL, result)

    def test_handleAuthResponse_SetsRedirectURI(self):
        # Test to ensure that handleAuthResponse sets the flow's redirect_uri

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        testRedirectURI = "TEST_AUTH_URL"
        testAuthResponse = ""

        #  -- ACT --

        # Build the gCaleIntegratinator that will have use the mocked Flow
        gCalIntObj = gCalIntegratinator()

        # Run the auth url generation process
        gCalIntObj.handleAuthResponse(testAuthResponse, testRedirectURI)

        #  -- ASSERT --

        # Make sure that the redirect_uri has been set
        self.assertEqual(self.mocked_flowInstance.redirect_uri, testRedirectURI)

    def test_handleAuthResponse_FetchesTheFlowToken(self):
        # Test to ensure that handleAuthResponse calls flow.fetch_token
        #  while passing it the authorization_response

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        testRedirectURI = "TEST_AUTH_URL"

        #  -- ACT --

        # Build the gCaleIntegratinator that will have use the mocked Flow
        gCalIntObj = gCalIntegratinator()

        # Run the auth url generation process
        gCalIntObj.handleAuthResponse(None, testRedirectURI)

        #  -- ASSERT --

        # Make sure that the redirect_uri has been set
        self.assertEqual(self.mocked_flowInstance.redirect_uri, testRedirectURI)

    def test_handleAuthResponse_ReturnsFlowCredentials(self):
        # Test to ensure that handleAuthResponse returns the flow.credentials

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        testRedirectURI = "TEST_AUTH_URL"

        #  -- ACT --

        # Build the gCaleIntegratinator that will have use the mocked Flow
        gCalIntObj = gCalIntegratinator()

        # Run the auth url generation process
        result = gCalIntObj.handleAuthResponse(None, testRedirectURI)

        #  -- ASSERT --

        # Make sure that the redirect_uri has been set
        self.assertEqual(self.credentials, result)

    def test_createGoogleCalendar_checksIfCredentialsAreValid(self):
        # Test to ensure that createGoogleCalendar checks to ensure
        #  that the passed credentials are valid

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()
        self.mocked_build.reset_mock()

        # Mock the client credentials
        mocked_creds = MagicMock(**{
            "valid": False,
            "expired": True,
            "refresh_token": True,
            "refresh": MagicMock(side_effect=AttributeError)
        })

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  -- ACT --
        #  -- ASSERT --

        # Call the createGoogleCalendar method and assert that we received an
        #  InvalidCalendarCredentialsError
        self.assertRaises(
            gCalIntegratinator.InvalidCalendarCredentialsError,     # Expected Exception
            gCalIntObj.createGoogleCalendar,                        # Method to be called
            mocked_creds                                            # Parameters to pass to method
        )

    def test_createGoogleCalendar_buildsCalendarV3Service(self):
        # Test to ensure that createGoogleCalendar builds the Calendar V3
        #  service with the client credentials

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()
        self.mocked_build.reset_mock()

        # Mock the client credentials
        mocked_creds = MagicMock(**{"valid": True})

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  -- ACT --

        # Call the createGoogleCalendar method
        gCalIntObj.createGoogleCalendar(mocked_creds)

        #  -- ASSERT --
        self.mocked_build.assert_called_once_with("calendar", "v3", credentials=mocked_creds)

    def test_createGoogleCalendar_InsertsExpectedCalendarBody(self):
        # Test to ensure that createGoogleCalendar calls the Google Calendar
        #  api to insert a calendar using the expected body

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        # Mock the client credentials
        mocked_creds = MagicMock(**{"valid": True})

        # Get the mocked "service" that is returned from the build function
        mocked_service = self.mocked_build("calendar", "v3", credentials=mocked_creds)

        # Reset the mocked "build" function so that the last call does not
        #  count towards it
        self.mocked_build.reset_mock()

        # Create the expected calendar body object
        expectedCalBody = {
            "summary": "RA Duty Schedule",
            "description": "Calendar for the Resident Assistant Duty Schedule.\n\nCreated and added to by the RA Duty Scheduler Application (RADSA)."
        }

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  -- ACT --

        # Call the createGoogleCalendar method
        gCalIntObj.createGoogleCalendar(mocked_creds)

        #  -- ASSERT --
        mocked_service.calendars().insert.assert_called_once_with(body=expectedCalBody)
        mocked_service.calendars().insert().execute.assert_called_once()

    def test_createGoogleCalendar_ReturnsNewGoogleCalendarId(self):
        # Test to ensure that createGoogleCalendar returns the newly
        #  created Google calendar ID

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        # Mock the client credentials
        mocked_creds = MagicMock(**{"valid": True})

        # Get the mocked "service" that is returned from the build function
        mocked_service = self.mocked_build("calendar", "v3", credentials=mocked_creds)

        # Reset the mocked "build" function so that the last call does not
        #  count towards it
        self.mocked_build.reset_mock()

        # Set up the mocked service to return a dict object with an "id" key
        expectedID = "TEST CALENDAR ID"
        mocked_service.calendars().insert().execute = MagicMock(return_value={"id": expectedID})

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  -- ACT --

        # Call the createGoogleCalendar method
        result = gCalIntObj.createGoogleCalendar(mocked_creds)

        #  -- ASSERT --
        self.assertEqual(expectedID, result)

    def test_exportScheduleToGoogleCalendar_checksIfCredentialsAreValid(self):
        # Test to ensure that exportScheduleToGoogleCalendar checks to ensure
        #  that the passed credentials are valid

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()
        self.mocked_build.reset_mock()

        # Mock the client credentials
        mocked_creds = MagicMock(**{
            "valid": False,
            "expired": True,
            "refresh_token": True,
            "refresh": MagicMock(side_effect=AttributeError)
        })

        # Create the calendarId and schedule objects that get passed in
        calendarId = "TEST CALENDAR ID"
        schedule = []
        desiredFlagLabel = "On-Call"

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  -- ACT --
        #  -- ASSERT --

        # Call the createGoogleCalendar method and assert that we received an
        #  InvalidCalendarCredentialsError
        self.assertRaises(
            gCalIntegratinator.InvalidCalendarCredentialsError,         # Expected Exception
            gCalIntObj.exportScheduleToGoogleCalendar,                  # Method to be called
            mocked_creds, calendarId, schedule, desiredFlagLabel        # Parameters to pass to method
        )

    def test_exportScheduleToGoogleCalendar_buildsCalendarV3Service(self):
        # Test to ensure that exportScheduleToGoogleCalendar builds the
        #  appropriate Calendar V3 Service

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()
        self.mocked_build.reset_mock()

        # Mock the client credentials
        mocked_creds = MagicMock(**{"valid": True})

        # Create the calendarId and schedule objects that get passed in
        calendarId = "TEST CALENDAR ID"
        schedule = []
        desiredFlagLabel = "On-Call"

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  -- ACT --

        # Call the createGoogleCalendar method
        gCalIntObj.exportScheduleToGoogleCalendar(mocked_creds, calendarId, schedule, desiredFlagLabel)

        #  -- ASSERT --
        self.mocked_build.assert_called_once_with("calendar", "v3", credentials=mocked_creds)

    def test_exportScheduleToGoogleCalendar_HandlesFindingExistingGoogleCalendar(self):
        # Test to ensure that exportScheduleToGoogleCalendar checks to ensure
        #  that the expected calendar exists for the user
        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        # Mock the client credentials
        mocked_creds = MagicMock(**{"valid": True})

        # Get the mocked "service" that is returned from the build function
        mocked_service = self.mocked_build("calendar", "v3", credentials=mocked_creds)

        # Reset the mocked "build" function so that the last call does not
        #  count towards it
        self.mocked_build.reset_mock()

        # Create the calendarId and schedule objects that get passed in
        calendarId = "TEST CALENDAR ID"
        schedule = [{
            "start": "00/00/0000",
            "title": "TEST EVENT TITLE",
            "extendedProps": {
                  "dutyType": "std",
                  "flagged": True,
                  "pts": 1
            }
        }]
        desiredFlagLabel = "On-Call"

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  -- ACT --

        # Call the createGoogleCalendar method
        gCalIntObj.exportScheduleToGoogleCalendar(mocked_creds, calendarId, schedule, desiredFlagLabel)

        #  -- ASSERT --
        # Assert that the Integration Object queried Google for the calendar
        mocked_service.calendarList().get.assert_called_once_with(calendarId=calendarId)
        mocked_service.calendarList().get().execute.assert_called_once()

    def test_exportScheduleToGoogleCalendar_GeneratesNewCalendarWhenOneDoesNotExist(self):
        # Test to ensure that exportScheduleToGoogleCalendar handles a case where
        #  it is unable to locate an existing calendar for the user

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        # Mock the client credentials
        mocked_creds = MagicMock(**{"valid": True})

        # Get the mocked "service" that is returned from the build function
        mocked_service = self.mocked_build("calendar", "v3", credentials=mocked_creds)

        # Create Mocks for the HttpError to use when attempting to print
        mocked_response = MagicMock(**{
            "reason": None,
            "status": 999
        })

        # Configure the mocked service to raise an HttpError when called
        mocked_service.calendarList().get().execute.side_effect = HttpError(
            mocked_response,
            bytes("Test".encode("UTF-8"))
        )

        # Reset the mocked "build" function so that the last call does not
        #  count towards it
        self.mocked_build.reset_mock()

        # Create the calendarId and schedule objects that get passed in
        calendarId = "TEST CALENDAR ID"
        schedule = [{
            "start": "00/00/0000",
            "title": "TEST EVENT TITLE",
            "extendedProps": {
                "dutyType": "std",
                "flagged": False,
                "pts": 1
            }
        }]
        desiredFlagLabel = "On-Call"

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  -- ACT --

        # Call the createGoogleCalendar method
        gCalIntObj.exportScheduleToGoogleCalendar(mocked_creds, calendarId, schedule, desiredFlagLabel)

        #  -- ASSERT --
        # Assert that the Integration Object queried Google for the calendar
        mocked_service.calendarList().get.assert_called_once_with(calendarId=calendarId)
        mocked_service.calendarList().get().execute.assert_called_once()

        # Assert that, when no calendar was returned (HttpError), a calendar was created
        #  via the API
        mocked_service.calendars().insert().execute.assert_called_once()

    def test_exportScheduleToGoogleCalendar_SendsEntireScheduleToGoogleCalendarAPI(self):
        # Test to ensure that exportScheduleToGoogleCalendar sends the entire schedule
        #  to the Google Calendar API

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        # Mock the client credentials
        mocked_creds = MagicMock(**{"valid": True})

        # Get the mocked "service" that is returned from the build function
        mocked_service = self.mocked_build("calendar", "v3", credentials=mocked_creds)

        # Reset the mocked "build" function so that the last call does not
        #  count towards it
        self.mocked_build.reset_mock()

        # Create the calendarId and schedule objects that get passed in
        calendarId = "TEST CALENDAR ID"
        schedule = []
        for i in range(12):
            schedule.append({
                "start": "00/00/0000",
                "title": "TEST EVENT TITLE",
                "extendedProps": {
                    "dutyType": "std",
                    "flagged": False,
                    "pts": 1
                }
            })
        desiredFlagLabel = "On-Call"

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  -- ACT --

        # Call the createGoogleCalendar method
        result = gCalIntObj.exportScheduleToGoogleCalendar(mocked_creds, calendarId, schedule, desiredFlagLabel)

        #  -- ASSERT --
        mocked_service.events().insert.assert_called()

        # Assert that the events().insert() was only called the same number of times
        #  as the number of days in the schedule
        numberEventsAdded = mocked_service.events().insert().execute.call_count
        self.assertEqual(len(schedule), numberEventsAdded)

        # Assert that the retun indicates that the export was successful
        self.assertIsNone(result)

    def test_exportScheduleToGoogleCalendar_withFlaggedDuty_BuildAppropriateEventObject(self):
        # Test to ensure that exportScheduleToGoogleCalendar formats the Event title and
        #  description appropriately when the duty is flagged.

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        # Mock the client credentials
        mocked_creds = MagicMock(**{"valid": True})

        # Get the mocked "service" that is returned from the build function
        mocked_service = self.mocked_build("calendar", "v3", credentials=mocked_creds)

        # Reset the mocked "build" function so that the last call does not
        #  count towards it
        self.mocked_build.reset_mock()

        # Create the calendarId and schedule objects that get passed in
        calendarId = "TEST CALENDAR ID"
        startDate = "00/00/0000"
        title = "TEST TITLE"
        schedule = [{
            "start": startDate,
            "title": title,
            "extendedProps": {
                "dutyType": "std",
                "flagged": True,
                "pts": 1
            }
        }]
        desiredFlagLabel = "On-Call"

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        # Create an Event object that we would expect to see passed to events().insert()
        expectedEventObj = Event(
            title + " ({})".format(desiredFlagLabel),
            title + " has been assigned for {} duty.".format(desiredFlagLabel),
            startDate
        )

        #  -- ACT --

        # Call the createGoogleCalendar method
        gCalIntObj.exportScheduleToGoogleCalendar(mocked_creds, calendarId, schedule, desiredFlagLabel)

        #  -- ASSERT --
        mocked_service.events().insert.assert_called_with(calendarId=calendarId,
                                                          body=expectedEventObj.getBody(),
                                                          supportsAttachments=False)

    def test_exportScheduleToGoogleCalendar_withoutFlaggedDuty_BuildAppropriateEventObject(self):
        # Test to ensure that exportScheduleToGoogleCalendar formats the Event title and
        #  description appropriately when the duty is NOT flagged.

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        # Mock the client credentials
        mocked_creds = MagicMock(**{"valid": True})

        # Get the mocked "service" that is returned from the build function
        mocked_service = self.mocked_build("calendar", "v3", credentials=mocked_creds)

        # Reset the mocked "build" function so that the last call does not
        #  count towards it
        self.mocked_build.reset_mock()

        # Create the calendarId and schedule objects that get passed in
        calendarId = "TEST CALENDAR ID"
        startDate = "00/00/0000"
        title = "TEST TITLE"
        schedule = [{
            "start": startDate,
            "title": title,
            "extendedProps": {
                "dutyType": "std",
                "flagged": False,
                "pts": 1
            }
        }]
        desiredFlagLabel = "On-Call"

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        # Create an Event object that we would expect to see passed to events().insert()
        expectedEventObj = Event(
            title,
            title + " has been assigned for duty.",
            startDate
        )

        #  -- ACT --

        # Call the createGoogleCalendar method
        gCalIntObj.exportScheduleToGoogleCalendar(mocked_creds, calendarId, schedule, desiredFlagLabel)

        #  -- ASSERT --
        mocked_service.events().insert.assert_called_with(calendarId=calendarId,
                                                          body=expectedEventObj.getBody(),
                                                          supportsAttachments=False)

    def test_exportScheduleToGoogleCalendar_HandlesUnknownHttpErrorFromEventCreation(self):
        # Test to ensure that exportScheduleToGoogleCalendar handles receiving an HttpError
        #  from the Google Calendar API when attempting to create new events

        #  -- ARRANGE --
        # Reset all of the mocked objects that will be used in this test
        self.mocked_flow.reset_mock()
        self.mocked_flowInstance.reset_mock()

        # Mock the client credentials
        mocked_creds = MagicMock(**{"valid": True})

        # Get the mocked "service" that is returned from the build function
        mocked_service = self.mocked_build("calendar", "v3", credentials=mocked_creds)

        # Create Mocks for the HttpError to use when attempting to print
        mocked_response = MagicMock(**{
            "reason": None,
            "status": 999
        })

        # Configure the mocked service to raise an HttpError when called
        mocked_service.events().insert().execute.side_effect = HttpError(
            mocked_response,
            bytes("Test".encode("UTF-8"))
        )

        # Reset the mocked "build" function so that the last call does not
        #  count towards it
        self.mocked_build.reset_mock()

        # Create the calendarId and schedule objects that get passed in
        calendarId = "TEST CALENDAR ID"
        schedule = [{
            "start": "00/00/0000",
            "title": "TEST EVENT TITLE",
            "extendedProps": {
                "dutyType": "std",
                "flagged": False,
                "pts": 1
            }
        }]
        desiredFlagLabel = "On-Call"

        # Create the gCalIntObj
        gCalIntObj = gCalIntegratinator()

        #  -- ACT --
        #  -- ASSERT --

        # Call the createGoogleCalendar method and assert that we received an
        #  InvalidCalendarCredentialsError
        self.assertRaises(
            gCalIntegratinator.ScheduleExportError,                 # Expected Exception
            gCalIntObj.exportScheduleToGoogleCalendar,              # Method to be called
            mocked_creds, calendarId, schedule, desiredFlagLabel    # Parameters to pass to method
        )

        # Assert that the Integration Object queried Google for the calendar
        mocked_service.events().insert().execute.assert_called_once()


class TestEventObject(unittest.TestCase):
    def setUp(self):
        self.summary = "This is a title"
        self.description = "This is a description"
        self.date = "This is a date string"

        self.event = Event(self.summary, self.description, self.date)

    def test_HasExpectedMethods(self):
        # Test to make sure the Event Object has the following methods:
        #  - getBody

        #  -- ARRANGE --
        #  --   ACT   --
        #  -- ASSERT  --

        self.assertTrue(hasattr(Event, "getBody"))

    def test_getBody_ReturnsExpectedBodyFormat(self):
        # Test to make sure that the Event's .getBody method
        #  returns the body is the format specified by Google

        #  -- ARRANGE --

        expectedFormat = {
            "summary": self.summary,
            "description": self.description,
            "start": {"date": self.date},
            "end": {"date": self.date},
            "status": "confirmed",
            "transparency": "opaque"
        }

        #  -- ACT --

        getBodyResult = self.event.getBody()

        #  -- ASSERT --

        self.assertEqual(getBodyResult, expectedFormat)


if __name__ == "__main__":
    unittest.main()
