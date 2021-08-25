from unittest.mock import MagicMock, patch
from calendar import monthrange
import datetime
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

    def test_whenPassedConfiguredStartMonth_returnsSchoolYearBeginningInProvidedYear(self):
        # Test to ensure that when the function is passed the month that has
        #  been configured by the hall to the be start of the year, the result
        #  will be a school year that begins in the same year that was passed.

        # -- Arrange --

        # Reset the mocks used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set the values needed in this test
        desiredMonthNum = 8
        desiredYear = 2021
        desiredHallID = 1

        configuredYearStartMonth = desiredMonthNum
        configuredYearEndMonth = 7

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (configuredYearStartMonth, configuredYearEndMonth),  # Return the year start and end month values
        ]

        expectedStartDate = datetime.date(desiredYear, configuredYearStartMonth, 1)
        expectedEndDate = datetime.date(
            desiredYear + 1,                                            # End School Year Year
            configuredYearEndMonth,                                     # End School Year Month
            monthrange(desiredYear + 1, configuredYearEndMonth)[-1]     # Last Day of End School Year Month
        )

        expectedResult = (expectedStartDate, expectedEndDate)

        # -- Act --

        # Call the function being tested
        result = getSchoolYear(desiredMonthNum, desiredYear, desiredHallID)

        # -- Assert --

        # Assert that we received the expected result.
        self.assertEqual(expectedResult, result)

    def test_whenPassedConfiguredEndMonth_returnsSchoolYearEndingInNextYear(self):
        # Test to ensure that when the function is passed the month that has
        #  been configured by the hall to the be end of the year, the result
        #  will be a school year that ends in the next year from the one
        #  that was passed.

        # -- Arrange --

        # Reset the mocks used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set the values needed in this test
        desiredMonthNum = 7
        desiredYear = 2021
        desiredHallID = 1

        configuredYearStartMonth = 8
        configuredYearEndMonth = desiredMonthNum

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.side_effect = [
            (configuredYearStartMonth, configuredYearEndMonth),  # Return the year start and end month values
        ]

        expectedStartDate = datetime.date(desiredYear - 1, configuredYearStartMonth, 1)
        expectedEndDate = datetime.date(
            desiredYear,                                            # End School Year Year
            configuredYearEndMonth,                                 # End School Year Month
            monthrange(desiredYear, configuredYearEndMonth)[-1]     # Last Day of End School Year Month
        )

        expectedResult = (expectedStartDate, expectedEndDate)

        # -- Act --

        # Call the function being tested
        result = getSchoolYear(desiredMonthNum, desiredYear, desiredHallID)

        # -- Assert --

        # Assert that we received the expected result.
        self.assertEqual(expectedResult, result)

    def test_whenPassedMonthNumGreaterThanConfiguredStartMonth_returnsSchoolYearBeginningInProvidedYear(self):
        # Test to ensure that when the function is passed a month number that
        #  is greater than the hall configured school year start month, the
        #  function returns a school year that begins in the year provided.

        # -- Arrange --

        # Reset the mocks used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set the values needed in this test
        desiredYear = 2021
        desiredHallID = 1

        configuredYearStartMonth = 8
        configuredYearEndMonth = 7

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.return_value = (configuredYearStartMonth, configuredYearEndMonth)

        expectedStartDate = datetime.date(desiredYear, configuredYearStartMonth, 1)
        expectedEndDate = datetime.date(
            desiredYear + 1,                                            # End School Year Year
            configuredYearEndMonth,                                     # End School Year Month
            monthrange(desiredYear + 1, configuredYearEndMonth)[-1]     # Last Day of End School Year Month
        )

        expectedResult = (expectedStartDate, expectedEndDate)

        # -- Act --
        # -- Assert --

        # Call the function being tested using different month num values
        for monthNum in range(configuredYearStartMonth, 13):
            result = getSchoolYear(monthNum, desiredYear, desiredHallID)

            # Assert that we received the expected results.
            self.assertEqual(expectedResult, result)

    def test_whenPassedMonthNumLessThanConfiguredStartMonth_returnsSchoolYearEndingInProvidedYear(self):
        # Test to ensure that when the function is passed a month number that
        #  is less than the hall configured school year start month, the
        #  function returns a school year that ends in the year provided.

        # -- Arrange --

        # Reset the mocks used in this test
        self.mocked_appGlobals.conn.reset_mock()

        # Set the values needed in this test
        desiredYear = 2021
        desiredHallID = 1

        configuredYearStartMonth = 8
        configuredYearEndMonth = 7

        # Configure the appGlobals.conn.cursor.execute mock to return different values
        #  after subsequent calls.
        self.mocked_appGlobals.conn.cursor().fetchone.return_value = (configuredYearStartMonth, configuredYearEndMonth)

        expectedStartDate = datetime.date(desiredYear - 1, configuredYearStartMonth, 1)
        expectedEndDate = datetime.date(
            desiredYear,                                            # End School Year Year
            configuredYearEndMonth,                                 # End School Year Month
            monthrange(desiredYear, configuredYearEndMonth)[-1]     # Last Day of End School Year Month
        )

        expectedResult = (expectedStartDate, expectedEndDate)

        # -- Act --
        # -- Assert --

        # Call the function being tested using different month num values
        for monthNum in range(1, configuredYearStartMonth):
            result = getSchoolYear(monthNum, desiredYear, desiredHallID)

            # Assert that we received the expected results.
            self.assertEqual(expectedResult, result)
