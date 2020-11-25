from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import google.oauth2.credentials
import google_auth_oauthlib.flow
from io import BytesIO
import datetime
import os.path
import logging
import pickle


class gCalIntegratinator:
    """Object for handling interactions between RADSA and Google Calendar API.

       This class uses the googleapiclient to interact with the Google Calendar API.

       AUTHORIZATION WORKFLOW:
            1) Redirect user to the Authorization URL
            2) User consents to Google Calendar integration and is
                redirected back to this application
            3) The Authorization Response and State are returned from Google
                and used to generate user credentials
            4) User credentials are returned back to the application where they
                are stored in the DB for later use



       Args:
           clientCreds ():
           appCreds ():
           scopes (lst):"""

    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

    def __init__(self, scopes=SCOPES):
        logging.debug("Creating gCalIntegratinator Object")

        # Load the application credentials from the client_secret.json file
        #  and use the scopes outlined in the scopes list
        self.flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            'client_secret.json', scopes=scopes)

        # The credentials that will allows us to interact with Google Calendar
        #  API on the client's behalf.
        self.credentials = None

        # Name of Google service being used
        self.serviceName = "calendar"

        # API version number of Google service being used
        self.serviceVersion = "v3"

        # Load the app credentials from the environment
        self.__appCreds = self.__getCredsFromEnv()

        # Generate the oAuth2 flow for handling the client/app authentication
        self.flow = google_auth_oauthlib.flow.Flow.from_client_config(
            self.__getCredsFromEnv(), scopes)


    def __getCredsFromEnv(self):
        # This will return a desearlized JSON object that is assembled per
        #  Google's specifications. This object will be configured for a 'web' app

        # This does assume the following parameters are available in the environment:
        #    CLIENT_ID
        #    PROJECT_ID
        #    AUTH_URI
        #    TOKEN_URI
        #    AUTH_PROVIDER_X509_CERT_URL
        #    CLIENT_SECRET
        #    REDIRECT_URIS -> This should be the urls separated by a ',' only
        #    JAVASCRIPT_ORIGINS -> This should be the urls separated by a ',' only

        logging.debug("Loading app settings from environment")

        return {
            "web": {
                "client_id": os.environ["CLIENT_ID"],
                "project_id": os.environ["PROJECT_ID"],
                "auth_uri": os.environ["AUTH_URI"],
                "token_uri": os.environ["TOKEN_URI"],
                "auth_provider_x509_cert_url": os.environ["AUTH_PROVIDER_X509_CERT_URL"],
                "client_secret": os.environ["CLIENT_SECRET"],
                "redirect_uris": [entry for entry in os.environ["REDIRECT_URIS"].split(",")],# ["https://b03bb12e8ff3.ngrok.io"],
                "javascript_origins": [entry for entry in os.environ["JAVASCRIPT_ORIGINS"].split(",")]
            }
        }

    def _checkIfValidCreds(self, creds):
        # Check to see if the client credentials are valid

        # Expected Return Statuses:
        #   -3: Invalid Credentials Received
        #   -2: Need to Renew Credentials
        #   -1: Unknown Error Occurred
        #    0: Credentials are valid
        #    1: Credentials are valid but needed refresh

        logging.debug("Checking Credentials")

        retStatus = 0

        try:
            # Are the credentials invalid?
            if not creds.valid:

                # If the credentials are expired and can be refreshed,
                #  then refresh the credentials
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    retStatus = 1

                else:
                    # Otherwise we will need to prompt the user to log in
                    #  and approve integration again.
                    logging.debug("Manual Credential Refresh Required")
                    retStatus = -2

            else:
                # If the credentials are valid, return successful
                logging.debug("Credentials Valid")


        except AttributeError:
            logging.info("Invalid Credentials Received")
            retStatus = -3

        except Exception as e:
            logging.exception(str(e))
            retStatus = -1

        logging.debug("Credential Status: {}".format(retStatus))
        return retStatus

    def generateAuthURL(self, redirect_uri):
        # Generate and return an authorization url as well as a state
        logging.debug("Generating Google Authorization URL")

        # Set the flow's redirect_uri
        self.flow.redirect_uri = redirect_uri

        # Return (auth_url, state) for the given redirect_uri
        return self.flow.authorization_url(accses_type="offline",
                                           include_granted_scopes="true",
                                           prompt="select_account")

    def handleAuthResponse(self, auth_response, redirect_uri):
        # Generate authorization credentials from the authorization response

        logging.debug("Generating Google Client Credentials")

        self.flow.redirect_uri = redirect_uri

        # Generate the token
        self.flow.fetch_token(authorization_response=auth_response)

        return self.flow.credentials

    def exportToGoogleCalendar(self, client_creds, schedule):
        # Export the provided schedule to Google Calendar

        # Check to make sure the credentials are valid
        if self._checkIfValidCreds(client_creds) < 0:
            logging.debug("Issue with Credentials")
            # If they are not valid, stop processing and report the
            #  result back to server.
            return self._checkIfValidCreds(client_creds)

    # def close(self):
    #     # Close down the connection to the Google API
    #     if self.service is not None:
    #         self.service.close()

    def testBit(self, client_creds):
        # Check to make sure the credentials are valid
        if self._checkIfValidCreds(client_creds) < 0:
            logging.debug("Issue with Credentials")
            # If they are not valid, stop processing and report the
            #  result back to server.
            return self._checkIfValidCreds(client_creds)

        # Build the Google Calendar service with appropriate version
        service = build(self.serviceName, self.serviceVersion, credentials=client_creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')

        # Print the events
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])



def main():
    pass

if __name__ == "__main__":
    main()
