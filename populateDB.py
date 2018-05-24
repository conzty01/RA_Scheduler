import psycopg2
import calendar
import os

def popResHall(cur):
	for n in ['Brandt','Olson','Larsen']:
		cur.execute("INSERT INTO res_hall (name) VALUES ('{}')".format(n))

def popRAs(cur):
	def popBrandtRA(cur):
		cur.execute("SELECT id FROM res_hall WHERE name = 'Brandt';")
		iD = cur.fetchone()[0]

		for n in ["Abby Korenchan" , "Anna Dewitt", "Claire Lutter", "Derek Barnhouse", "Elizabeth Myra", "Emily DeJong",
				  "Emma Deihl", "Jessica Skjonsby", "Kelvin Li", "Luise Johannes","Lukas Phillips","Mason Montuoro","Sam Storts","Tyler Conzett","Vicky Toriallas"]:
			cur.execute("INSERT INTO ra (first_name, last_name, hall_id, date_started, points) VALUES ('{}','{}',{},NOW(),0)".format(n.split()[0],n.split()[1],iD))

	def popLarsenRA(cur):
		cur.execute("SELECT id FROM res_hall WHERE name = 'Larsen';")
		iD = cur.fetchone()[0]

		for n in ["Jillian Hazlett", "Wylie Cook", "Celia Gould", "Miranda Poncelet", "Gillian Constable" "Ellen Larsen"]:
			cur.execute("INSERT INTO ra (first_name, last_name, hall_id, date_started, points) VALUES ('{}','{}',{},NOW(),0)".format(n.split()[0],n.split()[1],iD))

	def popOlsonRA(cur):
		cur.execute("SELECT id FROM res_hall WHERE name = 'Olson';")
		iD = cur.fetchone()[0]

		for n in ["David Lee", "Maren Phalen", "Hannah O''Polka", "Grace O''Brien", "Mareda Smith", "Katy Roets", "Isaiah Cammon", "Ryan Ehrhardt"]:
			cur.execute("INSERT INTO ra (first_name, last_name, hall_id, date_started, points) VALUES ('{}','{}',{},NOW(),0)".format(n.split()[0],n.split()[1],iD))

	popBrandtRA(cur)
	popLarsenRA(cur)
	popOlsonRA(cur)

def popMonth(cur):
	cur.execute("INSERT INTO month (name, year) VALUES ('January',to_date('2018', 'YYYY'))")
	cur.execute("INSERT INTO month (name, year) VALUES ('February',to_date('2018', 'YYYY'))")
	cur.execute("INSERT INTO month (name, year) VALUES ('March',to_date('2018', 'YYYY'))")

def popDay(cur):
	c = calendar.Calendar()
	for m in [("January",1),("February",2),("March",3)]:
		cur.execute("SELECT id FROM month WHERE name = '{}'".format(m[0]))
		mID = cur.fetchone()[0]

		for d in c.itermonthdays(2018,m[1]):
			if d > 0:
				if len(str(d)) < 2:
					dstr = "0"+str(d)
				else:
					dstr = str(d)
				s = dstr +" "+ m[0][:3] +" "+ "2018"
				cur.execute("INSERT INTO day (month_id, date) VALUES ({},to_date('{}', 'DD Mon YYYY'))".format(mID,s))


def main():
	conn = psycopg2.connect(os.environ["DATABASE_URL"])
	cur = conn.cursor()
	popResHall(cur)
	conn.commit()
	popRAs(cur)
	conn.commit()
	popMonth(cur)
	conn.commit()
	popDay(cur)
	conn.commit()

main()
