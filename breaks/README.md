# Breaks Module
This directory contains a Flask Blueprint that handles all of the 
functionality regarding Break Duties.

Template Folder: `./templates` <br />
Static Folder: `./static` <br />
Blueprint Prefix: `/breaks/...` <br />
Blueprint API Location: `/breaks/api/...` <br />

## Views
The following are the views which are available in this blueprint.

### [/editBreaks](https://localhost:5000/breaks/editBreaks)
The landing page for this blueprint that will display a calendar which
users can interact with to view, add, edit, and remove break duties.
RA break duty statistics will also be displayed in a side panel for the
user to see.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**GET**_

This endpoint will render and return the `editBreaks.html` template which inherits from `base.html`.

## API Methods
The following are the API methods which are available in this 
blueprint.


### [/getRABreakStats](https://localhost:5000/breaks/api/getRABreakStats)
API Method that will calculate a staff's RA Break Duty statistics for the given
time period. This method does not calculate the number of points an RA has
due to breaks, but rather counts the number of break duties the RA has been
assigned to for the given time period.

Required Auth Level (Role): _**None**_ <br />
Accepted Method(s): _**GET**_

If called from the server, this function accepts the following parameters:

| Name         | Type    | Description  |
|--------------|---------|--------------|
| hallId       | `<int>` | An integer representing the id of the desired residence hall in the res_hall table.|
| startDateStr | `<str>` | A string representing the first day that should be included for the duty points calculation.|
| endDateStr   | `<str>` | A string representing the last day that should be included for the duty points calculation.|

If called from a client, the following parameters are required:

| Name  | Type    | Description  |
|-------|---------|--------------|
| start | `<str>` | A string representing the first day that should be included for the break duty count calculation.|
| end   | `<str>` | A string representing the last day that should be included for the duty count calculation.|

This method returns an object with the following specifications:
```
{
    <ra.id 1> : {
        "name": ra.first_name + " " + ra.last_name,
        "count": <number of break duties RA 1 has>
    },
    <ra.id 2> : {
        "name": ra.first_name + " " + ra.last_name,
        "count": <number of break duties RA 2 has>
    },
    ...
}
```


### [/getBreakDuties](https://localhost:5000/breaks/api/getBreakDuties)
API Method that will calculate a staff's RA Break Duty statistics for the given
time period. This method does not calculate the number of points an RA has
due to breaks, but rather counts the number of break duties the RA has been
assigned to for the given time period.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**GET**_

If called from the server, this function accepts the following parameters:

| Name          | Type     | Description  |
|---------------|----------|--------------|
| hallId        | `<int>`  | An integer representing the id of the desired residence hall in the `res_hall` table.|
| start         | `<str>`  | A string representing the first day that should be included for the returned duty schedule.|
| end           | `<str>`  | A string representing the last day that should be included for the returned duty schedule.|
| showAllColors | `<bool>` | A boolean value representing whether the returned duty schedule should include the RA's `ra.color` value or if the generic value `#2C3E50` should be returned. Setting this value to True will return the RA's `ra.color` value. By default this parameter is set to False. |
| raId          | `<int>`  | An integer representing the id of the RA that should be considered the requesting user. By default this value is set to -1 which indicates that no RA should be considered the requesting user.|

If called from a client, the following parameters are required:

| Name      | Type     | Description  |
|-----------|----------|--------------|
| start     |  `<str>` | A string representing the first day that should be included for the returned duty schedule.|
| end       |  `<str>` | A string representing the last day that should be included for the returned duty schedule.|
| allColors | `<bool>` | A boolean value representing whether the returned duty schedule should include the RA's `ra.color` value or if the generic value `#2C3E50` should be returned. Setting this value to True will return the RA's `ra.color` value.|

_NOTE: Regardless of what value is specified for allColors, the if the ra.id
        that is associated with the user appears in the break schedule, the
        ra.color associated with the user will be displayed. This is so that
        the user can more easily identify when they are on duty._

This method returns an object with the following specifications:
```
[
    {
        "id": <ra.id>,
        "title": <ra.first_name + " " + ra.last_name>,
        "start": <string value of day.date associated with the scheduled duty>,
        "color": <ra.color OR #2C3E50 if allColors/showAllColors is False>,
        "extendedProps": {"dutyType":"brk"}
    },
    ...
]
```


### [/addBreakDuty](https://localhost:5000/breaks/api/addBreakDut)
API Method that adds a break duty into the client's Res Hall's schedule 
on the desired date.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name    | Type    | Description  |
|---------|---------|--------------|
| id      | `<int>` | An integer representing the ra.id for the RA that should be assigned to the break duty.|
| pts     | `<int>` | An integer represnting how many points the new break duty should be worth.|
| dateStr | `<str>` | A string representing the date that the break duty should occur on.|

This method returns a standard return object whose status is one of the
following:

 1 : the save was successful <br />
 0 : the client does not belong to the same hall as the provided RA <br />
-1 : the save was unsuccessful <br />


### [/deleteBreakDuty](https://localhost:5000/breaks/api/deleteBreakDuty)
API Method that removes the desired break duty from the client's Res Hall's schedule.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name    | Type    | Description  |
|---------|---------|--------------|
| raName  | `<str>` | A string denoting the full name of the RA associated with the break duty that should be removed.|
| dateStr | `<str>` | A string representing the date that the break duty should occur on.|

This method returns a standard return object whose status is one of the
following:

1 : the save was successful <br />
0 : the client does not belong to the same hall as the provided RA <br />
-1 : the save was unsuccessful <br />


### [/changeBreakDuty](https://localhost:5000/breaks/api/changeBreakDuty)
API Method that changes the RA assigned to a given break duty
in the client's Res Hall's schedule from one RA on their staff
to another.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name    | Type    | Description  |
|---------|---------|--------------|
| oldName | `<str>` | A string denoting the full name of the RA associated with the break duty that should be changed.|
| newId   | `<int>` | An integer representing the ra.id for the RA that should be assigned for the break duty.|
| dateStr | `<str>` | A string representing the date of the break duty.|

This method returns a standard return object whose status is one of the
following:

 1 : the save was successful <br />
 0 : the client does not belong to the same hall as the provided RA <br />
-1 : the save was unsuccessful <br />
