import re
import statistics
from datetime import datetime, timedelta, date
from calendar import isleap
import json

import unicodedata
import locale
from typing import NoReturn, Sequence, Any

import requests
from sqlalchemy import RowMapping, Row, exc

from db.db_client import Database
from config import Config

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
db = Database()
first_day_of_current_year = date(date.today().year, 1, 1)


def write_vacancies(response: requests, base_url: str) -> list[int]:
    """
    Get list of vacancies from response and write to "calendar" and "vacancies" tables.
    Return list of vacancies ID.
    """
    vac_list = response.json()["items"]
    items = []
    for vacancy in vac_list:
        db.insert_vac_id_to_calendar(vac_id=int(vacancy["id"]), published_at=vacancy["published_at"])

        # If vacancy is new, write description to "vacancies" table.
        if int(vacancy["id"]) not in db.get_all_vacancies_ids():
            # Get vacancies by ID
            r = requests.get(base_url + (vacancy["id"]))
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
            db.insert_vacancy(vac_id=vacancy['id'], json=json_dump, published_at=published_at)
    return items


def chart_with_category_filter(types: list, chart_name: str, update, year) -> NoReturn:
    """ Function count a number of entries of some string from param_list in all vacancies. """
    for param in types:
        vac_qty = db.count_vacancy_by_search_phrase_and_year(search_phrase=param[0], year=year)
        if update:
            if param[0] == 'py.test':
                db.update_charts(chart_name=chart_name, parent=param[1],
                                 popularity=db.get_pytest_data(year=year) + vac_qty,
                                 year=year, data='pytest')
            else:
                db.update_charts(chart_name=chart_name, parent=param[1], popularity=vac_qty,
                                 year=year, data=param[0])
        else:
            if param[0] == 'py.test':
                db.update_charts(chart_name=chart_name, parent=param[1],
                                 popularity=db.get_pytest_data(year=year) + vac_qty,
                                 year=year, data='pytest')
            else:
                db.insert_in_charts(chart_name=chart_name, data=param[0],
                                    popularity=vac_qty,
                                    parent=param[1], year=year)


def count_per_year(chart_name: str, categories: list, year: int, update: bool = True) -> NoReturn:
    """ Function count a number of entries of some string from param_list
     in the JSON of all vacancies. """
    # Convert list to dictionary and set values to 0
    categories_dict = {_type: 0 for _type in categories}
    for param_type in categories_dict:
        type_count = db.count_vacancy_by_search_phrase_and_year(search_phrase=param_type, year=year)
        if update:
            db.update_charts(chart_name=chart_name, data=param_type,
                             popularity=type_count, year=year)
        else:
            db.insert_in_charts(chart_name=chart_name, data=param_type,
                                popularity=type_count, year=year)


def count_types_per_year(types: list, chart_name: str,
                         all_vacancies:  Sequence[Row[Any] | RowMapping],
                         year: int, update: bool) -> NoReturn:
    # Convert list to dict with zero values.
    types = {_type: 0 for _type in types}
    # Count vacancies with given type in current year.
    for vacancy in all_vacancies:
        body = json.loads(str(vacancy))
        types[(body[chart_name]['id'])] += 1
    # Write ready data to DB.
    for _type in types:
        if update:
            db.update_charts(chart_name=chart_name, data=_type,
                             popularity=types[_type], year=year)
        else:
            db.insert_in_charts(chart_name=chart_name, data=_type,
                                popularity=types[_type], year=year)


def count_salary_types(types: list, chart_name: str, year: int,
                       all_vacancies: Sequence[Row[Any] | RowMapping],
                       update: bool) -> NoReturn:
    # Convert list to dict with zero values.
    types = {_type: 0 for _type in types}
    # Count vacancies with given type in given year.
    for vacancy in all_vacancies:
        body = json.loads(str(vacancy))

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
    for _type in types:
        if update:
            db.update_charts(chart_name=chart_name, data=_type,
                             popularity=types[_type], year=year)
        else:
            db.insert_in_charts(chart_name=chart_name, data=_type,
                                popularity=types[_type], year=year)


def count_salary(year: int, update: bool, vacancies: Sequence[Row[Any] | RowMapping]) -> NoReturn:
    """Заполняет таблицу данными для графика зарплат в зависимости от опыта."""
    for experience in Config.EXPERIENCE:
        median = count_salary_median(vacancies, experience, Config.EXCHANGE_RATES)
        if update:
            db.update_charts(chart_name='salary', data=experience,
                             year=year, popularity=median)
        else:
            db.insert_in_charts(chart_name='salary', data=experience,
                                year=year, popularity=median)


