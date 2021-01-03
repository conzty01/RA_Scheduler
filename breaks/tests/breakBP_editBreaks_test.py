from unittest.mock import MagicMock, patch
from scheduleServer import app
import unittest

class TestBreakBP_editBreaks(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config[""]
        # Mock appGlobals
        # Mock getCurSchoolYear
        # Mock getAuth
        # Mock stdRet

    def tearDown(self):
        pass

    def test_WithAuthorizedUser_RendersAppropriateTemplate(self):
        pass

    def test_WithUnauthorizedUser_ReturnsNotAuthorizedJSON(self):
        pass

    def test_BlueprintExposesBlueprintToApp(self):
        pass
