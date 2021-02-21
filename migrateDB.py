from logging.config import dictConfig
from psycopg2.extras import Json
import psycopg2
import logging
import os


def migrate(conn):
    cur = conn.cursor()

    # ------------------------------------
    # --  Remove staff_membership rows  --
    # ------------------------------------

    logging.info("  Deleting staff_membership records")

    # Remove all entries from the staff_membership table
    #  where the res_hall_id = 0
    cur.execute("DELETE FROM staff_membership WHERE res_hall_id = 0")

    # --------------------------------------------
    # --  Remove "NOT ASSIGNED" res_hall Entry  --
    # --------------------------------------------

    logging.info("  Deleting res_hall record")

    # Remove the "NOT ASSIGNED" Res Hall Entry from
    #  the res_hall table.
    cur.execute("DELETE FROM res_hall WHERE id = 0 AND name = 'NOT ASSIGNED';")


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
