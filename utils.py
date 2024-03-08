import sqlite3
import re
import statistics
from datetime import datetime, timedelta, date
from calendar import isleap
from operator import itemgetter
import json

import sqlalchemy
import unicodedata
import locale
from typing import NoReturn, Sequence, Any

import requests
from sqlalchemy import RowMapping, Row

from db_client import Database
from config import ConfigObj

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
db = Database()
config = ConfigObj()
first_day_of_current_year = date(date.today().year, 1, 1)


def reversed_years():
    return config.YEARS[::-1]


def write_vacancies(response: requests, base_url: str) -> list[int]:
    """
    Get list of vacancies from response and write to "calendar" and "vacancies" tables.
    Return list of vacancies ID.
    """

    vac_list = response.json()["items"]
    items = []
    for i in vac_list:
        db.insert_vac_id_to_calendar(vac_id=int(i["id"]), published_at=i["published_at"])

        # If vacancy is new, write description to "vacancies" table.
        if int(i["id"]) not in db.get_all_vacancies_ids():
            # Get vacancies by ID
            r = requests.get(base_url + (i["id"]))
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
            db.insert_vacancy(vac_id=i['id'], json=json_dump, published_at=published_at)
    return items


def chart_with_category_filter(chart_name: str, param_list: list, cur, update, year) -> NoReturn:
    """ Function count a number of entries of some string from param_list in all vacancies. """
    for i in param_list:
        vac_qty = db.count_vacancy_by_search_phrase_and_year(search_phrase=i[0], year=year)
        if update is True:
            if i[0] == 'py.test':
                db.update_charts(chart_name=chart_name, parent=i[1],
                                 popularity=db.get_pytest_data(year=year) + vac_qty,
                                 year=year, data='pytest')
            else:
                db.update_charts(chart_name=chart_name, parent=i[1], popularity=vac_qty,
                                 year=year, data=i[0])
        else:
            if i[0] == 'py.test':
                db.update_charts(chart_name=chart_name, parent=i[1],
                                 popularity=db.get_pytest_data(year=year) + vac_qty,
                                 year=year, data='pytest')
            else:
                db.insert_in_charts(chart_name=chart_name, data=i[0],
                                    popularity=vac_qty,
                                    parent=i[1], year=year)
    return


def count_per_year(chart_name: str, categories: list, year: int, cur, update=True) -> NoReturn:
    """ Function count a number of entries of some string from param_list
     in the JSON of all vacancies. """
    categories_dict = {i: 0 for i in categories}  # Convert list to dictionary
    categories_dict = categories_dict.fromkeys(categories_dict, 0)  # Reset all values to zero
    for param_type in categories_dict:
        print(param_type)
        type_count = db.count_vacancy_by_search_phrase_and_year(search_phrase=param_type, year=year)
        if update is True:
            sql = f"""
            UPDATE charts
            SET popularity = {type_count}
            WHERE charts.chart_name = '{chart_name}' AND charts.'data' = '{param_type}'
            AND charts.'year' = '{year}';"""
        else:
            sql = f"""INSERT INTO charts(chart_name, data, popularity, year)
                  VALUES('{chart_name}', '{param_type}', {type_count}, {str(year)});"""
        cur.executescript(sql)
    return


def count_types_per_year(types: dict, chart_name: str, key_name: str,
                         all_vacancies:  Sequence[Row[Any] | RowMapping],
                         cur, year: int, update: bool) -> NoReturn:

    # Count vacancies with given type in current year.
    for i in all_vacancies:
        body = json.loads(i)
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


def count_schedule_types(types: dict, chart_name: str, year: int,
                         all_vacancies:  Sequence[Row[Any] | RowMapping],
                         cur, conn, update: bool) -> NoReturn:
    # Count types of schedule in all vacancies.
    types = types.fromkeys(types, 0)  # set all values to zero
    # Count vacancies with given type in given year.
    for n in all_vacancies:
        body = json.loads(n)

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
        conn.commit()
    return


