from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest


class TestBreakBP_deleteBreakDuty(unittest.TestCase):
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

    def test_whenPassedInvalidRA_returnsInvalidParamsResponse(self):
        pass

    def test_whenPassedInvalidDay_returnsInvalidParamsResponse(self):
        pass

    def test_whenPassedInvalidMonth_returnsInvalidParamsResponse(self):
        pass
