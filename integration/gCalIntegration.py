from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google_auth_oauthlib.flow
import logging
import os


class gCalIntegratinator:
    """ Object for handling interactions between RADSA and Google Calendar API.

        This class uses the googleapiclient to interact with the Google Calendar API.

        AUTHORIZATION WORKFLOW:
            1) Redirect user to the Authorization URL
            2) User consents to Google Calendar integration and is
                redirected back to this application
            3) The Authorization Response and State are returned from Google
                and used to generate user credentials
            4) User credentials are returned back to the application where they
                are stored in the DB for later use

        Method Return Statuses:
            -5: Error Creating Google Calendar Event
            -4: Invalid Calendar Id
            -3: Invalid Credentials Received
            -2: Need to Renew Credentials
            -1: Unknown Error Occurred
             0: Credentials are valid but needed refresh
             1: Success

        Args:
            scopes (lst): A list containing the scopes required to interact with the
                           Google Calendar API. The default provided are
                             - .../auth/calendar.calendarlist.readonly
                             - .../auth/calendar.app.created
    """

    SCOPES = ['https://www.googleapis.com/auth/calendar.app.created',
              'https://www.googleapis.com/auth/calendar.calendarlist.readonly']

    def __init__(self, scopes=SCOPES):
        logging.debug("Creating gCalIntegratinator Object")

        # Name of Google service being used
        self.serviceName = "calendar"

        # API version number of Google service being used
        self.serviceVersion = "v3"

        # Set the scopes for reference
        self.scopes = scopes

        # Load the app credentials from the environment
        self.__appCreds = self._getCredsFromEnv()

        # Generate the oAuth2 flow for handling the client/app authentication
        self.flow = google_auth_oauthlib.flow.Flow.from_client_config(
            self.__appCreds, scopes=scopes)

    def _getCredsFromEnv(self):
        # This will return a deserialized JSON object that is assembled per
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

        logging.info("Loading app settings from environment")

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

    def _validateCredentials(self, creds):
        # Check to see if the client credentials are valid and that they have not
        #  expired. This method can have the following outcomes:
        #
        #  If the credentials are valid, then the credentials will be returned
        #  If the credentials are not valid, an InvalidCalendarCredentialsError will be raised.
        #  If the credentials have expired, an ExpiredCalendarCredentialsError will be raised.

        logging.debug("Checking Credentials")

        try:
            # Are the credentials invalid?
            if not creds.valid:

                # If the credentials are expired and can be refreshed,
                #  then refresh the credentials
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())

                else:
                    # Otherwise we will need to prompt the user to log in
                    #  and approve integration again.
                    logging.debug("Manual Credential Refresh Required")
                    raise self.ExpiredCalendarCredentialsError("Manual Credential Refresh Required")

            else:
                # If the credentials are valid, return successful
                logging.debug("Credentials Valid")

        except AttributeError:
            # If we receive an AttributeError, then we did not receive the expected
            #  credentials object.

            # Log the occurrence
            logging.info("Invalid Credentials Received")

            # Raise an InvalidCalendarCredentialsError
            raise self.InvalidCalendarCredentialsError("Invalid Credentials Received")

        except self.ExpiredCalendarCredentialsError as e:
            # If we receive an ExpiredCalendarCredentialsError, then simply pass that up to
            #  the calling method.
            raise e

        except Exception as e:
            # If we receive some other, unexpected Exception, then notify the calling method

            # Log the occurrence
            logging.error(str(e))

            # Raise an UnknownError
            raise self.UnexpectedError("Calendar Credential Validation", e, str(e))

        # If we made it this far without raising an exception,
        #  then the credentials are valid.
        return creds

    def generateAuthURL(self, redirect_uri):
        # Generate and return an authorization url as well as a state
        logging.info("Generating Google Authorization URL")

        # Set the flow's redirect_uri
        self.flow.redirect_uri = redirect_uri

        # Return (auth_url, state) for the given redirect_uri
        return self.flow.authorization_url(access_type="offline",
                                           include_granted_scopes="true",
                                           prompt="select_account")

    def handleAuthResponse(self, auth_response, redirect_uri):
        # Generate authorization credentials from the authorization response

        logging.info("Generating Google Client Credentials")

        self.flow.redirect_uri = redirect_uri

        # Generate the token
        self.flow.fetch_token(authorization_response=auth_response)

        return self.flow.credentials

    def createGoogleCalendar(self, client_creds):
        # Create a Secondary Google Calendar using the user credentials

        logging.info("Creating Google Calendar")

        # Check to make sure the credentials are valid
        client_creds = self._validateCredentials(client_creds)

        # Build the Google Calendar service with appropriate version
        service = build(self.serviceName, self.serviceVersion, credentials=client_creds)

        # Create the body of the request to create a new Google Calendar.
        newCalBody = {
            "summary": "RA Duty Schedule",
            "description": "Calendar for the Resident Assistant Duty Schedule.\n\n"
                           "Created and added to by the RA Duty Scheduler Application (RADSA)."
        }

        try:
            # Call the Google Calendar API Service to have the new calendar created
            created_calendar = service.calendars().insert(body=newCalBody).execute()

        except Exception as e:
            # If we received an exception, then wrap it in an CalendarCreationError and
            #  pass that up to the calling function.

            # Log the occurrence
            logging.error("Error encountered when attempting to create Google Calendar: {}".format(str(e)))

            # Raise the CalendarCreationError
            raise self.CalendarCreationError(str(e))

        logging.info("Calendar Creation Complete")

        # Return the ID of the new calendar.
        return created_calendar["id"]

    def exportScheduleToGoogleCalendar(self, client_creds, calendarId, schedule, flaggedDutyLabel):
        # Export the provided schedule to Google Calendar

        # Check to make sure the credentials are valid
        client_creds = self._validateCredentials(client_creds)

        # Create the Google Calendar Service
        service = build(self.serviceName, self.serviceVersion, credentials=client_creds)

        # Check to see if the 'RA Duty Schedule' calendar exists. If not, create
        #  the calendar.
        try:
            logging.debug("Verifying that the 'RA Schedule Calendar' exists.")
            res = service.calendarList().get(calendarId=calendarId).execute()
            logging.debug("CalendarList().get() Result: {}".format(res))

        except HttpError as e:
            # An HttpError occurred which could indicate that the calendar no longer exists.
            #  If this is the case, the HttpError would be a 404 error.

            # Log the occurrence of this issue.
            logging.info("'RA Schedule Calendar' not found for client.")
            logging.error(str(e))

            # Plan B is to create a new Google Calendar.
            try:
                # Create the calendar using the client_creds
                calendarId = self.createGoogleCalendar(client_creds)

            except self.CalendarCreationError as subE:
                # An error occurred when attempting to create the Calendar.

                # Wrap the exception in a ScheduleExportError and raise it
                raise self.ScheduleExportError(subE, "Unable to locate valid Google Calendar.")

        # Once we are able to locate the calendar, start adding the events to it!
        try:
            logging.info("Exporting schedule")

            # Iterate through the schedule
            for duty in schedule:

                # Check to see if this duty should be flagged
                if "flagged" in duty["extendedProps"].keys() and duty["extendedProps"]["flagged"]:
                    # If so, then set the summary and description messages to include the flagged
                    #  duty label.
                    summaryMsg = duty["title"] + " ({})".format(flaggedDutyLabel)
                    descriptionMsg = duty["title"] + " has been assigned for {} duty.".format(flaggedDutyLabel)

                else:
                    # Otherwise, set the summary and description messages to be the default
                    summaryMsg = duty["title"]
                    descriptionMsg = duty["title"] + " has been assigned for duty."

                # Create an Event Object that will handle assembling the event's body for the Google Calendar API
                eb = Event(summaryMsg,
                           descriptionMsg,
                           duty["start"])

                # Call the Google Calendar API to add the event
                service.events().insert(calendarId=calendarId,
                                        body=eb.getBody(),
                                        supportsAttachments=False).execute()

        except HttpError as e:
            # An HttpError could indicate a number of things including a missing calendar or a
            #  Bad Request/malformed data. If this occurs, stop processing and report back to the
            #  server.

            # Log the occurrence
            logging.info("Error encountered while pushing Event: {} to Google Calendar".format(duty["start"]))
            logging.error(str(e))

            # Wrap the exception in a ScheduleExportError and raise it
            raise self.ScheduleExportError(e, "Unable to export schedule to Google Calendar.")

        logging.info("Export complete")

    class BaseGCalIntegratinatorException(Exception):
        # Base GCalIntegratinator Exception

        def __init__(self, *args):
            # If args are provided
            if args:
                # Then set the message as the first argument
                self.message = args[0]
                logging.debug("BASE ERROR CREATION: {}".format(args))

            else:
                # Otherwise set the message to None
                self.message = None

            # Set the exception name to GCalIntegratinatorError
            self.exceptionName = "GCalIntegratinatorError"

        def __str__(self):
            # If a message has been defined
            if self.message is not None:
                # Then put the message in the string representation
                return "{}".format(self.message)

            else:
                # Otherwise return a default string
                return "{} has been raised".format(self.exceptionName)

    class CalendarCreationError(BaseGCalIntegratinatorException):
        """GCalIntegratinator Exception to be raised when an error occurs
            during the creation of the a Google Calendar."""

        def __init__(self, *args):
            # Pass the arguments to the parent class.
            super().__init__(*args)

            # Set the name of the exception
            self.exceptionName = "GoogleCalendarCreationError"

    class InvalidCalendarCredentialsError(BaseGCalIntegratinatorException):
        """GCalIntegratinator Exception to be raised if the provided
            Google Calendar credentials are invalid."""

        def __init__(self, *args):
            # Pass the arguments to the parent class.
            super().__init__(*args)

            # Set the name of the exception
            self.exceptionName = "InvalidCalendarCredentialsError"

    class ExpiredCalendarCredentialsError(BaseGCalIntegratinatorException):
        """GCalIntegratinator Exception to be raised if the provided Google
            Calendar calendar credentials have expired."""

        def __init__(self, *args):
            # Pass the arguments to the parent class.
            super().__init__(*args)

            # Set the name of the exception
            self.exceptionName = "ExpiredCalendarCredentialsError"

    class ScheduleExportError(BaseGCalIntegratinatorException):
        """GCalIntegratinator Exception to be raised if an error is encountered
            when attempting to export a schedule to Google Calendar."""

        def __init__(self, wrappedException, *args):
            # Pass the arguments to the parent class.
            super().__init__(*args)

            # Set the name of the exception
            self.exceptionName = "ScheduleExportError"

            # Set the wrappedException
            self.wrappedException = wrappedException

    class UnexpectedError(BaseGCalIntegratinatorException):
        """GCalIntegratinator Exception to be raised if an unknown
            error occurs within the GCalIntegratintor object"""

        def __init__(self, location, wrappedException, *args):
            # Pass the arguments to the parent class.
            super().__init__(self, args)

            # Set the name of the exception
            self.exceptionName = "GCalIntegratinatorUnknownError"

            # Set the location of where the error occurred.
            self.exceptionLocation = location

            # Set the wrapped exception
            self.wrappedException = wrappedException


