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
            WHERE table_name='duties' AND column_name='flagged'
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

    # ------------------------
    # --  staff_membership  --
    # ------------------------

    # Check to see if the staff_membership table exists
    cur.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'staff_membership');")

    exists = cur.fetchone()

    logging.info("  'staff_membership' Table Exists: {}".format(exists))

    if not exists[0]:
        # If the table does not exist, create the table

        logging.info("  Creating 'staff_membership' Table.")

        # Create the staff_membership table
        cur.execute("""
        CREATE TABLE staff_membership(
            id              serial UNIQUE,
            ra_id           int NOT NULL,
            res_hall_id     int NOT NULL,
            start_date      date NOT NULL DEFAULT NOW(),
            auth_level      int NOT NULL DEFAULT 1,
            selected        boolean NOT NULL DEFAULT false,

            PRIMARY KEY (ra_id, res_hall_id),
            FOREIGN KEY (ra_id) REFERENCES ra(id),
            FOREIGN KEY (res_hall_id) REFERENCES res_hall(id)
        );""")

    # Check to see if the hall_id and date_started columns exist in the ra table.
    cur.execute("""
        SELECT COUNT(*) != 3
        FROM (
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='ra' AND (column_name='hall_id' OR column_name='date_started' OR column_name='auth_level')
        ) AS subquery;""")

    alreadyFullyMigrated = cur.fetchone()

    logging.info("  Previously migrated data from <ra> table to <staff_membership> table: {}"
                 .format(alreadyFullyMigrated[0]))

    # Check to see what state we are in
    if not alreadyFullyMigrated[0]:
        # If we have not already fully migrated (meaning the hall_id and date_started columns of
        #  the <ra> table have not been dropped), then we need to move this data from the <ra>
        #  table to the staff_membership table.

        logging.info("  Migrating data from <ra> table to <staff_membership> table")

        # Query the DB for all of the records in the <ra> table
        cur.execute("SELECT id, hall_id, date_started, auth_level FROM ra;")

        # Iterate over our results
        rows = cur.fetchall()
        for row in rows:
            # Attempt to insert a record into the <staff_membership> table
            try:

                # Insert a record into the staff_membership table
                cur.execute("""
                    INSERT INTO staff_membership (ra_id, res_hall_id, start_date, auth_level, selected)
                    VALUES (%s, %s, %s, %s, true);
                    """, (row[0], row[1], row[2], row[3]))

                # Commit the change to the DB
                conn.commit()

            except psycopg2.IntegrityError:
                # If we encounter an IntegrityError, then that means we have already
                #  created a record in the <staff_membership> table for this RA.

                logging.info("    Record already exists: {}, {}".format(row[0], row[1]))

                # Rollback the change
                conn.rollback()

        logging.info("    Migration Complete")

        # Once we have gotten out of the for loop, we will have moved all of the data from the
        #  <ra> table to the <staff_membership> table.

        logging.info("  Dropping ra.hall_id, ra.date_started and ra.auth_level columns")

        # Delete the hall_id and date_started columns from the <ra> table
        cur.execute("""
            ALTER TABLE ra
            DROP COLUMN hall_id,
            DROP COLUMN date_started,
            DROP COLUMN auth_level;
        """)

        # Commit the change to the DB
        conn.commit()

        logging.info("    <ra> Table Alteration Complete")


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