def count_salary_median(vacancies: Sequence[Row[Any] | RowMapping],
                        experience: str, exchange_rate: dict) -> int:
    """Приводит зарплаты к общему виду (нетто, руб.) и записывает в отдельную таблицу для быстрого
    отображения на графике."""
    # Отбираем вакансии с нужным опытом и собираем зарплаты в список
    salary_list = []
    for vacancy in vacancies:
        if json.loads(str(vacancy))['experience']['id'] == experience and json.loads(str(vacancy))['salary'] is not None:
            salary_dict = json.loads(str(vacancy))['salary']
            salary_dict.update({'id': json.loads(str(vacancy))['id']})
            salary_dict.update({'published_at': json.loads(str(vacancy))['published_at']})
            salary_dict.update({'alternate_url': json.loads(str(vacancy))['alternate_url']})
            salary_dict.update({'experience': json.loads(str(vacancy))['experience']['id']})
            salary_dict.update({'description': json.loads(str(vacancy))['description']})
            salary_list.append(salary_dict)

    # Считаем средний разброс для вакансий с закрытым диапазоном
    closed_salary = []
    for salary in salary_list:
        if salary['from'] is None or salary['to'] is None:
            pass
        else:
            closed_salary.append((salary['to'] - salary['from'])*exchange_rate[salary['currency']])

    closed_salary_sum = 0
    for salary in closed_salary:
        closed_salary_sum += salary

    average_delta_for_closed_salary = 0

    try:
        average_delta_for_closed_salary = closed_salary_sum/len(closed_salary)
    except ZeroDivisionError:
        print('closed salary list is empty!')

    # Считаем среднюю предполагаемую зарплату с учетом открытых диапазонов и НДФЛ.
    all_salaries = []
    for salary in salary_list:
        # "Чистая" зарплата
        if salary['gross'] is False:
            # закрытый диапазон
            if (salary['from'] is not None) and (salary['to'] is not None):
                calc_salary = (salary['from'] + (salary['to'] - salary['from'])/2) * exchange_rate[salary['currency']]
                if calc_salary < Config.MROT:   # Пишем в базу МРОТ, если расчетная ЗП меньше минимальной.
                    calc_salary = Config.MROT
                all_salaries.append(calc_salary)
                db.insert_in_vac_with_salary(salary, calc_salary)
            # открытый вверх
            elif salary['to'] is None:
                calc_salary = salary['from'] * exchange_rate[salary['currency']] + average_delta_for_closed_salary/2
                if calc_salary < Config.MROT:
                    continue
                all_salaries.append(calc_salary)
                db.insert_in_vac_with_salary(salary, calc_salary)
            # открытый вниз
            elif salary['from'] is None:
                calc_salary = salary['to'] * exchange_rate[salary['currency']] - average_delta_for_closed_salary/2
                if calc_salary < Config.MROT:
                    continue
                all_salaries.append(calc_salary)
                db.insert_in_vac_with_salary(salary, calc_salary)

        # "Грязная" зарплата
        elif salary['gross']:
            # закрытый диапазон
            if (salary['from'] is not None) and (salary['to'] is not None):
                gross_salary = (salary['from'] + (salary['to'] - salary['from'])/2) * exchange_rate[salary['currency']]
                calc_salary = gross_salary - gross_salary * 0.13
                if calc_salary < Config.MROT:
                    continue
                all_salaries.append(calc_salary)
                db.insert_in_vac_with_salary(salary, calc_salary)
            # открытый вверх
            elif salary['to'] is None:
                gross_salary = (salary['from'] * exchange_rate[salary['currency']] + average_delta_for_closed_salary/2)
                calc_salary = gross_salary - gross_salary * 0.13
                if calc_salary < Config.MROT:
                    continue
                all_salaries.append(calc_salary)
                db.insert_in_vac_with_salary(salary, calc_salary)
            # открытый вниз
            elif salary['from'] is None:
                gross_salary = (salary['to'] * exchange_rate[salary['currency']] - average_delta_for_closed_salary/2)
                calc_salary = gross_salary - gross_salary * 0.13
                if calc_salary < Config.MROT:
                    continue
                all_salaries.append(calc_salary)
                db.insert_in_vac_with_salary(salary, calc_salary)

    salary_sum = 0
    if len(all_salaries) == 0:
        return 0
    else:
        for salary in all_salaries:
            salary_sum += salary
        median_salary = int(statistics.median(all_salaries))
        return median_salary


def get_vacancies_qty_by_day_of_week() -> list:
    today = date.today() - timedelta(days=6)
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
        start_n_end = get_start_and_finish_of_calendar_week(Config.YEARS[-1], int(week[0]))
        week.append(f'{start_n_end[0].strftime("%Y.%m.%d")} - ' +
                    f'{start_n_end[1].strftime("%Y.%m.%d")}' +
                    f'\nКоличество вакансий: {week[1]}')
    return output_list


