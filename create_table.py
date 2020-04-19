import sqlite3

# Open database
con = sqlite3.connect("testdb.db")

# Create cursor
cur = con.cursor()

# sql = """CREATE TABLE IF NOT EXISTS vacancies (id INTEGER PRIMARY KEY, json TEXT);"""
# cur.execute(sql)
# sql = """
# CREATE TABLE IF NOT EXISTS calendar
# (
#   id INTEGER,
#   data TEXT,
#   CONSTRAINT vac_data UNIQUE (id, data)
# );
# """
# cur.execute(sql)

# cur.execute("DROP TABLE  languages;")
# cur.execute("DROP TABLE  frameworks;")
cur.execute("DROP TABLE  charts;")

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


con.close()  # Close database
