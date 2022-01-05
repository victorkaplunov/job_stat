import sqlite3
import re
import statistics
from datetime import datetime, timedelta
import requests
import json
import unicodedata
from datetime import date

today = date.today()
first_day_of_current_year = date(date.today().year, 1, 1)


def years_tuple():
    return 2019, 2020, 2021, 2022


def reversed_years():
    years = years_tuple()
    return years[::-1]


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
    """ Get list of vacancies from response and write to "calendar" and "vacancies" tables."""
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
            # break

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
            published_at = json.loads(json_dump)['published_at']
            sql_in = f"""INSERT INTO vacancies (id, json, published_at)
                         VALUES ({int(i['id'])}, '{json_dump}', '{published_at}');"""
            try:
                cur.executescript(sql_in)
            except sqlite3.IntegrityError as error:
                print("Error: ", error)
    con.close()
    return items


def chart_with_category_filter(chart_name: str, param_list: list, cur, update, year):
    """ Function count a number of entries of some string from param_list in all vacancies. """
    for i in param_list:
        print(i[0], i[1])
        sql = f"""SELECT json FROM vacancies WHERE json LIKE '%%%{i[0]}%%' AND
                 published_at BETWEEN '{year}-01-01T00:00:00+0300' AND '{year}-12-31T11:59:59+0300';"""
        cur.execute(sql)
        vac = cur.fetchall()
        if update is True:
            sql = f"""
            UPDATE charts
            SET popularity = {len(vac)}
            WHERE charts.chart_name = '{chart_name}' AND charts.'data' = '{i[0]}'
            AND charts.'parent' = '{i[1]}' AND year = {year};"""
        else:
            sql = f"""INSERT INTO charts(chart_name, data, popularity, parent, year)
                  VALUES('{chart_name}', '{i[0]}', {len(vac)}, '{i[1]}', {year});"""
        try:
            cur.executescript(sql)
        except sqlite3.IntegrityError as error:
            print("Error: ", error)

    # Sum data for Py.test and Pytest and delete Py.test row
    sql = f"""SELECT popularity FROM charts WHERE data = 'py.test' AND year = {year};"""
    cur.execute(sql)
    py_test_popularity = cur.fetchall()
    if not py_test_popularity:
        py_test_popularity = 0
    else:
        print(py_test_popularity)
        py_test_popularity = py_test_popularity[0][0]
    print('py.test popularity: ', py_test_popularity)

    sql = f"""SELECT popularity FROM charts WHERE data = 'pytest' AND year = {year};"""
    cur.execute(sql)
    pytest_popularity = cur.fetchall()
    if not pytest_popularity:
        pytest_popularity = 0
    else:
        print(pytest_popularity)
        pytest_popularity = pytest_popularity[0][0]
    print('pytest popularity: ', pytest_popularity)

    sum_pop = py_test_popularity + pytest_popularity
    sql = f"""UPDATE charts SET popularity = "{sum_pop}" WHERE data = 'pytest' AND year = {year};"""
    cur.execute(sql)
    sql = f"""DELETE FROM charts WHERE data = 'py.test' AND year = {year};"""
    cur.execute(sql)

    # con.close()
    return


def stat_with_one_year(chart_name: str, param_list: list, year: int, cur, update=True):
    """ Function count a number of entries of some string from param_list in the JSON of all vacancies. """
    types = {i: 0 for i in param_list}  # Convert list to dictionary
    types = types.fromkeys(types, 0)  # Reset all values to zero
    for t in types:
        print(t)

        sql = f"""SELECT COUNT(*), json
                FROM vacancies
                WHERE json LIKE '%{t}%' AND
                published_at BETWEEN '{year}-01-01T00:00:00+0300' AND '{year}-12-31T11:59:59+0300';"""
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


def types_stat_with_year(types: dict, chart_name: str, key_name: str, all_vacancies, cur, year, update):

    # Count vacancies with given type in current year.
    for i in all_vacancies:
        body = json.loads(i[0])
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