def count_salary_median(experience: str, exchange_rate: float, conn, year: int):
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


def get_vacancies_qty_by_day_of_week() -> list:
    today = date.today() - timedelta(days=6)  #???
    yesterday = today - timedelta(days=1)
    start_weekday_num = yesterday.weekday()
    weekday_name = ['пн.', 'вт.', 'ср.', 'чт', 'пт.', 'сб.', 'вс.']
    weekday_list = []
    for i in range(0, 7):
        weekday_list.append(weekday_name[start_weekday_num])
        if start_weekday_num < 6:
            start_weekday_num += 1
        else:
            start_weekday_num = 0
    output_list = [['Неделя за неделей', 'текущая неделя', 'прошлая неделя', 'две недели назад', 'три недели назад']]
    for count, value in enumerate(weekday_list):
        day_list = [value]
        for n in range(0, 28, 7):
            day = yesterday - timedelta(days=n-count)
            day_list.append(db.get_vacancy_qty_by_day(day=day))
        output_list.append(day_list)
    return output_list


def get_vacancies_qty_week_by_week() -> list[list[str | int | dict]]:
    delta = date.today() - first_day_of_current_year
    day = first_day_of_current_year
    weeks_dictionary = dict(Неделя="количество вакансий")
    for i in range(0, delta.days):
        # ToDo: Делать запросы по неделям, а не дням.
        vacancy_qty = db.get_vacancy_qty_by_day(day)
        week_number = str(day.isocalendar()[1])
        if week_number in weeks_dictionary:
            weeks_dictionary[week_number] += vacancy_qty
        else:
            weeks_dictionary[week_number] = vacancy_qty
        day = day + timedelta(days=1)
    # Convert dictionary to list of lists
    output_list = []
    for key, value in weeks_dictionary.items():
        output_list.append([key, value])

    # Add 'tooltip' column to chart
    output_list[0].append(json.loads('{"role": "tooltip"}'))

    def get_start_and_finish_of_calendar_week(year: int, calendar_week: int):
        monday = datetime.strptime(f'{year}.{calendar_week}.1', "%Y.%W.%w").date()
        return monday, monday + timedelta(days=6.9)

    for week in output_list[1:]:
        start_n_end = get_start_and_finish_of_calendar_week(config.YEARS[-1], int(week[0]))
        week.append(f'{start_n_end[0].strftime("%Y.%m.%d")} - ' +
                    f'{start_n_end[1].strftime("%Y.%m.%d")}' +
                    f'\nКоличество вакансий: {week[1]}')
    return output_list


def get_vacancies_qty_by_month_of_year():
    month_tuples = ((1, 'январь', 31), (2, 'февраль', 28), (3, 'март', 31),
                    (4, 'апрель', 30), (5, 'май', 31), (6, 'июнь', 30),
                    (7, 'июль', 31), (8, 'август', 31), (9, 'сентябрь', 30),
                    (10, 'октябрь', 31), (11, 'ноябрь', 30), (12, 'декабрь', 31)
    )

    years = config.YEARS
    head_time_series = [['Месяц']]
    output_list = []
    for year in years:
        head_time_series[0].append(str(year))
        for n, month in enumerate(month_tuples):
            start_day = datetime(year, month[0], 1)
            # Processing for leap years
            if isleap(year) and (month[0] == 2):
                end_day = datetime(year, month[0], 29)
            else:
                end_day = datetime(year, month[0], month[2])
            vacancies_qty = db.get_vacancies_qty_by_period(start_day=start_day,
                                                           end_day=end_day)
            # Удаляем данные в неполных месяцах, вместо неполных данных пишем ноль.
            if year == 2019:
                if month[1] == 'февраль':
                    output_list.append([month[1], 0])
                else:
                    output_list.append([month[1], vacancies_qty])
            elif year == 2023:
                if (month[1] == 'июнь') or (month[1] == 'июль'):
                    output_list[n].append(0)
                else:
                    output_list[n].append(vacancies_qty)
            elif year == 2024:
                if month[1] == 'январь':
                    output_list[n].append(0)
                else:
                    output_list[n].append(vacancies_qty)
            else:
                output_list[n].append(vacancies_qty)
    output_list = head_time_series + output_list
    return output_list


