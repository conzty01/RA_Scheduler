from gCalIntegration import gCalIntegratinator, Event
from google_auth_oauthlib.flow import Flow
from unittest.mock import MagicMock, patch
import unittest

class TestGCalIntegratinatorObject(unittest.TestCase):
    def setUp(self):
        # Create the gCalIntegrantinator object
        self.gCalIntObj = gCalIntegratinator()

        # # Mocked values
        # self.authorization_url = "https://success.html"
        # self.credentials = "VALID Credentials"
        #
        # # Replace the flow with a Mocked flow
        # flowMockAttrs = {
        #     "authorization_url.return_value" : self.authorization_url,
        #     "credentials.return_value" : self.credentials,
        # }
        #
        # flowMock = MagicMock()
        # flowMock.configure_mock(**flowMockAttrs)
        # self.gCalIntObj.flow = flowMock
        #
        #
        # # Replace client credentials with Mocked client credentials

    def test_HasExpectedMethods(self):
        # Test to make sure the Integration Object has the following methods:
        #  - generateAuthURL
        #  - handleAuthResponse
        #  - createGoogleCalendar
        #  - exportScheduleToGoogleCalendar
        #  - _checkIfValidCreds

        self.assertTrue(hasattr(gCalIntegratinator, "generateAuthURL"))
        self.assertTrue(hasattr(gCalIntegratinator, "handleAuthResponse"))
        self.assertTrue(hasattr(gCalIntegratinator, "createGoogleCalendar"))
        self.assertTrue(hasattr(gCalIntegratinator, "exportScheduleToGoogleCalendar"))
        self.assertTrue(hasattr(gCalIntegratinator, "_checkIfValidCreds"))
    def test_HasExpectedProperties(self):
        # Test to make sure the Integration Object has the following properties:
        #  - flow            :: Flow
        #  - serviceName     :: str
        #  - serviceVersion  :: str
        #  - scopes          :: list<str>

        self.assertEqual(type(self.gCalIntObj.flow), Flow)
        self.assertEqual(type(self.gCalIntObj.serviceName), str)
        self.assertEqual(type(self.gCalIntObj.serviceVersion), str)
        self.assertEqual(type(self.gCalIntObj.scopes), list)
    def test_HasExpectedDefaultScopes(self):
        # Test to make sure the Integration Object has the default scopes:
        #  - https://www.googleapis.com/auth/calendar.app.created
        #  - https://www.googleapis.com/auth/calendar.calendarlist.readonly

        defaultScopes = ['https://www.googleapis.com/auth/calendar.app.created',
                         'https://www.googleapis.com/auth/calendar.calendarlist.readonly']

        self.assertEqual(self.gCalIntObj.scopes, defaultScopes)
    @patch("gCalIntegration.google_auth_oauthlib.flow.Flow", autospec=True)
    @patch.dict("gCalIntegration.os.environ", {"CLIENT_ID": "TEST CLIENT_ID",
                                               "PROJECT_ID": "TEST PROJECT_ID",
                                               "AUTH_URI": "TEST AUTH_URI",
                                               "TOKEN_URI": "TEST TOKEN_URI",
                                               "AUTH_PROVIDER_X509_CERT_URL": "TEST AUTH_PROVIDER_X509_CERT_URL",
                                               "CLIENT_SECRET": "TEST CLIENT_SECRET",
                                               "REDIRECT_URIS": "TEST1,TEST2,TEST3,TEST4",
                                               "JAVASCRIPT_ORIGINS": "TEST5,TEST6"})
    def test_HasExpectedFlow(self, mocked_flow):
        # Test to ensure that the Google API Flow is created
        #  as expected

        #  -- ARRANGE --

        # Configure the mocked_os to return results as we would expect

        # The mocked_os object has been created via the @patch decorator.

        # The expected .__appCreds that should be passed into the flow upon construction
        expectedConfigFormat = {
            "web": {
                "client_id": "TEST CLIENT_ID",
                "project_id": "TEST PROJECT_ID",
                "auth_uri": "TEST AUTH_URI",
                "token_uri": "TEST TOKEN_URI",
                "auth_provider_x509_cert_url": "TEST AUTH_PROVIDER_X509_CERT_URL",
                "client_secret": "TEST CLIENT_SECRET",
                "redirect_uris": [entry for entry in "TEST1,TEST2,TEST3,TEST4".split(",")],
                "javascript_origins": [entry for entry in "TEST5,TEST6".split(",")]
            }
        }

        # The following are the default scopes which we also expect to be passed into the
        #  flow upon construction.
        expectedScopes = ['https://www.googleapis.com/auth/calendar.app.created',
                          'https://www.googleapis.com/auth/calendar.calendarlist.readonly']

        # Create the .from_client_config method for the mocked flow
        mocked_FromClientConfigMethod = MagicMock()

        # Pass the mocked .from_client_config method to the mocked_flow object
        mocked_flow.from_client_config = mocked_FromClientConfigMethod

        #  -- ACT --

        # Build the gCaleIntegratinator that will have the mocked Flow and os
        gCalIntObj = gCalIntegratinator()

        #  -- ASSERT --

        mocked_FromClientConfigMethod.assert_called_once_with(expectedConfigFormat, scopes=expectedScopes)

    def test_UsesCalendarService(self):
        # Test to make sure the Integration Object has a serviceName of 'calendar':

        self.assertEqual(self.gCalIntObj.serviceName, "calendar")
    def test_UsesCalendarVersion3(self):
        # Test to make sure the Integration Object has a serviceVersion of 'v3':

        self.assertEqual(self.gCalIntObj.serviceVersion, "v3")

    def test_checkIfValidCreds_AcceptsValidCreds(self):
        # Test to make sure _checkIfValidCreds accepts valid credentials

        #  -- ARRANGE --

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

        #  -- ACT --

        validationStatus = self.gCalIntObj._checkIfValidCreds(mockedClientCreds)

        #  -- ASSERT --

        # Assert that we received a validation status of 1
        self.assertEqual(validationStatus, 1)

        # Assert that the .expired .refresh_token properties
        #  and .refresh method were not called
        mocked_RefreshMethod.assert_not_called()
        mocked_ExpiredMethod.assert_not_called()
        mocked_RefreshTokenMethod.assert_not_called()
    def test_checkIfValidCreds_RefreshesExpiredCredentials_WithRefreshToken(self):
        # Test to make sure _checkIfValidCreds attempts to refresh credentials
        #  that have expired but do have a refresh token associated with them.

        #  -- ARRANGE --

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

        validationStatus = self.gCalIntObj._checkIfValidCreds(mockedClientCreds)

        #  -- ASSERT --

        # Assert that we received a validation status of 0
        self.assertEqual(validationStatus, 0)

        # Assert that .refresh was called passing it a Request() Object
        mocked_RefreshMethod.assert_called_once()
    def test_checkIfValidCreds_ReturnsExpectedStatus_WithoutRefreshToken(self):
        # Test to make sure _checkIfValidCreds returns the appropriate validation
        #  status if it is passed expired credentials that do not have a refresh
        #  token associated with them.

        #  -- ARRANGE --

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

        validationStatus = self.gCalIntObj._checkIfValidCreds(mockedClientCreds)

        #  -- ASSERT --

        # Assert that we received a validation status of -2
        self.assertEqual(validationStatus, -2)

        # Assert that .refresh was not called
        mocked_RefreshMethod.assert_not_called()
    def test_checkIfValidCreds_HandlesInvalidCredentials(self):
        # Test to make sure _checkIfValidCreds handles a scenario where it
        #  receives an object that is not a Google Credential

        #  -- ARRANGE --

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

        validationStatus = self.gCalIntObj._checkIfValidCreds(mockedClientCreds)

        #  -- ASSERT --

        # Assert that we received a validation status of -3
        self.assertEqual(validationStatus, -3)
    def test_checkIfValidCreds_HandlesUnknownError(self):
        # Test to make sure _checkIfValidCreds handles if an unknown error
        #  occurs when attempting to validate credentials

        #  -- ARRANGE --

        # Create the Mocked objects
        #  In this test, when the credentials are called, they should raise
        #   an AttributeError
        mockedClientCreds = MagicMock()
        mocked_RefreshMethod = MagicMock(side_effect=KeyError)

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

        validationStatus = self.gCalIntObj._checkIfValidCreds(mockedClientCreds)

        #  -- ASSERT --

        # Assert that we received a validation status of -3
        self.assertEqual(validationStatus, -1)

    @patch("gCalIntegration.os", autospec=True)
    def test_getCredsFromEnv_ReturnsConfigurationInExpectedFormat(self, mocked_os):
        # Test to ensure that the proper values get imported from
        #  the environment.

        #  -- ARRANGE --

        # Create the Mocked objects

        # Helper Dict to keep track of the keys we want
        helperDict = {
            "CLIENT_ID": "TEST CLIENT_ID",
            "PROJECT_ID": "TEST PROJECT_ID",
            "AUTH_URI": "TEST AUTH_URI",
            "TOKEN_URI": "TEST TOKEN_URI",
            "AUTH_PROVIDER_X509_CERT_URL": "TEST AUTH_PROVIDER_X509_CERT_URL",
            "CLIENT_SECRET": "TEST CLIENT_SECRET",
            "REDIRECT_URIS": "TEST1,TEST2,TEST3,TEST4",
            "JAVASCRIPT_ORIGINS": "TEST5,TEST6"
        }

        # Create the .environ Mock object
        mocked_EnvironMethod = MagicMock()
        mocked_EnvironMethod.__getitem__.side_effect = helperDict.__getitem__

        # Mock the os module
        osMockAttrs = {
            "environ": mocked_EnvironMethod
        }

        # The expected dictionary to be returned
        expectedConfigFormat = {
            "web": {
                "client_id": helperDict["CLIENT_ID"],
                "project_id": helperDict["PROJECT_ID"],
                "auth_uri": helperDict["AUTH_URI"],
                "token_uri": helperDict["TOKEN_URI"],
                "auth_provider_x509_cert_url": helperDict["AUTH_PROVIDER_X509_CERT_URL"],
                "client_secret": helperDict["CLIENT_SECRET"],
                "redirect_uris": [entry for entry in helperDict["REDIRECT_URIS"].split(",")],
                "javascript_origins": [entry for entry in helperDict["JAVASCRIPT_ORIGINS"].split(",")]
            }
        }

        # Configure the mocked_os
        mocked_os.configure_mock(**osMockAttrs)

        #  -- ACT --

        returnConfigurationDict = self.gCalIntObj._getCredsFromEnv()

        #  -- ASSERT --

        # Ensure that the return dict is in the format the Flow expects
        self.assertEqual(returnConfigurationDict, expectedConfigFormat)

    @patch("gCalIntegration.google_auth_oauthlib.flow.Flow", autospec=True)
    @patch.dict("gCalIntegration.os.environ", {"CLIENT_ID": "TEST CLIENT_ID",
                                               "PROJECT_ID": "TEST PROJECT_ID",
                                               "AUTH_URI": "TEST AUTH_URI",
                                               "TOKEN_URI": "TEST TOKEN_URI",
                                               "AUTH_PROVIDER_X509_CERT_URL": "TEST AUTH_PROVIDER_X509_CERT_URL",
                                               "CLIENT_SECRET": "TEST CLIENT_SECRET",
                                               "REDIRECT_URIS": "TEST1,TEST2,TEST3,TEST4",
                                               "JAVASCRIPT_ORIGINS": "TEST5,TEST6"})
    def test_generateAuthURL_SetsRedirectURI(self, mocked_flow):
        # Test to ensure that generateAuthURL sets the redirect_uri
        #  of the flow

        #  -- ARRANGE --

        testAuthURI = "TEST_AUTH_URL"

        # Create the result from .from_client_config
        mocked_FromClientConfigResult = MagicMock()

        # Add the mocked .from_client_config method to mocked flow
        mocked_flow.configure_mock(**{"from_client_config.return_value": mocked_FromClientConfigResult})

        # Since the .from_client_config method returns a Flow that is used by the gCalIntegratinator,
        #  we will create a new variable name for the same object to keep it clear in our heads
        #  as to how we want to use it.
        mocked_FlowInstance = mocked_FromClientConfigResult

        #  -- ACT --

        # Build the gCaleIntegratinator that will have use the mocked Flow
        gCalIntObj = gCalIntegratinator()

        # Run the auth url generation process
        gCalIntObj.generateAuthURL(testAuthURI)

        #  -- ASSERT --

        # Make sure that the redirect_uri has been set
        self.assertEqual(mocked_FlowInstance.redirect_uri, testAuthURI)
    @patch("gCalIntegration.google_auth_oauthlib.flow.Flow", autospec=True)
    @patch.dict("gCalIntegration.os.environ", {"CLIENT_ID": "TEST CLIENT_ID",
                                               "PROJECT_ID": "TEST PROJECT_ID",
                                               "AUTH_URI": "TEST AUTH_URI",
                                               "TOKEN_URI": "TEST TOKEN_URI",
                                               "AUTH_PROVIDER_X509_CERT_URL": "TEST AUTH_PROVIDER_X509_CERT_URL",
                                               "CLIENT_SECRET": "TEST CLIENT_SECRET",
                                               "REDIRECT_URIS": "TEST1,TEST2,TEST3,TEST4",
                                               "JAVASCRIPT_ORIGINS": "TEST5,TEST6"})
    def test_generateAuthURL_PassesExpectedParametersToFlowAuthorizationUrl(self, mocked_flow):
        # Test to ensure that generateAuthURL passes the expected parameters into
        #  flow.authorization_url()

        #  -- ARRANGE --

        # Create the result from .from_client_config
        mocked_FromClientConfigResult = MagicMock()

        # Add the mocked .from_client_config method to mocked flow
        mocked_flow.configure_mock(**{"from_client_config.return_value": mocked_FromClientConfigResult})

        # Since the .from_client_config method returns a Flow that is used by the gCalIntegratinator,
        #  we will create a new variable name for the same object to keep it clear in our heads
        #  as to how we want to use it.
        mocked_FlowInstance = mocked_FromClientConfigResult

        #  -- ACT --

        # Build the gCaleIntegratinator that will have use the mocked Flow
        gCalIntObj = gCalIntegratinator()

        # Run the auth url generation process
        gCalIntObj.generateAuthURL("TEST")

        #  -- ASSERT --

        # Make sure that the expected parameters were passed to the authorization_url
        #  method within the mocked Flow
        mocked_FlowInstance.authorization_url.assert_called_once_with(access_type="offline",
                                                                      include_granted_scopes="true",
                                                                      prompt="select_account")
    @patch("gCalIntegration.google_auth_oauthlib.flow.Flow", autospec=True)
    @patch.dict("gCalIntegration.os.environ", {"CLIENT_ID": "TEST CLIENT_ID",
                                               "PROJECT_ID": "TEST PROJECT_ID",
                                               "AUTH_URI": "TEST AUTH_URI",
                                               "TOKEN_URI": "TEST TOKEN_URI",
                                               "AUTH_PROVIDER_X509_CERT_URL": "TEST AUTH_PROVIDER_X509_CERT_URL",
                                               "CLIENT_SECRET": "TEST CLIENT_SECRET",
                                               "REDIRECT_URIS": "TEST1,TEST2,TEST3,TEST4",
                                               "JAVASCRIPT_ORIGINS": "TEST5,TEST6"})
    def test_generateAuthURL_ReturnsAuthorizationURL(self, mocked_flow):
        # Test to ensure that generateAuthURL returns an authorization url

        #  -- ARRANGE --

        expectedAuthURL = "The Expected Authorization URL"

        # Create the result from .from_client_config
        mocked_FromClientConfigResult = MagicMock()

        # Configure the mocked_FromClientConfigResult to return
        #  the expectedAuthURL when called
        mocked_FromClientConfigResult.configure_mock(**{"authorization_url.return_value": expectedAuthURL})

        # Add the mocked .from_client_config method to mocked flow
        mocked_flow.configure_mock(**{"from_client_config.return_value": mocked_FromClientConfigResult})

        # Since the .from_client_config method returns a Flow that is used by the gCalIntegratinator,
        #  we will create a new variable name for the same object to keep it clear in our heads
        #  as to how we want to use it.
        mocked_FlowInstance = mocked_FromClientConfigResult

        #  -- ACT --

        # Build the gCaleIntegratinator that will have use the mocked Flow
        gCalIntObj = gCalIntegratinator()

        # Run the auth url generation process
        result = gCalIntObj.generateAuthURL("TEST")

        #  -- ASSERT --
        mocked_FlowInstance.authorization_url.assert_called_once()
        self.assertEqual(expectedAuthURL, result)

    def test_handleAuthResponse_SetsRedirectURI(self):
        # Test to ensure that handleAuthResponse sets the flow's redirect_uri

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass
    def test_handleAuthResponse_FetchesTheFlowToken(self):
        # Test to ensure that handleAuthResponse calls flow.fetch_token
        #  while passing it the authorization_response

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass
    def test_handleAuthResponse_ReturnsFlowCredentials(self):
        # Test to ensure that handleAuthResponse returns the flow.credentials

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass

    def test_createGoogleCalendar_checksIfCredentialsAreValid(self):
        # Test to ensure that createGoogleCalendar checks to ensure
        #  that the passed credentials are valid

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass
    def test_createGoogleCalendar_buildsCalendarV3Service(self):
        # Test to ensure that createGoogleCalendar builds the Calendar V3
        #  service with the client credentials

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass
    def test_createGoogleCalendar_buildsInsertsExpectedCalendarBody(self):
        # Test to ensure that createGoogleCalendar calls the Google Calendar
        #  api to insert a calendar using the expected body

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass
    def test_createGoogleCalendar_buildsCalendarService(self):
        # Test to ensure that createGoogleCalendar returns the newly
        #  created Google calendar ID

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass

    def test_exportScheduleToGoogleCalendar_checksIfCredentialsAreValid(self):
        # Test to ensure that exportScheduleToGoogleCalendar checks to ensure
        #  that the passed credentials are valid

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass
    def test_exportScheduleToGoogleCalendar_buildsCalendarV3Service(self):
        # Test to ensure that exportScheduleToGoogleCalendar builds the
        #  appropriate Calendar V3 Service

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass
    def test_exportScheduleToGoogleCalendar_HandlesFindingExistingGoogleCalendar(self):
        # Test to ensure that exportScheduleToGoogleCalendar checks to ensure
        #  that the expected calendar exists for the user

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass
    def test_exportScheduleToGoogleCalendar_GeneratesNewCalendarWhenOneDoesNotExist(self):
        # Test to ensure that exportScheduleToGoogleCalendar handles a case where
        #  it is unable to locate an existing calendar for the user

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass
    def test_exportScheduleToGoogleCalendar_HandlesUnknownHttpErrorCalendarLookup(self):
        # Test to ensure that exportScheduleToGoogleCalendar handles receiving
        #  an unknown HttpError from the Google API

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass
    def test_exportScheduleToGoogleCalendar_SendsEntireScheduleToGoogleCalendarAPI(self):
        # Test to ensure that exportScheduleToGoogleCalendar sends the entire schedule
        #  to the Google Calendar API

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass
    def test_exportScheduleToGoogleCalendar_HandlesUnknownHttpErrorFromEventCreation(self):
        # Test to ensure that exportScheduleToGoogleCalendar handles receiving an HttpError
        #  from the Google Calendar API when attempting to create new events

        #  -- ARRANGE --

        #  -- ACT --

        #  -- ASSERT --
        pass


class TestEventObject(unittest.TestCase):
    def setUp(self):
        self.summary = "This is a title"
        self.description = "This is a description"
        self.date = "This is a date string"

        self.event = Event(self.summary, self.description, self.date)

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