def salary_to_db(experience, exchange_rate, conn, year):
    """Приводит зарплаты к общему виду (нетто, руб.) и записывает в отдельную таблицу для быстрого
    отображения на графике."""
    cur = conn.cursor()
    sql = f"""SELECT DISTINCT json FROM vacancies WHERE published_at
              BETWEEN '{year}-01-01T00:00:00+0300' AND '{year}-12-31T11:59:59+0300';"""
    cur.execute(sql)
    vacancies = cur.fetchall()

    # Отбираем вакансии с нужным опытом и собираем зарплаты в список
    salary_list = []
    for i in vacancies:
        if json.loads(i[0])['experience']['id'] == experience and json.loads(i[0])['salary'] is not None:
            salary_obj = json.loads(i[0])['salary']
            salary_obj.update({'id': json.loads(i[0])['id']})
            salary_obj.update({'published_at': json.loads(i[0])['published_at']})
            salary_obj.update({'alternate_url': json.loads(i[0])['alternate_url']})
            salary_obj.update({'experience': json.loads(i[0])['experience']['id']})
            salary_list.append(salary_obj)

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

    average_delta_for_closed_salary = 0

    try:
        average_delta_for_closed_salary = closed_salary_sum/len(closed_salary)
        print('average_delta_for_closed_salary: ', average_delta_for_closed_salary)
    except ZeroDivisionError:
        print('closed salary list is empty!')

    def write_to_vac_with_salary(item, salary):
        """ Записываем вакансии с указанной зарплатой в промежуточную таблицу vac_with_salary."""
        today = datetime.today()
        delta = timedelta(days=30)
        last_month = today - delta
        vac_date = datetime.strptime(item['published_at'][:-5], "%Y-%m-%dT%H:%M:%S")
        if (vac_date <= today) and (vac_date >= last_month):
            cur.execute(f"""INSERT INTO vac_with_salary(id, published_at, calc_salary, experience, url)
                            VALUES(?,?,?,?,?);""", (item['id'], str(item['published_at']),
                                                    salary, item['experience'], item['alternate_url']))
            conn.commit()

    # Считаем среднюю предполагаемую зарплату с учетом открытых диапазонов и НДФЛ.
    all_salary = []
    for i in salary_list:
        # "Чистая" зарплата
        if i['gross'] is False:
            # закрытый диапазон
            if (i['from'] is not None) and (i['to'] is not None):
                calc_salary = (i['from'] + (i['to'] - i['from'])/2) * exchange_rate[i['currency']]
                if calc_salary < 12792:   # Пишем в базу МРОТ, если расчетная ЗП меньше минимальной.
                    calc_salary = 12792
                all_salary.append(calc_salary)
                write_to_vac_with_salary(i, calc_salary)
            # открытый вверх
            elif i['to'] is None:
                calc_salary = i['from'] * exchange_rate[i['currency']] + average_delta_for_closed_salary/2
                if calc_salary < 12792:
                    calc_salary = 12792
                all_salary.append(calc_salary)
                write_to_vac_with_salary(i, calc_salary)
            # открытый вниз
            elif i['from'] is None:
                calc_salary = i['to'] * exchange_rate[i['currency']] - average_delta_for_closed_salary/2
                if calc_salary < 12792:
                    calc_salary = 12792
                all_salary.append(calc_salary)
                write_to_vac_with_salary(i, calc_salary)

        # "Грязная" зарплата
        elif i['gross'] is True:
            # закрытый диапазон
            if (i['from'] is not None) and (i['to'] is not None):
                gross_salary = (i['from'] + (i['to'] - i['from'])/2) * exchange_rate[i['currency']]
                calc_salary = gross_salary - gross_salary * 0.13
                if calc_salary < 12792:
                    calc_salary = 12792
                all_salary.append(calc_salary)
                write_to_vac_with_salary(i, calc_salary)
            # открытый вверх
            elif i['to'] is None:
                gross_salary = (i['from'] * exchange_rate[i['currency']] + average_delta_for_closed_salary/2)
                calc_salary = gross_salary - gross_salary * 0.13
                if calc_salary < 12792:
                    calc_salary = 12792
                all_salary.append(calc_salary)
                write_to_vac_with_salary(i, calc_salary)
            # открытый вниз
            elif i['from'] is None:
                gross_salary = (i['to'] * exchange_rate[i['currency']] - average_delta_for_closed_salary/2)
                calc_salary = gross_salary - gross_salary * 0.13
                if calc_salary < 12792:
                    calc_salary = 12792
                all_salary.append(calc_salary)
                write_to_vac_with_salary(i, calc_salary)

    salary_sum = 0
    print('salary qty: ', len(all_salary))
    if len(all_salary) == 0:
        return 0
    else:
        for i in all_salary:
            salary_sum += i
        median_salary = int(statistics.median(all_salary))
        print("median: ", median_salary)
        return median_salary
