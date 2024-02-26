from datetime import date
import json
import sqlite3

import requests

import utils
from config import ConfigObj
import db_client

db = db_client.Database()
config = ConfigObj()
base_url = config.BASE_URL

update = True
years_tuple = (config.YEARS[-1],)

today = date.today()
first_day_of_current_year = date(date.today().year, 1, 1)
conn = sqlite3.connect("testdb.db")  # Open database
cur = conn.cursor()  # Create cursor

search_string = u'?text=QA OR Qa OR QА OR Qа Q.A. тест* OR Тест* OR ТЕСТ* ' \
                u' OR SDET OR test* OR Test* OR TEST* OR Quality OR quality&' \
                'no_magic=true&order_by=publication_time&' \
                'area=1&specialization=1.117&' \
                'search_field=name&' \
                'page=0'  # &per_page=100

req = requests.get((base_url + search_string).encode('utf-8'))

# Get quantity of pages in response
pages = 12  # req.json()["pages"]

# Put new vacancies to DB
for page_num in range(0, pages):
    search_url = base_url + search_string.replace("page=0", "page=" + str(page_num))
    resp = requests.get(search_url)
    s = utils.write_vacancies(resp, base_url)
    print("Items on page: ", len(set(s)))

# Delete vacancies, which contain words from stop list.
for word in config.STOP_LIST:
    sql = f"""DELETE FROM vacancies WHERE json LIKE '%{word}%';"""
    response = cur.execute(sql)
    print(f'Number of occurrences for substring "{word}": {response.rowcount}')
    conn.commit()

# Drop table 'vac_with_salary' and recreate it
sql = """DROP TABLE IF EXISTS vac_with_salary;"""
cur.execute(sql)
conn.commit()

sql = f"""CREATE TABLE IF NOT EXISTS vac_with_salary
(
  id INTEGER,
  published_at TEXT,
  calc_salary NUMERIC,
  experience TEXT,
  url TEXT,
  description TEXT
);"""
cur.execute(sql)
conn.commit()

if update is False:
    # Drop table 'charts' with statistics and recreate it
    cur.execute("""DROP TABLE IF EXISTS charts;""")
    conn.commit()
    sql = """
    CREATE TABLE IF NOT EXISTS charts
    (
        id INTEGER PRIMARY KEY,
        chart_name NOT NULL,
        data NOT NULL,
        popularity  INTEGER,
        parent,
        year INTEGER
    );
    """
    cur.execute(sql)
    conn.commit()


# Wright statistics data to database
for year in years_tuple:
    all_vacancies_jsons = db.get_json_from_vacancies_per_year(year=year)

    utils.count_per_year(chart_name='languages',
                         param_list=config.PROGRAM_LANGUAGES,
                         year=year, cur=cur, update=update)

    utils.count_per_year(chart_name='bdd_frameworks',
                         param_list=config.BDD_FRAMEWORKS,
                         year=year, cur=cur, update=update)

    utils.count_per_year(chart_name='load_testing_tools',
                         param_list=config.LOAD_TESTING_TOOLS,
                         year=year, cur=cur, update=update)

    utils.count_per_year(chart_name='ci_cd',
                         param_list=config.CI_CD,
                         year=year, cur=cur, update=update)

    utils.count_per_year(chart_name='monitoring',
                         param_list=config.MONITORING,
                         year=year, cur=cur, update=update)

    utils.count_per_year(chart_name='web_ui_tools',
                         param_list=config.WEB_UI_TOOLS,
                         year=year, cur=cur, update=update)

    utils.count_per_year(chart_name='mobile_testing_frameworks',
                         param_list=config.MOBILE_TESTING_FRAMEWORKS,
                         year=year, cur=cur, update=update)

    utils.count_per_year(chart_name='bugtracking_n_tms',
                         param_list=config.BUGTRACKING_N_TMS,
                         year=year, cur=cur, update=update)

    utils.count_per_year(chart_name='cvs',
                         param_list=config.CVS,
                         year=year, cur=cur, update=update)

    schedule_types = dict(fullDay=0, flexible=0, shift=0, remote=0, flyInFlyOut=0)
    utils.count_types_per_year(schedule_types, 'schedule_type',
                               'schedule', all_vacancies_jsons,
                               cur, year, update)

    experience_types = dict(noExperience=0, between1And3=0,
                            between3And6=0, moreThan6=0)
    utils.count_types_per_year(experience_types, 'experience',
                               'experience', all_vacancies_jsons,
                               cur, year, update)

    employment_types = dict(full=0, part=0, project=0,
                            probation=0, volunteer=0)
    utils.count_types_per_year(employment_types, 'employment_type',
                               'employment', all_vacancies_jsons, cur,
                               year, update)

    with_salary = dict(without_salary=0, closed=0, open_up=0, open_down=0)
    utils.count_schedule_types(with_salary, 'with_salary', year,
                               all_vacancies_jsons, cur, update)

    utils.chart_with_category_filter(
        'frameworks',
        [['pytest', 'Python'], ['py.test', 'Python'],
         ['Unittest', 'Python'], ['Nose', 'Python'],
         ['JUnit', 'Java'], ['TestNG', 'Java'],
         ['PHPUnit', 'PHP'], ['Codeception', 'PHP'],
         ['RSpec', 'Ruby'], ['Capybara', 'Ruby'],
         ['Spock', 'C#'], ['NUnit', 'C#'],
         ['Mocha', 'JavaScript'], ['Serenity', 'JavaScript'],
         ['Jest', 'JavaScript'], ['Jasmine', 'JavaScript'],
         ['Nightwatch', 'JavaScript'], ['Karma', 'JavaScript'],
         ['CodeceptJS', 'JavaScript'],
         ['Robot_Framework', 'multiple_language']], cur, update, year)
    # Count salary
    for experience in config.EXPERIENCE_GRADES:
        print("Опыт: ", experience)
        try:
            median = utils.salary_to_db(experience,
                                        config.EXCHANGE_RATES,
                                        conn, year)

            if update is True:
                sql = f"""
                        UPDATE charts
                        SET popularity = {median} WHERE data = '{experience}'
                        AND chart_name = 'salary' AND year = {str(year)};
                        """
            else:
                sql = f"""
                INSERT INTO charts(chart_name, data, popularity, year)
                VALUES("salary", "{experience}", "{median}", {str(year)});"""

            cur.executescript(sql)
        except sqlite3.OperationalError:
            print('Some sqlite3.OperationalError')

