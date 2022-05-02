import sqlite3
import re
import statistics
from datetime import datetime, timedelta, date
from operator import itemgetter
import requests
import json
import unicodedata


translation_dict = dict(noExperience="Без опыта", between1And3="От года до трех",
                        between3And6="От трех до шести лет", moreThan6="Более шести лет",
                        fullDay='Полный день', flexible='Гибкий график',
                        shift='Сменный график', remote='Удаленная работа',
                        full='Полная занятость', part='Частичная занятость',
                        project="Проектная работа", probation='Стажировка',
                        without_salary='Зарплата не указана', closed='Закрытый диапазон',
                        open_up='Зарплата от...', open_down='Зарплата до...')

today = date.today() - timedelta(days=6)
first_day_of_current_year = date(date.today().year, 1, 1)

MROT = 13890


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
            salary_obj.update({'description': json.loads(i[0])['description']})
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
        # today = datetime.today()
        # delta = timedelta(days=30)
        # last_month = today - delta
        # vac_date = datetime.strptime(item['published_at'][:-5], "%Y-%m-%dT%H:%M:%S")
        # if (vac_date <= today) and (vac_date >= last_month):
        cur.execute(f"""INSERT INTO vac_with_salary(id, published_at, calc_salary, experience, url, description)
                        VALUES(?,?,?,?,?,?);""", (item['id'], str(item['published_at']), salary,
                                                  item['experience'], item['alternate_url'], item['description']))
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


def salary_to_db_new(year, experience, exchange_rate, conn):
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
            # salary_obj.update({'from': json.loads(i[0])['salary']['from']})
            # salary_obj.update({'to': json.loads(i[0])['salary']['to']})
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

    def write_to_vac_with_salary(item, salary_from, salary_to, conn):
        """ Записываем вакансии с указанной зарплатой в промежуточную таблицу vac_with_salary."""
        today = datetime.today()
        delta = timedelta(days=30)
        last_month = today - delta
        vac_date = datetime.strptime(item['published_at'][:-5], "%Y-%m-%dT%H:%M:%S")
        cur = conn.cursor()
        if (vac_date <= today) and (vac_date >= last_month):
            sql = f"""INSERT INTO vac_with_salary(id, published_at, salary_from, salary_to, experience, url)
                            VALUES({item['id']},'{str(item['published_at'])}',
                            {salary_from}, {salary_to}, '{item['experience']}',
                            '{item['alternate_url']}');"""
            print(sql)
            cur.execute(sql)
            conn.commit()

    # Считаем среднюю предполагаемую зарплату с учетом открытых диапазонов и НДФЛ.
    all_salary = []
    for i in salary_list:
        # Если расчетная ЗП меньше минимальной, пропускаем значение.
        if (i['from'] or i['to']) < MROT:
            continue

        # "Чистая" зарплата
        if i['gross'] is False:
            # закрытый диапазон
            if (i['from'] is not None) and (i['to'] is not None):
                calc_salary = (i['from'] + (i['to'] - i['from'])/2) * exchange_rate[i['currency']]
                all_salary.append(calc_salary)
                salary_from = i['from'] * exchange_rate[i['currency']]
                salary_to = i['to'] * exchange_rate[i['currency']]
                write_to_vac_with_salary(i, salary_from, salary_to, conn)
            # открытый вверх
            elif i['to'] is None:
                calc_salary = i['from'] * exchange_rate[i['currency']] + average_delta_for_closed_salary/2
                all_salary.append(calc_salary)
                salary_from = i['from'] * exchange_rate[i['currency']]
                salary_to = salary_from + average_delta_for_closed_salary
                write_to_vac_with_salary(i, salary_from, salary_to, conn)
            # открытый вниз
            elif i['from'] is None:
                calc_salary = i['to'] * exchange_rate[i['currency']] - average_delta_for_closed_salary/2
                all_salary.append(calc_salary)
                salary_from = salary_to + average_delta_for_closed_salary
                salary_to = i['to'] * exchange_rate[i['currency']]
                write_to_vac_with_salary(i, salary_from, salary_to, conn)

        # "Грязная" зарплата
        elif i['gross'] is True:
            # закрытый диапазон
            if (i['from'] is not None) and (i['to'] is not None):
                gross_salary = (i['from'] + (i['to'] - i['from'])/2) * exchange_rate[i['currency']]
                calc_salary = gross_salary - gross_salary * 0.13
                all_salary.append(calc_salary)
                salary_from = i['from'] * exchange_rate[i['currency']]
                clear_salary_from = salary_from - salary_from * 0.13
                salary_to = i['to'] * exchange_rate[i['currency']]
                clear_salary_to = salary_to - salary_to * 0.13
                write_to_vac_with_salary(i, clear_salary_from, clear_salary_to, conn)
            # открытый вверх
            elif i['to'] is None:
                gross_salary = (i['from'] * exchange_rate[i['currency']] + average_delta_for_closed_salary/2)
                calc_salary = gross_salary - gross_salary * 0.13
                all_salary.append(calc_salary)
                salary_from = i['from'] * exchange_rate[i['currency']]
                clear_salary_from = salary_from - salary_from * 0.13
                clear_salary_to = clear_salary_from + average_delta_for_closed_salary
                write_to_vac_with_salary(i, clear_salary_from, clear_salary_to, conn)
            # открытый вниз
            elif i['from'] is None:
                gross_salary = (i['to'] * exchange_rate[i['currency']] - average_delta_for_closed_salary/2)
                calc_salary = gross_salary - gross_salary * 0.13
                all_salary.append(calc_salary)
                salary_to = i['to'] * exchange_rate[i['currency']]
                clear_salary_to = salary_to - salary_to * 0.13
                clear_salary_from = clear_salary_to + average_delta_for_closed_salary
                write_to_vac_with_salary(i, clear_salary_from, clear_salary_to, conn)

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


