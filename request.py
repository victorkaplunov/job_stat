# -*- encoding=utf8 -*-
import requests
import json
import sqlite3
import unicodedata
import re

years_tuple = (2019, 2020,)

con = sqlite3.connect("testdb.db")  # Open database
cur = con.cursor()  # Create cursor

base_url = 'https://api.hh.ru/'
api_method = 'vacancies/'
search_string = u'?text=QA OR Qa OR QА OR Qа Q.A. тест* OR Тест* OR ТЕСТ* ' \
                u' OR SDET OR test* OR Test* OR TEST* OR Quality OR quality&' \
                'no_magic=true&order_by=publication_time&' \
                'area=1&specialization=1.117&' \
                'search_field=name&' \
                'page=0'

req = requests.get((base_url + api_method + search_string).encode('utf-8'))

# Get quantity of pages in responce
pages = req.json()["pages"]

# Get list of id from "vacancies" table
vac_id_list = []
sql = "SELECT id FROM vacancies"
try:
    cur.execute(sql)
    # print(type((cur.fetchall()[0])[0]))
    for n in cur.fetchall():
        vac_id_list.append(n[0])
except sqlite3.IntegrityError as err:
    print("Error: ", err)


def resp(n):
    """Make search request"""
    return requests.get(base_url + api_method + search_string.replace("page=0", "page=" + str(n))
                        # , proxies=proxies
                        )


