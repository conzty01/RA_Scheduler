from psycopg2.extras import Json
import psycopg2
import os

def createHallDB(conn):
    conn.execute("DROP TABLE IF EXISTS res_hall CASCADE;")
    conn.execute("""
        CREATE TABLE res_hall(
            id				 serial UNIQUE,
            name			 varchar(50),
            
        PRIMARY KEY (name)
        );""")

def createScheduleDB(conn):
    conn.execute("DROP TABLE IF EXISTS schedule CASCADE;")
    conn.execute("""
        CREATE TABLE schedule(
            id				serial UNIQUE,
            hall_id			int,
            month_id		int,
            created			date,

        PRIMARY KEY (id),
        FOREIGN KEY (hall_id) REFERENCES res_hall(id),
        FOREIGN KEY (month_id) REFERENCES month(id)
        );""")

def createRaDB(conn):
    conn.execute("DROP TABLE IF EXISTS ra CASCADE;")
    conn.execute("""
        CREATE TABLE ra(
            id				serial UNIQUE,
            first_name		varchar(20),
            last_name		varchar(50),
            color			varchar(7),
            email			varchar(256) UNIQUE,

            PRIMARY KEY (id)
        );""")

def createConflictDB(conn):
    conn.execute("DROP TABLE IF EXISTS conflicts CASCADE;")
    conn.execute("""
        CREATE TABLE conflicts(
            id		serial UNIQUE,
            ra_id	int,
            day_id	int,

            PRIMARY KEY (ra_id, day_id),
            FOREIGN KEY (ra_id) REFERENCES ra(id),
            FOREIGN KEY (day_id) REFERENCES day(id)
        );""")

def createDutyDB(conn):
    conn.execute("DROP TABLE IF EXISTS duties CASCADE;")

    conn.execute("""
        CREATE TABLE duties(
            id			serial UNIQUE,
            hall_id		int,
            ra_id		int,
            day_id		int,
            sched_id	int,
            point_val	int DEFAULT 0 CONSTRAINT pos_duty_point_value CHECK (point_val >= 0),
            flagged		boolean NOT NULL DEFAULT FALSE,

            PRIMARY KEY (id),
            FOREIGN KEY (hall_id) REFERENCES res_hall(id),
            FOREIGN KEY (day_id) REFERENCES day(id),
            FOREIGN KEY (ra_id) REFERENCES ra(id),
            FOREIGN KEY (sched_id) REFERENCES schedule(id)
        );""")

def createDayDB(conn):
    conn.execute("DROP TABLE IF EXISTS day CASCADE;")

    conn.execute("""
        CREATE TABLE day(
            id			serial UNIQUE,
            month_id	int,
            date		date,

            PRIMARY KEY (month_id,date),
            FOREIGN KEY (month_id) REFERENCES month(id)
        );""")

def createMonthDB(conn):
    conn.execute("DROP TABLE IF EXISTS month CASCADE;")

    conn.execute("""
        CREATE TABLE month(
            id			serial UNIQUE,
            num			int,
            name		varchar(10),
            year		date,

            PRIMARY KEY (name,year)
        );""")

def createUserDB(conn):
    conn.execute('DROP TABLE IF EXISTS "user" CASCADE;')

    conn.execute("""
        CREATE TABLE "user"(
            id			serial UNIQUE,
            ra_id		int UNIQUE,
            username	varchar(50) UNIQUE,

            PRIMARY KEY (id),
            FOREIGN KEY (ra_id) REFERENCES ra(id)
        );""")

def createOAuthDB(conn):
    conn.execute('DROP TABLE IF EXISTS flask_dance_oauth CASCADE;')

    conn.execute("""
        CREATE TABLE flask_dance_oauth(
            id					serial UNIQUE,
            provider			varchar(50),
            created_at			timestamp without time zone,
            token				json,
            provider_user_id	varchar(256),
            user_id				int,

            PRIMARY KEY (id)
        );""")

def createBreakDutiesTable(conn):
    conn.execute('DROP TABLE IF EXISTS break_duties CASCADE;')

    conn.execute("""
        CREATE TABLE break_duties(
            id			serial UNIQUE,
            ra_id		int,
            hall_id		int,
            month_id	int,
            day_id		int,
            point_val	int DEFAULT 0 CONSTRAINT pos_break_duty_point_value CHECK (point_val >= 0),

            PRIMARY KEY (hall_id, month_id, day_id, ra_id),
            FOREIGN KEY (ra_id) 	REFERENCES ra(id),
            FOREIGN KEY (hall_id) 	REFERENCES res_hall(id),
            FOREIGN KEY (month_id) 	REFERENCES month(id),
            FOREIGN KEY (day_id) 	REFERENCES day(id)
        );""")