def get_vacancy_count_by_year(cursor):
    month_tuples = (('01', 'январь', '31'), ('02', 'февраль', "29"), ('03', 'март', '31'),
                    ('04', 'апрель', '30'), ('05', 'май', '31'), ('06', 'июнь', '30'),
                    ('07', 'июль', '31'), ('08', 'август', '31'), ('09', 'сентябрь', '30'),
                    ('10', 'октябрь', '31'), ('11', 'ноябрь', '30'), ('12', 'декабрь', '31'))

    year_tuple = years_tuple()
    head_time_series = [['Месяц']]
    output_list = []
    for y in year_tuple:
        head_time_series[0].append(str(y))
        for n, month in enumerate(month_tuples):
            # Запрашиваем количество вакансий за месяц
            sql = f'''
            SELECT DISTINCT id FROM calendar WHERE data 
            BETWEEN "{str(y)}-{month[0]}-01T00:00:00+03:00" and "{str(y)}-{month[0]}-{month[2]}T23:59:59+03:00";'''
            cursor.execute(sql)
            vacancies_tuple = (cursor.fetchall())
            if str(y) == '2019':
                # Данные за февраль неполные, поэтому вместо них пишем ноль
                if month[1] == 'февраль':
                    output_list.append([month[1], 0])
                else:
                    output_list.append([month[1], len(vacancies_tuple)])
            else:
                output_list[n].append(len(vacancies_tuple))
    output_list = head_time_series + output_list
    return output_list


def get_vacancy_count_week_by_week(cursor):
    yesterday = today - timedelta(days=1)
    print(yesterday)
    start_weekday_num = yesterday.weekday()
    print('start_weekday_num', start_weekday_num)
    weekday_name = ['пн.', 'вт.', 'ср.', 'чт', 'пт.', 'сб.', 'вс.']
    weekday_list = []
    for i in range(0, 7):
        print(start_weekday_num)
        weekday_list.append(weekday_name[start_weekday_num])
        if start_weekday_num < 6:
            start_weekday_num += 1
        else:
            start_weekday_num = 0
    print(weekday_list)
    output_list = [['Неделя', 'current week', 'last week', 'two weeks ago', 'three weeks ago']]
    for count, value in enumerate(weekday_list):
        print('count', count)
        day_list = [value]
        print(value)
        for n in range(0, 28, 7):
            day = yesterday - timedelta(days=n-count)
            sql = f'''SELECT COUNT(DISTINCT id) FROM calendar WHERE data
                  BETWEEN "{day}T00:00:00+03:00" and "{day}T23:59:59+03:00";'''
            cursor.execute(sql)
            vacancies_tuple = (cursor.fetchall())
            print(day, vacancies_tuple[0][0])
            day_list.append(vacancies_tuple[0][0])
        output_list.append(day_list)
    return output_list


