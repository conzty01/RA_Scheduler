# Resident Assistant Duty Scheduling Application
The Resident Assistant Duty Scheduling Application (RADSA) is Web application that schedules Resident Assistants for nightly duty shifts and displays the schedule for the RAs to see. The application allows RAs to login and submit any conflicts they might have for a particular month, and a Hall Director, or their Assistants, may run the scheduling algorithm, view the result and make any changes before displaying it to the RAs.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

RADSA utilizes a Flask web server to serve pages to the client. The web server also communicates with a PostgreSQL database to display the proper information to the client in addition to running the scheduling algorithm. For this application, you will need:

* PostgreSQL 9.5
* Python 3.5
* VirtualEnv 15.1

### Installing

Here is a step by step series of examples that tells you how to get the development environment up and running.

Installing PostgreSQL

```
$ sudo apt-get update
$ sudo apt-get install postgresql postgresql-contrib
$ sudo -u postgres createuser --interactive
```
Follow the prompts to create a role for yourself. I suggest creating a role that is the same name as your username and making yourself a superuser.

Installing Python

```
$ sudo apt-get install python3.5
```

Installing VirtualEnv

```
$ sudo pip install virtualenv
$ virtualenv -p python3 /path/to/home/MyEnv
$ source /path/to/home/MyEnv/bin/activate
```
In order to develop in the correct Python environment, you will need to perform the last step each time you close your terminal. Similarly, if you would like to exit the virtual enviromnet, simply type `deactivate` in the terminal.

With all of the above prerequisites installed, you should be able to run
```
$ python createDB.py
$ python scheduleServer.py
```
to start the Flask server. You can then open the browser of your choice and go to `localhost:8000/`.

<!-- ## Running the tests

Explain how to run the automated tests for this system 

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```
-->
## Deployment

RADSA is deployed on [Heroku](https://www.heroku.com/).
<!--
## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 
-->
## Authors

* **Tyler Conzett** - *Initial work* - [conzty01](https://github.com/conzty01)
* **Ryan Ehrhardt** - *Initial work* - [Hoxios](https://github.com/Hoxios)

See also the list of [contributors](https://github.com/conzty01/RA_Scheduler/contributors) who participated in this project.

<!--## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc
-->
