# -*- encoding=utf8 -*-
import requests
import json
import sqlite3
import utils
from datetime import date

update = True
years_tuple = (
    # 2019,
    # 2020,
    2021,
)
exchange_rates = {'RUR': 1, 'EUR': 86, 'USD': 73, 'UAH': 2.58}
experience_grades = ('noExperience', 'between1And3', 'between3And6', 'moreThan6')
today = date.today()
first_day_of_current_year = date(date.today().year, 1, 1)
conn = sqlite3.connect("testdb.db")  # Open database
cur = conn.cursor()  # Create cursor

base_url = 'http://api.hh.ru/vacancies/'
search_string = u'?text=QA OR Qa OR QА OR Qа Q.A. тест* OR Тест* OR ТЕСТ* ' \
                u' OR SDET OR test* OR Test* OR TEST* OR Quality OR quality&' \
                'no_magic=true&order_by=publication_time&' \
                'area=1&specialization=1.117&' \
                'search_field=name&' \
                'page=0'  # &per_page=100

req = requests.get((base_url + search_string).encode('utf-8'))

# http_proxy = "http://127.0.0.1:8888"
# https_proxy = "http://127.0.0.1:8888"
# proxies = {"http": http_proxy, "https": https_proxy}

# Get quantity of pages in responce
pages = 15  # req.json()["pages"]


for page_num in range(0, pages):
    search_url = base_url + search_string.replace("page=0", "page=" + str(page_num))
    resp = requests.get(search_url)
    s = utils.id_list(resp, base_url)
    print("Items on page: ", len(set(s)))