def get_key_skills_data(chart_name, cursor):
    """ Get data from 'charts' DB table for chart drawing"""
    if chart_name == 'frameworks':
        request = f'SELECT data, popularity, parent FROM charts WHERE chart_name="{chart_name}";'

    else:
        request = f'SELECT data, popularity FROM charts WHERE chart_name="{chart_name}";'
    cursor.execute(request)
    statistics_data = cursor.fetchall()
    # Convert list of tuples to list of lists
    data_list = []
    for i in statistics_data:
        data_list.append(list(i))
    return data_list


def get_salary_data_with_year(cursor):
    experience_ranges = dict(noExperience=[], between1And3=[], between3And6=[], moreThan6=[])

    data = [['Range']]
    for year in years_tuple():
        data[0].append(str(year))  # Добавляем года в колонку легенды.
        request = f'SELECT data, popularity ' \
                  f'FROM charts ' \
                  f'WHERE chart_name="salary" AND year={str(year)};'
        cursor.execute(request)
        statistics_data = cursor.fetchall()
        for i in statistics_data:
            experience_ranges[i[0]].append(i[1])
    for i in experience_ranges:
        rang_data = experience_ranges[i]
        rang_data.insert(0, translation_dict[i])
        data.append(rang_data)
    return data


def get_data_with_year(cursor, year, chart_name, sort=True):
    request = f"""
    SELECT data, popularity FROM charts WHERE chart_name='{chart_name}' AND year='{year}';
    """
    head = [['Type', 'Popularity']]
    cursor.execute(request)
    statistics_data = cursor.fetchall()
    data_list = []
    for i in statistics_data:
        if chart_name in ['schedule_type', 'employment_type', 'experience', 'with_salary']:
            row = [translation_dict[i[0]], i[1]]
            data_list.append(row)
        else:
            data_list.append(list(i))
    data_list.sort(reverse=sort
                   , key=itemgetter(1))
    return head + data_list


def get_vac_with_salary(cursor, exp):
    today = date.today()
    delta = timedelta(days=30)
    last_month = today - delta
    sql = f"SELECT * FROM vac_with_salary WHERE experience = '{exp}' AND" \
          f" published_at BETWEEN '{last_month}' AND '{today}' ORDER BY published_at ASC;"
    cursor.execute(sql)
    response = cursor.fetchall()
    chart_data_list = []
    for i in response:
        template = f"[new Date('{i[1]}'),{i[2]},'<a href=\"{i[4]}\">{int(i[2])}</a>'],\n"
        chart_data_list.append(template)
    chart_data = ''.join(chart_data_list)
    return chart_data


def get_frameworks_data(cursor, year, chart_name):
    head = [['Framework', 'Popularity', 'Language']]
    request = f"""
        SELECT data, popularity, parent FROM charts WHERE chart_name='{chart_name}' AND year='{year}';
            """
    cursor.execute(request)
    statistics_data = cursor.fetchall()
    data_list = []
    for i in statistics_data:
        data_list.append(list(i))
    data_list.sort(reverse=True, key=itemgetter(1))
    return head + data_list


def render_framework_charts(title, chart, cursor):
    charts = ''
    divs = ''
    for year in reversed_years():
        data = get_frameworks_data(cursor, year, chart)
        charts = charts + f"""
        google.charts.setOnLoadCallback(Chart{year});
        function Chart{year}() {{
        var data = google.visualization.arrayToDataTable({data});
        
        var dashboard{year} = new google.visualization.Dashboard(
            document.getElementById('dashboard{year}_div'));
            
        var CategoryFilter{year} = new google.visualization.ControlWrapper({{
          'controlType': 'CategoryFilter',
          'containerId': 'filter_div{year}',
          'options': {{
            'filterColumnLabel': 'Language',
            'ui': {{
                'caption': 'Выберите язык',
                'selectedValuesLayout': 'belowStacked',
                'labelStacking': 'vertical',
                'label': 'Языки программирования',
                'labelStacking': 'vertical'
            }},
            'useFormattedValue': true
          }}
        }});
        
        // Create a pie chart, passing some options
        var pieChart{year} = new google.visualization.ChartWrapper({{
          'chartType': 'PieChart',
          'containerId': 'chart_div{year}',
          'options': {{
            'title':'{title}',
            chartArea:{{width:'100%',height:'75%'}},
            'height':500,
            'pieSliceText': 'value',
            'legend': 'right'
          }}
        }});

        dashboard{year}.bind(CategoryFilter{year}, pieChart{year});
        dashboard{year}.draw(data);
      }}"""
        # Генерация разделов в которые будут вставляться графики.
        divs = divs + f'''
        <div id="chart_div{year}"></div>
        <div id="filter_div{year}"></div>'''
    return charts, divs


