# -*- encoding=utf8 -*-
import requests
import json
import sqlite3
import unicodedata
import re

con = sqlite3.connect("testdb.db")  # Open database
cur = con.cursor()  # Create cursor

base_url = 'https://api.hh.ru/'
api_method = 'vacancies/'
search_string = u'?text=(QA+OR+тест*+OR+Тест*+OR+SDET)+NOT+"Аналитик"&' \
                'no_magic=true&' \
                'order_by=publication_time&' \
                'area=1&specialization=1.117&' \
                'search_field=description&' \
                'search_field=name&' \
                'page=0'

req = requests.get((base_url + api_method + search_string).encode('utf-8'))
pages = req.json()["pages"]
proxies = {
    "http": "http://127.0.0.1:8888",
    "https": "http://127.0.0.1:8888",
}

# Get list of id from "vacancies" table
vac_id_list = []
sql = "SELECT id FROM vacancies"
try:
    cur.execute(sql)
    # print(type((cur.fetchall()[0])[0]))
    for i in cur.fetchall():
        vac_id_list.append(i[0])
except sqlite3.IntegrityError as err:
        print("Error: ", err)


# Make search request
def resp(n):
    return requests.get(base_url + api_method + search_string.replace("page=0", "page=" + str(n))
                        # , proxies=proxies
                        )


# Get list of vacancies from response and write id and data to "calendar" table.
def id_list(response):
    vac_list = response.json()["items"]
    items = []
    for i in vac_list:
        items.append(i["id"])
        sql = 'INSERT INTO calendar (id, data) VALUES (%d, "%s");' % (int(i["id"]), i["published_at"])
        print(sql)
        try:
            cur.executescript(sql)
        except sqlite3.IntegrityError as err:
            print("Error: ", err)

        # If vacancy is new, write description to "vacancies" table.
        if int(i["id"]) not in vac_id_list:
            # Get vacancies by ID
            r = requests.get(base_url + api_method + (i["id"])
                             # , proxies=proxies
                             )
            vac = r.json()
            del vac["branded_description"]  # Remove description in HTML format
            d = json.dumps(vac, indent=None, ensure_ascii=False, separators=(', ', ': ', ))
            d = re.sub(r"'", '', d)  # Remove apostrophes from JSON for SQL request safety
            d = unicodedata.normalize("NFKD", d)  # Return the normal form for the Unicode string
            sql_in = "INSERT INTO vacancies (id, json) VALUES (%d, '%s');" % (int(i["id"]), d)
            print(sql_in)
            try:
                cur.executescript(sql_in)
            except sqlite3.IntegrityError as error:
                print("Error: ", error)
    return items


for n in range(0, pages):
    s = id_list(resp(n))
    # print("Items on page: ", len(set(s)))

# Close database connection
con.close()
