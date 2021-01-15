from unittest.mock import MagicMock, patch
import unittest

from helperFunctions.helperFunctions import getCurSchoolYear


class TestHelperFunctions_getCurSchoolYear(unittest.TestCase):
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

        # -- Create a patcher for the datetime module --
        self.patcher_datetime = patch("helperFunctions.helperFunctions.datetime", autospec=True)

        # Start the patcher - mock returned
        self.mocked_datetime = self.patcher_datetime.start()

    def tearDown(self):
        # Stop all of the patchers
        self.patcher_appGlobals.stop()
        self.patcher_osEnviron.stop()
        self.patcher_datetime.stop()

    @patch("helperFunctions.helperFunctions.getSchoolYear")
    def test_returnsCurrentSchoolYear_inExpectedFormat(self, mocked_getSchoolYear):
        # Test to ensure that the function returns the current
        #  school year which should be between August and July.

        # -- Arrange --

        # Reset the mocks used in this test
        self.mocked_datetime.reset_mock()

        expectedMonth = 7
        expectedYear = 2021

        # Set the value for the current month and year
        self.mocked_datetime.date.today().month = expectedMonth
        self.mocked_datetime.date.today().year = expectedYear

        # -- Act --

        # Call the function
        result = getCurSchoolYear()

        # -- Assert --

        # Assert that the current month and year were polled
        self.assertEqual(self.mocked_datetime.date.today.call_count, 4)

        # Assert that the getSchoolYear function was called as expected
        mocked_getSchoolYear.assert_called_once_with(expectedMonth, expectedYear)

        # Assert that we received the expected result
        self.assertEqual(mocked_getSchoolYear(), result)
