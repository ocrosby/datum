import os
import psycopg2

from dotenv import load_dotenv
from typing import List, Tuple

load_dotenv()

# Code of your application, which uses environment variables (e.g. from `os.environ` or
# `os.getenv`) as if they came from the actual environment.


def get_tables(cursor) -> List[Tuple]:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = cursor.fetchall()

    return tables


if __name__ == "__main__":
    try:
        conn = psycopg2.connect(database=os.getenv("DB_NAME"),
                                user=os.getenv("DB_USER"),
                                password=os.getenv("DB_PASS"),
                                host=os.getenv("DB_HOST"),
                                port=os.getenv("DB_PORT"))


        cursor = conn.cursor()

        tables = get_tables(cursor)

        for table in tables:
            print(table)

        cursor.execute("SELECT * FROM countries WHERE id = 1")

        # returns a single row in the form of a tuple, with the information arranged in the
        # order specified by the query's supplied columns
        print(cursor.fetchone())

        # fetchall returns all the rows
        print(cursor.fetchall())

        # allows us to get a number of records out of the database and gives us additional
        # control over the precise number of rows we get
        print(cursor.fetchmany(size=3))

        cursor.execute("SELECT * FROM states")

        for record in cursor.fetchall():
            print(record)

        cursor.close()
    except psycopg2.OperationalError as e:
        print(f"Error: {e}")