if update is False:
    # Drop table with statistics and recreate it
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
    sql = f"""SELECT json FROM vacancies WHERE published_at
              BETWEEN '{year}-01-01T00:00:00+0300' AND '{year}-12-31T11:59:59+0300';"""
    cur.execute(sql)
    all_vacancies = cur.fetchall()

    utils.stat_with_one_year('languages',
                             ['Java', 'Python', 'JavaScript', 'C#', "PHP", 'C++',
                              'Ruby', 'Groovy', ' Go ', 'Scala', 'Swift',
                              'Kotlin', 'TypeScript', 'VBScript', 'tcl', 'Perl',
                              'AutoIT'
                              ], year, cur, update)

    utils.stat_with_one_year('bdd_frameworks',
                             ['Cucumber', 'Robot_Framework', 'SpecFlow', 'TestLeft', 'RSpec', 'JBehave',
                              'HipTest', "Jasmine", 'Behat', 'behave', 'Fitnesse', 'Cucumber-JVM',
                              'pytest-bdd', 'NSpec', 'Serenity BDD'
                              ], year, cur, update)

    utils.stat_with_one_year('load_testing_tools',
                             ['JMeter', 'LoadRunner', 'Locust', 'Gatling', 'Yandex.Tank', 'ApacheBench',
                              'Grinder', 'Performance Center', 'IBM Rational Performance'],
                             year, cur, update)

    utils.stat_with_one_year('web_ui_tools',
                             ['Selenium', 'Ranorex', 'Selenide', 'Selenoid', 'Selene',
                              'Cypress', 'Splinter', 'Puppeteer', 'WebDriverIO', 'Galen',
                              'Playwright', 'Protractor', 'TestCafe'],
                             year, cur, update)

    utils.stat_with_one_year('mobile_testing_frameworks',
                             ['Appium', 'Selendroid', 'Espresso', 'Detox', 'robotium',
                              'Calabash', 'UI Automation', 'UIAutomator', 'XCTest', 'Kobiton'],
                             year, cur, update)

    utils.stat_with_one_year('bugtracking_n_tms',
                             ['Youtrack', 'TestRail', 'TestLink', 'TestLodge',
                              'Jira', 'Confluence', 'Redmine', 'TFS', 'Zephyr',
                              'Hiptest', 'Xray', 'PractiTest', 'Testpad',
                              'Deviniti', 'Qase', 'IBM Rational Quality Manager',
                              'HP Quality Center', 'HP ALM', 'TestIt',
                              'Gemini', 'BugZilla', 'Fitnesse'], year, cur, update)

    utils.stat_with_one_year('cvs', ['git', 'SVN', 'Subversion', 'Mercurial'],
                             year, cur, update)

    utils.stat_with_one_year('ci_cd', ['GitLab', 'GitHub', 'Bitbucket', 'Jenkins',
                                       'Cirlce CI', 'Travis CI', 'Bamboo', 'TeamCity'],
                             year, cur, update)

    schedule_types = dict(fullDay=0, flexible=0, shift=0, remote=0)
    utils.types_stat_with_year(schedule_types, 'schedule_type', 'schedule', all_vacancies,
                               cur, year, update)

    experience_types = dict(noExperience=0, between1And3=0, between3And6=0, moreThan6=0)
    utils.types_stat_with_year(experience_types, 'experience', 'experience', all_vacancies,
                               cur, year, update)

    employment_types = dict(full=0, part=0, project=0, probation=0)
    utils.types_stat_with_year(employment_types, 'employment_type', 'employment', all_vacancies,
                               cur, year, update)

    with_salary = dict(without_salary=0, closed=0, open_up=0, open_down=0)
    utils.vacancy_with_salary(with_salary, 'with_salary', year, all_vacancies, cur, update)

    utils.chart_with_category_filter('frameworks',
                                     [['pytest', 'Python'], ['py.test', 'Python'], ['Unittest', 'Python'],
                                      ['Nose', 'Python'],
                                      ['JUnit', 'Java'], ['TestNG', 'Java'],
                                      ['PHPUnit', 'PHP'], ['Codeception', 'PHP'],
                                      ['RSpec', 'Ruby'], ['Capybara', 'Ruby'],
                                      ['Spock', 'C#'], ['NUnit', 'C#'],
                                      ['Mocha', 'JavaScript'], ['Serenity', 'JavaScript'], ['Jest', 'JavaScript'],
                                      ['Jasmine', 'JavaScript'], ['Nightwatch', 'JavaScript'], ['Karma', 'JavaScript'],
                                      ['CodeceptJS', 'JavaScript'],
                                      ['Robot_Framework', 'multiple_language']], cur, update, year)
    # Count salary
    for experience in experience_grades:
        print("Опыт: ", experience)
        median = utils.salary_to_db(experience, exchange_rates, conn, year)

        if update is True:
            sql = f"""
                    UPDATE charts SET popularity = {median} WHERE data = '{experience}'
                    AND chart_name = 'salary' AND year = {str(year)};
                    """
        else:
            sql = f"""INSERT INTO charts(chart_name, data, popularity, year)
                          VALUES("salary", "{experience}", "{median}", {str(year)});"""

        cur.executescript(sql)

sql = f"""SELECT id, json FROM vacancies WHERE published_at
          BETWEEN '{first_day_of_current_year}' AND '{today}';"""
cur.execute(sql)
all_vacancies = (cur.fetchall())

# Populate skills set
key_skills = set()
for n in all_vacancies:
    body = json.loads((n[1]))
    try:
        for m in body['key_skills']:
            key_skills.add(m['name'])
    except IndexError:
        continue
    except KeyError:
        continue

# Count skills
key_skills_dict = dict.fromkeys(key_skills, 0)
for i in all_vacancies:
    body = json.loads((i[1]))
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
        UPDATE charts SET popularity = {key_skills_dict[n]} WHERE data = '{n}'
        AND chart_name = 'key_skills';
        """
    else:
        sql = f"""INSERT INTO charts(chart_name, data, popularity)
              VALUES("key_skills", "{n}", {key_skills_dict[n]});"""
    try:
        cur.executescript(sql)
    except sqlite3.IntegrityError as error:
        print("Error: ", error)
    sql = f"""
    UPDATE charts SET popularity = {key_skills_dict[n]} WHERE data = '{n}'
    AND chart_name = 'key_skills';"""
    cur.executescript(sql)
    counter -= 1
    if counter == 0:
        break

sql = "VACUUM;"
cur.execute(sql)
conn.commit()
# Close database connection
conn.close()
