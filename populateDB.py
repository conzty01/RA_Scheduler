from scheduler import scheduling
from ra_sched import RA, Day, Schedule
from datetime import date
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
	cur.execute("INSERT INTO month (name, year) VALUES ('January',to_date('January 2018', 'Month YYYY'))")
	cur.execute("INSERT INTO month (name, year) VALUES ('February',to_date('February 2018', 'Month YYYY'))")
	cur.execute("INSERT INTO month (name, year) VALUES ('March',to_date('March 2018', 'Month YYYY'))")

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

def popSchedule(cur):
	cur.execute("SELECT name, year FROM month ORDER BY year ASC;")
	d = cur.fetchone()[-1]
	year = d.year
	month = d.month

	cur.execute("""SELECT first_name,last_name,id,hall_id,date_started,points,cons.array_agg
				   FROM ra JOIN (SELECT ra_id, ARRAY_AGG(days.date)
								 FROM conflicts JOIN (SELECT id, date
													  FROM day
													  WHERE month_id = 1) AS days
				   				 ON (conflicts.day_id = days.id)
								 WHERE ra_id = 1
				  			     GROUP BY ra_id) AS cons
						   ON (ra.id = cons.ra_id)
				   WHERE ra.hall_id = 1;""")
	
	for res in cur.fetchall():
		print(res)

    # times = 1
    # for t in range(times):
    #     ra_list
	#
    #     s2 = scheduling(ra_list,year,month,[date(year,month,14),date(year,month,15),date(year,month,16),date(year,month,17)])


def main():
	conn = psycopg2.connect(os.environ["DATABASE_URL"])
	cur = conn.cursor()
	# popResHall(cur)
	# conn.commit()
	# popRAs(cur)
	# conn.commit()
	# popMonth(cur)
	# conn.commit()
	# popDay(cur)
	# conn.commit()
	popSchedule(cur)

main()
