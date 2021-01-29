# Integration Module
This directory contains a Flask Blueprint that handles all of the 
functionality regarding integration with other applications.

Blueprint Prefix: `/int/...` <br />
Blueprint API Location: `/int/api...` <br />

## Current Integrations
- [Google Calendar](google-calendar)


## Google Calendar

### Functions
The following are functions that aid in the integration 
with Google Calendar.

#### createGoogleCalendar(calInfoId)
Create a Secondary Google Calendar for the provided 
hall using the passed Google Calendar Account information.

Required Auth Level (Role): _**None**_

When called from the server, this function accepts 
the following parameters:

| Name      | Type    | Description  |
|-----------|---------|--------------|
| calInfoId | `<int>` | Integer representing the google_calendar_info.id field in the DB that should be used to find the appropriate account credentials.|

This method returns a standard return object whose status is one of the
following:

 1 : the calendar creation was successful <br />
-1 : the calendar creation was unsuccessful


### Integration Process Methods
The following are the HTTPS endpoints relating to connecting to 
and disconnecting from Google Calendar which are made available
in this blueprint.

#### [/GCalRedirect](https://localhost:5000/int/GCalRedirect)
Method that initializes the process for connecting a Google
Calendar Account to the hall associated with the user.

Required Auth Level (Role): _**>= HD**_ <br />
Accepted Method(s): _**GET**_

This method is currently unable to be called from the server.

If called from a client, no parameters are required.

This method returns Flask redirect to redirect the user to
the Google Authorization URL to take the next steps for
connecting a Google Calendar Account on Google's side of things.

#### [/GCalAuth](https://localhost:5000/int/GCalAuth)
Method that handles the Google Calendar authorization response
and generates Google Calendar credentials that are to be saved 
in the DB.

Required Auth Level (Role): _**>= HD**_ <br />
Accepted Method(s): _**GET**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name  | Type    | Description  |
|-------|---------|--------------|
| state | `<str>` | A string denoting the authorization state associated with this authorization response.|

This method returns a Flask redirect to redirect the user to
the hall_bp.manHall page.

#### [/disconnectGCal](https://localhost:5000/int/disconnectGCal)
Method that disconnect the Google Calendar for the requesting
user's Res Hall.

Required Auth Level (Role): _**>= HD**_ <br />
Accepted Method(s): _**GET**_

This method is currently unable to be called from the server.

If called from a client, no parameters are required.

This method returns a Flask redirect to redirect the user to
the hall_bp.manHall page.

### API Methods
The following are the API endpoints relating to Google Calendar 
which are available in this blueprint.

#### [/exportToGCal](https://localhost:5000/int/api/exportToGCal)
API Method that exports the given schedule to the Google
Calendar associated with the user's Res Hall.

Required Auth Level (Role): _**>= AHD**_ <br />
Accepted Method(s): _**GET**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name     | Type    | Description  |
|----------|---------|--------------|
| monthNum | `<int>` | An integer representing the numeric month number for the desired month using the standard gregorian calendar convention.|
| year     | `<int>` | An integer denoting the year for the desired time period using the standard gregorian calendar convention.|

This method returns a standard return object whose status is one of the
following:

 1 : the export was successful <br />
 0 : the user's Res Hall must reconnect the Google Calendar Account <br />
-1 : the export was unsuccessful
