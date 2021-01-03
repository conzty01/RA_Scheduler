from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest


class TestBreakBP_addBreakDuty(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config[""]
        # Mock appGlobals
        # Mock getCurSchoolYear
        # Mock getAuth
        # Mock stdRet

    def tearDown(self):
        pass

    def test_whenCalledFromClient_acceptsExpectedParameters(self):
        pass

    def test_whenPassedValidParams_returnsSuccessfulResponse(self):
        pass

    def test_WithUnauthorizedUser_returnsNotAuthorizedResponse(self):
        pass

    def test_WhenPassedInvalidRA_returnsInvalidRAResult(self):
        pass

    def test_WhenPassedInvalidDay_returnsInvalidDayResult(self):
        pass

    def test_WhenPassedInvalidMonth_returnsInvalidMonthResult(self):
        pass
