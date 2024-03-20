import os
from argparse import ArgumentParser

import requests

import utils
from config import ConfigObj
from db import db_client

db = db_client.Database()
config = ConfigObj()

parser = ArgumentParser()
parser.add_argument("-r", "--rebuild", dest='rebuild', action="store_true",
                    help="rebuild all calculated tables for all years.")
args = parser.parse_args()

# По умолчанию значения в данных обновляются только за последний год.
update = True
years_tuple = (config.YEARS[-1],)

# При опции CLI "-r" или "--rebuild", старые данные удаляются и пересчитываются за все годы.
if args.rebuild:
    update = False
    years_tuple = tuple(config.YEARS)

# Put new vacancies to DB
for page_num in range(0, config.PAGES_QTY):
    search_url = config.BASE_URL + config.SEARCH_STRING.replace("page=0", "page=" + str(page_num))
    resp = requests.get(search_url)
    s = utils.write_vacancies(resp, config.BASE_URL)

for word in config.STOP_LIST:
    db.delete_vacancy_with_json_like(word=word)

db.drop_and_recreate_vac_with_salary_table()
if update is False:
    db.drop_and_recreate_charts_table()

# Count data for charts per year.
for year in years_tuple:
    all_vacancies_jsons = db.get_json_from_vacancies_by_year(year=year)

    pie_charts = {
        'languages': config.PROGRAM_LANGUAGES,
        'bdd_frameworks': config.BDD_FRAMEWORKS,
        'load_testing_tools': config.LOAD_TESTING_TOOLS,
        'ci_cd': config.CI_CD,
        'monitoring': config.MONITORING,
        'web_ui_tools': config.WEB_UI_TOOLS,
        'mobile_testing_frameworks': config.MOBILE_TESTING_FRAMEWORKS,
        'bugtracking_n_tms': config.BUGTRACKING_N_TMS,
        'cvs': config.CVS
    }

    for chart_name, categories in pie_charts.items():
        utils.count_per_year(chart_name=chart_name,
                             categories=categories,
                             year=year, update=update)

    pie_charts_for_types = {
        'schedule': config.SCHEDULE,
        'experience': config.EXPERIENCE,
        'employment': config.EMPLOYMENT,
    }
    for chart_name, types in pie_charts_for_types.items():
        utils.count_types_per_year(types=types,
                                   chart_name=chart_name,
                                   all_vacancies=all_vacancies_jsons,
                                   year=year, update=update)

    utils.count_salary_types(types=config.WITH_SALARY,
                             chart_name='with_salary',
                             all_vacancies=all_vacancies_jsons,
                             year=year, update=update)

    utils.chart_with_category_filter(types=config.UNIT_FRAMEWORKS,
                                     chart_name='frameworks',
                                     year=year, update=update)

    utils.count_salary(year=year, update=update,
                       vacancies=all_vacancies_jsons)


# Count data for current year only charts
utils.fill_skill_set_chart(update=update)
utils.fill_top_employers_chart()
db.vacuum_db()

username = config.PA_USERNAME
headers = {'Authorization': f'Token {os.getenv("PA_TOKEN")}'}
base_url = f'https://www.pythonanywhere.com/api/v0/user/{username}/'

# Get first webapps name
response = requests.get(base_url + 'webapps/', headers=headers)
domain_name = response.json()[0]['domain_name']

# Reload first webapps
response = requests.post(base_url + f'webapps/{domain_name}/reload/', headers=headers)
print(response.status_code)
