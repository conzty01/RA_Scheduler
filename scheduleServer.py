from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import psycopg2
import sqlalchemy
import calendar
import json
import os

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
Bootstrap(app)
#conn = psycopg2.connect(dbname="conzty01",user="conzty01",host="knuth.luther.edu")

#     -- Views --

@app.route("/")
def index():
    c = calendar.Calendar(6)
    cDict = {"year":2017,
             "month":5,
             "Tmonth":"May"}

    return render_template("index.html", calDict=cDict,cal=c.monthdays2calendar(cDict["year"],cDict["month"]))

@app.route("/conflicts")
def conflicts():
    pass

@app.route("/archive")
def archive():
    pass

#     -- Functional --

@app.route("/conflicts/parse", methods=["POST"])
def parseConflicts():
    pass

#     -- api --

@app.route("/api/v1/")
def apiSearch():
    pass

if __name__ == "__main__":
    app.run(debug=True)
