from logging.config import dictConfig
from psycopg2.extras import Json
import psycopg2
import logging
import os


def migrate(conn):
    cur = conn.cursor()

    # -----------------------------------
    # --  Create scheduer_queue table  --
    # -----------------------------------

    # Check to see if the table already exists
    cur.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'scheduler_queue' AND schemaname = 'public');"
    )

    # If the table does not already exist...
    if not cur.fetchone()[0]:

        logging.info("  Creating scheduler_queue table")

        # Create the scheduler_queue table
        cur.execute("""
            CREATE TABLE scheduler_queue(
                id              serial UNIQUE,
                status          int NOT NULL DEFAULT 0,
                reason          varchar(255) NOT NULL DEFAULT '',
                res_hall_id     int NOT NULL,
                created_ra_id   int NOT NULL,
                created_date    timestamp WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                PRIMARY KEY (id),
                FOREIGN KEY (res_hall_id) REFERENCES res_hall(id),
                FOREIGN KEY (created_ra_id) REFERENCES ra(id)
            );""")

        logging.info("  Finished creating scheduler_queue table")


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
