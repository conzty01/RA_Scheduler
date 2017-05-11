from flask import Flask, render_template, request, jsonify
from flask_bootstrap import Bootstrap
from scheduler import scheduling
import datetime
import psycopg2
import calendar
import os

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
Bootstrap(app)
conn = psycopg2.connect(os.environ["DATABASE_URL"])
ct = datetime.datetime.now()
fDict = {"text_month":calendar.month_name[(ct.month+1)%12], "num_month":(ct.month+1)%12, "year":(ct.year if ct.month <= 12 else ct.year+1)}
cDict = {"text_month":calendar.month_name[ct.month], "num_month":ct.month, "year":ct.year}
cc = calendar.Calendar(6) #format calendar so Sunday starts the week

#     -- Views --

@app.route("/")
def index():
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM lc_res_hall;")
    return render_template("index.html", calDict=fDict, hall_list=cur.fetchall(), \
                            cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]))

@app.route("/conflicts")
def conflicts():
    cur = conn.cursor()
    cur2 = conn.cursor()
    cur.execute("SELECT id, first_name, last_name FROM lc_resident_assistant WHERE hall_id = 1 ORDER BY last_name ASC;")
    cur2.execute("SELECT id, name FROM lc_res_hall;")
    return render_template("conflicts.html", calDict=fDict, hall_list=cur2.fetchall(), \
                            cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]), ras=cur.fetchall())

@app.route("/archive")
def archive():
    #This will largely be interactive with javascript to ping back and forth years and schedule 'Objects'
    #Javascript will also be able to reset the view of the calendar below the selector
    # No forms necessary
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM lc_res_hall;")

    return render_template("archive.html", calDict=fDict, hall_list=cur.fetchall(), \
                            cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]))

#     -- Functional --

@app.route("/conflicts/p", methods=['POST'])
def processConflicts():
    hallId = 1
    month = 6
    year = 2017
    insert_cur = conn.cursor()

    dateList = []
    for key in request.form:
        if "day" in key:
            dateList.append(key.split("y")[-1])

    for d in dateList:

        insert_cur.execute("INSERT INTO lc_conflict (ra_id, date) VALUES ({},TO_DATE('{}-{:>2}-{:>2}','YYYY/MM/DD'));"\
                            .format(int(request.form["selectRA"]),fDict["year"],fDict["num_month"],d))

    conn.commit()

    if request.form["runScheduler"] == "noRun":
        cur = conn.cursor()
        cur.execute("SELECT id, first_name, last_name FROM lc_resident_assistant WHERE hall_id = {} ORDER BY last_name ASC;".format(hallId))
        return render_template("conflicts.html", calDict=fDict, \
                                cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]), ras=cur.fetchall())

    else:
        runScheduler(hallId, month, year)
        return index()

def runScheduler(hallId, month, year):
    # need to pass algorithm a dict with keys of names and values of lists of int date conflicts
    # also needs to pass year and month as ints
    d = {}

    # -- conflicts --
    cur = conn.cursor()
    cur.execute("""SELECT first_name, last_name, date
                   FROM lc_resident_assistant JOIN lc_conflict ON (lc_resident_assistant.id = lc_conflict.ra_id)
                   WHERE lc_resident_assistant.hall_id = {} AND date >= '2017-06-01'::date;
    """.format(hallId))
    res = cur.fetchall()

    for tup in res:
        d[tup[0]+" "+tup[1]] = []

    for tup in res:
        d[tup[0]+" "+tup[1]].append(tup[2].day)
        d[tup[0]+" "+tup[1]].sort()

    # -- no conflicts --

    cur.execute("""SELECT first_name, last_name
                   FROM lc_resident_assistant
                   WHERE lc_resident_assistant.id NOT IN (SELECT ra_id FROM lc_conflict WHERE date >= '2017-06-01'::date) AND
                         lc_resident_assistant.hall_id = {}""".format(hallId))

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
    cur.execute("""INSERT INTO lc_schedule (hall_id,month{}) VALUES ({},'2017-06-01'::date{})"""\
                    .format(dateStr,hallId,exStr))
    conn.commit()

def raIDmap(hallId):
    d = {}
    cur = conn.cursor()
    cur.execute("SELECT first_name || ' ' || last_name, id FROM lc_resident_assistant WHERE hall_id = {}".format(hallId))
    for key in cur.fetchall():
        d[key[0]] = key[1]

    return d

#     -- api --

@app.route("/api/v1/curSchedule/<string:hallID>")
def apiSearch(hallID):
    cur = conn.cursor()
    cur.execute("""SELECT * FROM lc_schedule WHERE hall_id = {};""".format(hallID))
    res = {"schedule":cur.fetchall()[0],"raList":raIDmap(hallID),"cal":cc.monthdays2calendar(fDict["year"],fDict["num_month"])}
    return jsonify(res)

@app.route("/api/v1/arcSchedule/<string:hallId>", methods=["GET"])
def apiArchive(hallId):
    formdates = []
    cur = conn.cursor()
    cur.execute("SELECT month FROM lc_schedule WHERE hall_id = {};".format(hallId))

    for date in cur.fetchall():
        formdates.append(str(date[0]))

    cur2 = conn.cursor()
    cur2.execute("SELECT id, first_name || ' ' || last_name FROM lc_resident_assistant WHERE hall_id = {}".format(hallId))

    res = {"hallID":hallId, "archive":formdates, "raList":raIDmap(hallId)}
    return jsonify(res)

@app.route("/api/v1/arcRetrieve/<string:stuff>")
def apiArchiveRetrieve(stuff):
    s = stuff.split("_")
    cur = conn.cursor()
    cur.execute("SELECT * FROM lc_schedule WHERE hall_id = {} AND month = '{}'::date;".format(s[1],s[0]))
    sched = cur.fetchall()[0]
    raMap = raIDmap(s[1])
    res = {"schedule":sched,"raList":raMap, "cal":cc.monthdays2calendar(fDict["year"],fDict["num_month"])}
    return jsonify(res)

@app.route("/api/v1/getRAs/<string:hallId>")
def getRAs(hallId):
    cur = conn.cursor()
    cur.execute("SELECT id, first_name || ' ' || last_name FROM lc_resident_assistant WHERE hall_id = {}".format(hallId))
    return jsonify(cur.fetchall())



if __name__ == "__main__":
    app.run(debug=True)
