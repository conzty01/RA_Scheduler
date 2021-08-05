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
        # Test to ensure that the AuthenticatedUser Object has the following methods:
        #  - email
        #  - ra_id
        #  - first_name
        #  - last_name
        #  - name
        #  - hall_id
        #  - auth_level
        #  - hall_name
        #  - getAllAssociatedResHalls
        #  - selectResHall

        # -- Arrange --
        # -- Act --
        # -- Assert --

        self.assertTrue(hasattr(AuthenticatedUser, "email"))
        self.assertTrue(hasattr(AuthenticatedUser, "ra_id"))
        self.assertTrue(hasattr(AuthenticatedUser, "first_name"))
        self.assertTrue(hasattr(AuthenticatedUser, "last_name"))
        self.assertTrue(hasattr(AuthenticatedUser, "name"))
        self.assertTrue(hasattr(AuthenticatedUser, "hall_id"))
        self.assertTrue(hasattr(AuthenticatedUser, "auth_level"))
        self.assertTrue(hasattr(AuthenticatedUser, "hall_name"))
        self.assertTrue(hasattr(AuthenticatedUser, "getAllAssociatedResHalls"))
        self.assertTrue(hasattr(AuthenticatedUser, "selectResHall"))

    def test_email_returnsEmail(self):
        # Test to ensure that the email() method returns the email provided to the
        #  AuthenticatedUser Object.

        # -- Arrange --

        # Create the parameters to be used in this test
        desiredEmail = "test@email.com"
        desiredRAID = 9
        desiredFName = "Test"
        desiredLName = "User"
        desiredResHalls = [{
            "name": "Test Hall",
            "id": 1,
            "auth_level": 4
        }]
        testAuthenticatedUserObject = AuthenticatedUser(
            desiredEmail,
            desiredRAID,
            desiredFName,
            desiredLName,
            desiredResHalls
        )

        # -- Act --

        # Call the method being tested
        result = testAuthenticatedUserObject.email()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredEmail, result)

    def test_raID_returnsRAID(self):
        # Test to ensure that the ra_id() method returns the raID provided to the
        #  AuthenticatedUser Object.

        # -- Arrange --

        # Create the parameters to be used in this test
        desiredEmail = "test@email.com"
        desiredRAID = 9
        desiredFName = "Test"
        desiredLName = "User"
        desiredResHalls = [{
            "name": "Test Hall",
            "id": 1,
            "auth_level": 4
        }]
        testAuthenticatedUserObject = AuthenticatedUser(
            desiredEmail,
            desiredRAID,
            desiredFName,
            desiredLName,
            desiredResHalls
        )

        # -- Act --

        # Call the method being tested
        result = testAuthenticatedUserObject.ra_id()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredRAID, result)

    def test_firstName_returnsFirstName(self):
        # Test to ensure that the first_name() method returns the fName provided to the
        #  AuthenticatedUser Object.

        # -- Arrange --

        # Create the parameters to be used in this test
        desiredEmail = "test@email.com"
        desiredRAID = 9
        desiredFName = "Test"
        desiredLName = "User"
        desiredResHalls = [{
            "name": "Test Hall",
            "id": 1,
            "auth_level": 4
        }]
        testAuthenticatedUserObject = AuthenticatedUser(
            desiredEmail,
            desiredRAID,
            desiredFName,
            desiredLName,
            desiredResHalls
        )

        # -- Act --

        # Call the method being tested
        result = testAuthenticatedUserObject.first_name()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredFName, result)

    def test_lastName_returnsLastName(self):
        # Test to ensure that the last_name() method returns the lName provided to the
        #  AuthenticatedUser Object.

        # -- Arrange --

        # Create the parameters to be used in this test
        desiredEmail = "test@email.com"
        desiredRAID = 9
        desiredFName = "Test"
        desiredLName = "User"
        desiredResHalls = [{
            "name": "Test Hall",
            "id": 1,
            "auth_level": 4
        }]
        testAuthenticatedUserObject = AuthenticatedUser(
            desiredEmail,
            desiredRAID,
            desiredFName,
            desiredLName,
            desiredResHalls
        )

        # -- Act --

        # Call the method being tested
        result = testAuthenticatedUserObject.last_name()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredLName, result)

    def test_name_returnsFullName(self):
        # Test to ensure that the name() method returns the full name provided to the
        #  AuthenticatedUser Object.

        # -- Arrange --

        # Create the parameters to be used in this test
        desiredEmail = "test@email.com"
        desiredRAID = 9
        desiredFName = "Test"
        desiredLName = "User"
        desiredResHalls = [{
            "name": "Test Hall",
            "id": 1,
            "auth_level": 4
        }]
        testAuthenticatedUserObject = AuthenticatedUser(
            desiredEmail,
            desiredRAID,
            desiredFName,
            desiredLName,
            desiredResHalls
        )

        # -- Act --

        # Call the method being tested
        result = testAuthenticatedUserObject.name()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredFName + " " + desiredLName, result)

    def test_hallID_returnsSelectedDefaultHallID(self):
        # Test to ensure that the hall_id() method returns the ID of the first
        #  hall in the resHalls list provided to the AuthenticatedUser Object.

        # -- Arrange --

        # Create the parameters to be used in this test
        desiredEmail = "test@email.com"
        desiredRAID = 9
        desiredFName = "Test"
        desiredLName = "User"
        desiredResHalls = [
            {
                "name": "Test Hall",
                "id": 1,
                "auth_level": 4
            },
            {
                "name": "Test Hall2",
                "id": 2,
                "auth_level": 1
            }
        ]
        testAuthenticatedUserObject = AuthenticatedUser(
            desiredEmail,
            desiredRAID,
            desiredFName,
            desiredLName,
            desiredResHalls
        )

        # -- Act --

        # Call the method being tested
        result = testAuthenticatedUserObject.hall_id()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredResHalls[0]["id"], result)

    def test_authLevel_returnsSelectedDefaultAuthLevel(self):
        # Test to ensure that the auth_level() method returns the auth_level of the first
        #  hall in the resHalls list provided to the AuthenticatedUser Object.

        # -- Arrange --

        # Create the parameters to be used in this test
        desiredEmail = "test@email.com"
        desiredRAID = 9
        desiredFName = "Test"
        desiredLName = "User"
        desiredResHalls = [
            {
                "name": "Test Hall",
                "id": 1,
                "auth_level": 4
            },
            {
                "name": "Test Hall2",
                "id": 2,
                "auth_level": 1
            }
        ]
        testAuthenticatedUserObject = AuthenticatedUser(
            desiredEmail,
            desiredRAID,
            desiredFName,
            desiredLName,
            desiredResHalls
        )

        # -- Act --

        # Call the method being tested
        result = testAuthenticatedUserObject.auth_level()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredResHalls[0]["auth_level"], result)

    def test_hallName_returnsSelectedDefaultHallName(self):
        # Test to ensure that the hall_name() method returns the name of the first
        #  hall in the resHalls list provided to the AuthenticatedUser Object.

        # -- Arrange --

        # Create the parameters to be used in this test
        desiredEmail = "test@email.com"
        desiredRAID = 9
        desiredFName = "Test"
        desiredLName = "User"
        desiredResHalls = [
            {
                "name": "Test Hall",
                "id": 1,
                "auth_level": 4
            },
            {
                "name": "Test Hall2",
                "id": 2,
                "auth_level": 1
            }
        ]
        testAuthenticatedUserObject = AuthenticatedUser(
            desiredEmail,
            desiredRAID,
            desiredFName,
            desiredLName,
            desiredResHalls
        )

        # -- Act --

        # Call the method being tested
        result = testAuthenticatedUserObject.hall_name()

        # -- Assert --

        # Assert that we received the expected result
        self.assertEqual(desiredResHalls[0]["name"], result)

    def test_getAllAssociatedResHalls_returnsResHallList(self):
        # Test to ensure that the getAllAssociatedResHalls() method returns the resHall list
        #  provided to the AuthenticatedUser Object.

        # -- Arrange --

        # Create the parameters to be used in this test
        desiredEmail = "test@email.com"
        desiredRAID = 9
        desiredFName = "Test"
        desiredLName = "User"
        desiredResHalls = [
            {
                "name": "Test Hall",
                "id": 1,
                "auth_level": 4,
                "school_id": 2,
                "school_name": "Test School"
            },
            {
                "name": "Test Hall2",
                "id": 2,
                "auth_level": 1,
                "school_id": 2,
                "school_name": "Test School"
            }
        ]
        testAuthenticatedUserObject = AuthenticatedUser(
            desiredEmail,
            desiredRAID,
            desiredFName,
            desiredLName,
            desiredResHalls
        )

        # -- Act --

        # Call the method being tested
        result = testAuthenticatedUserObject.getAllAssociatedResHalls()

        # -- Assert --

        # Assert that we received the expected result
        self.assertListEqual(desiredResHalls, result)

    def test_selectResHall_setsSelectedDefaultResHall(self):
        # Test to ensure that the selectResHall() method sets the Res Hall at the
        #  provided index to be the selected default res hall.

        # -- Arrange --

        # Create the parameters to be used in this test
        desiredEmail = "test@email.com"
        desiredRAID = 9
        desiredFName = "Test"
        desiredLName = "User"
        desiredResHalls = [
            {
                "name": "Test Hall",
                "id": 1,
                "auth_level": 4,
                "school_id": 2,
                "school_name": "Test School"
            },
            {
                "name": "Test Hall2",
                "id": 2,
                "auth_level": 1,
                "school_id": 2,
                "school_name": "Test School"
            }
        ]
        testAuthenticatedUserObject = AuthenticatedUser(
            desiredEmail,
            desiredRAID,
            desiredFName,
            desiredLName,
            desiredResHalls
        )

        # -- Act --

        # Get the name of the default selected Res Hall
        hallName1 = testAuthenticatedUserObject.hall_name()

        # Change the selected Res Hall to the second entry
        testAuthenticatedUserObject.selectResHall(1)

        # Get the name of the default selected Res Hall
        hallName2 = testAuthenticatedUserObject.hall_name()

        # -- Assert --

        # Assert that the first Hall was as we expected
        self.assertEqual(desiredResHalls[0]["name"], hallName1)

        # Assert that the second Hall was as we expected
        self.assertEqual(desiredResHalls[1]["name"], hallName2)

        # Assert that the first and second halls are not the same
        self.assertNotEqual(hallName1, hallName2)
