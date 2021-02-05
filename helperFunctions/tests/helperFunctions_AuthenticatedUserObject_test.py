from helperFunctions.helperFunctions import AuthenticatedUser
from unittest.mock import patch
import unittest


class TestAuthenticatedUserObject(unittest.TestCase):
    def setUp(self):

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
        self.patcher_loggingDEBUG.stop()
        self.patcher_loggingINFO.stop()
        self.patcher_loggingWARNING.stop()
        self.patcher_loggingCRITICAL.stop()
        self.patcher_loggingERROR.stop()

    # ----------------------------------------
    # -- Tests for AuthenticatedUser Object --
    # ----------------------------------------

    def test_hasExpectedMethods(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        raise Exception("Not Implemented")

    def test_hasExpectedProperties(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        raise Exception("Not Implemented")

    def test_email_returnsEmail(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        raise Exception("Not Implemented")

    def test_raID_returnsRAID(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        raise Exception("Not Implemented")

    def test_firstName_returnsFirstName(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        raise Exception("Not Implemented")

    def test_lastName_returnsLastName(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        raise Exception("Not Implemented")

    def test_name_returnsFullName(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        raise Exception("Not Implemented")

    def test_hallID_returnsSelectedDefaultHallID(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        raise Exception("Not Implemented")

    def test_authLevel_returnsSelectedDefaultAuthLevel(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        raise Exception("Not Implemented")

    def test_hallName_returnsSelectedDefaultHallName(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        raise Exception("Not Implemented")

    def test_getAllAssociatedResHalls_returnsResHallList(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        raise Exception("Not Implemented")

    def test_selectResHall_setsSelectedDefaultResHall(self):
        # -- Arrange --
        # -- Act --
        # -- Assert --
        raise Exception("Not Implemented")
