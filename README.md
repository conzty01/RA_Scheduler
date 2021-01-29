# Resident Assistant Duty Scheduling Application
The Resident Assistant Duty Scheduling Application (RADSA) 
is Web application that schedules Resident Assistants for 
nightly duty shifts and displays the schedule for the RAs 
to see. The application allows RAs to login and submit any 
conflicts they might have for a particular month. Then a 
Hall Director (HD), or their Assistants (AHDs), may run 
the scheduling algorithm, manually manipulate the result
and export the schedule to Google Calendar.


## Getting Started

These instructions will get you a copy of the project up 
and running on your local machine for development and 
testing purposes. See deployment for notes on how to 
deploy the project on a live system.


### Prerequisites

RADSA utilizes a Flask web server to serve pages to 
the client. The web server also communicates with a 
PostgreSQL database to display the proper information 
to the client in addition to running the scheduling 
algorithm. For this application, you will need:

* PostgreSQL 9.5
* Python 3.5
* VirtualEnv 15.1


### Installing

Here is a step by step series of examples that tells 
you how to get the development environment up and running.

#### Installing PostgreSQL

```
$ sudo apt-get update
$ sudo apt-get install postgresql postgresql-contrib
$ sudo -u postgres createuser --interactive
```
Follow the prompts to create a role for yourself. I 
suggest creating a role that is the same name as your 
username and making yourself a superuser.

#### Installing Python

```
$ sudo apt-get install python3.5
```

#### Installing VirtualEnv

```
$ sudo pip install virtualenv
$ virtualenv -p python3 /path/to/home/MyEnv
$ source /path/to/home/MyEnv/bin/activate
```
In order to develop in the correct Python environment, 
you will need to perform the last step each time you close 
your terminal. Similarly, if you would like to exit the 
virtual environment, simply type `deactivate` in the terminal.

With all of the above prerequisites installed, you should 
be able to run
```
$ python createDB.py
$ python populateDB.py
$ python scheduleServer.py
```
to create the Database, populate it with some starting data,
and start the Flask server. You can then open the browser 
of your choice and navigate to `localhost:5000/`.


## Running the tests

Unit tests are automatically run against each branch and
PR by [Travis CI](https://travis-ci.com/), however they can
also be run manually by following the steps below:

1. Open a terminal and navigate to the application directory
    (`~/RAscheduler/` for example).
2. Execute the following command: 
    `python -m unittest discover -s ./tests/ -p "*_test.py"`


## Deployment

RADSA is deployed on [Heroku](https://www.heroku.com/).


## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) 
for details on our code of conduct, and the process for 
submitting pull requests to us.


## Versioning

We use [CalVer](https://calver.org/) for versioning. The schema used
by this project is YY.MM.DD

For the versions available, see the 
[releases on this repository](https://github.com/conzty01/RA_Scheduler/releases). 


## Authors

* **Tyler Conzett** - [conzty01](https://github.com/conzty01)

See also the list of [contributors](https://github.com/conzty01/RA_Scheduler/contributors) 
who participated in this project.


## License

This project is licensed under the MIT License - see 
the [LICENSE.md](LICENSE.md) file for details


## Acknowledgments

Special thanks to [Ryan Ehrhardt](https://github.com/Hoxios)
for the inspiration for this project.
