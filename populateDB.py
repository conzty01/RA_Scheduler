from schedule.ra_sched import RA
import scheduler4_0 as scheduler
import copy as cp
import psycopg2
import calendar
import random
import os


# -----------------------------------------
# --      Methods to Populate the DB     --
# -----------------------------------------

def randomColor():
    colors = ['#DEB887', '#5F9EA0', '#7FFF00', '#D2691E', '#FF7F50', '#6495ED', '#DC143C',
              '#00FFFF', '#A9A9A9', '#BDB76B', '#FF8C00', '#E9967A', '#8FBC8F', '#00CED1',
              '#FF1493', '#00BFFF', '#1E90FF', '#228B22', '#FF00FF', '#FFD700', '#DAA520',
              '#808080', '#008000', '#FF69B4', '#CD5C5C', '#ADD8E6', '#F08080', '#90EE90',
              '#FFB6C1', '#FFA07A', '#20B2AA', '#87CEFA', '#B0C4DE', '#00FF00', '#32CD32',
              '#FF00FF', '#66CDAA', '#BA55D3', '#9370DB', '#3CB371', '#7B68EE', '#00FA9A',
              '#48D1CC', '#C71585', '#FFA500', '#FF4500', '#DA70D6', '#DB7093', '#CD853F',
              '#FFC0CB', '#DDA0DD', '#B0E0E6', '#FF0000', '#BC8F8F', '#4169E1', '#FA8072',
              '#F4A460', '#2E8B57', '#A0522D', '#C0C0C0', '#87CEEB', '#6A5ACD', '#708090',
              '#00FF7F', '#4682B4', '#D2B48C', '#D8BFD8', '#FF6347', '#40E0D0', '#EE82EE',
              '#F5DEB3']

    return colors[random.randint(0, len(colors) - 1)]


def popResHall(cur):
    for n in ['Brandt', 'Olson', 'Larsen']:
        cur.execute("INSERT INTO res_hall (name) VALUES ('{}')".format(n))

    cur.execute("INSERT INTO res_hall (id,name) VALUES (0,'Not Assigned');")


def popRAs(cur):

    def popBrandtRA(cur):
        cur.execute("SELECT id FROM res_hall WHERE name = 'Brandt';")
        iD = cur.fetchone()[0]

        for n in ["Alfonzo Doerr", "Lahoma Berns", "Lue Girardin", "Donald Demartini", "Aubrey Mandell",
                  "Stormy Dunigan", "Arron Kernan", "Betty Chmiel", "Gerardo Spells", "Epifania Soucy",
                  "Tristan Hedgepeth", "Neil Frix", "Marvin Cheatam", "Carmen Broadnax", "Milford Schroyer"]:

            c = randomColor()

        cur.execute("INSERT INTO ra (first_name, last_name, hall_id, date_started, color) VALUES (%s,%s,%s,NOW(),%s)"
                    .format(n.split()[0], n.split()[1], iD, c))

    def popLarsenRA(cur):
        cur.execute("SELECT id FROM res_hall WHERE name = 'Larsen';")
        iD = cur.fetchone()[0]

        for n in ["Contessa Clardy", "Lolita Marcelino", "Wan Waddington", "Venus Maus", "Rosamond Chesson",
                  "Mitzie Sickels"]:

            c = randomColor()

            cur.execute("INSERT INTO ra (first_name, last_name, hall_id, date_started, color) VALUES (%s,%s,%s,NOW(),%s)"
                        .format(n.split()[0], n.split()[1], iD, c))

    def popOlsonRA(cur):
        cur.execute("SELECT id FROM res_hall WHERE name = 'Olson';")
        iD = cur.fetchone()[0]

        for n in ["Nick Vankirk", "Eldon Sweetman", "Zita Gans", "Claudia Hole", "Dane Agarwal", "Verna Korb",
                  "Ray Housman", "Zulema Robitaille"]:

            c = randomColor()

            cur.execute("INSERT INTO ra (first_name, last_name, hall_id, date_started, color) VALUES (%s,%s,%s,NOW(),%s)"
                .format(n.split()[0], n.split()[1], iD, c))

    popBrandtRA(cur)
    popLarsenRA(cur)
    popOlsonRA(cur)


def popMonth(cur):
    cur.execute("INSERT INTO month (num, name, year) VALUES (8,'August',to_date('08 2018', 'MM YYYY'))")
    cur.execute("INSERT INTO month (num, name, year) VALUES (9,'September',to_date('09 2018', 'MM YYYY'))")
    cur.execute("INSERT INTO month (num, name, year) VALUES (10,'October',to_date('10 2018', 'MM YYYY'))")
    cur.execute("INSERT INTO month (num, name, year) VALUES (11,'November',to_date('11 2018', 'MM YYYY'))")
    cur.execute("INSERT INTO month (num, name, year) VALUES (12,'December',to_date('12 2018', 'MM YYYY'))")
    cur.execute("INSERT INTO month (num, name, year) VALUES (1,'January',to_date('01 2019', 'MM YYYY'))")
    cur.execute("INSERT INTO month (num, name, year) VALUES (2,'February',to_date('02 2019', 'MM YYYY'))")
    cur.execute("INSERT INTO month (num, name, year) VALUES (3,'March',to_date('03 2019', 'MM YYYY'))")
    cur.execute("INSERT INTO month (num, name, year) VALUES (4,'April',to_date('04 2019', 'MM YYYY'))")
    cur.execute("INSERT INTO month (num, name, year) VALUES (5,'May',to_date('05 2019', 'MM YYYY'))")


