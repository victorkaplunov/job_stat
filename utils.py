import sqlite3
import re
import requests
import json
import unicodedata

con = sqlite3.connect("testdb.db")  # Open database
cur = con.cursor()


def vac_id_list():
    """Get list of id from "vacancies" table"""
    id_list = []
    sql = "SELECT id FROM vacancies"
    try:
        cur.execute(sql)
        # print(type((cur.fetchall()[0])[0]))
        for n in cur.fetchall():
            id_list.append(n[0])
    except sqlite3.IntegrityError as err:
        print("Error: ", err)
    return id_list


def id_list(response, base_url):
    """ Get list of vacancies from response and write "calendar" and "vacancies" tables."""
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
            break

        # If vacancy is new, write description to "vacancies" table.
        if int(i["id"]) not in vac_id_list():
            # Get vacancies by ID
            r = requests.get(base_url + (i["id"])
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


def chart_with_category_filter(chart_name: str, param_list: list):
    """ Function count a number of entries of some string from param_list in all vacancies. """
    for i in param_list:
        print(i[0], i[1])
        sql = "SELECT json FROM vacancies WHERE json LIKE '%%%s%%';" % i[0]
        cur.execute(sql)
        vac = cur.fetchall()
        sql = 'INSERT INTO charts(chart_name, data, popularity, parent) VALUES("%s", "%s", %i, "%s");' \
                                                                    % (chart_name, i[0], len(vac), i[1])
        print(sql)
        try:
            cur.executescript(sql)
        except sqlite3.IntegrityError as error:
            print("Error: ", error)

    # Sum data for Py.test and Pytest and delete Py.test row
    sql = """SELECT popularity FROM charts WHERE data = 'py.test';"""
    cur.execute(sql)
    py_test_popularity = cur.fetchall()[0][0]
    print('py_test_popularity: ', py_test_popularity)
    sql = """SELECT popularity FROM charts WHERE data = 'pytest';"""
    cur.execute(sql)
    pytest_popularity = cur.fetchall()[0][0]
    print('pytest_popularity: ', pytest_popularity)
    sql = """UPDATE charts SET popularity = "%i" WHERE data = 'pytest';""" \
                                    % (py_test_popularity + pytest_popularity)
    cur.execute(sql)
    sql = """DELETE FROM charts WHERE data = 'py.test';"""
    cur.execute(sql)
    return


def stat_with_year(chart_name: str, param_list: list, years: tuple, all_vacancies):
    """ Function count a number of entries of some string from param_list in the JSON of all vacancies. """
    types = {i: 0 for i in param_list}  # Convert list to dictionary
    for y in years:
        types = types.fromkeys(types, 0)  # Reset all values to zero
        # Count vacancies with given type in current year.
        for n in all_vacancies:
            for t in types:
                body = json.loads((n[1]))
                if (f"{str(y-1)}-12-31T23:59:59+0300" < body['created_at']) and \
                        (body['created_at'] < f"{str(y+1)}-01-01T00:00:00+0300") and \
                        (t in body['description']):
                    types[t] += 1
                else:
                    continue
        # Write ready data to DB.
        print(types)
        for n in types:
            sql = f'INSERT INTO charts(chart_name, data, popularity, year) ' \
                  f'VALUES("{chart_name}", "{n}", {types[n]}, {str(y)});'
            cur.executescript(sql)
    return


def wright_statistic_to_db(chart_name: str, param_list: list):
    """ Function count a number of entries of some string from param_list in the JSON of all vacancies. """
    for i in param_list:
        sql = "SELECT json FROM vacancies WHERE json LIKE '%%%s%%';" % i
        cur.execute(sql)
        vac = cur.fetchall()
        sql = 'INSERT INTO charts(chart_name, data, popularity) VALUES("%s", "%s",%i);' % (chart_name, i, len(vac))
        try:
            cur.executescript(sql)
        except sqlite3.IntegrityError as error:
            print("Error: ", error)

        sql = 'UPDATE charts SET popularity = "%i" WHERE data = "%s";' % (len(vac), i)
        print(sql)
        cur.executescript(sql)
    return


def types_stat_with_year(types: dict, chart_name: str, key_name: str, years: tuple, all_vacancies):
    # Count types of schedule in all vacancies.
    for y in years:
        types = types.fromkeys(types, 0)  # set all values to zero
        # Count vacancies with given type in current year.
        for n in all_vacancies:
            body = json.loads((n[1]))
            if (f"{str(y-1)}-12-31T23:59:59+0300" < body['created_at']) and \
                    (body['created_at'] < f"{str(y+1)}-01-01T00:00:00+0300"):
                types[(body[key_name]['id'])] += 1
            else:
                continue
        # Write ready data to DB.
        print(types)
        for n in types:
            sql = f'INSERT INTO charts(chart_name, data, popularity, year) ' \
                  f'VALUES("{chart_name}", "{n}", {types[n]}, {str(y)});'
            cur.executescript(sql)
    return


def vacancy_with_salary(types: dict, chart_name: str, years: tuple, all_vacancies):
    # Count types of schedule in all vacancies.
    for y in years:
        types = types.fromkeys(types, 0)  # set all values to zero
        # Count vacancies with given type in current year.
        for n in all_vacancies:
            body = json.loads((n[1]))
            if (f"{str(y-1)}-12-31T23:59:59+0300" < body['created_at']) and \
                    (body['created_at'] < f"{str(y+1)}-01-01T00:00:00+0300"):
                if body['salary'] is None:
                    types['without_salary'] += 1
                else:
                    if body['salary']['to'] is None:
                        types['open_up'] += 1
                    elif body['salary']['from'] is None:
                        types['open_down'] += 1
                    else:
                        types['closed'] += 1

            else:
                continue
        # Write ready data to DB.
        print(types)
        for n in types:
            sql = f'INSERT INTO charts(chart_name, data, popularity, year) ' \
                  f'VALUES("{chart_name}", "{n}", {types[n]}, {str(y)});'
            cur.executescript(sql)
    return