def createGoogleCalendarDB(conn):
    conn.execute("DROP TABLE IF EXISTS google_calendar_info CASCADE;")
    conn.execute("""
        CREATE TABLE google_calendar_info(
            id				serial UNIQUE,
            res_hall_id		int,
            auth_state		varchar(30),
            token 			bytea,
            calendar_id		varchar(60),

            PRIMARY KEY (res_hall_id),
            FOREIGN KEY (res_hall_id) REFERENCES res_hall(id)
        );""")


def createPointModifierDB(conn):
    conn.execute("DROP TABLE IF EXISTS point_modifier CASCADE;")
    conn.execute("""
        CREATE TABLE point_modifier(
            id				serial UNIQUE,
            ra_id			int,
            res_hall_id		int,
            modifier		int DEFAULT 0,
            
            PRIMARY KEY (ra_id, res_hall_id),
            FOREIGN KEY (ra_id) REFERENCES ra(id),
            FOREIGN KEY (res_hall_id) REFERENCES res_hall(id)
        );""")

def createHallSettingsDB(conn):
    conn.execute("DROP TABLE IF EXISTS hall_settings CASCADE;")

    defaultJSON = {
        "reg_duty_num_assigned": 1,     # Number of RAs to be assigned on regular duty days.
        "multi_duty_num_assigned": 2,   # Number of RAs to be assigned on multi-duty days.
        "brk_duty_num_assigned": 1,     # Number of RAs to be assigned on break duty days.
        "reg_duty_pts": 1,              # Number of points to be awarded for regular duties.
        "multi_duty_pts": 2,            # Number of points to be awarded for multi-day duties.
        "brk_duty_pts": 3,              # Number of points to be awarded for break duties.
        "multi_duty_days": [4, 5]       # Days of the week which are considered multi-duty days.
                                        #    Mon, Tues, Wed, Thurs, Fri, Sat, Sun
                                        #     0    1     2     3     4    5    6
    }

    conn.execute("""
        CREATE TABLE hall_settings(
            id				        serial UNIQUE,
            res_hall_id		        int NOT NULL,
            year_start_mon          int     NOT NULL DEFAULT 8 CHECK (year_start_mon >= 1 AND 
                                                                        year_start_mon <= 12),
            year_end_mon            int     NOT NULL DEFAULT 7 CHECK (year_end_mon >= 1 AND 
                                                                        year_end_mon <= 12),
            duty_config             json    NOT NULL DEFAULT %s::JSON,
            auto_adj_excl_ra_pts    boolean NOT NULL DEFAULT false,
            flag_multi_duty         boolean NOT NULL DEFAULT false,
            duty_flag_label         VARCHAR(20) NOT NULL DEFAULT 'Secondary Personnel',
            
            PRIMARY KEY (res_hall_id),
            FOREIGN KEY (res_hall_id) REFERENCES res_hall(id)
        );""", (Json(defaultJSON),))

def createStaffMembershipDB(conn):
    conn.execute("DROP TABLE IF EXISTS staff_membership CASCADE;")
    conn.execute("""
        CREATE TABLE staff_membership(
            id              serial UNIQUE,
            ra_id           int NOT NULL,
            res_hall_id     int NOT NULL,
            start_date      date NOT NULL DEFAULT NOW(),
            auth_level		int NOT NULL DEFAULT 1,
            selected        boolean NOT NULL DEFAULT false,
            
            PRIMARY KEY (ra_id, res_hall_id),
            FOREIGN KEY (ra_id) REFERENCES ra(id),
            FOREIGN KEY (res_hall_id) REFERENCES res_hall(id)
        );""")


def main():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    createHallDB(conn.cursor())
    createRaDB(conn.cursor())
    createMonthDB(conn.cursor())
    createDayDB(conn.cursor())
    createConflictDB(conn.cursor())
    createScheduleDB(conn.cursor())
    createDutyDB(conn.cursor())
    createBreakDutiesTable(conn.cursor())
    createUserDB(conn.cursor())
    createOAuthDB(conn.cursor())
    createGoogleCalendarDB(conn.cursor())
    createPointModifierDB(conn.cursor())
    createHallSettingsDB(conn.cursor())
    createStaffMembershipDB(conn.cursor())

    conn.commit()


if __name__ == "__main__":
    main()
