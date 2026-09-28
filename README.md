# ticket_sales — Event Ticket System Mini-Project

A small pipeline that loads a third-party vendor's ticket-sales CSV into a
MySQL `sales` table, then reports the most popular events over the past
month.

## What it does

1. **DDL** (`sql/create_sales_table.sql`): defines and creates the `sales`
   table matching the assignment's schema.
2. **Load** (`load_third_party`): reads the vendor CSV row by row and
   inserts each record into `sales`, using `INSERT ... ON DUPLICATE KEY
   UPDATE` so re-running the loader on the same file is safe (no duplicate
   rows).
3. **Query** (`query_popular_tickets`): sums `num_tickets` per event over
   the past month and returns the top 5.
4. **Display**: prints the result as a simple bulleted list, matching the
   assignment's example output format.

## Project layout

```
ticket_sales_mini_project/
├── ticket_pipeline.py        # get_db_connection / create_sales_table /
│                              # load_third_party / query_popular_tickets / main
├── sql/
│   └── create_sales_table.sql
├── data/
│   └── third_party_sales_1.csv   # sample vendor file provided with the assignment
├── docker-compose.yaml       # throwaway MySQL 8.0 container
├── requirements.txt
├── .env.example               # copy to .env -- DB connection settings
└── docs/
    └── execution_log.txt     # real output from a successful run
```

## 1. Start MySQL

Requires Docker Desktop (already set up if you did the `airflow_mini_project`
in this series).

```bash
cd ticket_sales_mini_project
cp .env.example .env
docker compose up -d
```

First run pulls the `mysql:8.0` image (~600 MB). Wait for it to report
healthy:

```bash
docker compose ps
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Run the pipeline

```bash
python3 ticket_pipeline.py data/third_party_sales_1.csv
```

This creates the `sales` table (if it doesn't already exist), loads the CSV,
and prints the most popular events:

```
Ensured table 'sales' exists (from create_sales_table.sql)
Loaded 6 rows from data/third_party_sales_1.csv into 'sales'
Here are the most popular tickets in the past month:
- Washington Spirits vs Sky Blue FC
- Christmas Spectacular
- The North American International Auto Show
- Carlisle Ford Nationals
```

## 4. Verify the result

Connect to the database directly and check the row count / contents:

```bash
docker compose exec mysql mysql -u ticket_app -p ticket_system \
  -e "SELECT * FROM sales;"
```

(password is `ticket_app_pw`, from `.env`)

You should see all 6 rows from `data/third_party_sales_1.csv`.

## Known corners cut / deliberate choices

- **`trans_date` is stored as an `INT` date-key (`YYYYMMDD`, e.g.
  `20200801`), not a real `DATE`.** This matches the assignment's literal
  schema (`trans_date INT`) even though the source CSV writes it as
  `2020-08-01`. `event_date` is a genuine calendar date and stays `DATE`.
- **"Past month" is relative to the newest transaction already in the
  table, not wall-clock today.** The sample data is dated August 2020 — if
  the query used `CURDATE()`, it would return nothing no matter when this
  is actually run. Computing it relative to `MAX(trans_date)` keeps the
  demo meaningful regardless of when you run it.
- **Loader is idempotent** (`ON DUPLICATE KEY UPDATE` on `ticket_id`,
  the primary key) — not required by the assignment, but re-running the
  same file twice shouldn't double-count sales.
- **`.env` is gitignored**; `.env.example` is committed as the template.
  Copy it to `.env` before running — the defaults are throwaway local dev
  credentials for a disposable Docker container.
