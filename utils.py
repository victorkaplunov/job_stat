import sqlite3
import re
import statistics
import requests
import json
import unicodedata


def years_tuple():
    return 2019, 2020, 2021


def vac_id_list():
    """Get list of id from "vacancies" table"""
    con = sqlite3.connect("testdb.db")  # Open database
    cur = con.cursor()
    id_list = []
    sql = "SELECT id FROM vacancies"
    try:
        cur.execute(sql)
        # print(type((cur.fetchall()[0])[0]))
        for n in cur.fetchall():
            id_list.append(n[0])
    except sqlite3.IntegrityError as err:
        print("Error: ", err)
    con.close()
    return id_list


def id_list(response, base_url):
    """ Get list of vacancies from response and write "calendar" and "vacancies" tables."""
    con = sqlite3.connect("testdb.db")  # Open database
    cur = con.cursor()
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
    con.close()
    return items


def chart_with_category_filter(chart_name: str, param_list: list, cur, update):
    """ Function count a number of entries of some string from param_list in all vacancies. """
    for i in param_list:
        print(i[0], i[1])
        sql = "SELECT json FROM vacancies WHERE json LIKE '%%%s%%';" % i[0]
        cur.execute(sql)
        vac = cur.fetchall()
        if update is True:
            sql = f"""
            UPDATE charts
            SET popularity = {len(vac)}
            WHERE charts.chart_name = '{chart_name}' AND charts.'data' = '{i[0]}'
            AND charts.'parent' = '{i[1]}';"""
        else:
            sql = f"""INSERT INTO charts(chart_name, data, popularity, parent)
                  VALUES('{chart_name}', '{i[0]}', {len(vac)}, '{i[1]}');"""
        try:
            cur.executescript(sql)
        except sqlite3.IntegrityError as error:
            print("Error: ", error)

    # Sum data for Py.test and Pytest and delete Py.test row
    sql = """SELECT popularity FROM charts WHERE data = 'py.test';"""
    cur.execute(sql)
    py_test_popularity = cur.fetchall()
    if py_test_popularity == []:
        py_test_popularity = 0
    else:
        print(py_test_popularity)
        py_test_popularity = py_test_popularity[0][0]

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

    # con.close()
    return


def stat_with_year(chart_name: str, param_list: list, years: tuple, cur):
    """ Function count a number of entries of some string from param_list in the JSON of all vacancies. """
    types = {i: 0 for i in param_list}  # Convert list to dictionary
    for y in years:
        types = types.fromkeys(types, 0)  # Reset all values to zero
        for t in types:
            # Count vacancies with given type in current year.
            sql = f"""SELECT COUNT(*),v.json
                    FROM vacancies v
                    INNER JOIN calendar c
                    ON v.id = c.id
                    WHERE c.data LIKE "{y}%" AND json LIKE '%{t}%';"""
            cur.execute(sql)
            type_count = cur.fetchall()
            sql = f'INSERT INTO charts(chart_name, data, popularity, year) ' \
                  f'VALUES("{chart_name}", "{t}", {type_count[0][0]}, {str(y)});'
            cur.executescript(sql)
    return


def stat_with_one_year(chart_name: str, param_list: list, year: int, cur, update=True):
    """ Function count a number of entries of some string from param_list in the JSON of all vacancies. """
    types = {i: 0 for i in param_list}  # Convert list to dictionary
    types = types.fromkeys(types, 0)  # Reset all values to zero
    for t in types:
        print(t)
        sql = f"""SELECT COUNT(*), json
                FROM temp_table
                WHERE json LIKE '%{t}%';"""
        cur.execute(sql)
        type_count = cur.fetchall()[0][0]
        if update is True:
            sql = f"""
            UPDATE charts
            SET popularity = {type_count}
            WHERE charts.chart_name = '{chart_name}' AND charts.'data' = '{t}'
            AND charts.'year' = '{year}';"""
        else:
            sql = f"""INSERT INTO charts(chart_name, data, popularity, year)
                  VALUES('{chart_name}', '{t}', {type_count}, {str(year)});"""
        cur.executescript(sql)
    return


def wright_statistic_to_db(chart_name: str, param_list: list, cur):
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


def types_stat_with_year(types: dict, chart_name: str, key_name: str, all_vacancies, cur, year, update):

    # Count vacancies with given type in current year.
    for i in all_vacancies:
        # print(i[0])
        body = json.loads(i[0])
        # print((body[key_name]['id']))
        types[(body[key_name]['id'])] += 1
    # Write ready data to DB.
    print(types)
    for i in types:
        if update is True:
            sql = f"""UPDATE charts
                      SET popularity = {types[i]}
                      WHERE charts.chart_name = '{chart_name}' AND charts.'data' = '{i}'
                      AND charts.'year' = '{year}';"""
        else:
            sql = f"""INSERT INTO charts(chart_name, data, popularity, year)
                        VALUES('{chart_name}', '{i}', {types[i]}, {str(year)});"""
        cur.execute(sql)
    return


