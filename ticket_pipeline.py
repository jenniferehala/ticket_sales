"""
ticket_pipeline
----------------
Loads a third-party ticket-sales CSV into a MySQL "sales" table, then
reports the most popular events over the past month.

Usage:
    python3 ticket_pipeline.py <csv_path>
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR = Path(__file__).resolve().parent
DDL_PATH = SCRIPT_DIR / "sql" / "create_sales_table.sql"

INSERT_SQL = """
INSERT INTO sales
    (ticket_id, trans_date, event_id, event_name, event_date,
     event_type, event_city, customer_id, price, num_tickets)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    trans_date = VALUES(trans_date),
    event_id = VALUES(event_id),
    event_name = VALUES(event_name),
    event_date = VALUES(event_date),
    event_type = VALUES(event_type),
    event_city = VALUES(event_city),
    customer_id = VALUES(customer_id),
    price = VALUES(price),
    num_tickets = VALUES(num_tickets)
"""

# "Past month" relative to the newest transaction already in the table,
# not wall-clock today -- otherwise this sample data (dated 2020-08) would
# never show up as "recent" no matter when the pipeline is actually run.
POPULAR_TICKETS_SQL = """
SELECT event_id, event_name, SUM(num_tickets) AS total_tickets
FROM sales
WHERE STR_TO_DATE(CAST(trans_date AS CHAR), '%Y%m%d') >= (
    SELECT DATE_SUB(STR_TO_DATE(CAST(MAX(trans_date) AS CHAR), '%Y%m%d'), INTERVAL 1 MONTH)
    FROM sales
)
GROUP BY event_id, event_name
ORDER BY total_tickets DESC
LIMIT 5
"""


def get_db_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=os.environ.get("DB_PORT", "3306"),
            database=os.environ["DB_NAME"],
        )
    except Exception as error:
        print("Error while connecting to database for ticket pipeline:", error)
    return connection


def create_sales_table(connection) -> None:
    ddl = DDL_PATH.read_text()
    cursor = connection.cursor()
    cursor.execute(ddl)
    connection.commit()
    cursor.close()
    print(f"Ensured table 'sales' exists (from {DDL_PATH.name})")


def _to_date_key(date_str: str) -> int:
    """'2020-08-01' -> 20200801"""
    return int(date_str.replace("-", ""))


def load_third_party(connection, file_path_csv: str) -> int:
    cursor = connection.cursor()
    rows_loaded = 0

    with open(file_path_csv, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            (
                ticket_id, trans_date, event_id, event_name, event_date,
                event_type, event_city, customer_id, price, num_tickets,
            ) = row

            cursor.execute(
                INSERT_SQL,
                (
                    int(ticket_id),
                    _to_date_key(trans_date),
                    int(event_id),
                    event_name,
                    event_date,
                    event_type,
                    event_city,
                    int(customer_id),
                    float(price),
                    int(num_tickets),
                ),
            )
            rows_loaded += 1

    connection.commit()
    cursor.close()
    print(f"Loaded {rows_loaded} rows from {file_path_csv} into 'sales'")
    return rows_loaded


def query_popular_tickets(connection):
    cursor = connection.cursor()
    cursor.execute(POPULAR_TICKETS_SQL)
    records = cursor.fetchall()
    cursor.close()
    return records


def display_popular_tickets(records) -> None:
    print("Here are the most popular tickets in the past month:")
    for event_id, event_name, total_tickets in records:
        print(f"- {event_name}")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <csv_path>", file=sys.stderr)
        sys.exit(1)

    csv_path = sys.argv[1]

    connection = get_db_connection()
    if connection is None:
        sys.exit(1)

    try:
        create_sales_table(connection)
        load_third_party(connection, csv_path)
        records = query_popular_tickets(connection)
        display_popular_tickets(records)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
