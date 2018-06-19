from flask import Flask, render_template, request, jsonify
from flask_bootstrap import Bootstrap
from scheduler import scheduling
from ra_sched import RA
import datetime
import psycopg2
import calendar
import os

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
Bootstrap(app)
conn = psycopg2.connect(os.environ["DATABASE_URL"])
ct = datetime.datetime.now()
fDict = {"text_month":calendar.month_name[(ct.month+2)%12], "num_month":(ct.month+2)%12, "year":(ct.year if ct.month <= 12 else ct.year+1)}
cDict = {"text_month":calendar.month_name[ct.month], "num_month":ct.month, "year":ct.year}
cc = calendar.Calendar(6) #format calendar so Sunday starts the week

#     -- Views --

@app.route("/")
def index():
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM res_hall;")
    return render_template("index.html", calDict=fDict, hall_list=cur.fetchall(), \
                            cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]))

@app.route("/conflicts")
def conflicts():
    cur = conn.cursor()
    cur2 = conn.cursor()
    cur.execute("SELECT id, first_name, last_name FROM ra WHERE hall_id = 1 ORDER BY last_name ASC;")
    cur2.execute("SELECT id, name FROM res_hall;")
    return render_template("conflicts.html", calDict=fDict, hall_list=cur2.fetchall(), \
                            cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]), ras=cur.fetchall())

@app.route("/archive")
def archive():
    #This will largely be interactive with javascript to ping back and forth years and schedule 'Objects'
    #Javascript will also be able to reset the view of the calendar below the selector
    # No forms necessary
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM res_hall;")

    return render_template("archive.html", calDict=fDict, hall_list=cur.fetchall(), \
                            cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]))

#     -- Functional --

@app.route("/conflicts/p", methods=['POST'])
def processConflicts():
    hallId = 3
    month = 6
    year = 2017
    insert_cur = conn.cursor()

    dateList = []
    for key in request.form:
        if "day" in key:
            dateList.append(key.split("y")[-1])

    for d in dateList:

        insert_cur.execute("INSERT INTO conflict (ra_id, date) VALUES ({},TO_DATE('{}-{:>2}-{:>2}','YYYY/MM/DD'));"\
                            .format(int(request.form["selectRA"]),fDict["year"],fDict["num_month"],d))

    conn.commit()

    if request.form["runScheduler"] == "noRun":
        cur = conn.cursor()
        cur.execute("SELECT id, first_name, last_name FROM ra WHERE hall_id = {} ORDER BY last_name ASC;".format(hallId))
        return render_template("conflicts.html", calDict=fDict, \
                                cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]), ras=cur.fetchall())

    else:
        runScheduler(hallId, month, year)
        return index()

def runScheduler(hallId, month, year):
    # need to pass algorithm a dict with keys of names and values of lists of
    # int date conflicts also needs to pass year and month as ints
    d = {}

    # -- conflicts --
    cur = conn.cursor()
    cur.execute("""SELECT first_name, last_name, date
                   FROM ra JOIN lc_conflict ON (ra.id = conflict.ra_id)
                   WHERE ra.hall_id = {} AND date >= '2017-06-01'::date;
    """.format(hallId))
    res = cur.fetchall()

    for tup in res:
        d[tup[0]+" "+tup[1]] = []

    for tup in res:
        d[tup[0]+" "+tup[1]].append(tup[2].day)
        d[tup[0]+" "+tup[1]].sort()

    # -- no conflicts --

    cur.execute("""SELECT first_name, last_name
                   FROM ra
                   WHERE ra.id NOT IN (SELECT ra_id FROM conflict WHERE date >= '2017-06-01'::date) AND
                         ra.hall_id = {}""".format(hallId))

    res2 = cur.fetchall()
    for tup in res2:
        d[tup[0]+" "+tup[1]] = []

    sched = scheduling(d,year,month)
    print(sched)
    addSchedule(sched,year,month,hallId)

def addSchedule(s, year, month, hallId):
    idMap = raIDmap(hallId)
    dateStr = ""
    exStr = ""
    cur = conn.cursor()

    for day in range(1,calendar.monthrange(year, month)[1]+1):
        dateStr += ",day_{}".format(day)
        ras = []
        for key in s:
            if day in s[key]:
                ras.append(idMap[key])


        exStr += ",ARRAY"+str(ras)

    print(exStr)
    print(dateStr)
    cur.execute("""INSERT INTO schedule (hall_id,month{}) VALUES ({},'2017-06-01'::date{})"""\
                    .format(dateStr,hallId,exStr))
    conn.commit()

