import psycopg2

def popResHall(cur):
	for n in ['Brandt','Olson','Miller','Dieseth','PFABS','Ylvisaker']:
		cur.execute("INSERT INTO lc_res_hall (name) VALUES ('{}')".format(n))

def main():
	conn = psycopg2.connect(dbname="conzty01",user="conzty01")
	cur = conn.cursor()
	popResHall(cur)
	
	conn.commit()

main()