class Event:
    """ Object for abstracting the Event schema that is used by the Google Calendar API """

    def __init__(self, summary, description, date):
        self.__body = {
            # Taken from https://googleapis.github.io/google-api-python-client/docs/dyn/calendar_v3.events.html#insert
            #  with supplemental information from https://developers.google.com/calendar/v3/reference/events/insert

            "summary": summary,  # Title of the event.

            "description": description,  # Description of the event. Can contain HTML. Optional.

            "start": {          # The (inclusive) start time of the event. For a recurring event, this is the
                                #  start time of the first instance.
                "date": date    # The date, in the format "yyyy-mm-dd", if this is an all-day event.
            },

            "end": {            # The (exclusive) end time of the event. For a recurring event,
                                #  this is the end time of the first instance.
                "date": date    # The date, in the format "yyyy-mm-dd", if this is an all-day event.
            },

            "status": "confirmed",  # Status of the event. Optional. Possible values are:
                                    #    - "confirmed" - The event is confirmed. This is the default status.
                                    #    - "tentative" - The event is tentatively confirmed.
                                    #    - "cancelled" - The event is cancelled (deleted). The list method returns
                                    #                    cancelled events only on incremental sync (when syncToken or
                                    #                    updatedMin are specified) or if the showDeleted flag is set to
                                    #                    true. The get method always returns them. A cancelled status
                                    #                    represents two different states depending on the event type:
                                    #                       - Cancelled exceptions of an uncancelled recurring event
                                    #                          indicate that this instance should no longer be presented
                                    #                          to the user. Clients should store these events for the
                                    #                          lifetime of the parent recurring event.
                                    #                          Cancelled exceptions are only guaranteed to have values
                                    #                          for the id, recurringEventId and originalStartTime fields
                                    #                          populated. The other fields might be empty.
                                    #                       - All other cancelled events represent deleted events.
                                    #                          Clients should remove their locally synced copies. Such
                                    #                          cancelled events will eventually disappear, so do not
                                    #                          rely on them being available indefinitely.
                                    #  Deleted events are only guaranteed to have the id field populated. On the
                                    #   organizer's calendar, cancelled events continue to expose event details
                                    #   (summary, location, etc.) so that they can be restored (undeleted). Similarly,
                                    #   the events to which the user was invited and that they manually removed continue
                                    #   to provide details. However, incremental sync requests with showDeleted set to
                                    #   false will not return these details.
                                    #  If an event changes its organizer (for example via the move operation) and the
                                    #   original organizer is not on the attendee list, it will leave behind a cancelled
                                    #   event where only the id field is guaranteed to be populated.

            "transparency": "opaque",   # Whether the event blocks time on the calendar. Optional. Possible values are:
                                        #   - "opaque" - Default value. The event does block time on the calendar. This
                                        #                is equivalent to setting Show me as to Busy in the Calendar UI.
                                        #   - "transparent" - The event does not block time on the calendar. This is
                                        #                      equivalent to setting Show me as to Available in the
                                        #                      Calendar UI.
        }

    def getBody(self):
        # Return the Event Body
        return self.__body


if __name__ == "__main__":
    g = gCalIntegratinator()
