import psycopg2

def popResHall(cur):
	for n in ['Brandt','Olson','Miller','Dieseth','PFABS','Ylvisaker']:
		cur.execute("INSERT INTO lc_res_hall (name) VALUES ('{}')".format(n))

def popBrandtRA(cur):
	for n in ["Abby Korenchan", "Anna Dewitt", "Claire Lutter", "Derek Barnhouse", "Elizabeth Myra", "Emily DeJong",
			  "Emma Deihl", "Jessica Skjonsby", "Kelvin Li", "Luise Johannes","Lukas Phillips","Mason Montuoro","Sam Storts","Tyler Conzett","Vicky Toriallas"]:
		cur.execute("INSERT INTO lc_resident_assistant (first_name, last_name, hall_id) VALUES ('{}','{}',1)".format(n.split()[0],n.split()[1]))

def main():
	conn = psycopg2.connect(dbname="conzty01",user="conzty01")
	cur = conn.cursor()
	popResHall(cur)

	conn.commit()

main()
