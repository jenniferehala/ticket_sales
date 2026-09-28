-- Ticket Sales Table DDL
--
-- trans_date is stored as an integer date-key (YYYYMMDD, e.g. 20200801),
-- not a real DATE column -- this matches the assignment's literal schema
-- (trans_date INT) even though the source CSV writes it as "2020-08-01".
-- event_date is a genuine calendar date and stays DATE.
CREATE TABLE IF NOT EXISTS sales (
    ticket_id    INT PRIMARY KEY,
    trans_date   INT NOT NULL,
    event_id     INT NOT NULL,
    event_name   VARCHAR(50) NOT NULL,
    event_date   DATE NOT NULL,
    event_type   VARCHAR(10) NOT NULL,
    event_city   VARCHAR(20) NOT NULL,
    customer_id  INT NOT NULL,
    price        DECIMAL(10, 2) NOT NULL,
    num_tickets  INT NOT NULL
);
