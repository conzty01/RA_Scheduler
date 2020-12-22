from flask_login import UserMixin, current_user, LoginManager, login_required, login_user, logout_user
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
from flask import Flask, render_template, request, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from logging.config import dictConfig
import logging
import os

# Import the appGlobals for this blueprint to use
import appGlobals as ag

# Import the needed functions from other parts of the application
from helperFunctions.helperFunctions import getAuth

# Import the blueprints that will be used.
from breaks.breaks import breaks_bp
from conflicts.conflicts import conflicts_bp
from hall.hall import hall_bp
from integration.integrations import integration_bp
from schedule.schedule import schedule_bp
from staff.staff import staff_bp

# Configure the logger immediately per Flask recommendation

# Get the logging level from the environment
logLevel = os.environ["LOG_LEVEL"].upper()

# Create the logging configuration
dictConfig({
    'version': 1,  # logging module specific-- DO NOT CHANGE
    'formatters': {'default': {
        'format': '[%(asctime)s.%(msecs)d] %(levelname)s in %(module)s: %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': logLevel,
        'handlers': ['wsgi']
    }
})

# Load the HOST_URL from the environment.
HOST_URL = os.environ["HOST_URL"]

# Create the Flask application
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]
app.config["EXPLAIN_TEMPLATE_LOADING"] = os.environ["EXPLAIN_TEMPLATE_LOADING"]

# Set up the Bootstrap application
Bootstrap(app)

# Setup for flask_dance with oauth
app.secret_key = os.environ["SECRET_KEY"]
gBlueprint = make_google_blueprint(
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    scope=["profile", "email"],
    redirect_to="index"
)

# Register our Flask Blueprints
app.register_blueprint(gBlueprint,     url_prefix="/login")
app.register_blueprint(hall_bp,        url_prefix="/hall")
app.register_blueprint(schedule_bp,    url_prefix="/schedule")
app.register_blueprint(integration_bp, url_prefix="/int")
app.register_blueprint(staff_bp,       url_prefix="/staff")
app.register_blueprint(conflicts_bp,   url_prefix="/conflicts")
app.register_blueprint(breaks_bp,      url_prefix="/breaks")

# Set the upload folder for the application
UPLOAD_FOLDER = "./static"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create he SQLAlchemy DB connection for the Flask app
#  SQLAlchemy is used for flask_dance/oauth
db = SQLAlchemy(app)

# Create the login manager for the application
login_manager = LoginManager()
login_manager.init_app(app)

# ----------------------------------
# --      SQLAlchemy Classes      --
# ----------------------------------

class User(UserMixin, db.Model):
    # Contains information about the user
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True)
    ra_id = db.Column(db.Integer, unique=True)


class OAuth(OAuthConsumerMixin, db.Model):
    # Contains information about OAuth tokens
    provider_user_id = db.Column(db.String(256), unique=True)
    # The below links the tokens to the user
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

# The following creates the backend for flask_dance which associates users to OAuth tokens
#   user_required is set to False because of issues when users would first arrive to the
#   application before being authorized by Google and flask_dance would not be able to look
#   them up since they were not already authorized. By setting it to False, the app does not
#   require a user to already exist in our database to continue.
gBlueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user, user_required=False)

# --------------------------------
# --      OAuth Decorators      --
# --------------------------------

@login_manager.user_loader
def load_user(user_id):
    # Query the DB for the given user and return the result.
    return User.query.get(int(user_id))


@app.before_request
def before_request():
    # Before a request is handled, make sure we are communicating
    #  over HTTPS

    # If the request is over HTTP
    if request.url.startswith('http://'):
        # Then replace with HTTPS
        url = request.url.replace('http://', 'https://', 1)
        # Set the code to redirect
        code = 301
        # Return a redirect to the HTTPS url
        return redirect(url, code=code)