def popDay(cur):
    c = calendar.Calendar()
    for m in [("January", 1, 2019), ("February", 2, 2019), ("March", 3, 2019), ("April", 4, 2019), ("May", 5, 2019),
              ("August", 8, 2018), ("September", 9, 2018), ("October", 10, 2018), ("November", 11, 2018),
              ("December", 12, 2018)]:
        cur.execute("SELECT id FROM month WHERE name = '{}'".format(m[0]))
        mID = cur.fetchone()[0]

        for d in c.itermonthdays(m[2], m[1]):
            if d > 0:
                if len(str(d)) < 2:
                    dstr = "0" + str(d)
                else:
                    dstr = str(d)
                s = dstr + " " + m[0][:3] + " " + str(m[2])
                cur.execute("INSERT INTO day (month_id, date) VALUES ({},to_date('{}', 'DD Mon YYYY'))".format(mID, s))


def popConflicts(cur):
    cur.execute("SELECT id FROM day WHERE month_id = 1;")
    days = cur.fetchall()

    cur.execute("SELECT id FROM ra WHERE hall_id = 1;")
    ras = cur.fetchall()

    for raID in ras:
        daysCopy = days[:]
        for i in range(0, random.randint(0, 15)):
            dID = daysCopy.pop(random.randint(0, len(daysCopy) - 1))
            cur.execute("INSERT INTO conflicts (ra_id, day_id) VALUES ({},{})".format(raID[0], dID[0]))


def popDuties(cur, conn):
    cur.execute("SELECT id, year FROM month ORDER BY year ASC;")
    monthId, date = cur.fetchone()
    hallId = 1
    year = 2018
    month = 8

    cur.execute("SELECT id FROM ra WHERE hall_id = {}".format(hallId))
    eligibleRAs = [int(i[0]) for i in cur.fetchall()]
    eligibleRAStr = "AND ra.id IN ({});".format(str(eligibleRAs)[1:-1])

    queryStr = """
        SELECT first_name, last_name, id, hall_id, date_started,
               COALESCE(cons.array_agg, ARRAY[]::date[])
        FROM ra LEFT OUTER JOIN (
            SELECT ra_id, ARRAY_AGG(days.date)
            FROM conflicts JOIN (
                SELECT id, date
                FROM day
                WHERE month_id = {}
                ) AS days
            ON (conflicts.day_id = days.id)
            GROUP BY ra_id
            ) AS cons
        ON (ra.id = cons.ra_id)
        WHERE ra.hall_id = {}
        AND ra.auth_level < 3 {}
    """.format(monthId, hallId, eligibleRAStr)

    cur.execute(queryStr)  # Query the database for the appropriate RAs and their respective information
    partialRAList = cur.fetchall()

    start = "2018-08-01"
    end = "2019-07-31"

    ra_list = [RA(res[0], res[1], res[2], res[3], res[4], res[5], 0) for res in partialRAList]

    noDutyList = [1, 2, 15, 16, 28]

    ldat = (len(ra_list) // 2) + 1

    copy_raList = cp.deepcopy(ra_list)
    copy_noDutyList = cp.copy(noDutyList)

    completed = False
    successful = True
    while not completed:
        # Create the Schedule
        sched = scheduler.schedule(copy_raList, year, month, noDutyDates=copy_noDutyList, ldaTolerance=ldat)

        if len(sched) == 0:
            # If we were unable to schedule with the previous parameters,

            if ldat > 1:
                # And the LDATolerance is greater than 1
                #  then decrement the LDATolerance by 1 and try again

                # print("DECREASE LDAT: ", ldat)
                ldat -= 1
                copy_raList = cp.deepcopy(ra_list)
                copy_noDutyList = cp.copy(noDutyList)

            else:
                # The LDATolerance is not greater than 1 and we were unable to schedule
                completed = True
                successful = False

        else:
            # We were able to create a schedule
            completed = True

    cur.execute(
        "INSERT INTO schedule (hall_id, month_id, created) VALUES ({},{},NOW()) RETURNING id;".format(hallId, monthId))
    schedId = cur.fetchone()[0]
    conn.commit()

    days = {}
    cur.execute("SELECT EXTRACT(DAY FROM date), id FROM day WHERE month_id = {};".format(monthId))
    for res in cur.fetchall():
        days[res[0]] = res[1]

    # Iterate through the schedule
    dutyDayStr = ""
    noDutyDayStr = ""
    for d in sched:
        # If there are RAs assigned to this day
        if d.numberOnDuty() > 0:
            for r in d:
                dutyDayStr += "({},{},{},{},{}),".format(hallId, r.getId(), days[d.getDate()], schedId, d.getPoints())

        else:
            noDutyDayStr += "({},{},{},{}),".format(hallId, days[d.getDate()], schedId, d.getPoints())

    # Attempt to save the schedule to the DB
    try:
        # Add all of the duties that were scheduled for the month
        if dutyDayStr != "":
            cur.execute("""
                    INSERT INTO duties (hall_id, ra_id, day_id, sched_id, point_val) VALUES {};
                    """.format(dutyDayStr[:-1]))

        # Add all of the blank duty values for days that were not scheduled
        if noDutyDayStr != "":
            cur.execute("""
                    INSERT INTO duties (hall_id, day_id, sched_id, point_val) VALUES {};
                    """.format(noDutyDayStr[:-1]))

    except psycopg2.IntegrityError:
        # print("ROLLBACK")
        conn.rollback()

    conn.commit()

    cur.close()


def main():
    # This program assumes that the database is completely clean
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
    popConflicts(cur)
    conn.commit()
    popDuties(cur, conn)
    conn.commit()


main()
