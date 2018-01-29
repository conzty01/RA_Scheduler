import psycopg2
import os

def createHallDB(conn):
	conn.execute("DROP TABLE IF EXISTS res_hall CASCADE;")
	conn.execute("""
		CREATE TABLE res_hall(
			id	serial,
			name	varchar(50),
			calendar_id	int,

		PRIMARY KEY (id)
		);""")

def createConflictDB(conn):
	conn.execute("DROP TABLE IF EXISTS conflict CASCADE;")
	conn.execute("""
		CREATE TABLE conflict(
			ra_id	int,
			date	date,

			PRIMARY KEY (ra_id, date),
			FOREIGN KEY (ra_id) REFERENCES ra(id)
		);""")

def createRaDB(conn):
	conn.execute("DROP TABLE IF EXISTS ra CASCADE;")
	conn.execute("""
		CREATE TABLE ra(
			id	serial,
			first_name	varchar(20),
			last_name	varchar(50),
			hall_id		int,

			PRIMARY KEY (id),
			FOREIGN KEY (hall_id) REFERENCES res_hall(id)
		);""")

def createScheduleDB(conn):
	conn.execute("DROP TABLE IF EXISTS schedule CASCADE;")

	exStr = ""

	for num in range(1,32):
		exStr += "day_{}  int[],\n".format(num)

	conn.execute("""
		CREATE TABLE schedule(
			id	serial,
			hall_id	int,
			month	date,
			{}

			PRIMARY KEY (id),
			FOREIGN KEY (hall_id) REFERENCES res_hall(id)

		);""".format(exStr))


def main():
	#conn = psycopg2.connect(os.environ["DATABASE_URL"])
	conn = psycopg2.connect(dbname="ra_sched", user="conzty01")
	createHallDB(conn.cursor())
	createRaDB(conn.cursor())
	createConflictDB(conn.cursor())
	createScheduleDB(conn.cursor())

	conn.commit()
main()
