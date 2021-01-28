# Staff Module
This directory contains a Flask Blueprint that handles 
all of the functionality regarding Staff Management

Template Folder: `./templates` <br />
Static Folder: `./static` <br />
Blueprint Prefix: `/staff/...` <br />
Blueprint API Location: `/staff/api/...` <br />

## Views
The following are the views which are available in this blueprint

### [/](https://localhost:5000/staff/)
The landing page for this blueprint that will display the list of
staff members to the user and provide a way for them to edit individual
staff members' information and add or remove staff as well.

Required Auth Level (Role): _**≥ HD**_ <br />
Accepted Method(s): _**GET**_


## API Methods
The following are the API methods which are available in this 
blueprint.

### [/getStats](https://localhost:5000/staff/api/getStats)
API Method that will calculate and return the RA duty statistics for a given month.

Required Auth Level (Role): _**None**_ <br />
Accepted Method(s): _**GET**_

If called from the server, this function accepts the following parameters:

| Name         | Type    | Description  |
|--------------|---------|--------------|
| hallId       | `<int>` | An integer representing the id of the desired residence hall in the res_hall table.|
| startDateStr | `<str>` | A string representing the first day that should be included for the duty points calculation.|
| endDateStr   | `<str>` | A string representing the last day that should be included for the duty points calculation.|
| maxBreakDay  | `<str>` | A string representing the latest break duty that should be included for the duty points calculation.|

If called from a client, the following parameters are required:

| Name  | Type    | Description  |
|-------|---------|--------------|
| start | `<str>` | A string representing the first day that should be included for the duty points calculation.|
| end   | `<str>` | A string representing the last day that should be included for the duty points calculation.|

This method returns an object with the following specifications:
```
{
    <ra.id 1> : {
        "name": ra.first_name + " " + ra.last_name,
        "pts": <number of duty points for RA 1>
    },
    <ra.id 2> : {
        "name": ra.first_name + " " + ra.last_name,
        "pts": <number of duty points for RA 2>
    },
    ...
}
```

### [/getStaffInfo](https://localhost:5000/staff/api/getStaffInfo)
API Method that will calculate and return the RA duty statistics as for the
user's staff for the current school year.

Required Auth Level (Role): _**≥ HD**_ <br />
Accepted Method(s): _**GET**_

This method is currently unable to be called from the server.

If called from a client, this function does not accept any parameters, but
rather, uses the hall id that is associated with the user.

This method returns an object with the following specifications:
```
{
    raList : [
        [
            <ra.id 1>,
            <ra.first_name 1>,
            <ra.last_name 1>,
            <ra.email 1>,
            <ra.date_started 1>,
            <res_hall.name>,
            <ra.color 1>,
            <ra.auth_level 1>
        ],
        [...],
        ...
    ],
    pts : {
        <ra.id 1> : {
            "name": ra.first_name + " " + ra.last_name,
            "pts": <number of duty points for RA 1>
        },
        <ra.id 2> : {
            "name": ra.first_name + " " + ra.last_name,
            "pts": <number of duty points for RA 2>
        },
        ...
    }
}
```

### [/changeStaffInfo](https://localhost:5000/staff/api/changeStaffInfo)
API Method that updates an RA record with the provided information.

Required Auth Level (Role): _**≥ HD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name      | Type    | Description  |
|-----------|---------|--------------|
| fName     | `<str>` | The new value for the RA's first name (ra.first_name)|
| lName     | `<str>` | The new value for the RA's last name (ra.last_name)|
| startDate | `<str>` | The new date string value for the RA's start date (ra.start_date). Must be provided in YYYY-MM-DD format.|
| color     | `<str>` | The new value for the RA's color (ra.color)|
| email     | `<str>` | The new value for the RA's email (ra.email)|
| authLevel | `<int>` | An integer denoting the authorization level for the RA. Must be an integer value in the range: 1-3.|
| raID      | `<int>` | An integer denoting the row id for the desired RA in the ra table.|

This method returns a standard return object whose status is one of the
following:

 1 : the save was successful <br />
 0 : the client does not belong to the same hall as the provided RA <br />
-1 : the save was unsuccessful

### [/removeStaffer](https://localhost:5000/staff/api/removeStaffer)
API Method that removes a staff member from the client's res hall. The staff
member that is removed is then associated with the 'Not Assigned' record in
the res_hall table.

Required Auth Level (Role): _**≥ HD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name | Type    | Description  |
|------|---------|--------------|
| raID | `<int>` | An integer denoting the row id for the desired RA in the ra table.|

This method returns a standard return object whose status is one of the
following:

 1 : the removal was successful <br />
 0 : the client does not belong to the same hall as the provided RA <br />
-1 : the removal was unsuccessful

### [/addStaffer](https://localhost:5000/staff/api/addStaffer)
API Method that adds a new staff member to the same res hall as the client.

Required Auth Level (Role): _**≥ HD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name      | Type    | Description  |
|-----------|---------|--------------|
| fName     | `<str>` | The value for the RA's first name (ra.first_name)|
| lName     | `<str>` | The value for the RA's last name (ra.last_name)|
| color     | `<str>` | The value for the RA's color (ra.color)|
| email     | `<str>` | The value for the RA's email (ra.email)|
| authLevel | `<int>` | An integer denoting the authorization level for the RA. Must be an integer value in the range: 1-3.|

This method returns a standard return object whose status is one of the
following:

 1 : the addition was successful <br />
 0 : the client does not belong to the same hall as the provided RA <br />
-1 : the addition was unsuccessful

### [/importStaff](https://localhost:5000/staff/api/importStaff)
API Method that uses an uploaded file to import multiple staff members into
the client's staff. The file must be either a .csv or .txt file that is in
a specific format. An example of this format can be seen in the
'importExample.csv' file located in this blueprint's static folder.

Required Auth Level (Role): _**≥ HD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name | Type              | Description  |
|------|-------------------|--------------|
| file | `<TextIOWrapper>` | An uploaded file that will be used to import multiple staff members into the client's staff.|

This method returns a standard return object whose status is one of the
following:

 1 : the import was successful <br />
 0 : there was an error transmitting the file to the server <br />
-1 : the import was unsuccessful


## Functions

### validateImportStaffUpload(partList)
Helper function designed for the staff_bp.importStaff endpoint that
ensures that the provided row parts fit our expected schema.

This function accepts the following parameters:

| Name     | Type         | Description  |
|----------|--------------|--------------|
| partList | `<lst<str>>` | A list containing string values that have been pulled from a row in the file provided in the import staff process.|

This function returns a tuple containing the following in order:

| Pos | Name    | Type         | Description  |
|-----|---------|--------------|--------------|
| 0   | pl      | `<lst<str>>  -  a list containing string values that have been derived and cleaned from the provided partList input parameter.|
| 1   | valid   | `<bool>      -  a boolean representing whether the parts in the provided partList input parameter fits the expected schema.|
| 2   | reasons | `<lst<str>>  -  a list containing string values that inform the user what, if anything is incorrectly formatted about this row.|
