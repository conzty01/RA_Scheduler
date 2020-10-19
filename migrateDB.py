import psycopg2
import logging
import os

def migrate(conn):
    cur = conn.cursor()

    logging.info("Creating Table: break_duties")
    con.execute("""
		CREATE TABLE break_duties(
			id			serial UNIQUE,
			ra_id		int,
			hall_id		int,
			day_id		int,
			month_id	int,
			point_val	int DEFAULT 0 CONSTRAINT pos_break_duty_point_value CHECK (point_val >= 0),

			PRIMARY KEY (hall_id, month_id, day_id, ra_id),
			FOREIGN KEY (ra_id) 	REFERENCES ra(id),
			FOREIGN KEY (hall_id) 	REFERENCES res_hall(id),
			FOREIGN KEY (month_id) 	REFERENCES month(id),
			FOREIGN KEY (day_id) 	REFERENCES day(id),
		);""")
    logging.info("  Finished Creating Table: break_duties")


if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s.%(msecs)d %(levelname)s: %(message)s', \
                        datefmt='%H:%M:%S', \
                        level=logging.INFO, \
                        #filename="migrateDB.log", \
                        #filemode="w"
                        )

    conn = psycopg2.connect(os.environ["DATABASE_URL"])

    logging.info("Beginning Migration")
    migrate(conn)

    logging.info("Committing Changes")
    conn.commit()
    loging.info("  Finished Committing Changes")

    logging.info("Finished Migration")
