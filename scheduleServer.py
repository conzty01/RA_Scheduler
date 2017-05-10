from flask import Flask, render_template, request, jsonify
from flask_bootstrap import Bootstrap
import datetime
import psycopg2
import sqlalchemy
import calendar
import os

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
Bootstrap(app)
conn = psycopg2.connect(dbname="conzty01",user="conzty01",host="knuth.luther.edu")
ct = datetime.datetime.now()
fDict = {"text_month":calendar.month_name[(ct.month+1)%12], "num_month":(ct.month+1)%12, "year":(ct.year if ct.month <= 12 else ct.year+1)}
cDict = {"text_month":calendar.month_name[ct.month], "num_month":ct.month, "year":ct.year}
cc = calendar.Calendar(6) #format calendar so Sunday starts the week

#     -- Views --

@app.route("/")
def index():
    cur = conn.cursor()
    cur.execute("SELECT id, name, calendar_id FROM lc_res_hall;")
    return render_template("index.html", hall_list=cur.fetchall())

@app.route("/conflicts")
def conflicts():
    cur = conn.cursor()
    cur.execute("SELECT id, first_name, last_name FROM lc_resident_assistant WHERE hall_id = 1 ORDER BY last_name ASC;")

    return render_template("conflicts.html", calDict=fDict, \
                            cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]), ras=cur.fetchall())

@app.route("/archive")
def archive():
    #This will largely be interactive with javascript to ping back and forth years and schedule 'Objects'
    #Javascript will also be able to reset the view of the calendar below the selector
    # No forms necessary
    cur = conn.cursor()

    return render_template("archive.html")

#     -- Functional --

@app.route("/conflicts/p", methods=['POST'])
def processConflicts():
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
        cur.execute("SELECT id, first_name, last_name FROM lc_resident_assistant WHERE hall_id = 1 ORDER BY last_name ASC;")
        return render_template("conflicts.html", calDict=fDict, \
                                cal=cc.monthdays2calendar(fDict["year"],fDict["num_month"]), ras=cur.fetchall())

    else:
        runScheduler()
        return render_template("index.html", calDict=cDict, \
                                cal=cc.monthdays2calendar(cDict["year"],cDict["num_month"]))

def runScheduler():
    return

#     -- api --

@app.route("/api/v1/curSchedule")
def apiSearch():
    cur = conn.cursor()
    cur.execute("""SELECT * FROM lc_schedule WHERE EXTRACT(MONTH FROM month) = EXTRACT(MONTH FROM NOW()) AND
                                                   EXTRACT(YEAR FROM month) = EXTRACT(YEAR FROM NOW());""")

    return jsonify(cur.fetchall())

if __name__ == "__main__":
    app.run(debug=True)
