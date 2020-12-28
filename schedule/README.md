# Schedule Module
This directory contains a Flask Blueprint that handles 
all of the functionality regarding Duty Scheduling.

Template Folder: `./templates` <br />
Static Folder: `./static` <br />
Blueprint Prefix: `/schedule/...` <br />
Blueprint API Location: `/schedule/api/...` <br />

## Views
The following are the views which are available in this blueprint.

### [/editSched](https://localhost:5000/schedule/editSched)
The landing page for this blueprint that will display the Hall Settings
to the user and provide a way for them to edit said settings.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**GET**_


## API Methods
The following are the API methods which are available in this 
blueprint.

### [/getSchedule](https://localhost:5000/schedule/api/getSchedule)
API Method used to return the regularly scheduled duties for the given hall
and timeframe. This method also allows for specification on whether or not
the returned duties should be associated with their RA's respective colors
or a default color. Regardless of this value, any duties associated with
the user are associated with their color.

Required Auth Level (Role): _**None**_ <br />
Accepted Method(s): _**GET**_

If called from the server, this function accepts the following parameters:

| Name          | Type     | Description  |
|---------------|----------|--------------|
| start         | `<str>`  | A string representing the first day that should be included for the returned RA conflicts.|
| end           | `<str>`  | A string representing the last day that should be included for the returned RA conflicts.|
| hallId        | `<int>`  | An integer representing the id of the desired residence hall in the res_hall table.|
| showAllColors | `<bool>` | A boolean that, if set to True, will associate the returned duties with their RA's respective color. Setting this to False will associate each duty with the default color of #2C3E50.|

If called from a client, the following parameters are required:

| Name          | Type     | Description  |
|---------------|----------|--------------|
| start         | `<str>`  | A string representing the first day that should be included for the returned RA conflicts.|
| end           | `<str>`  | A string representing the last day that should be included for the returned RA conflicts.|
| showAllColors | `<bool>` | A boolean that, if set to True, will associate the returned duties with their RA's respective color. Setting this to False will associate each duty with the default color of #2C3E50.|

This method returns an object with the following specifications:
```
[
    {
        "id": <ra.id>,
        "title": <ra.first_name> + " " + <ra.last_name>,
        "start": <day.date>,
        "color": <ra.color or "#2C3E50">,
        "extendedProps": {"dutyType": "std"}
    }
]
```

### [/runScheduler](https://localhost:5000/schedule/api/runScheduler)
API Method that runs the duty scheduler for the given
Res Hall and month. Any users associated with the staff
that have an auth_level of HD will not be scheduled.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name        | Type    | Description  |
|-------------|---------|--------------|
| monthNum    | `<int>` | An integer representing the numeric month number for the desired month using the standard gregorian calendar convention.|
| year        | `<int>` | An integer denoting the year for the desired time period using the standard gregorian calendar convention.|
| noDuty      | `<str>` | A string containing comma separated integers that represent a date in the month in which no duty should be scheduled. If set to an empty string, then all days in the month will be scheduled.|
| eligibleRAs | `<str>` | A string containing comma separated integers that represent the ra.id for all RAs that should be considered for duties. If set to an empty string, then all ras with an auth_level of less than HD will be scheduled.|

This method returns a standard return object whose status is one of the
following:

 1 : the duty scheduling was successful <br />
 0 : the duty scheduling was unsuccessful <br />
-1 : an error occurred while scheduling

### [/changeRAonDuty](https://localhost:5000/schedule/api/changeRAonDuty)
API Method will change the RA assigned for a given duty
from one RA to another in the same hall.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name    | Type    | Description  |
|---------|---------|--------------|
| dateStr | `<str>` | A string denoting the duty for the user's hall that is to be altered.|
| newId   | `<int>` | An integer representing the ra.id value for the RA that is to be assigned for the given duty.|
| oldName | `<str>` | A string containing the name of the RA that is currently on duty for the given day.|

This method returns a standard return object whose status is one of the
following:

 1 : the save was successful <br />
 0 : the save was unsuccessful <br />
-1 : an error occurred while changing the RA on duty

### [/addNewDuty](https://localhost:5000/schedule/api/addNewDuty)
API Method that will add a regularly scheduled duty
with the assigned RA on the given day.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name    | Type    | Description  |
|---------|---------|--------------|
| dateStr | `<str>` | A string denoting the duty for the user's hall that is to be altered.|
| id      | `<int>` | An integer representing the ra.id value for the RA that is to be assigned for the given duty.|

This method returns a standard return object whose status is one of the
following:

 1 : the save was successful <br />
 0 : the save was unsuccessful <br />
-1 : an error occurred while creating the new duty

### [/deleteDuty](https://localhost:5000/schedule/api/deleteDuty)
API Method that will delete a regularly scheduled duty
with the given RA and day.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name    | Type    | Description  |
|---------|---------|--------------|
| dateStr | `<str>` | A string denoting the duty for the user's hall that is to be altered.|
| raName  | `<str>` | A string containing the name of the RA that is currently on duty for the given day.|

This method returns a standard return object whose status is one of the
following:

 1 : the save was successful <br />
 0 : the save was unsuccessful <br />
-1 : an error occurred while deleting the duty

