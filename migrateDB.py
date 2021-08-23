from logging.config import dictConfig
from psycopg2.extras import Json
import psycopg2
import logging
import os


def migrate(conn):
    cur = conn.cursor()

    # --------------------------------------------
    # --  Add enabled column to res_hall table  --
    # --------------------------------------------

    # Check to see if the column already exists
    cur.execute(
        """SELECT EXISTS (
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='res_hall' 
            AND column_name='enabled');"""
    )

    # If the column does not already exist...
    if not cur.fetchone()[0]:
        logging.info("  Adding 'enabled' column to res_hall table")

        # Create the column in the res_hall.
        cur.execute("""
            ALTER TABLE res_hall
            ADD COLUMN enabled BOOLEAN
            ;""")

        # Set a default value for the enabled column
        cur.execute("UPDATE res_hall SET enabled = TRUE;")

        # Set the enabled column to not allow Null values
        cur.execute("ALTER TABLE res_hall ALTER COLUMN enabled SET NOT NULL;")

        # Set the enabled column to have a default value
        cur.execute("ALTER TABLE res_hall ALTER COLUMN enabled SET DEFAULT FALSE;")

        logging.info("  Finished adding 'enabled' column to res_hall table")


if __name__ == "__main__":

    conn = psycopg2.connect(os.environ["DATABASE_URL"])

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
            'level': os.environ["LOG_LEVEL"],
            'handlers': ['wsgi']
        }
    })

    logging.info("Beginning Migration")
    migrate(conn)

    logging.info("Committing Changes")
    conn.commit()
    logging.info("  Finished Committing Changes")

    logging.info("Finished Migration")
