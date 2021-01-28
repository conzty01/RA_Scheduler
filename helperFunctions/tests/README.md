# HelperFunctions Module /tests Folder
This folder contains all of the Python unittests for the components of 
the RADSA application which reside in the HelperFunctions module. The 
purpose of these unittests are to ensure predictable functionality of 
the various components of RADSA while development continues. These tests 
will be run on each Github pull request before it is allowed to be merged.

## Running Tests

Developers are encouraged to run these tests on their repos before 
submitting a pull request to speed up the debugging process. The following 
commands will run the test suite using the `runTests` script:

```
cd \path\to\repo\
runTests
```

The expected output of a repo that passes all tests should be 'OK' with all 
tests being represented by a '.' rather than an E. Additionally, there 
should be no error messages displayed (although errors should be tested for 
in the unittests).

## Creating Tests

Ideally, each component of RADSA should have a corresponding test file 
describing the expected behavior. Developers will be required to create a 
test file for any new components that they may create before their PR will 
be accepted.

### Conventions

For consistency, all tests will be required to adhere to the following 
conventions.

#### Naming

In order for automated testing and human readability, all tests should follow 
the same naming convention. The name of the test file should be the name of 
the component that is being tested, followed by `_test.py`. For example, a 
test for the RA object would be named `RA_test.py`.

#### Coding

Refer to the Python unittest documentation 
[here](https://docs.python.org/3/library/unittest.html) for syntax and 
unittest related questions. All tests should be self contained and should not 
rely on changes that are created in other tests-- even if they are in the same 
file. If tests need to share data between themselves, then this data should be 
created in the `setUp` method. Additionally, if there are steps that need to 
occur at the end of the tests, then this should be executed in the `tearDown` 
method.
