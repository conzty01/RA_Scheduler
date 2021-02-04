from logging.config import dictConfig
from psycopg2.extras import Json
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

    # ---------------------
    # --  hall_settings  --
    # ---------------------

    # Check to see if the hall_settings table exists
    cur.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'hall_settings');")

    exists = cur.fetchone()

    logging.info("  'hall_settings' Table Exists: {}".format(exists))

    if not exists[0]:
        # If the table does not exist, create the table

        logging.info("  Creating 'hall_settings' Table.")

        defaultJSON = {
            "reg_duty_num_assigned": 1,     # Number of RAs to be assigned on regular duty days.
            "multi_duty_num_assigned": 2,   # Number of RAs to be assigned on multi-duty days.
            "brk_duty_num_assigned": 1,     # Number of RAs to be assigned on break duty days.
            "reg_duty_pts": 1,              # Number of points to be awarded for regular duties.
            "multi_duty_pts": 2,            # Number of points to be awarded for multi-day duties.
            "brk_duty_pts": 3,              # Number of points to be awarded for break duties.
            "multi_duty_days": [4, 5]       # Days of the week which are considered multi-duty days.
                                            #    Mon, Tues, Wed, Thurs, Fri, Sat, Sun
                                            #     0    1     2     3     4    5    6
        }

        # Create the hall_settings table
        cur.execute("""
        CREATE TABLE hall_settings(
            id				        serial UNIQUE,
            res_hall_id		        int NOT NULL,
            
            year_start_mon          int     NOT NULL DEFAULT 8 CHECK (year_start_mon >= 1 AND 
                                                                       year_start_mon <= 12),
            year_end_mon            int     NOT NULL DEFAULT 7 CHECK (year_end_mon >= 1 AND 
                                                                       year_end_mon <= 12),
            duty_config             json    NOT NULL DEFAULT %s::JSON,
            auto_adj_excl_ra_pts    boolean NOT NULL DEFAULT false,
            flag_multi_duty         boolean NOT NULL DEFAULT false,
            duty_flag_label         VARCHAR(20) NOT NULL DEFAULT 'Secondary Personnel',
            
            PRIMARY KEY (res_hall_id),
            FOREIGN KEY (res_hall_id) REFERENCES res_hall(id)
        );""", (Json(defaultJSON),))


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
