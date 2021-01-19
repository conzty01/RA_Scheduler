from unittest.mock import MagicMock, patch
import unittest

from helperFunctions.helperFunctions import formatDateStr


class TestHelperFunctions_fileAllowed(unittest.TestCase):
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
        self.patcher_appGlobals.stop()
        self.patcher_osEnviron.stop()

        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

    def test_whenProvidedSingleDigitDayOrMonth_returnsPaddedDateStr(self):
        # Test to ensure that when provided with a single digit day or month
        #  value, the function will pad those days to two digits.

        # -- Arrange --

        expectedSingleDayStr = "2021-10-01"
        expectedSingleMonthStr = "2021-02-11"
        expectedSingleDayMonthStr = "2021-03-01"

        expectedNonSingleDayMonthStr = "2021-12-24"

        # -- Act --

        singleDay = formatDateStr(1, 10, 2021)
        singleMonth = formatDateStr(11, 2, 2021)
        singleDayMonth = formatDateStr(1, 3, 2021)

        nonSingleDayMonth = formatDateStr(24, 12, 2021)

        # -- Assert

        # Assert that singleDay has a padded Day value
        self.assertEqual(expectedSingleDayStr, singleDay)

        # Assert that singleMonth has a padded Month value
        self.assertEqual(expectedSingleMonthStr, singleMonth)

        # Assert that singleDayMonth has padded Day and Month values
        self.assertEqual(expectedSingleDayMonthStr, singleDayMonth)

        # Assert that nonSingleDayMonth has no padded values
        self.assertEqual(expectedNonSingleDayMonthStr, nonSingleDayMonth)

    def test_whenProvidedFormatString_returnsDateInProvidedFormat(self):
        # Test to ensure that when provided a format string, the function
        #  returns a date string that is formatted per the provided
        #  specification.

        # -- Arrange --

        format1 = "MM-DD-YYYY"
        expectedFormat1Str = "01-14-2021"

        format2 = "DD-MM-YYYY"
        expectedFormat2Str = "14-01-2021"

        format3 = "YYYY-DD-MM"
        expectedFormat3Str = "2021-14-01"

        format4 = "MM-YYYY-DD"
        expectedFormat4Str = "01-2021-14"

        # -- Act --

        format1Res = formatDateStr(14, 1, 2021, format=format1)
        format2Res = formatDateStr(14, 1, 2021, format=format2)
        format3Res = formatDateStr(14, 1, 2021, format=format3)
        format4Res = formatDateStr(14, 1, 2021, format=format4)

        # -- Assert

        # Assert that the formatted date strings came out as expected
        self.assertEqual(expectedFormat1Str, format1Res)
        self.assertEqual(expectedFormat2Str, format2Res)
        self.assertEqual(expectedFormat3Str, format3Res)
        self.assertEqual(expectedFormat4Str, format4Res)

    def test_whenProvidedDivider_returnsDateUsingProvidedDivider(self):
        # Test to ensure that when provided a divider character, the
        #  function returns a date string that uses the provided divider.

        # -- Arrange --

        # Create the dividers and their expected results
        divider1 = "/"
        desiredFormat1 = "YYYY/MM/DD"
        expectedDivider1Str = "2021/01/14"

        divider2 = "?"
        desiredFormat2 = "YYYY?MM?DD"
        expectedDivider2Str = "2021?01?14"

        divider3 = "."
        desiredFormat3 = "YYYY.MM.DD"
        expectedDivider3Str = "2021.01.14"

        divider4 = " "
        desiredFormat4 = "YYYY MM DD"
        expectedDivider4Str = "2021 01 14"

        # -- Act --

        # Get the results
        divider1Res = formatDateStr(14, 1, 2021, format=desiredFormat1, divider=divider1)
        divider2Res = formatDateStr(14, 1, 2021, format=desiredFormat2, divider=divider2)
        divider3Res = formatDateStr(14, 1, 2021, format=desiredFormat3, divider=divider3)
        divider4Res = formatDateStr(14, 1, 2021, format=desiredFormat4, divider=divider4)

        # -- Assert

        # Assert that the formatted date strings came out as expected
        self.assertEqual(expectedDivider1Str, divider1Res)
        self.assertEqual(expectedDivider2Str, divider2Res)
        self.assertEqual(expectedDivider3Str, divider3Res)
        self.assertEqual(expectedDivider4Str, divider4Res)
