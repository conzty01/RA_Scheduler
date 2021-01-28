# Hall Module
This directory contains a Flask Blueprint that handles all of the 
functionality regarding Residence Hall Management.

Template Folder: `./templates` <br />
Static Folder: `./static` <br />
Blueprint Prefix: `/hall/...` <br />
Blueprint API Location: `/hall/api/...` <br />


## Views
The following are the views which are available in this blueprint.

### [/hall](https://localhost:5000/hall/)
The landing page for this blueprint that will display the Hall Settings
to the user and provide a way for the user to edit those settings.

Required Auth Level (Role): _**≥ HD**_ <br />
Accepted Method(s): _**GET**_


## API Methods
The following are the API methods which are available in this 
blueprint.

### [/getHallSettings](https://localhost:5000/hall/api/getHallSettings)
API Method used to return an object containing the list of hall settings
for the desired hall.

Required Auth Level (Role): _**≥ HD**_ <br />
Accepted Method(s): _**GET**_

If called from the server, this function accepts the following parameters:

| Name   | Type    | Description  |
|--------|---------|--------------|
| hallId | `<int>` | An integer representing the id of the desired residence hall in the res_hall table.|

If called from a client, this function does not accept any parameters, but
rather, uses the hall id that is associated with the user.

This method returns an object with the following specifications:
```
[
    {
        "settingName": ""
        "settingDesc": ""
        "settingVal": ""
    },
    ...
]
```

### [/saveHallSettings](https://localhost:5000/hall/api/saveHallSettings)
API Method used to save changes made to the Hall Settings for the user's hall.

Required Auth Level (Role): _**≥ HD**_ <br />
Accepted Method(s): _**POST**_

This method is currently unable to be called from the server.

If called from a client, the following parameters are required:

| Name  | Type    | Description  |
|-------|---------|--------------|
| name  | `<str>` | The name of the Hall Setting that has been changed.|
| value | `<ukn>` | The new value for the setting that has been altered.|

This method returns a standard return object whose status is one of the
following:

 1 : the save was successful <br />
 0 : the user does not belong to the provided hall <br />
-1 : the save was unsuccessful <br />