def get_vacancies_qty_by_month_of_year() -> list[list]:
    month_tuples = ((1, 'январь', 31), (2, 'февраль', 28), (3, 'март', 31),
                    (4, 'апрель', 30), (5, 'май', 31), (6, 'июнь', 30),
                    (7, 'июль', 31), (8, 'август', 31), (9, 'сентябрь', 30),
                    (10, 'октябрь', 31), (11, 'ноябрь', 30), (12, 'декабрь', 31))
    years = Config.YEARS
    head_time_series = [['Месяц']]
    output_list = [[i[1]] for i in month_tuples]

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


def get_salary_data_per_year() -> list[list[str | int]]:
    # Convert list to dict with empty lists values.
    experience_ranges = {_type: list() for _type in Config.EXPERIENCE}

    data = [['Range']]
    for year in Config.YEARS:
        data[0].append(str(year))  # Добавляем года в колонку легенды.
        # Добавляем расчетные зарплаты в соответствии с диапазоном опыта.
        statistics_data = db.get_data_for_chart_per_year(year=year, chart_name='salary')
        for i in statistics_data:
            experience_ranges[i.data].append(i.popularity)
    # Переводим названия диапазонов на русский
    for i in experience_ranges:
        rang_data = experience_ranges[i]
        rang_data.insert(0, Config.TRANSLATIONS[i])
        data.append(rang_data)
    return data


def get_vacancies_with_salary(experience: str) -> str:
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


def get_formatted_salary(salary: int) -> str:
    salary = str(salary)
    return f'{salary[:-3]} {salary[-3:]}'


def get_salary_by_category_data() -> list[list]:
    languages = Config.PROGRAM_LANGUAGES
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
        tooltip = f'минимум: {get_formatted_salary(round(min(salary_list)))}\xa0р.\n' \
                  f'медиана: {get_formatted_salary(round(median))}\xa0р.\n' \
                  f'максимум: {get_formatted_salary(round(max(salary_list)))}\xa0р.\n' \
                  f'на данных {len(salary_list)} вакансий'
        data_list.append(
            [language, min(salary_list), median, median,  max(salary_list), tooltip])
        salary_list = []
    # Sort by median value.
    data_list.sort(key=lambda row: row[2], reverse=True)
    return data_list


def fill_skill_set_chart(update: bool) -> None:
    """Заполнение данных для графика 'Ключевые навыки'."""
    current_year_vacancies = db.get_json_from_vacancies_by_year(Config.YEARS[-1])
    # Populate skills set
    key_skills = set()
    for vacancy in current_year_vacancies:
        body = json.loads(str(vacancy))
        try:
            for m in body['key_skills']:
                key_skills.add(m['name'])
        except IndexError:
            continue
        except KeyError:
            continue

    # Count skills
    key_skills_dict = dict.fromkeys(key_skills, 0)
    for vacancy in current_year_vacancies:
        body = json.loads(str(vacancy))
        try:
            for x in body['key_skills']:
                key_skills_dict[(x['name'])] += 1
        except IndexError:
            continue
        except KeyError:
            continue

    key_skills_dict = dict(sorted(key_skills_dict.items(),
                                  key=lambda item: item[1],
                                  reverse=True))

    # Wright first 50 skills data to DB
    counter = 50
    for skill in key_skills_dict:
        if update:
            try:
                db.update_charts(chart_name='key_skills', data=skill,
                                 parent=None, year=None,
                                 popularity=key_skills_dict[skill])
            except exc.NoResultFound:
                db.insert_in_charts(chart_name='key_skills', data=skill,
                                    parent=None, year=None,
                                    popularity=key_skills_dict[skill])

        else:
            db.insert_in_charts(chart_name='key_skills', data=skill,
                                parent=None, year=None,
                                popularity=key_skills_dict[skill])
        counter -= 1
        if counter == 0:
            break


def fill_top_employers_chart() -> None:
    """Заполнение данных для графика 'Топ 50 работодателей'."""
    current_year_vacancies = db.get_json_from_vacancies_by_year(Config.YEARS[-1])
    # Delete employers data
    db.delete_chart_data(chart_name='top_employers')

    # Populate employers set
    employers = set()
    for vacancy in current_year_vacancies:
        body = json.loads(str(vacancy))
        try:
            employers.add(body['employer']['name'])
        except IndexError:
            continue
        except KeyError:
            continue

    # Count employers
    employers_dict = dict.fromkeys(employers, 0)  # Make dict from set
    for vacancy in current_year_vacancies:
        body = json.loads(str(vacancy))
        employer = body['employer']['name']
        if employer in employers_dict:
            employers_dict[employer] += 1
        else:
            continue

    # Sort dict
    employers_dict = dict(sorted(employers_dict.items(),
                                 key=lambda item: item[1],
                                 reverse=True))

    # Wright first 50 employers data to DB
    counter = 50
    for employer in employers_dict:
        db.insert_in_charts(chart_name='top_employers', data=employer,
                            parent=None, year=None,
                            popularity=employers_dict[employer])
        counter -= 1
        if counter == 0:
            break
