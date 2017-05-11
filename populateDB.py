import psycopg2

def popResHall(cur):
	for n in ['Brandt','Olson','Miller','Dieseth','PFABS','Ylvisaker','Larsen']:
		cur.execute("INSERT INTO lc_res_hall (name) VALUES ('{}')".format(n))

def popBrandtRA(cur):
	for n in ["Abby Korenchan" , "Anna Dewitt", "Claire Lutter", "Derek Barnhouse", "Elizabeth Myra", "Emily DeJong",
			  "Emma Deihl", "Jessica Skjonsby", "Kelvin Li", "Luise Johannes","Lukas Phillips","Mason Montuoro","Sam Storts","Tyler Conzett","Vicky Toriallas"]:
		cur.execute("INSERT INTO lc_resident_assistant (first_name, last_name, hall_id) VALUES ('{}','{}',1)".format(n.split()[0],n.split()[1]))
def popLarsenRA(cur):
	for n in ["Jillian Hazlett", "Wylie Cook", "Celia Gould", "Miranda Poncelet", "Gillian Constable" "Ellen Larsen"]:
		cur.execute("INSERT INTO lc_resident_assistant (first_name, last_name, hall_id) VALUES ('{}','{}',7)".format(n.split()[0],n.split()[1]))
def popOlsonRA(cur):
	for n in ["David Lee", "Maren Phalen", "Hannah O''Polka", "Grace O''Brien", "Mareda Smith", "Katy Roets", "Isaiah Cammon", "Ryan Ehrhardt"]:
		cur.execute("INSERT INTO lc_resident_assistant (first_name, last_name, hall_id) VALUES ('{}','{}',2)".format(n.split()[0],n.split()[1]))

def main():
	conn = psycopg2.connect(os.environ["DATABASE_URL"])
	cur = conn.cursor()
	popResHall(cur)
	popBrandtRA(cur)
	popLarsenRA(cur)
	popOlsonRA(cur)
	conn.commit()

main()
