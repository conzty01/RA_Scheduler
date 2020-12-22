import psycopg2
import os

# Set up baseOpts to be sent to each HTML template
baseOpts = {
    "HOST_URL": os.environ["HOST_URL"]
}

# Establish DB connection
conn = psycopg2.connect(os.environ["DATABASE_URL"])

# Set up various global variables
UPLOAD_FOLDER = "./static"
ALLOWED_EXTENSIONS = {'txt', 'csv'}
