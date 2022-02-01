from psycopg2.extensions import cursor
from psycopg2 import connect
import logging
import os


class RADSADatabaseCursor(cursor):
    """ Object for wrapping the psycopg2 cursor class for RADSA. """

    def execute(self, sql, args=None):

        try:
            # Execute the provided SQL
            cursor.execute(self, sql, args)

        except Exception as e:
            # Log the occurrence
            logging.exception("Error encountered querying database - {}:{}".format(e.__class__.__name__, e))

            # Rollback the transaction
            self.connection.rollback()


# Set up baseOpts to be sent to each HTML template
baseOpts = {
    "HOST_URL": os.getenv("HOST_URL", "https://localhost:5000")
}

# Establish DB connection
conn = connect(
    os.getenv("DATABASE_URL", "postgres:///ra_sched"),
    cursor_factory=RADSADatabaseCursor
)

# Set up various global variables
UPLOAD_FOLDER = "./static"
ALLOWED_EXTENSIONS = {'txt', 'csv'}

