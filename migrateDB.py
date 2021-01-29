from logging.config import dictConfig
import psycopg2
import logging
import os


def migrate(conn):
    cur = conn.cursor()

    # ----------------------
    # --  duties.flagged  --
    # ----------------------

    # Check to see if the duties.flagged column exists
    cur.execute(
        """SELECT EXISTS 
        (
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='duties' and column_name='flagged'
        );"""
    )

    exists = cur.fetchone()

    logging.info("  'duties.flagged' Column Exists: {}".format(exists))

    if not exists[0]:
        # If the table does not exist, create the column

        logging.info("  Creating 'duties.flagged' Column.")

        # Create the flagged column
        cur.execute("""ALTER TABLE duties ADD COLUMN "flagged" BOOLEAN NOT NULL DEFAULT FALSE;""")


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
