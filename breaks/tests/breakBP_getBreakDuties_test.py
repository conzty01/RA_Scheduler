from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest


class TestBreakBP_getBreakDuties(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config[""]
        # Mock appGlobals
        # Mock getCurSchoolYear
        # Mock getAuth
        # Mock stdRet

    def tearDown(self):
        pass

    def test_whenCalledFromServer_acceptsExpectedParameters(self):
        pass

    def test_whenCalledFromClient_acceptsExpectedParameters(self):
        pass

    def test_whenCalledFromClient_returnScheduleInExpectedJSONFormat(self):
        pass

    def test_whenCalledFromServer_returnsScheduleInExpectedFormat(self):
        pass

    def test_whenShowAllColorsIsTrue_returnsScheduleWithAllColors(self):
        pass

    def test_whenShowAllColorsIsFalse_returnsScheduleWithDefaultColor(self):
        pass
