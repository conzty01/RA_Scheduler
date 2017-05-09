import psycopg2

def createHallDB(conn):
	conn.execute("DROP TABLE IF EXISTS lc_res_hall CASCADE;")
	conn.execute("""
		CREATE TABLE lc_res_hall(
			id	serial,
			name	varchar(50),
			calendar_id	int,

		PRIMARY KEY (id)
		);""")

def createConflictDB(conn):
	conn.execute("DROP TABLE IF EXISTS lc_conflict CASCADE;")
	conn.execute("""
		CREATE TABLE lc_conflict(
			ra_id	int,
			date	date,

			PRIMARY KEY (ra_id, date),
			FOREIGN KEY (ra_id) REFERENCES lc_resident_assistant(id)
		);""")

def createRaDB(conn):
	conn.execute("DROP TABLE IF EXISTS lc_resident_assistant CASCADE;")
	conn.execute("""
		CREATE TABLE lc_resident_assistant(
			id	serial,
			first_name	varchar(20),
			last_name	varchar(50),
			hall_id		int,

			PRIMARY KEY (id),
			FOREIGN KEY (hall_id) REFERENCES lc_res_hall(id)
		);""")

def createScheduleDB(conn):
	conn.execute("DROP TABLE IF EXISTS lc_schedule CASCADE;")

	exStr = ""

	for num in range(1,32):
		exStr += "ra_id_day_{}  int[],\n".format(num)

	conn.execute("""
		CREATE TABLE lc_schedule(
			id	serial,
			hall_id	int,
			month	date,
			{}
			
			PRIMARY KEY (id),
			FOREIGN KEY (hall_id) REFERENCES lc_res_hall(id)
			
		);""".format(exStr))
		
	
def main():
	conn = psycopg2.connect(dbname="conzty01", user="conzty01")
	createHallDB(conn.cursor())
	createRaDB(conn.cursor())
	createConflictDB(conn.cursor())
	createScheduleDB(conn.cursor())

	conn.commit()
main()