def id_list(response):
    """ Get list of vacancies from response and write id and data to "calendar" table."""
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
        if int(i["id"]) not in vac_id_list:
            # Get vacancies by ID
            r = requests.get(base_url + api_method + (i["id"])
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
    return items


def wright_statistic_to_db(chart_name: str, param_list: list):
    """ Function count an inclusions of some string from param_list in the JSON of all vacancies. """
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


def chart_with_category_filter(chart_name: str, param_list: list):
    """ Function count an inclusions of some string from param_list in all vacancies. """
    for i in param_list:
        print(i[0], i[1])
        sql = "SELECT json FROM vacancies WHERE json LIKE '%%%s%%';" % i[0]
        cur.execute(sql)
        vac = cur.fetchall()
        sql = 'INSERT INTO charts(chart_name, data, popularity, parent) VALUES("%s", "%s", %i, "%s");' % (chart_name, i[0],
                                                                                                   len(vac), i[1])
        try:
            cur.executescript(sql)
        except sqlite3.IntegrityError as error:
            print("Error: ", error)

        sql = 'UPDATE charts SET popularity = "%i" WHERE data = "%s" AND chart_name = "%s";' % (len(vac), i, chart_name)
        print(sql)
        cur.executescript(sql)
    return


# Run request to HH.ru API
for x in range(0, pages):
    s = id_list(resp(x))
    print("Items on page: ", len(set(s)))

sql = "SELECT id, json FROM vacancies;"
cur.execute(sql)
all_vacancies = (cur.fetchall())

cur.execute("DROP TABLE IF EXISTS charts;")

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


#  Wright statistics data to database

wright_statistic_to_db('languages',
                       ['Java', 'Python', 'JavaScript', 'C#', "PHP", 'C++',
                        'Ruby', 'Groovy', ' Go ', 'Scala', 'Swift',
                        'Kotlin', 'TypeScript', 'VBScript', 'tcl', 'Perl',
                        'AutoIT'
                        ])

chart_with_category_filter('frameworks',
                           [['pytest', 'Python'], ['Py.test', 'Python'], ['Unittest', 'Python'], ['Nose', 'Python'],
                            ['JUnit', 'Java'], ['TestNG', 'Java'],
                            ['PHPUnit', 'PHP'], ['Codeception', 'PHP'],
                            ['RSpec', 'Ruby'], ['Capybara', 'Ruby'],
                            ['Spock', 'C#'], ['NUnit', 'C#'],
                            ['Mocha', 'JavaScript'], ['Serenity', 'JavaScript'], ['Jest', 'JavaScript'],
                            ['Jasmine', 'JavaScript'], ['Nightwatch', 'JavaScript'], ['Karma', 'JavaScript'],
                            ['CodeceptJS', 'JavaScript'],
                            ['Robot_Framework', 'multiple_language']]
                           )

wright_statistic_to_db('lt_frameworks',
                       ['JMeter', 'LoadRunner', 'Locust', 'Gatling', 'Yandex.Tank', 'ApacheBench',
                        'Grinder', 'Performance Center', 'IBM Rational Performance'])

wright_statistic_to_db('monitoring_tools',
                       ['Zabbix', 'nmon', 'Oracle EM', 'Grafana', 'ELK', 'Influxdb', 'Nagios', 'Cacti'])

wright_statistic_to_db('bdd_frameworks',
                       ['Cucumber', 'SpecFlow', 'TestLeft', 'RSpec', 'JBehave',
                        'HipTest', "Jasmine", 'Behat', 'behave', 'Fitnesse', 'Concordion',
                        'JDave', "EasyB", 'Lettuce', 'SubSpec', 'Cucumber-JVM', 'pytest-bdd',
                        'radish', "Spinach", 'Yadda', 'Vows', 'NSpec', 'Serenity BDD', 'xBehave.net'])

wright_statistic_to_db('web_ui_tools',
                       ['Selenium', 'Ranorex', 'Selenide', 'Selenoid', 'Selene', 'Cypress', 'Splinter',
                        'Puppeteer', 'WebDriverIO', 'Galen', 'Playwright', 'Protractor', 'TestCafe'])

wright_statistic_to_db('mobile_testing_frameworks',
                       ['Appium', 'Selendroid', 'Espresso', 'Detox', 'robotium',
                        'Calabash', 'UI Automation', 'UIAutomator', 'XCTest'])

wright_statistic_to_db('bugtracking_n_tms',
                       ['Youtrack', 'TestRail', 'TestLink', 'TestLodge', 'Jira',
                        'Confluence', 'Redmine', 'TFS', 'Zephyr',
                        'Hiptest', 'TestMonitor', 'Xray', 'PractiTest', 'Testpad',
                        'Deviniti', 'Qase', 'Klaros-Testmanagement',
                        'IBM Rational Quality Manager', 'HP Quality Center', 'HP ALM',
                        'TestIt', 'XQual', 'Borland Silk Central', 'Testuff',
                        'Gemini', 'BugZilla', 'Fitnesse', 'RTH-Turbo',
                        'Stryka', 'Test Case Lab'])

wright_statistic_to_db('cvs',
                       ['git', 'SVN', 'Subversion', 'Mercurial'])

wright_statistic_to_db('ci_cd',
                       ['GitLab', 'GitHub', 'Bitbucket', 'Jenkins', 'Cirlce CI', 'Travis CI',
                        'Bamboo', 'TeamCity', 'Apache Gump'])


def stat_with_year(types, chart_name, key_name):
    # Count types of schedule in all vacancies.
    for y in years_tuple:
        types = types.fromkeys(types, 0)  # set all values to zero
        # Count vacancies with given type in current year.
        for n in all_vacancies:
            body = json.loads((n[1]))
            if (f"{str(y-1)}-12-31T23:59:59+0300" < body['created_at']) and \
                    (body['created_at'] < f"{str(y+1)}-01-01T00:00:00+0300"):
                types[(body[key_name]['id'])] += 1
            else:
                continue
        # Write ready data to DB.
        print(types)
        for n in types:
            sql = f'INSERT INTO charts(chart_name, data, popularity, year) ' \
                  f'VALUES("{chart_name}", "{n}", {types[n]}, {str(y)});'
            cur.executescript(sql)
    return


schedule_types_dict = dict(fullDay=0, flexible=0, shift=0, remote=0)
stat_with_year(schedule_types_dict, 'schedule_type', 'schedule')

experience_types_dict = dict(noExperience=0, between1And3=0, between3And6=0, moreThan6=0)
stat_with_year(experience_types_dict, 'experience', 'experience')

employment_types_dict = dict(full=0, part=0, project=0, probation=0)
stat_with_year(employment_types_dict, 'employment_type', 'employment')


def vacancy_with_salary(types: dict, chart_name: str):
    # Count types of schedule in all vacancies.
    for y in years_tuple:
        types = types.fromkeys(types, 0)  # set all values to zero
        # Count vacancies with given type in current year.
        for n in all_vacancies:
            body = json.loads((n[1]))
            if (f"{str(y-1)}-12-31T23:59:59+0300" < body['created_at']) and \
                    (body['created_at'] < f"{str(y+1)}-01-01T00:00:00+0300"):
                if body['salary'] is not None:
                    types['with_salary'] += 1
                else:
                    types['without_salary'] += 1
            else:
                continue
        # Write ready data to DB.
        print(types)
        for n in types:
            sql = f'INSERT INTO charts(chart_name, data, popularity, year) ' \
                  f'VALUES("{chart_name}", "{n}", {types[n]}, {str(y)});'
            cur.executescript(sql)
    return


with_salary = dict(with_salary=0, without_salary=0)
vacancy_with_salary(with_salary, 'with_salary')


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
print(key_skills_dict)

# Wright skills data to DB
for n in key_skills_dict:
    sql = f'INSERT INTO charts(chart_name, data, popularity) ' \
          f'VALUES("key_skills", "{n}", {key_skills_dict[n]});'
    try:
        cur.executescript(sql)
    except sqlite3.IntegrityError as error:
        print("Error: ", error)
    sql = f'UPDATE charts SET popularity = {key_skills_dict[n]} WHERE data = "{n}" AND chart_name = "key_skills";'
    cur.executescript(sql)

# Close database connection
con.close()
