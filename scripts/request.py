import os
from argparse import ArgumentParser

import requests

import utils
from config import Config
from db import db_client

db = db_client.Database()

parser = ArgumentParser()
parser.add_argument("-r", "--rebuild", dest='rebuild', action="store_true",
                    help="rebuild all calculated tables for all years.")
args = parser.parse_args()

# По умолчанию значения в данных обновляются только за последний год.
update = True
years_tuple = (Config.YEARS[-1],)

# При опции CLI "-r" или "--rebuild", старые данные удаляются и пересчитываются за все годы.
if args.rebuild:
    update = False
    years_tuple = tuple(Config.YEARS)

# Put new vacancies to DB
for page_num in range(0, Config.PAGES_QTY):
    search_url = Config.BASE_URL + Config.SEARCH_STRING.replace("page=0", "page=" + str(page_num))
    resp = requests.get(search_url)
    s = utils.write_vacancies(resp, Config.BASE_URL)

for word in Config.STOP_LIST:
    db.delete_vacancy_with_json_like(word=word)

db.drop_and_recreate_vac_with_salary_table()
if update is False:
    db.drop_and_recreate_charts_table()

# Count data for charts per year.
for year in years_tuple:
    all_vacancies_jsons = db.get_json_from_vacancies_by_year(year=year)

    pie_charts = {
        'languages': Config.PROGRAM_LANGUAGES,
        'bdd_frameworks': Config.BDD_FRAMEWORKS,
        'load_testing_tools': Config.LOAD_TESTING_TOOLS,
        'traffic_generators': Config.TRAFFIC_GENERATORS,
        'tracing_system': Config.TRACING_SYSTEM,
        'api_testing_tools': Config.API_TESTING_TOOLS,
        'ci_cd': Config.CI_CD,
        'monitoring': Config.MONITORING,
        'web_ui_tools': Config.WEB_UI_TOOLS,
        'mobile_testing_frameworks': Config.MOBILE_TESTING_FRAMEWORKS,
        'bugtracking_n_tms': Config.BUGTRACKING_N_TMS,
        'cvs': Config.CVS
    }

    for chart_name, categories in pie_charts.items():
        utils.count_per_year(chart_name=chart_name,
                             categories=categories,
                             year=year, update=update)

    pie_charts_for_types = {
        'schedule': Config.SCHEDULE,
        'experience': Config.EXPERIENCE,
        'employment': Config.EMPLOYMENT,
    }
    for chart_name, types in pie_charts_for_types.items():
        utils.count_types_per_year(types=types,
                                   chart_name=chart_name,
                                   all_vacancies=all_vacancies_jsons,
                                   year=year, update=update)

    utils.count_salary_types(types=Config.WITH_SALARY,
                             chart_name='with_salary',
                             all_vacancies=all_vacancies_jsons,
                             year=year, update=update)

    utils.chart_with_category_filter(types=Config.UNIT_FRAMEWORKS,
                                     chart_name='frameworks',
                                     year=year, update=update)

    utils.count_salary(year=year, update=update,
                       vacancies=all_vacancies_jsons)


# Count data for current year only charts
utils.fill_skill_set_chart(update=update)
utils.fill_top_employers_chart()
db.vacuum_db()
db.close_session()
