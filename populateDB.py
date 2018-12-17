from ra_sched import RA, Day, Schedule
from scheduler import scheduling
from datetime import date
import psycopg2
import calendar
import random
import os

def popResHall(cur):
	for n in ['Brandt','Olson','Larsen']:
		cur.execute("INSERT INTO res_hall (name) VALUES ('{}')".format(n))

def popRAs(cur):
	def randomColor():
		colors = ['#DEB887','#5F9EA0','#7FFF00','#D2691E','#FF7F50','#6495ED','#DC143C',
		'#00FFFF','#A9A9A9','#BDB76B','#FF8C00','#E9967A','#8FBC8F','#00CED1','#FF1493',
		'#00BFFF','#1E90FF','#228B22','#FF00FF','#FFD700','#DAA520','#808080','#008000',
		'#FF69B4','#CD5C5C','#ADD8E6','#F08080','#90EE90','#FFB6C1','#FFA07A','#20B2AA',
		'#87CEFA','#B0C4DE','#00FF00','#32CD32','#FF00FF','#66CDAA','#BA55D3','#9370DB',
		'#3CB371','#7B68EE','#00FA9A','#48D1CC','#C71585','#FFA500','#FF4500','#DA70D6',
		'#DB7093','#CD853F','#FFC0CB','#DDA0DD','#B0E0E6','#FF0000','#BC8F8F','#4169E1',
		'#FA8072','#F4A460','#2E8B57','#A0522D','#C0C0C0','#87CEEB','#6A5ACD','#708090',
		'#00FF7F','#4682B4','#D2B48C','#D8BFD8','#FF6347','#40E0D0','#EE82EE','#F5DEB3']
		return colors[random.randint(0,len(colors)-1)]

	def popBrandtRA(cur):
		cur.execute("SELECT id FROM res_hall WHERE name = 'Brandt';")
		iD = cur.fetchone()[0]

		for n in ["Alfonzo Doerr" , "Lahoma Berns", "Lue Girardin", "Donald Demartini", "Aubrey Mandell", "Stormy Dunigan","Arron Kernan",
				  "Betty Chmiel", "Gerardo Spells", "Epifania Soucy", "Tristan Hedgepeth","Neil Frix","Marvin Cheatam","Carmen Broadnax","Milford Schroyer"]:
			c = randomColor()
			cur.execute("INSERT INTO ra (first_name, last_name, hall_id, date_started, points, color) VALUES ('{}','{}',{},NOW(),0,'{}')".format(n.split()[0],n.split()[1],iD,c))

	def popLarsenRA(cur):
		cur.execute("SELECT id FROM res_hall WHERE name = 'Larsen';")
		iD = cur.fetchone()[0]

		for n in ["Contessa Clardy", "Lolita Marcelino", "Wan Waddington", "Venus Maus", "Rosamond Chesson" "Mitzie Sickels"]:
			c = randomColor()
			cur.execute("INSERT INTO ra (first_name, last_name, hall_id, date_started, points, color) VALUES ('{}','{}',{},NOW(),0,'{}')".format(n.split()[0],n.split()[1],iD,c))

	def popOlsonRA(cur):
		cur.execute("SELECT id FROM res_hall WHERE name = 'Olson';")
		iD = cur.fetchone()[0]

		for n in ["Nick Vankirk", "Eldon Sweetman", "Zita Gans", "Claudia Hole", "Dane Agarwal", "Verna Korb", "Ray Housman", "Zulema Robitaille"]:
			c = randomColor()
			cur.execute("INSERT INTO ra (first_name, last_name, hall_id, date_started, points, color) VALUES ('{}','{}',{},NOW(),0,'{}')".format(n.split()[0],n.split()[1],iD,c))

	popBrandtRA(cur)
	popLarsenRA(cur)
	popOlsonRA(cur)

