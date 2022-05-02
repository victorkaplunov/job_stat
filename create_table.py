import sqlite3

# Open database
con = sqlite3.connect("testdb.db")

# Create cursor
cur = con.cursor()

sql = "CREATE TABLE IF NOT EXISTS vacancies (id INTEGER PRIMARY KEY, " \
      "json TEXT, published_at TEXT, schedule_type TEXT);"
cur.execute(sql)

sql = """
CREATE TABLE IF NOT EXISTS calendar
(
  id INTEGER,
  data TEXT,
  CONSTRAINT vac_data UNIQUE (id, data)
);
"""
cur.execute(sql)


sql = """
CREATE TABLE IF NOT EXISTS charts
(
    id INTEGER PRIMARY KEY,
    chart_name NOT NULL,
    data NOT NULL UNIQUE,
    popularity  INTEGER
);
"""
cur.execute(sql)


sql = """
CREATE TABLE IF NOT EXISTS vac_with_salary
(
    id INTEGER PRIMARY KEY,
    published_at TEXT,
    calc_salary NUMERIC,
    experience TEXT,
    url TEXT,
    from NUMERIC,
    to NUMERIC
);
"""
cur.execute(sql)

con.close()  # Close database
