from logging.config import dictConfig
import psycopg2
import logging
import os

def migrate(conn):
    cur = conn.cursor()

    # Check to see if the google_calendar_info table exists
    cur.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'google_calendar_info');")

    exists = cur.fetchone()

    if not exists:
        # If the table does not exist, create the table

        # Create the google_calendar_info table
        cur.execute("""
            CREATE TABLE google_calendar_info(
                id				serial UNIQUE.
                res_hall_id		int,
                auth_state		varchar(30),
                token 			bytea,
                calendar_id		varchar(60),
    
                PRIMARY KEY (res_hall_id),
                FOREIGN KEY (res_hall_id) REFERENCES res_hall(id));
            );""")

    # Drop all Google related columns in the res_hall table
    cur.execute("""
        ALTER TABLE res_hall
        DROP COLUMN IF EXISTS calendar_id,
        DROP COLUMN IF EXISTS g_cal_token,
        DROP COLUMN IF EXISTS g_cal_auth_state
    """)




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
