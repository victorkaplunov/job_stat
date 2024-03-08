from datetime import date
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
pages = 0  # req.json()["pages"]

# Put new vacancies to DB
for page_num in range(0, pages):
    search_url = base_url + search_string.replace("page=0", "page=" + str(page_num))
    resp = requests.get(search_url)
    s = utils.write_vacancies(resp, base_url)
    print("Items on page: ", len(set(s)))

# Delete vacancies, which contain words from stop list.
for word in config.STOP_LIST:
    db.delete_vacancy_with_json_like(word=word)

# Drop table 'vac_with_salary' and recreate it
db.drop_and_recreate_vac_with_salary_table()

if update is False:
    # Drop table 'charts' with statistics and recreate it
    db.drop_and_recreate_charts_table()


# Wright statistics data to database
for year in years_tuple:
    all_vacancies_jsons = db.get_json_from_vacancies_by_year(year=year)

    pie_diagrams = {'languages': config.PROGRAM_LANGUAGES,
                    'bdd_frameworks': config.BDD_FRAMEWORKS,
                    'load_testing_tools': config.LOAD_TESTING_TOOLS,
                    'ci_cd': config.CI_CD,
                    'monitoring': config.MONITORING,
                    'web_ui_tools': config.WEB_UI_TOOLS,
                    'mobile_testing_frameworks': config.MOBILE_TESTING_FRAMEWORKS,
                    'bugtracking_n_tms': config.BUGTRACKING_N_TMS,
                    'cvs': config.CVS}

    for chart_name, categories in pie_diagrams.items():
        utils.count_per_year(chart_name=chart_name,
                             categories=categories,
                             year=year, update=update)

    schedule_types = dict(fullDay=0, flexible=0, shift=0, remote=0, flyInFlyOut=0)
    utils.count_types_per_year(schedule_types, 'schedule_type',
                               'schedule', all_vacancies_jsons,
                               year, update)

    experience_types = dict(noExperience=0, between1And3=0,
                            between3And6=0, moreThan6=0)
    utils.count_types_per_year(experience_types, 'experience',
                               'experience', all_vacancies_jsons,
                               year, update)

    employment_types = dict(full=0, part=0, project=0,
                            probation=0, volunteer=0)
    utils.count_types_per_year(employment_types, 'employment_type',
                               'employment', all_vacancies_jsons,
                               year, update)

    with_salary = dict(without_salary=0, closed=0, open_up=0, open_down=0)
    utils.count_schedule_types(with_salary, 'with_salary', year,
                               all_vacancies_jsons, update)

    utils.chart_with_category_filter(
        'frameworks', config.UNIT_FRAMEWORKS, update, year)

    # Count salary
    for experience in config.EXPERIENCE_GRADES:
        print("Опыт: ", experience)
        median = utils.count_salary_median(experience,
                                           config.EXCHANGE_RATES,
                                           conn, year)
        if update is True:
            db.update_charts(chart_name='salary', data=experience,
                             year=year, popularity=median)
        else:
            db.insert_in_charts(chart_name='salary', data=experience,
                                year=year, popularity=median)


utils.fill_skill_set_chart(update=update)
utils.fill_top_employers_chart(update=update)
db.vacuum_db()

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
