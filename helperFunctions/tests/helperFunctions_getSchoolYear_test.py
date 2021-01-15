from unittest.mock import MagicMock, patch
import unittest

from helperFunctions.helperFunctions import getSchoolYear


class TestHelperFunctions_getSchoolYear(unittest.TestCase):
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

    def tearDown(self):
        # Stop all of the patchers
        self.patcher_appGlobals.stop()
        self.patcher_osEnviron.stop()

    def test_whenPassedAugust_returnsSchoolYearBeginningInAugust(self):
        # Test to ensure that when the function is passed the month of August
        #  the result will be a school year that begins in August of the same
        #  year that was passed.

        # -- Arrange --

        # Set the values needed in this test
        curMonthNum = 8
        curYear = 2021

        expectedResult = ("2021-08-01", "2022-07-31")

        # -- Act --

        # Call the function
        result = getSchoolYear(curMonthNum, curYear)

        # -- Assert --

        # Assert that we received the expected result.
        self.assertEqual(expectedResult, result)


    def test_whenPassedJuly_returnsSchoolYearEndingInJuly(self):
        # Test to ensure that when the function is passed the month of July
        #  the result will be a school year that ends in July of the same
        #  year that was passed.

        # -- Arrange --

        # Set the values needed in this test
        curMonthNum = 7
        curYear = 2022

        expectedResult = ("2021-08-01", "2022-07-31")

        # -- Act --

        # Call the function
        result = getSchoolYear(curMonthNum, curYear)

        # -- Assert --

        # Assert that we received the expected result.
        self.assertEqual(expectedResult, result)

    def test_whenPassedMonthSeptemberThroughDecember_returnsSchoolYearBeginningInProvidedYear(self):
        # Test to ensure that when the function is passed a month between September - December
        #  (inclusive), the function returns a school year that begins in the year provided.

        # -- Arrange --

        expectedResult = ("2021-08-01", "2022-07-31")

        # -- Act --

        # Call the function
        sepResult = getSchoolYear(9, 2021)
        octResult = getSchoolYear(10, 2021)
        novResult = getSchoolYear(11, 2021)
        decResult = getSchoolYear(12, 2021)

        # -- Assert --

        # Assert that we received the expected results.
        self.assertEqual(expectedResult, sepResult)
        self.assertEqual(expectedResult, octResult)
        self.assertEqual(expectedResult, novResult)
        self.assertEqual(expectedResult, decResult)

    def test_whenPassedMonthJanuaryThroughJune_returnsSchoolYearEndingInProvidedYear(self):
        # Test to ensure that when the function is passed a month between January - June
        #  (inclusive), the function returns a school year that ends in the year provided.

        # -- Arrange --

        expectedResult = ("2021-08-01", "2022-07-31")

        # -- Act --

        # Call the function
        janResult = getSchoolYear(1, 2022)
        febResult = getSchoolYear(2, 2022)
        marResult = getSchoolYear(3, 2022)
        aprResult = getSchoolYear(4, 2022)
        mayResult = getSchoolYear(5, 2022)
        junResult = getSchoolYear(6, 2022)

        # -- Assert --

        # Assert that we received the expected results.
        self.assertEqual(expectedResult, janResult)
        self.assertEqual(expectedResult, febResult)
        self.assertEqual(expectedResult, marResult)
        self.assertEqual(expectedResult, aprResult)
        self.assertEqual(expectedResult, mayResult)
        self.assertEqual(expectedResult, junResult)
