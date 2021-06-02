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

    # ---------------------------
    # --  Create school table  --
    # ---------------------------

    # Check to see if the table already exists
    cur.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'school' AND schemaname = 'public');"
    )

    # If the table does not already exist...
    if not cur.fetchone()[0]:
        logging.info("  Creating school table")

        # Create the scheduler_queue table
        cur.execute("""
            CREATE TABLE school(
                id              serial UNIQUE,
                name            varchar(255) NOT NULL,
                city            varchar(255) NOT NULL,
                state           varchar(2) NOT NULL,
                
                PRIMARY KEY (name, city, state)
        );""")

        logging.info("  Finished creating school table")

        logging.info("  Adding RADSA Support info into school table")

        # Add a record for RADSA support into the school table for
        cur.execute("INSERT INTO school (name, city, state) VALUES ('ConzTech', 'Deco', 'IA');")

        logging.info("  Finished adding RADSA Support info into school table")

    # ----------------------------------------------
    # --  Add school_id column to res_hall table  --
    # ----------------------------------------------

    # Check to see if the column already exists
    cur.execute(
        """SELECT EXISTS (
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='res_hall' 
            AND column_name='school_id');"""
    )

    # If the column does not already exist...
    if not cur.fetchone()[0]:
        logging.info("  Adding school_id column to res_hall table")

        # Create the column in the res_hall.
        cur.execute("""
            ALTER TABLE res_hall
            ADD COLUMN school_id int
            ;""")

        # Set a default value for the school_id column so that we can set it as a foreign key
        cur.execute("UPDATE res_hall SET school_id = (SELECT id FROM school LIMIT(1));")

        # Set the school_id column as a foreign key to the school table
        cur.execute("ALTER TABLE res_hall ADD FOREIGN KEY (school_id) REFERENCES school(id);")

        # Set the school_id column to not allow Null values
        cur.execute("ALTER TABLE res_hall ALTER COLUMN school_id SET NOT NULL;")

        logging.info("  Finished adding school_id column to res_hall table")


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
