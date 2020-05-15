import json
from re import search
import sqlite3

con = sqlite3.connect("testdb.db")
cur = con.cursor()
sql = "SELECT * FROM vacancies"  # WHERE json LIKE '%опыт разработки%';"
cur.execute(sql)
vac = cur.fetchall()
id_list = []
for i in vac:
    name = json.loads(i[1])['name']
    if search("QA|Qa|QА|Qа|Q.A.|тест|Тест|ТЕСТ|Test|test|SDET|Quality", name):
        continue
    else:
        vac_id = json.loads(i[1])['id']
        id_list.append(vac_id)

print(id_list, len(id_list))

for i in id_list:
    sql = f"DELETE FROM vacancies WHERE id = {i}"
    cur.execute(sql)
    con.commit()