@oauth_authorized.connect_via(gBlueprint)
def googleLoggedIn(blueprint, token):
    # Method that will handle the login response from Google

    logging.debug('googleLoggedIn')

    # If we don't have a token
    if not token:
        # Then return False to notify the blueprint
        return False

    # Load the response from the blueprint
    resp = blueprint.session.get("/oauth2/v2/userinfo")

    # If the response is bad
    if not resp.ok:

        logging.info("Google Login Response not OK")
        # Return False to notify the blueprint

        return False

    # Load the Google information from the response json
    google_info = resp.json()

    # Get the user's email from the response
    username = google_info["email"]
    # Get the user's Google id from the response
    gID = str(google_info["id"])

    # Generate a query for the DB to find the appropriate OAuth token
    #  in the database
    query = OAuth.query.filter_by(provider=blueprint.name,
                                  provider_user_id=gID)

    try:
        # Execute the query against the DB
        oauth = query.one()

    except NoResultFound:
        # If there are no result found...
        logging.info("Unable to find user in DB - Creating new user")

        # Then create a new user record in our database
        oauth = OAuth(provider=blueprint.name,
                      provider_user_id=gID,
                      token=token)

    # If we have found a user
    if oauth.user:
        logging.debug("Logging in user")

        # Then log them in
        login_user(oauth.user)

    else:
        # Otherwise, we have a new user that needs to have an RA
        #  associated with them.
        logging.info("Create New User - Searching for Appropriate RA")

        # Create a DB cursor
        cur = ag.conn.cursor()

        # Query the DB for an RA with the matching email so that we can link RAs to their emails
        cur.execute("SELECT id FROM ra WHERE email = %s", (username,))

        # Load the query result
        raId = cur.fetchone()

        # Close the DB cursor
        cur.close()

        # Create a new user in the database
        user = User(username=username, ra_id=raId)

        # Associate it with the OAuth token
        oauth.user = user
        db.session.add_all([user, oauth])

        # Commit hte changes to the DB
        db.session.commit()

        # Log the user in
        login_user(user)

    # Function should return False so that flask_dance won't try to store the token itself
    return False


# ---------------------
# --      Views      --
# ---------------------

@app.route("/logout")
@login_required
def logout():
    # A page where users will be logged out of the system. This method
    #  will return a redirect to the login page.
    #
    #  Required Auth Level: None

    # Authenticate the user against the DB
    userDict = getAuth()

    logging.info("Logout User: {}".format(userDict["ra_id"]))

    # Log out the user
    logout_user()

    # Redirect the client to the login page.
    return redirect(url_for('.login'))


@app.route("/")
def login():
    # A page where users will be logged in to the system. This method
    #  will return a redirect to the Google Login blueprint.
    #
    #  Required Auth Level: None

    logging.info("Redirecting client to Google Login")

    # Redirect the user to the Google Login Blueprint
    return redirect(url_for("google.login"))


@app.route("/home")
@login_required
def index():
    # The landing page for this blueprint that will display the Hall Settings
    #  to the user and provide a way for them to edit said settings.
    #
    #  Required Auth Level: >= RA

    # Authenticate the user against the DB
    userDict = getAuth()

    # Render the appropriate template
    return render_template("index.html", auth_level=userDict["auth_level"],
                           curView=1, opts=ag.baseOpts, hall_name=userDict["hall_name"])


# ------------------------------
# --      Error Handling      --
# ------------------------------

@app.route("/error/<string:msg>")
def err(msg):
    # The error page for errors encountered in the index and login pages.
    #
    #  Required Auth Level: None

    logging.warning("Rendering error page with Message: {}".format(msg))

    # Render the error page with the appropriate message.
    return render_template("error.html", errorMsg=msg)


if __name__ == "__main__":
    # Load the USE_ADHOC value from the environment
    local = bool(os.environ["USE_ADHOC"])

    # If we are running this application on a local machine
    if local:
        # Then run in Debug mode
        app.run(ssl_context="adhoc", debug=True, host='0.0.0.0')

    else:
        # Otherwise run in Production mode
        app.run()