# Получаем поле 'json' для каждой из вакансий за последний год.
current_year_vacancies = db.get_json_from_vacancies_per_year(config.YEARS[-1])

# Populate skills set
key_skills = set()
for n in current_year_vacancies:
    body = json.loads(n)
    try:
        for m in body['key_skills']:
            key_skills.add(m['name'])
    except IndexError:
        continue
    except KeyError:
        continue

# Count skills
key_skills_dict = dict.fromkeys(key_skills, 0)
for i in current_year_vacancies:
    body = json.loads(i)
    try:
        for x in body['key_skills']:
            key_skills_dict[(x['name'])] += 1
    except IndexError:
        continue
    except KeyError:
        continue

# Sort dict
key_skills_dict = dict(sorted(key_skills_dict.items(),
                              key=lambda item: item[1],
                              reverse=True))

# Wright first 50 skills data to DB
counter = 50
for n in key_skills_dict:
    print(n, key_skills_dict[n])
    if update is True:
        sql = f"""
        UPDATE charts SET popularity = {key_skills_dict[n]}
        WHERE data = '{n}' AND chart_name = 'key_skills';
        """
    else:
        sql = f"""
        INSERT INTO charts(chart_name, data, popularity)
        VALUES("key_skills", "{n}", {key_skills_dict[n]});"""
    try:
        cur.executescript(sql)
    except sqlite3.IntegrityError as error:
        print("Error: ", error)
    sql = f"""
    UPDATE charts
    SET popularity = {key_skills_dict[n]}
    WHERE data = '{n}' AND chart_name = 'key_skills';"""
    cur.executescript(sql)
    counter -= 1
    if counter == 0:
        break

# Delete employers data
sql = f"""DELETE FROM charts WHERE chart_name = 'top_employers';"""
cur.executescript(sql)
conn.commit()

# Populate employers set
employers = set()
for vacancy in current_year_vacancies:
    # Convert JSON description to dict.
    body = json.loads(vacancy)
    try:
        employers.add(body['employer']['name'])
    except IndexError:
        continue
    except KeyError:
        continue

# Count employers
employers_dict = dict.fromkeys(employers, 0)  # Make dict from set
for item in current_year_vacancies:
    body = json.loads(item)
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
for n in employers_dict:
    print(n, employers_dict[n])
    sql = f"""
    INSERT INTO charts(chart_name, data, popularity)
    VALUES("top_employers", "{n}", {employers_dict[n]});"""
    try:
        cur.executescript(sql)
    except sqlite3.IntegrityError as error:
        print("Error: ", error)
    sql = f"""
    UPDATE charts
    SET popularity = {employers_dict[n]}
    WHERE data = '{n}' AND chart_name = 'top_employers';"""
    cur.executescript(sql)
    conn.commit()
    counter -= 1
    if counter == 0:
        break


sql = "VACUUM;"
cur.execute(sql)
conn.commit()
# Close database connection
conn.close()

# username = 'clingon'
# TOKEN = os.getenv('PA_TOKEN')
# headers = {'Authorization': f'Token {TOKEN}'}
# base_url = f'https://www.pythonanywhere.com/api/v0/user/{username}/'
#
# # Get first webapps name
# response = requests.get(base_url + 'webapps/', headers=headers)
# domain_name = response.json()[0]['domain_name']
# print(domain_name)
#
# # Reload first webapps
# response = requests.post(base_url + f'webapps/{domain_name}/reload/', headers=headers)
# print(response.status_code)
