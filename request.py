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
search_string = u'?text=(QA+OR+тест*+OR+Тест*+OR+SDET+OR+test*)' \
                u'+NOT+%22%D0%90%D0%BD%D0%B0%D0%BB%D0%B8%D1%82%D0%B8%D0%BA%22&' \
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
        # print(sql)
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
            json_dump = json.dumps(vac, indent=None, ensure_ascii=False, separators=(', ', ': ', ))
            json_dump = re.sub(r"'", '', json_dump)  # Remove apostrophes from JSON for SQL request safety
            json_dump = re.sub(r"’", '', json_dump)  # Remove apostrophes from JSON for SQL request safety
            json_dump = re.sub(r"&#39;", '', json_dump)  # Remove apostrophes from JSON for SQL request safety, again
            json_dump = unicodedata.normalize("NFKD", json_dump)  # Return the normal form for the Unicode string

            cleaner = re.compile('<.*?>')  # Remove HTML tags
            json_dump = re.sub(cleaner, '', json_dump)

            sql_in = "INSERT INTO vacancies (id, json) VALUES (%d, '%s');" % (int(i["id"]), json_dump)
            try:
                cur.executescript(sql_in)
            except sqlite3.IntegrityError as error:
                print("Error: ", error)
    return items


for n in range(0, pages):
    s = id_list(resp(n))
    print("Items on page: ", len(set(s)))

# Wright languages statistics data to database
languages_list = ['Java', 'Python', 'JavaScript', 'C#', "PHP", 'C++', 'Ruby', 'Groovy']
for i in languages_list:
    sql = "SELECT json FROM vacancies WHERE json LIKE '%%%s%%';" % i
    cur.execute(sql)
    vac = cur.fetchall()
    sql = 'INSERT INTO languages(language_name, popularity) VALUES("%s", %i);' % (i, len(vac))
    try:
        cur.executescript(sql)
    except sqlite3.IntegrityError as error:
        print("Error: ", error)

    sql = 'UPDATE languages SET popularity = "%i" WHERE language_name = "%s";' % (len(vac), i)
    cur.executescript(sql)


# Wright test frameworks statistics data to database
frameworks_list = ['Pytest', 'Py.test', 'Unittest', 'Nose',
                   'jUnit', 'TestNG',
                   'PHPUnit', 'Codeception',
                   'RSpec',
                   'Spock',
                   'Mocha', 'Serenity', 'Jest', 'Jasmine', 'Nightwatch', 'Protractor', 'Karma',
                   'Robot Framework']

for i in frameworks_list:
    sql = 'SELECT json FROM vacancies WHERE json  LIKE "%%%s%%";' % i
    cur.execute(sql)
    vac = cur.fetchall()

    sql = 'INSERT INTO frameworks(framework_name, popularity) VALUES("%s", %i);' % (i, len(vac))
    try:
        cur.executescript(sql)
    except sqlite3.IntegrityError as error:
        print("Error: ", error)

    sql = 'UPDATE frameworks SET popularity = "%i" WHERE framework_name = "%s";' % (len(vac), i)
    cur.executescript(sql)

# Close database connection
con.close()
