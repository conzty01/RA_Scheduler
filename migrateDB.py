from logging.config import dictConfig
import psycopg2
import logging
import os


def migrate(conn):
    cur = conn.cursor()

    # Check to see if the google_calendar_info table exists
    cur.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'point_modifier');")

    exists = cur.fetchone()

    logging.info("  'point_modifier' Table Exists: {}".format(exists))

    if not exists[0]:
        # If the table does not exist, create the table

        logging.info("  Creating 'point_modifier' Table.")

        # Create the point_modifier table
        conn.execute("""
        CREATE TABLE point_modifier(
            id				serial UNIQUE,
            ra_id			int,
            res_hall_id		int,
            month_id		int,
            modifier		int,

            PRIMARY KEY (ra_id, res_hall_id),
            FOREIGN KEY (ra_id) REFERENCES ra(id),
            FOREIGN KEY (res_hall_id) REFERENCES res_hall(id),
            FOREIGN KEY (month_id) REFERENCES month(id)
        );""")


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
