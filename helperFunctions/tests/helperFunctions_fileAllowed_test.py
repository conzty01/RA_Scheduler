from unittest.mock import MagicMock, patch
import unittest

from helperFunctions.helperFunctions import fileAllowed


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

    def tearDown(self):
        # Stop all of the patchers
        self.patcher_appGlobals.stop()
        self.patcher_osEnviron.stop()

    def test_whenExtensionIsAtEndOfFilename_withAllowedExtension_returnsTrue(self):
        # Test to ensure that when a filename is provided that has the
        #  extension at the end of the filename and the extension is allowed
        #  the function returns True.

        # -- Arrange --

        # Create the allowed file extensions
        self.mocked_appGlobals.ALLOWED_EXTENSIONS = {"txt", "csv"}

        # Create our filename
        txtFilename = "testName.txt"
        csvFilename = "testName.csv"

        # -- Act --

        # Call the fileAllowed function on our two filenames
        txtRes = fileAllowed(txtFilename)
        csvRes = fileAllowed(csvFilename)

        # -- Assert --

        # Assert that the txtRes is True
        self.assertTrue(txtRes)

        # Assert that the csvRes is True
        self.assertTrue(csvRes)

    def test_whenExtensionIsNotAllowed_returnsFalse(self):
        # Test to ensure that when a filename is provided that has
        #  an extension that is not allowed, the function returns False.

        # -- Arrange --

        # Create the allowed file extensions
        self.mocked_appGlobals.ALLOWED_EXTENSIONS = {"txt", "csv"}

        # Create our filename
        pngFilename = "testName.png"
        pdfFilename = "testName.pdf"

        # -- Act --

        # Call the fileAllowed function on our two filenames
        pngRes = fileAllowed(pngFilename)
        pdfRes = fileAllowed(pdfFilename)

        # -- Assert --

        # Assert that the pngRes is True
        self.assertFalse(pngRes)

        # Assert that the pdfRes is True
        self.assertFalse(pdfRes)

    def test_withCapitalizedFilename_canIdentifyFilenameAsAllowed(self):
        # Test to ensure that when a filename is provided that has an
        #  extension that is all capitalized, but otherwise is allowed,
        #  returns True.

        # -- Arrange --

        # Create the allowed file extensions
        self.mocked_appGlobals.ALLOWED_EXTENSIONS = {"txt", "csv"}

        # Create our filename
        txtFilename = "testName.TXT"
        csvFilename = "testName.CSV"

        # -- Act --

        # Call the fileAllowed function on our two filenames
        txtRes = fileAllowed(txtFilename)
        csvRes = fileAllowed(csvFilename)

        # -- Assert --

        # Assert that the txtRes is True
        self.assertTrue(txtRes)

        # Assert that the csvRes is True
        self.assertTrue(csvRes)

    def test_withCapitalizedFilename_canIdentifyFilenameAsNotAllowed(self):
        # Test to ensure that when a filename is provided that has an
        #  extension that is all capitalized, but otherwise is NOT allowed,
        #  returns False.

        # -- Arrange --

        # Create the allowed file extensions
        self.mocked_appGlobals.ALLOWED_EXTENSIONS = {"txt", "csv"}

        # Create our filename
        pngFilename = "testName.PNG"
        pdfFilename = "testName.JPEG"

        # -- Act --

        # Call the fileAllowed function on our two filenames
        pngRes = fileAllowed(pngFilename)
        pdfRes = fileAllowed(pdfFilename)

        # -- Assert --

        # Assert that the pngRes is True
        self.assertFalse(pngRes)

        # Assert that the pdfRes is True
        self.assertFalse(pdfRes)

    def test_whenPassedFilenameWithoutPeriod_returnsFalse(self):
        # Test to ensure that when a filename is provided that does NOT
        #  have an extension in it (does not contain a period) the
        #  function returns False.

        # -- Arrange --

        # Create the allowed file extensions
        self.mocked_appGlobals.ALLOWED_EXTENSIONS = {"txt", "csv"}

        # Create our filename
        filename1 = "testName1"
        filename2 = "testName2"

        # -- Act --

        # Call the fileAllowed function on our two filenames
        res1 = fileAllowed(filename1)
        res2 = fileAllowed(filename2)

        # -- Assert --

        # Assert that the res1 is True
        self.assertFalse(res1)

        # Assert that the res2 is True
        self.assertFalse(res2)

    def test_whenPassedFilenameWithoutExtensionAsRightMostPeriod_returnsFalse(self):
        # Test to ensure that when a filename is provided that has multiple
        #  periods in it, the function looks for the extension following the
        #  last period of the file.

        # -- Arrange --

        # Create the allowed file extensions
        self.mocked_appGlobals.ALLOWED_EXTENSIONS = {"txt", "csv"}

        # Create our filename
        filename1 = "testName.png"
        filename2 = "test.tiff.Name.csv"
        filename3 = "test1.0.txt"
        filename4 = ".txt.csv.pdf"
        filename5 = "test.txtName"

        # -- Act --

        # Call the fileAllowed function on our two filenames
        res1 = fileAllowed(filename1)
        res2 = fileAllowed(filename2)
        res3 = fileAllowed(filename3)
        res4 = fileAllowed(filename4)
        res5 = fileAllowed(filename5)

        # -- Assert --

        # Assert that the res1 is True
        self.assertFalse(res1)

        # Assert that the res2 is True
        self.assertTrue(res2)

        # Assert that the res3 is True
        self.assertTrue(res3)

        # Assert that the res4 is True
        self.assertFalse(res4)

        # Assert that the res5 is False
        self.assertFalse(res5)
