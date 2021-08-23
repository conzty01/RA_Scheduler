# Helper Functions Module
This directory is a module that contains functions
which can be used by any Blueprint or submodule in
this project. These functions cannot be reached through 
an HTTP endpoint but can be imported and utilized by
any Python script.

## Functions

### getAuth()
Validate the user against the DB and return the user's information 
as a dictionary

This function does not accept any parameters.

This function returns an AuthenticatedUser Object.


### stdRet(status, msg)
Create a standard return object to help simplify/unify API responses
going back to the client when no additional data is to be sent.

This function accepts the following parameters:

| Name   | Type    | Description  |
|--------|---------|--------------|
| status | `<int>` | The status of the message which indicates whether an operation was successful or if it encountered an error.|
| msg    | `<str>` | The message that should be associated with the provided status.|

This function returns a dictionary in the following format:
```
{
    "status": <value of status parameter",
    "msg": <value of msg parameter"
}
```

### fileAllowed(filename)
Return a boolean denoting whether a particular file should be allowed to be
uploaded based on its filename. Only files with extensions that are in the
ALLOWED_EXTENSIONS global variable will be accepted.

This function accepts the following parameter:

| Name     | Type    | Description  |
|----------|---------|--------------|
| filename | `<str>` | The full name of a file that is to be checked|

This function returns boolean denoting whether a particular file should be allowed to be
uploaded to the server.
For example, it `.txt` and `.csv` files are allowed but `.png` files are not:
```
>>> fileAllowed("test.txt")
>>> True
>>> 
>>> fileAllowed("test.csv")
>>> True
>>> 
>>> fileAllowed("test.png")
>>> False
```

### getSchoolYear(month, year)
Return a tuple containing two strings that denote the start and end date of 
the school year that the provided month and year belong to.

_NOTE: A school year is considered to take place between August 1st of 
        a given year and July 31st of the following year._

This function accepts the following parameters:

| Name   | Type    | Description  |
|--------|---------|--------------|
| month  | `<int>` | The integer value representing the month following the standard gregorian calendar convention.|
| year   | `<str>` | The integer value representing the calendar year following the standard gregorian calendar convention.|

This function returns a tuple of strings that represent the start and end
date of the school year.
For example:
```
>>> getSchoolYear(11, 2020)
>>> ("2020-08-01", "2021-07-31")
>>> 
>>> getSchoolYear(3, 2021)
>>> ("2020-08-01", "2021-07-31")
>>> 
>>> getSchoolYear(1, 2020)
>>> ("2019-08-01", "2020-07-31")
```

### getCurSchoolYear()
Calculate what school year it is based on the current date and return a tuple
containing two strings that represent the start and end date of the school year.

This function does not accept any parameters.

This function returns a tuple of strings that represent the start and end
date of the school year.
For example, if the function is executed on 11-07-2020:
```
>>> getCurSchoolYear()
>>> ("2020-08-01", "2021-07-31")
```

### formatDateStr(day, month, year, format="YYYY-MM-DD", divider="-")
Generate a date string using the provided day, month, and year values
that adheres to the provided format.

This function accepts the following parameters:

| Name    | Type    | Description |
|---------|---------|-------------|
| day     | `<int>` | The integer value representing the day following the standard gregorian calendar convention.|
| month   | `<int>` | The integer value representing the month following the standard gregorian calendar convention.|
| year    | `<int>` | The integer value representing the calendar year following the standard gregorian calendar convention.|
| format  | `<str>` | A string denoting the expected desired format for the date string. In this format, `Y` denotes year, `M` denotes month, and `D` denotes day. By default, this value is "YYYY-MM-DD".|
| divider | `<str>` | A string denoting the character that divides the parts of the format input string. By default, this value is `-`.|

This function returns a string that is formatted to fit the schema provided.
For example:
```
>>> formatDateStr(7, 11, 2020)
>>> "2020-11-07"
>>>
>>> formatDateStr(7, 11, 2020, format="DD-MM-YYYY")
>>> "07-11-2020"
>>>
>>> formatDateStr(7, 11, 2020, format="DD/MM/YYYY", divider="/")
>>> "07/11/2020"
```

### packageReturnObject(obj, fromServer)
Package up the provided object. If the fromServer parameter is set to
True, then the object will be returned as-is. If it is set to False,
then a serialized version of the object is returned.

 This function accepts the following parameters:

| Name       | Type      | Description |
|------------|-----------|-------------|
| obj        | `<obj>`   | Object to be packaged. |
| fromServer | `<bool>`  | Boolean denoting whether the object should be packaged as a Flask response or not. |