def vacancy_with_salary(types: dict, chart_name: str, year, all_vacancies, cur, update):
    # Count types of schedule in all vacancies.
    types = types.fromkeys(types, 0)  # set all values to zero
    # Count vacancies with given type in current year.
    for n in all_vacancies:
        body = json.loads((n[0]))

        if body['salary'] is None:
            types['without_salary'] += 1
        else:
            if body['salary']['to'] is None:
                types['open_up'] += 1
            elif body['salary']['from'] is None:
                types['open_down'] += 1
            else:
                types['closed'] += 1

    # Write ready data to DB.
    print(types)
    for n in types:
        if update is True:
            sql = f"""UPDATE charts
                      SET popularity = {types[n]}
                      WHERE charts.chart_name = '{chart_name}' AND charts.'data' = '{n}'
                      AND charts.'year' = '{year}';"""
        else:
            sql = f"""INSERT INTO charts(chart_name, data, popularity, year)
                        VALUES('{chart_name}', '{n}', {types[n]}, '{year}');"""
        cur.execute(sql)
    return


def salary_to_db(year, experience, exchange_rate, cur):
    # Загружаем вакансии из БД
    sql = f"""SELECT v.json
    FROM vacancies v
    INNER JOIN calendar c
    ON v.id = c.id
    WHERE c.data LIKE "{year}%";"""
    cur.execute(sql)
    vac = cur.fetchall()

    # Отбираем вакансии с нужным опытом и собираем зарплаты в список
    salary_list = []
    for i in vac:
        if json.loads(i[0])['experience']['id'] == experience and json.loads(i[0])['salary'] is not None:
            salary_obj = json.loads(i[0])['salary']
            salary_obj.update({'id': json.loads(i[0])['id']})
            salary_list.append(salary_obj)

    # Подсчет зарплат с "чистой" и "грязной" зарплатой
    net_list = []
    gross_list = []
    for i in salary_list:
        if i['gross'] is True:
            gross_list.append(i)
        else:
            net_list.append(i)
    # print('net: ', len(net_list))
    # print('gross: ', len(gross_list))

    # Считаем средний разброс для вакансий с закрытым диапазоном
    closed_salary = []
    for i in salary_list:
        if i['from'] is None or i['to'] is None:
            pass
        else:
            closed_salary.append((i['to'] - i['from'])*exchange_rate[i['currency']])

    closed_salary_sum = 0
    for i in closed_salary:
        closed_salary_sum += i

    average_delta_for_closed_salary = closed_salary_sum/len(closed_salary)

    # Считаем среднюю предполагаемую зарплату с учетом открытых диапазонов и НДФЛ.
    all_salary = []
    for i in salary_list:
        # "Чистая" зарплата
        if i['gross'] is False:
            # закрытый диапазон
            if (i['from'] is not None) and (i['to'] is not None):
                all_salary.append((i['to'] + (i['to'] - i['from'])/2) * exchange_rate[i['currency']])
            # открытый вверх
            elif i['to'] is None:
                all_salary.append(i['from'] * exchange_rate[i['currency']] + average_delta_for_closed_salary/2)
            # открытый вниз
            elif i['from'] is None:
                all_salary.append(i['to'] * exchange_rate[i['currency']] - average_delta_for_closed_salary/2)

        # "Грязная" зарплата
        elif i['gross'] is True:
            # закрытый диапазон
            if (i['from'] is not None) and (i['to'] is not None):
                gross_salary = (i['to'] + (i['to'] - i['from']) / 2) * exchange_rate[i['currency']]
                all_salary.append(gross_salary - gross_salary * 0.13)
            # открытый вверх
            elif i['to'] is None:
                gross_salary = (i['from'] * exchange_rate[i['currency']] + average_delta_for_closed_salary / 2)
                all_salary.append(gross_salary - gross_salary * 0.13)
            # открытый вниз
            elif i['from'] is None:
                gross_salary = (i['to'] * exchange_rate[i['currency']] - average_delta_for_closed_salary / 2)
                all_salary.append(gross_salary - gross_salary * 0.13)

    salary_sum = 0
    for i in all_salary:
        salary_sum += i

    average_salary = salary_sum/len(all_salary)
    print("average_salary: ", average_salary)
    # Rounding salary to roubles
    median_salary = int(statistics.median(all_salary))
    print("median: ", median_salary)
    return median_salary
