import psycopg2
import loging
import os

def migrate(conn):
    cur = conn.cursor()

    


if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s.%(msecs)d %(levelname)s: %(message)s', \
                        datefmt='%H:%M:%S', \
                        level=logging.INFO, \
                        #filename="migrateDB.log", \
                        #filemode="w"
                        )

    conn = psycopg2.connect(os.environ["DATABASE_URL"])

    logging.info("Beginning Migration")
    migrate(conn)

    logging.info("Committing Changes")
    conn.commit()
    loging.info("  Finished Committing Changes")

    logging.info("Finished Migration")
