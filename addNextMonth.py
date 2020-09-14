import psycopg2
import calendar
import sys
import os

# TODO: add ability to either add entire year or specific month from command line
# TODO: Implement argparse to add functionality to CLI

def addYear(cur,year):
    # Add the months of the specified year into the Database

    monthList = []
    monthNameList = calendar.month_name[1:]

    # Run addMonth passing the cursor, month name, month number, and year
    # (calendar.month_name starts with a blank string)
    for num, name in enumerate(monthNameList, start=1):
        print("  Adding Month: {}".format(name))
        addMonth(cur,(name, num, year))

def addMonth(cur,mt):
    # Adds the specified month into the Database
    c = calendar.Calendar()

    # Add the month the DB
    cur.execute("INSERT INTO month (name, num, year) VALUES ('{}',{},to_date('{}', 'MM YYYY')) RETURNING id".format(mt[0],mt[1],str(mt[1])+" "+str(mt[2])))
    mId = cur.fetchone()[0]

    # Add the corresponding days to the DB
    # itermonthdays acccepts year, month number
    for d in c.itermonthdays(mt[2],mt[1]):
        if d > 0:
            #print("    Adding Day: {}".format(d))
            if len(str(d)) < 2:
                dstr = "0"+str(d)
            else:
                dstr = str(d)

            s = dstr +" "+ mt[0][:3] +" "+ str(mt[2])
            cur.execute("INSERT INTO day (month_id, date) VALUES ({},to_date('{}', 'DD Mon YYYY'))".format(mId,s))


def main():
    # Connect to the Database
    print("STARTING")
    conn = psycopg2.connect(os.environ["DATABASE_URL"])

    # Check sys.argv
    # position 1 should be the year that should be added to the DB

    if len(sys.argv) < 2:
        raise TypeError("Too few arguments provided. Expected 2, {} provided".format(len(sys.argv)))

    else:
        addYear(conn.cursor(), int(sys.argv[1]))
        conn.commit()
        print("FINISHED")


if __name__ == "__main__":
    main()