def get_data_for_horizontal_bar_chart(chart_name: str) -> list[list[str | int]]:
    statistics_data = db.get_data_for_chart(chart_name=chart_name)
    data_list = [[i.data, i.popularity] for i in statistics_data]
    return data_list


def get_salary_data_per_year() -> list[list[str | int]]:
    experience_ranges = dict(noExperience=[], between1And3=[], between3And6=[], moreThan6=[])

    data = [['Range']]
    for year in config.YEARS:
        data[0].append(str(year))  # Добавляем года в колонку легенды.
        # Добавляем расчетные зарплаты в соответствии с диапазоном опыта.
        statistics_data = db.get_data_for_chart_per_year(year=year, chart_name='salary')
        for i in statistics_data:
            experience_ranges[i.data].append(i.popularity)
    # Переводим названия диапазонов на русский
    for i in experience_ranges:
        rang_data = experience_ranges[i]
        rang_data.insert(0, config.TRANSLATIONS[i])
        data.append(rang_data)
    return data


def get_data_per_year(year: int, chart_name: str, sort=True) -> list[list[str | int]]:
    """Формирует данные для графиков по годам на основе запроса в БД."""
    head = [['Type', 'Popularity']]
    statistics_data = db.get_data_for_chart_per_year(year=year, chart_name=chart_name)
    data_list = []
    for i in statistics_data:
        # Переводим параметры для перечисленных видов графиков
        if chart_name in ['schedule_type', 'employment_type', 'experience', 'with_salary']:
            row = [config.TRANSLATIONS[i.data], i.popularity]
            data_list.append(row)
        else:  # Для остальных не переводим
            data_list.append([i.data, i.popularity])
    data_list.sort(reverse=sort, key=itemgetter(1))
    return head + data_list


def get_vacancies_with_salary(experience):
    last_month = date.today() - timedelta(days=30)
    response = db.find_vacancy_with_salary_by_substring_per_period(experience=experience,
                                                                   start_day=last_month,
                                                                   end_day=date.today())
    chart_data_list = []
    for i in response:
        template = (f"[new Date('{i.published_at}'),{i.calc_salary},"
                    f"'<a href=\"{i.url}\">{int(i.calc_salary)}</a>'],\n")
        chart_data_list.append(template)
    chart_data = ''.join(chart_data_list)
    return chart_data


def get_frameworks_data(year: int, chart_name: str) -> list[list[str | int]]:
    """Формирует данные для графика популярности фреймворков юнит-тестирования по годам."""
    head = [['Framework', 'Popularity', 'Language']]
    statistics_data = db.get_data_for_chart_per_year(year=year, chart_name=chart_name)
    data_list = []
    for i in statistics_data:
        data_list.append([i.data, i.popularity, i.parent])
    data_list.sort(reverse=True, key=itemgetter(1))
    return head + data_list


def render_framework_charts(title, chart):
    """Генерация кода JS-функций графиков популярности фреймворков юнит-тестирования по годам."""
    charts = ''
    divs = ''
    for year in reversed_years():
        data = get_frameworks_data(year, chart)
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
            'title':'{title} в {year} году.',
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


def get_salary_by_category_data():
    languages = config.PROGRAM_LANGUAGES
    data_list = []
    salary_list = []
    for language in languages:
        salary = db.find_vacancy_with_salary_by_substring(search_phrase=language)
        for i in salary:
            salary_list.append(float(i.calc_salary))
        try:
            median = statistics.median(salary_list)
        except statistics.StatisticsError:
            continue
        if len(salary_list) < 10:
            continue
        data_list.append(
            [language, min(salary_list), median, median,  max(salary_list)])
        salary_list = []
    # Sort by median value.
    data_list.sort(key=lambda row: row[2], reverse=True)
    print(f'{data_list=}')
    return data_list