def raIDmap(hallId):
    d = {}
    cur = conn.cursor()
    cur.execute("SELECT first_name || ' ' || last_name, id FROM ra WHERE hall_id = {}".format(hallId))
    for key in cur.fetchall():
        d[key[0]] = key[1]

    return d

#     -- api --

@app.route("/api/testAPI", methods=["GET"])
def testAPI():
    cookie = request.cookies.get("username")
    print(request.cookies)
    print(cookie)
    for v in request.args:
        print(v)


    year = 2018
    month = 5
    ra_list = [RA("Ryan","E",1,1,datetime.date(2017,8,22),[datetime.date(year,month,1),datetime.date(year,month,10),datetime.date(year,month,11)]),
               RA("Sarah","L",1,2,datetime.date(2017,8,22),[datetime.date(year,month,2),datetime.date(year,month,12),datetime.date(year,month,22)]),
               RA("Steve","B",1,3,datetime.date(2017,8,22),[datetime.date(year,month,3),datetime.date(year,month,13),datetime.date(year,month,30)]),
               RA("Tyler","C",1,4,datetime.date(2017,8,22),[datetime.date(year,month,4),datetime.date(year,month,14)]),
               RA("Casey","K",1,5,datetime.date(2017,8,22),[datetime.date(year,month,5)])]

    s2 = scheduling(ra_list,year,month,[datetime.date(year,month,14),datetime.date(year,month,15),datetime.date(year,month,16),datetime.date(year,month,17)])

    return jsonify(s2)

@app.route("/api/getSchedule", methods=["GET"])
def getSchedule():
    # API Hook that will get the requested schedule for a given month
    #  The month will be given via request.args as 'monthNum' and 'year'.
    #  The server will then query the database for the appropriate schedule
    #  and send back a jsonified version of the schedule.
    year = 2018
    month = 5
    ra_list = [RA("Ryan","E",1,1,date(2017,8,22),[date(year,month,1),date(year,month,10),date(year,month,11)]),
               RA("Sarah","L",1,2,date(2017,8,22),[date(year,month,2),date(year,month,12),date(year,month,22)]),
               RA("Steve","B",1,3,date(2017,8,22),[date(year,month,3),date(year,month,13),date(year,month,30)]),
               RA("Tyler","C",1,4,date(2017,8,22),[date(year,month,4),date(year,month,14)]),
               RA("Casey","K",1,5,date(2017,8,22),[date(year,month,5)])]

    s2 = scheduling(ra_list,year,month,[date(year,month,14),date(year,month,15),date(year,month,16),date(year,month,17)])

    return jsonify(s2)

@app.route("/api/v1/curSchedule/<string:hallID>")
def apiSearch(hallID):
    cur = conn.cursor()
    cur.execute("""SELECT * FROM schedule WHERE hall_id = {};""".format(hallId))
    res = {"schedule":cur.fetchall()[0],"raList":raIDmap(hallID),"cal":cc.monthdays2calendar(fDict["year"],fDict["num_month"])}
    return jsonify(res)

@app.route("/api/v1/arcSchedule/<string:hallId>", methods=["GET"])
def apiArchive(hallId):
    formdates = []
    cur = conn.cursor()
    cur.execute("SELECT month FROM schedule WHERE hall_id = {};".format(hallId))

    for date in cur.fetchall():
        formdates.append(str(date[0]))

    cur2 = conn.cursor()
    cur2.execute("SELECT id, first_name || ' ' || last_name FROM ra WHERE hall_id = {}".format(hallId))

    res = {"hallID":hallId, "archive":formdates, "raList":raIDmap(hallId)}
    return jsonify(res)

@app.route("/api/v1/arcRetrieve/<string:stuff>")
def apiArchiveRetrieve(stuff):
    s = stuff.split("_")
    cur = conn.cursor()
    cur.execute("SELECT * FROM schedule WHERE hall_id = {} AND month = '{}'::date;".format(s[1],s[0]))
    sched = cur.fetchall()[0]
    raMap = raIDmap(s[1])
    res = {"schedule":sched,"raList":raMap, "cal":cc.monthdays2calendar(fDict["year"],fDict["num_month"])}
    return jsonify(res)

@app.route("/api/v1/getRAs/<string:hallId>")
def getRAs(hallId):
    cur = conn.cursor()
    cur.execute("SELECT id, first_name || ' ' || last_name FROM ra WHERE hall_id = {}".format(hallId))
    return jsonify(cur.fetchall())

if __name__ == "__main__":
    app.run(debug=True)
