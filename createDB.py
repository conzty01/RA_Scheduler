import psycopg2
import os

def createHallDB(conn):
	conn.execute("DROP TABLE IF EXISTS res_hall CASCADE;")
	conn.execute("""
		CREATE TABLE res_hall(
			id				serial UNIQUE,
			name			varchar(50),
			calendar_id		text,

		PRIMARY KEY (name)
		);""")

def createScheduleDB(conn):
	conn.execute("DROP TABLE IF EXISTS schedule CASCADE;")
	conn.execute("""
		CREATE TABLE schedule(
			id				serial UNIQUE,
			hall_id			int,
			month_id		int,
			created			date,

		PRIMARY KEY (id),
		FOREIGN KEY (hall_id) REFERENCES res_hall(id),
		FOREIGN KEY (month_id) REFERENCES month(id)
		);""")

def createRaDB(conn):
	conn.execute("DROP TABLE IF EXISTS ra CASCADE;")
	conn.execute("""
		CREATE TABLE ra(
			id				serial UNIQUE,
			first_name		varchar(20),
			last_name		varchar(50),
			hall_id			int,
			date_started	date,
			points			int,
			color			varchar(7),
			email			varchar(256),
			auth_level		int DEFAULT 1,

			PRIMARY KEY (id, hall_id),
			FOREIGN KEY (hall_id) REFERENCES res_hall(id)
		);""")

def createConflictDB(conn):
	conn.execute("DROP TABLE IF EXISTS conflicts CASCADE;")
	conn.execute("""
		CREATE TABLE conflicts(
			id		serial UNIQUE,
			ra_id	int,
			day_id	int,

			PRIMARY KEY (ra_id, day_id),
			FOREIGN KEY (ra_id) REFERENCES ra(id),
			FOREIGN KEY (day_id) REFERENCES day(id)
		);""")

def createDutyDB(conn):
	conn.execute("DROP TABLE IF EXISTS duties CASCADE;")

	conn.execute("""
		CREATE TABLE duties(
			id			serial UNIQUE,
			hall_id		int,
			ra_id		int,
			day_id		int,
			sched_id	int,
			point_val	int,

			PRIMARY KEY (id),
			FOREIGN KEY (hall_id) REFERENCES res_hall(id),
			FOREIGN KEY (day_id) REFERENCES day(id),
			FOREIGN KEY (ra_id) REFERENCES ra(id),
			FOREIGN KEY (sched_id) REFERENCES schedule(id)
		);""")

def createDayDB(conn):
	conn.execute("DROP TABLE IF EXISTS day CASCADE;")

	conn.execute("""
		CREATE TABLE day(
			id			serial UNIQUE,
			month_id	int,
			date		date,

			PRIMARY KEY (month_id,date),
			FOREIGN KEY (month_id) REFERENCES month(id)
		);""")

def createMonthDB(conn):
	conn.execute("DROP TABLE IF EXISTS month CASCADE;")

	conn.execute("""
		CREATE TABLE month(
			id			serial UNIQUE,
			num			int,
			name		varchar(10),
			year		date,

			PRIMARY KEY (name,year)
		);""")

def createUserDB(conn):
	conn.execute('DROP TABLE IF EXISTS "user" CASCADE;')

	conn.execute("""
		CREATE TABLE "user"(
			id			serial UNIQUE,
			ra_id		int UNIQUE,
			username	varchar(20) UNIQUE,

			PRIMARY KEY (id),
			FOREIGN KEY (ra_id) REFERENCES ra(id)
		);""")

def createOAuthDB(conn):
	conn.execute('DROP TABLE IF EXISTS flask_dance_oauth CASCADE;')

	conn.execute("""
		CREATE TABLE flask_dance_oauth(
			id					serial UNIQUE,
			provider			varchar(50),
			created_at			timestamp without time zone,
			token				json,
			provider_user_id	varchar(256),
			user_id				int,

			PRIMARY KEY (id)
		);""")

def main():
	conn = psycopg2.connect(os.environ["DATABASE_URL"])
	createHallDB(conn.cursor())
	createRaDB(conn.cursor())
	createMonthDB(conn.cursor())
	createDayDB(conn.cursor())
	createConflictDB(conn.cursor())
	createScheduleDB(conn.cursor())
	createDutyDB(conn.cursor())
	createUserDB(conn.cursor())
	createOAuthDB(conn.cursor())

	conn.commit()

if __name__ == "__main__":
	main()
