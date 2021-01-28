# Conflicts Module
This directory contains a Flask Blueprint that handles all of the 
functionality regarding RA Duty Conflicts.

Template Folder: `./templates` <br />
Static Folder: `./static` <br />
Blueprint Prefix: `/conflicts/...` <br />
Blueprint API Location: `/conflicts/api/...` <br />

## Views
The following are the views which are available in this blueprint.

### [/conflicts](https://localhost:5000/conflicts/)
The landing page for this blueprint that will render a calendar
which displays the user's duty conflicts for the given month. The
user can also interact with this calendar to add and remove duty
conflicts for themselves.

Required Auth Level (Role): _**None**_ <br />
Accepted Method(s): _**GET**_

This endpoint will render and return the `conflicts.html` template 
which inherits from `base.html`.

### [/editCons](https://localhost:5000/conflicts/editCons)
An additional view for this blueprint that will render a calendar
which displays all of the duty conflicts entered for the user's
Res Hall.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**GET**_

This endpoint will render and return the `editCons.html` template 
which inherits from `base.html`.


## API Methods
The following are the API methods which are available in this 
blueprint.

### [/getConflicts](https://localhost:5000/conflicts/api/getConflicts)
API Method used to return the requested conflicts for a given user and month.

Required Auth Level (Role): _**None**_ <br />
Accepted Method(s): _**GET**_

If called from the server, this function accepts the following parameters:

| Name     | Type    | Description  |
|----------|---------|--------------|
| monthNum | `<int>` | An integer representing the numeric month number for the desired month using the standard gregorian calendar convention.|
| raID     | `<int>` | An integer denoting the row id for the desired RA in the `ra` table.|
| year     | `<int>` | An integer denoting the year for the desired time period using the standard gregorian calendar convention.|
| hallId   | `<int>` | An integer representing the id of the desired residence hall in the `res_hall` table.|

If called from a client, the following parameters are required:

| Name     | Type    | Description  |
|----------|---------|--------------|
| monthNum | `<int>` | An integer representing the numeric month number for the desired month using the standard gregorian calendar convention.|
| year     | `<int>` | An integer denoting the year for the desired time period using the standard gregorian calendar convention.|

This method returns an object with the following specifications:
```
{
    conflicts: [
        <Datetime object 1 for which the RA has a conflict>,
        <Datetime object 2 for which the RA has a conflict>,
        ...
    ]
}
```

### [/getRAConflicts](https://localhost:5000/conflicts/api/getRAConflicts)
API Method used to return all conflicts for a given RA. If an RA id of -1
is specified, then the result will include conflicts for _all_ RA's on the
user's staff.

Required Auth Level (Role): _**None**_ <br />
Accepted Method(s): _**GET**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name     | Type    | Description  |
|----------|---------|--------------|
| monthNum | `<int>` | An integer representing the numeric month number for the desired month using the standard gregorian calendar convention.|
| year     | `<int>` | An integer denoting the year for the desired time period using the standard gregorian calendar convention.|
| raID     | `<int>` | An integer denoting the row id for the RA in the ra table whose conflicts should be returned. If a value of -1 is passed, then all conflicts for the user's staff will be returned.|

This method returns an object with the following specifications:
```
[
    {
        "id": <conflict.id>,
        "title": <ra.first_name + " " + ra.last_name>,
        "start": <string value of day.date associated with the duty conflict>,
        "color": <ra.color>
    },
    ...
]
```

### [/getRACons](https://localhost:5000/conflicts/api/getRACons)
API Method used to return all duty conflicts for each RA that is part of
the given Res Hall staff.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**GET**_

If called from the server, this function accepts the following parameters:

| Name     | Type    | Description  |
|----------|---------|--------------|
| monthNum | `<int>` | An integer representing the numeric month number for the desired month using the standard gregorian calendar convention.|
| raID     | `<int>` | An integer denoting the row id for the desired RA in the ra table.|
| year     | `<int>` | An integer denoting the year for the desired time period using the standard gregorian calendar convention.|
| hallId   | `<int>` | An integer representing the id of the desired residence hall in the res_hall table.|

If called from a client, the following parameters are required:

| Name  | Type    | Description  |
|-------|---------|--------------|
| start | `<str>` | A string representing the first day that should be included for the returned RA conflicts.|
| end   | `<str>` | A string representing the last day that should be included for the returned RA conflicts.|

This method returns an object with the following specifications:
```
[
    {
        "id": <ra.id>,
        "title": <ra.first_name + " " + ra.last_name>,
        "start": <string value of day.date associated with the duty conflict>,
        "color": <ra.color>,
        },
        ...
]
```

### [/getNumberConflicts](https://localhost:5000/conflicts/api/getNumberConflicts)
API Method used to return a count of the number of conflicts each RA
has submitted for a given month and Res Hall.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**GET**_

If called from the server, this function accepts the following parameters:

| Name     | Type    | Description  |
|----------|---------|--------------|
| hallId   | `<int>` | An integer representing the id of the desired residence hall in the res_hall table.|
| monthNum | `<int>` | An integer representing the numeric month number for the desired month using the standard gregorian calendar convention.|
| year     | `<int>` | An integer denoting the year for the desired time period using the standard gregorian calendar convention.|

If called from a client, the following parameters are required:

| Name     | Type    | Description  |
|----------|---------|--------------|
| monthNum | `<int>` | An integer representing the numeric month number for the desired month using the standard gregorian calendar convention.|
| year     | `<int>` | An integer denoting the year for the desired time period using the standard gregorian calendar convention.|

This method returns an object with the following specifications:
```
{
    <ra.id 1> : <number of conflicts for the given timeframe>,
    <ra.id 2> : <number of conflicts for the given timeframe>,
    ...
}
```
        
### [/processConflicts](https://localhost:5000/conflicts/api/processConflicts)
API Method used to process and save the user's submitted duty conflicts.

Required Auth Level (Role): _**≥ AHD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name      | Type         | Description  |
|-----------|--------------|--------------|
| monthNum  |    `<int>`   | An integer representing the numeric month number for the desired month using the standard gregorian calendar convention.|
| year      |    `<int>`   | An integer denoting the year for the desired time period using the standard gregorian calendar convention.|
| conflicts | `<lst<str>>` | A list containing strings representing dates that the user has a duty conflict with.|

This method returns a standard return object whose status is one of the
following:

 1 : the save was successful <br />
-1 : the save was unsuccessful <br />