def render_pie_charts(years, title, chart, cursor):
    charts = ''
    divs = ''
    for year in years:
        data = get_data_with_year(cursor, year, chart)
        # Генерация функция JavaScript для отдельных графиков
        charts = charts + f'''

            google.charts.setOnLoadCallback(drawScheduleTypeChart{year});
            function drawScheduleTypeChart{year}() {{
            var data = google.visualization.arrayToDataTable({data});
            var options = {{'title':'{title} в {year} году.',
            chartArea:{{width:'90%',height:'80%'}},
            pieSliceTextStyle: {{fontSize: 11}}
            }};
            var chart = new google.visualization.PieChart(document.getElementById('chart_for_{year}'));
            chart.draw(data, options);
            }}'''
        # Генерация разделов в которые будут вставляться графики.
        divs = divs + f'<div id="chart_for_{year}" style="height: 300px;"></div>'
    return charts, divs


def get_salary_by_category_data(cursor):

    head = [['Language', 'Median salary']]

    request = f"SELECT DISTINCT data FROM charts WHERE chart_name='languages';"
    cursor.execute(request)
    languages = cursor.fetchall()
    today = date.today()
    last_year = today - timedelta(days=36)
    data_list = []
    salary_list = []
    for language in languages:
        request = f"""
        SELECT calc_salary FROM vac_with_salary 
        WHERE description LIKE "%{language[0]}%"
        ORDER BY published_at ASC;
        """
        cursor.execute(request)
        salary = cursor.fetchall()
        # print(salary)
        print(language)
        for i in salary:
            salary_list.append(i[0])
        try:
            median = statistics.median(salary_list)
        except statistics.StatisticsError:
            continue

        data_list.append([language[0], median])
        salary_list = []
    return head + data_list


def render_salary_by_category_charts(title, cursor):
    charts = ''
    divs = ''
    year = 'last'

    data = get_salary_by_category_data(cursor)
    charts = charts + f"""
    google.charts.setOnLoadCallback(Chart{year});
    function Chart{year}() {{
    var data = google.visualization.arrayToDataTable({data});

    var dashboard{year} = new google.visualization.Dashboard(
        document.getElementById('dashboard{year}_div'));

    var CategoryFilter{year} = new google.visualization.ControlWrapper({{
      'controlType': 'CategoryFilter',
      'containerId': 'filter_div{year}',
      'options': {{
        'filterColumnLabel': 'Language',
        'ui': {{
            'caption': 'Выберите язык',
            'selectedValuesLayout': 'belowStacked',
            'labelStacking': 'vertical',
            'label': 'Языки программирования',
            'labelStacking': 'vertical'
        }},
        'useFormattedValue': true
      }}
    }});

    // Create a column chart, passing some options
    var ColumnChart{year} = new google.visualization.ChartWrapper({{
      'chartType': 'ColumnChart',
      'containerId': 'chart_div{year}',
      'options': {{
        'title':'{title}',
        chartArea:{{width:'100%',height:'75%'}},
        'height':500,
        'pieSliceText': 'value',
        'legend': 'right'
    
    
    
      }}
    }});

    dashboard{year}.bind(CategoryFilter{year}, ColumnChart{year});
    dashboard{year}.draw(data);
  }}"""
    # Генерация разделов в которые будут вставляться графики.
    divs = divs + f'''
    <div id="chart_div{year}"></div>
    <div id="filter_div{year}"></div>'''
    return charts, divs