def popMonth(cur):
	cur.execute("INSERT INTO month (num, name, year) VALUES (8,'August',to_date('2018', 'YYYY'))")
	cur.execute("INSERT INTO month (num, name, year) VALUES (9,'September',to_date('2018', 'YYYY'))")
	cur.execute("INSERT INTO month (num, name, year) VALUES (10,'October',to_date('2018', 'YYYY'))")
	cur.execute("INSERT INTO month (num, name, year) VALUES (11,'November',to_date('2018', 'YYYY'))")
	cur.execute("INSERT INTO month (num, name, year) VALUES (12,'December',to_date('2018', 'YYYY'))")
	cur.execute("INSERT INTO month (num, name, year) VALUES (1,'January',to_date('2019', 'YYYY'))")
	cur.execute("INSERT INTO month (num, name, year) VALUES (2,'February',to_date('2019', 'YYYY'))")
	cur.execute("INSERT INTO month (num, name, year) VALUES (3,'March',to_date('2019', 'YYYY'))")
	cur.execute("INSERT INTO month (num, name, year) VALUES (4,'April',to_date('2019', 'YYYY'))")
	cur.execute("INSERT INTO month (num, name, year) VALUES (5,'May',to_date('2019', 'YYYY'))")

def popDay(cur):
	c = calendar.Calendar()
	for m in [("January",1,2019),("February",2,2019),("March",3,2019),("April",4,2019),("May",5,2019),("August",8,2018),("September",9,2018),("October",10,2018),("November",11,2018),("December",12,2018)]:
		cur.execute("SELECT id FROM month WHERE name = '{}'".format(m[0]))
		mID = cur.fetchone()[0]

		for d in c.itermonthdays(m[2],m[1]):
			if d > 0:
				if len(str(d)) < 2:
					dstr = "0"+str(d)
				else:
					dstr = str(d)
				s = dstr +" "+ m[0][:3] +" "+ str(m[2])
				cur.execute("INSERT INTO day (month_id, date) VALUES ({},to_date('{}', 'DD Mon YYYY'))".format(mID,s))

def popConflicts(cur):
	cur.execute("SELECT id FROM day WHERE month_id = 1;")
	days = cur.fetchall()

	cur.execute("SELECT id FROM ra WHERE hall_id = 1;")
	ras = cur.fetchall()

	for raID in ras:
		daysCopy = days[:]
		for i in range(0,random.randint(0,15)):
			dID = daysCopy.pop(random.randint(0,len(daysCopy)-1))
			cur.execute("INSERT INTO conflicts (ra_id, day_id) VALUES ({},{})".format(raID[0],dID[0]))

def popDuties(cur):
	cur.execute("SELECT year FROM month ORDER BY year ASC;")
	d = cur.fetchone()[0]
	year = d.year
	month = d.month

	cur.execute("""SELECT first_name, last_name, id, hall_id,
						  date_started, cons.array_agg, points
				   FROM ra JOIN (SELECT ra_id, ARRAY_AGG(days.date)
								 FROM conflicts JOIN (SELECT id, date FROM day
													  WHERE month_id = 1) AS days
				   				 ON (conflicts.day_id = days.id)
				  			     GROUP BY ra_id) AS cons
						   ON (ra.id = cons.ra_id)
				   WHERE ra.hall_id = 1;""")

	raList = [RA(res[0],res[1],res[2],res[3],res[4],res[5],res[6]) for res in cur.fetchall()]
	noDutyList = [date(year,month,1),date(year,month,2),date(year,month,3),date(year,month,4),date(year,month,5),date(year,month,6),date(year,month,31)]

	sched = scheduling(raList,year,month,noDutyList)

	days = {}
	cur.execute("SELECT id, date FROM day WHERE month_id = 1;")
	for res in cur.fetchall():
		days[res[1]] = res[0]

	for d in sched:
		for r in d:
			cur.execute("""
			INSERT INTO duties (hall_id,ra_id,day_id,sched_id) VALUES (1,{},{},1);
			""".format(r.getId(),days[d.getDate()],1))

def popSchedule(cur):
	cur.execute("INSERT INTO schedule (hall_id,month_id,created) VALUES (1,1,NOW());")

def main():
	# This program assumes that the database is completely clean
	conn = psycopg2.connect(os.environ["DATABASE_URL"])
	cur = conn.cursor()
	# popResHall(cur)
	# conn.commit()
	# popRAs(cur)
	# conn.commit()
	popMonth(cur)
	conn.commit()
	popDay(cur)
	conn.commit()
	# popConflicts(cur)
	# conn.commit()
	# popSchedule(cur)
	# conn.commit()
	# popDuties(cur)
	# conn.commit()

main()
