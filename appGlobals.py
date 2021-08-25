import psycopg2
import os

# Set up baseOpts to be sent to each HTML template
baseOpts = {
    "HOST_URL": os.getenv("HOST_URL", "https://localhost:5000")
}

# Establish DB connection
conn = psycopg2.connect(os.getenv("DATABASE_URL", "postgres:///ra_sched"))

# Set up various global variables
UPLOAD_FOLDER = "./static"
ALLOWED_EXTENSIONS = {'txt', 'csv'}

