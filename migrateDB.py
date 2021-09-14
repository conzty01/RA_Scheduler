from logging.config import dictConfig
from psycopg2.extras import Json
import psycopg2
import logging
import os


def migrate(conn):
    cur = conn.cursor()

    # ----------------------------------------
    # --  Create duty_trade_requests table  --
    # ----------------------------------------

    # Check to see if the table already exists
    cur.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'duty_trade_requests' AND schemaname = 'public');"
    )

    # If the table does not already exist...
    if not cur.fetchone()[0]:
        logging.info("  Creating 'duty_trade_requests' table")

        cur.execute("""
        CREATE TABLE duty_trade_requests(
            id                      serial UNIQUE,
            trader_ra_id            int NOT NULL,
            trade_with_ra_id        int,
            trade_duty_id           int NOT NULL,
            exchange_with_duty_id   int,
            res_hall_id             int NOT NULL,
            status                  int NOT NULL DEFAULT 0,
            trade_reason            varchar(255) NOT NULL DEFAULT '',
            reject_reason           varchar(255) NOT NULL DEFAULT '',
            
            PRIMARY KEY (id),
            FOREIGN KEY (res_hall_id) REFERENCES res_hall(id),
            FOREIGN KEY (trader_ra_id) REFERENCES ra(id),
            FOREIGN KEY (trade_with_ra_id) REFERENCES ra(id),
            FOREIGN KEY (trade_duty_id) REFERENCES duties(id),
            FOREIGN KEY (exchange_with_duty_id) REFERENCES duties(id)
        );""")

        logging.info("  Finished creating 'duty_trade_requests' table")

    # ---------------------------------------------------------
    # --  Add 'created' column to duty_trade_requests table  --
    # ---------------------------------------------------------

    # Check to see if the column already exists
    cur.execute(
        """SELECT EXISTS (
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='duty_trade_requests' 
            AND column_name='created');"""
    )

    # If the column does not already exist...
    if not cur.fetchone()[0]:
        logging.info("  Adding 'created' column to duty_trade_requests table")

        # Create the column in the duty_trade_requests.
        cur.execute("""
            ALTER TABLE duty_trade_requests
            ADD COLUMN created timestamp DEFAULT CURRENT_TIMESTAMP
            ;""")

        logging.info("  Finished adding 'created' column to duty_trade_requests table")

    # ----------------------------------------------------------
    # --  Add UNIQUE constraint to duty_trade_requests table  --
    # ----------------------------------------------------------

    # Check to see if the constraint already exists
    cur.execute(
        """SELECT EXISTS (
            SELECT constraint_name 
            FROM information_schema.constraint_column_usage 
            WHERE table_name='duty_trade_requests' 
            AND constraint_name='trader_id_duty_id');"""
    )

    # If the constraint does not already exist...
    if not cur.fetchone()[0]:
        logging.info("  Adding unique constraint to duty_trade_requests table")

        # Create the constraint in the res_hall.
        cur.execute("""
            ALTER TABLE duty_trade_requests
            ADD CONSTRAINT trader_id_duty_id UNIQUE (trader_ra_id, trade_duty_id)
            ;""")

        logging.info("  Finished adding unique constraint to duty_trade_requests table")


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
