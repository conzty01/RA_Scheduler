from logging.config import dictConfig
from psycopg2.extras import Json
import psycopg2
import logging
import os


def migrate(conn):
    cur = conn.cursor()

    # -------------------------------------------------
    # --  Remove unused duties and schedule entries  --
    # -------------------------------------------------

    logging.info("  Checking for unused 'duties' entries")

    # Check to see if there are unused duties
    cur.execute(
        """
        SELECT COUNT(*)
        FROM duties
        WHERE duties.sched_id IN 
        (
            SELECT schedule.id
            FROM schedule
            WHERE schedule.id NOT IN
            (
                -- Get the active schedule record associated with the given Res Hall for each month in the DB
                SELECT DISTINCT ON (schedule.month_id, schedule.hall_id) schedule.id
                FROM schedule
                ORDER BY schedule.month_id, schedule.hall_id, schedule.created DESC, schedule.id DESC
            )
        )
        """
    )

    numDuties = cur.fetchone()[0]

    logging.info("  {} unused 'duties' entries found.".format(numDuties))

    # If there are unused duties entries
    if numDuties > 0:
        # Then delete them
        logging.info("  Deleting unused 'duties' entries.")

        cur.execute(
            """
            DELETE FROM duties
            WHERE duties.id IN
            (
                SELECT COUNT(*)--duties.id
                FROM duties
                WHERE duties.sched_id IN 
                (
                    SELECT schedule.id
                    FROM schedule
                    WHERE schedule.id NOT IN
                    (
                        -- Get the active schedule record associated with the given Res Hall for each month in the DB
                        SELECT DISTINCT ON (schedule.month_id, schedule.hall_id) schedule.id
                        FROM schedule
                        ORDER BY schedule.month_id, schedule.hall_id, schedule.created DESC, schedule.id DESC
                    )
                    --AND schedule.hall_id = 2
                    --ORDER BY month_id, id
                )
            );
            """
        )

    logging.info("  Checking for unused 'schedule' entries")

    # Check to see if there are unused duties
    cur.execute(
        """
        SELECT COUNT(*)
        FROM schedule
        WHERE schedule.id NOT IN
        (
            -- Get the active schedule record associated with the given Res Hall for each month in the DB
            SELECT DISTINCT ON (schedule.month_id, schedule.hall_id) schedule.id
            FROM schedule
            ORDER BY schedule.month_id, schedule.hall_id, schedule.created DESC, schedule.id DESC
        )
        """
    )

    numScheds = cur.fetchone()[0]

    logging.info("  {} unused 'schedule' entries found.".format(numScheds))

    # If there are unused schedule entries
    if numScheds > 0:
        # Then delete them
        logging.info("  Deleting unused 'schedule' entries.")

        cur.execute(
            """
            DELETE FROM schedule
            WHERE schedule.id IN 
            (
                SELECT schedule.id
                FROM schedule
                WHERE schedule.id NOT IN
                (
                    -- Get the active schedule record associated with the given Res Hall for each month in the DB
                    SELECT DISTINCT ON (schedule.month_id, schedule.hall_id) schedule.id
                    FROM schedule
                    ORDER BY schedule.month_id, schedule.hall_id, schedule.created DESC, schedule.id DESC
                )
                ORDER BY month_id, id
            );
            """
        )


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
