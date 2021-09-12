import datetime
from operator import itemgetter
from flask import Flask, send_from_directory, url_for, render_template
from flask_bootstrap import Bootstrap
import os
import sqlite3
import json
import utils
from datetime import date, timedelta


app = Flask(__name__)
bootstrap = Bootstrap(app)
id_list = []
l_host = "http://127.0.0.1:5000"


def cur():
    con = sqlite3.connect("testdb.db")
    return con.cursor()


@app.route('/api')
def api():
    return f"""<html>
    <a href="{url_for('show_vac_calendar', vac_id='14658327')}">{url_for('show_vac_calendar', vac_id='14658327')}</a><br>
    <a href="{url_for('show_vac_description', vac_id='14658327')}">{url_for('show_vac_description', vac_id='14658327')}</a><br>
    <a href="{url_for('show_vac_top_new_by_id')}">{url_for('show_vac_top_new_by_id')}"</a><br>
    <a href="{url_for('show_vac_top_new_by_data')}">{url_for('show_vac_top_new_by_data')}"</a><br>
    <a href="{url_for('search_vac', search_phrase='Python')}">{url_for('search_vac', search_phrase='Python')}"</a><br>
    </html>"""


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/starter-template.css')
def starter_template():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'starter-template.css')  # , mimetype='image/vnd.microsoft.icon')


@app.route('/api/vac/cal/<int:vac_id>')
def show_vac_calendar(vac_id):
    """Show the publication data of vacancy with the given id"""
    con = sqlite3.connect("testdb.db")
    cur = con.cursor()
    sql = "SELECT data FROM calendar WHERE id = " + str(vac_id)
    cur.execute(sql)
    vac = cur.fetchall()
    con.close()
    data_list = []
    for i in vac:
        data_list.append(i[0])
    return str(data_list)


@app.route('/api/vac/<int:vac_id>')
def show_vac_description(vac_id):
    """Show the description of vacancy with the given id"""
    con = sqlite3.connect("testdb.db")
    cur = con.cursor()
    sql = "SELECT * FROM vacancies WHERE id = " + str(vac_id)
    cur.execute(sql)
    vac = cur.fetchone()
    return str(
        json.loads(vac[1])['employer']["name"] + "\n" +
        json.loads(vac[1])["name"] + "\n" +
        json.loads(vac[1])['description'])


@app.route('/api/vac/last100id')
def show_vac_top_new_by_id():
    """Get last 100 vacancies sorted by id"""
    con = sqlite3.connect("testdb.db")
    cur = con.cursor()
    sql = "SELECT * FROM calendar ORDER BY id DESC LIMIT 100;"
    cur.execute(sql)
    vac = cur.fetchall()
    con.close()
    data_list = []
    for i in vac:
        data_list.append('<a href="https://hh.ru/vacancy/' + str(i[0]) + '">' + str(i[0]) + '</a>')
    return str(data_list)


@app.route('/api/vac/last100data')
def show_vac_top_new_by_data():
    """Get last 100 vacancies sorted by last publication data"""
    con = sqlite3.connect("testdb.db")
    cur = con.cursor()
    sql = "SELECT * FROM calendar ORDER BY data DESC LIMIT 100;"
    cur.execute(sql)
    vac = cur.fetchall()
    con.close()
    data_list = []
    for i in vac:
        data_list.append('<a href="https://hh.ru/vacancy/' + str(i[0]) + '">' + str(i[0]) + '</a>')
    return str(data_list)


@app.route('/api/search/<search_phrase>')
def search_vac(search_phrase):
    """Get vacancies with search phrase in JSON"""
    con = sqlite3.connect("testdb.db")
    cur = con.cursor()
    sql = 'SELECT * FROM vacancies WHERE json LIKE "%{}%" ORDER BY id DESC LIMIT 100;'.format(search_phrase)
    cur.execute(sql)
    vac = cur.fetchall()
    con.close()
    data_list = []
    for i in vac:
        data_list.append('<a href="https://hh.ru/vacancy/' + str(i[0]) + '">' + str(i[0]) + '</a>')
    return str(data_list)


def get_statistics_data(chart_name, cursor):
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


def get_time_series_data(cursor):
    month_tuples = (('01', 'январь', '31'), ('02', 'февраль', "29"), ('03', 'март', '31'),
                    ('04', 'апрель', '30'), ('05', 'май', '31'), ('06', 'июнь', '30'),
                    ('07', 'июль', '31'), ('08', 'август', '31'), ('09', 'сентябрь', '30'),
                    ('10', 'октябрь', '31'), ('11', 'ноябрь', '30'), ('12', 'декабрь', '31'))

    year_tuple = utils.years_tuple()
    print(year_tuple)
    head_time_series = [['Месяц']]
    output_list = []
    for y in year_tuple:
        head_time_series[0].append(str(y))
        for n, month in enumerate(month_tuples):
            # Запрашиваем количество вакансий за месяц
            sql = f'SELECT DISTINCT id ' \
                  f'FROM calendar ' \
                  f'WHERE data ' \
                  f'BETWEEN "{str(y)}-{month[0]}-01T00:00:00+03:00" and "{str(y)}-{month[0]}-{month[2]}T23:59:59+03:00";'
            cursor.execute(sql)
            vacancies_tuple = (cursor.fetchall())
            print(vacancies_tuple)
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


def get_salary_data_with_year(cursor, chart_name):
    experience_ranges = dict(noExperience=[], between1And3=[], between3And6=[], moreThan6=[])
    data = [['Range']]
    for year in utils.years_tuple():
        data[0].append(str(year))
        request = f'SELECT data, popularity ' \
                  f'FROM charts ' \
                  f'WHERE chart_name="{chart_name}" AND year={str(year)};'
        cursor.execute(request)
        statistics_data = cursor.fetchall()
        for i in statistics_data:
            experience_ranges[i[0]].append(i[1])
    for i in experience_ranges:
        rang_data = experience_ranges[i]
        rang_data.insert(0, i)
        data.append(rang_data)
    return data


def get_vac_with_salary(cursor, exp):
    today = date.today()
    delta = timedelta(days=30)
    last_month = today - delta
    sql = f"SELECT * FROM vac_with_salary WHERE experience = '{exp}' AND" \
          f" published_at BETWEEN '{last_month}' AND '{today}' ORDER BY published_at ASC;"
    print(sql)
    cursor.execute(sql)
    response = cursor.fetchall()
    chart_data_list = []
    # Подставляем зарплату в соответствующую колонку данных графика.
    # <a href="https://habr.com/ru/article/569026/">первое полугодие 2021 г., </a>
    for i in response:
        template = f"[new Date('{i[1]}'),{i[2]},'<a href=\"{i[4]}\">{i[2]}</a>'],\n"
        chart_data_list.append(template)
    chart_data = ''.join(chart_data_list)
    print(chart_data)
    return chart_data


def get_data_with_year(cursor, year, chart_name, sort=True):
    request = f"""
    SELECT data, popularity FROM charts WHERE chart_name='{chart_name}' AND year='{year}';
    """
    head = [['Type', 'Popularity']]
    cursor.execute(request)
    statistics_data = cursor.fetchall()
    data_list = []
    print(request)
    for i in statistics_data:
        data_list.append(list(i))
    data_list.sort(reverse=sort
                   , key=itemgetter(1))
    return head + data_list


def get_framework_data_with_year(cursor, year, chart_name, sort=True):
    request = f"""
    SELECT data, popularity, parent FROM charts WHERE chart_name='{chart_name}' AND year='{year}';
    """
    head = [['Framework', 'Popularity', 'Language']]
    cursor.execute(request)
    statistics_data = cursor.fetchall()
    data_list = []
    print(request)
    for i in statistics_data:
        data_list.append(list(i))
    data_list.sort(reverse=sort
                   , key=itemgetter(1))
    print(head + data_list)
    return head + data_list


@app.route('/unit_test_frameworks')
def unit_test_frameworks():
    """Unit test frameworks popularity page"""
    chart = 'frameworks'
    return render_template(
        '/unit_test_frameworks.html',
        # name='языков программирования',
        chart2019=get_framework_data_with_year(cur(), 2019, chart),
        chart2020=get_framework_data_with_year(cur(), 2020, chart),
        chart2021=get_framework_data_with_year(cur(), 2021, chart),
    )


@app.route('/schedule_type')
def schedule_type():
    """Schedule type popularity page"""

    return render_template(
        '/schedule_type.html',
        schedule_type2019=get_data_with_year(cur(), 2019, 'schedule_type'),
        schedule_type2020=get_data_with_year(cur(), 2020, 'schedule_type'),
        schedule_type2021=get_data_with_year(cur(), 2021, 'schedule_type')
    )


@app.route('/employment_type')
def employment_type():
    """Employment type popularity page"""
    employment_type2019 = get_data_with_year(cur(), 2019, 'employment_type')
    import copy
    employment_table2019 = copy.deepcopy(employment_type2019)
    employment_table2019.remove(['Type', 'Popularity'])
    sum_vac = 0
    for i in employment_table2019:
        sum_vac += i[1]
    for i in employment_table2019:
        percent = str(round(i[1]/sum_vac * 100, 1))
        i.append(percent)

    employment_type2020 = get_data_with_year(cur(), 2020, 'employment_type')
    employment_table2020 = copy.deepcopy(employment_type2020)
    employment_table2020.remove(['Type', 'Popularity'])
    sum_vac = 0
    for i in employment_table2020:
        sum_vac += i[1]
    for i in employment_table2020:
        percent = str(round(i[1] / sum_vac * 100, 1))
        i.append(percent)

    employment_type2021 = get_data_with_year(cur(), 2021, 'employment_type')
    employment_table2021 = copy.deepcopy(employment_type2021)
    employment_table2021.remove(['Type', 'Popularity'])
    sum_vac = 0
    for i in employment_table2021:
        sum_vac += i[1]
    for i in employment_table2021:
        percent = str(round(i[1] / sum_vac * 100, 1))
        i.append(percent)
    return render_template(
        '/employment_type.html',
        employment_type_chart_2019=employment_type2019,
        employment_type_table_2019=employment_table2019,
        employment_type_chart_2020=employment_type2020,
        employment_type_table_2020=employment_table2020,
        employment_type_chart_2021=employment_type2021,
        employment_type_table_2021=employment_table2021
    )


@app.route('/experience')
def experience():
    """Schedule type popularity page"""
    experience_list = get_statistics_data('experience', cur())
    return render_template(
        '/experience.html',
        # experience=sorted(experience_list, key=itemgetter(1), reverse=True)
        experience2019=get_data_with_year(cur(), 2019, 'experience'),
        experience2020=get_data_with_year(cur(), 2020, 'experience'),
        experience2021=get_data_with_year(cur(), 2021, 'experience')
    )


@app.route('/with_salary')
def with_salary():
    """Schedule type popularity page"""
    return render_template(
        '/with_salary.html',
        with_salary2019=get_data_with_year(cur(), 2019, 'with_salary'),
        with_salary2020=get_data_with_year(cur(), 2020, 'with_salary'),
        with_salary2021=get_data_with_year(cur(), 2021, 'with_salary')
    )


@app.route('/time_series')
def time_series():
    """Time series page"""
    return render_template(
        '/time_series.html',
        time_series=get_time_series_data(cur())
    )


@app.route('/salary')
def salary():
    """Time series page"""
    return render_template(
        '/salary.html',
        salary=get_salary_data_with_year(cur(), 'salary'),
        no_experience_salary=get_vac_with_salary(cur(), 'noExperience'),
        between1And3_salary=get_vac_with_salary(cur(), 'between1And3'),
        between3And6_salary=get_vac_with_salary(cur(), 'between3And6'),
        moreThan6e_salary=get_vac_with_salary(cur(), 'moreThan6'),
    )


@app.route('/key_skills')
def key_skills():
    """Key skills popularity page"""
    key_skills_list = get_statistics_data('key_skills', cur())
    for i in key_skills_list:
        i.append(i[0])
    sorted_key_skills_list = sorted(key_skills_list, key=itemgetter(1), reverse=True)
    return render_template(
        '/key_skills.html',
        key_skills=sorted_key_skills_list[:50]
    )


@app.route('/programming_languages')
def programming_languages():
    """Load testing tools page"""
    chart = 'languages'
    return render_template(
        '/pie_chart_with_year.html',
        name='языков программирования',
        chart2019=get_data_with_year(cur(), 2019, chart),
        chart2020=get_data_with_year(cur(), 2020, chart),
        chart2021=get_data_with_year(cur(), 2021, chart),
    )


@app.route('/load_testing_tools')
def load_testing_tool():
    """Load testing tools page"""
    chart = 'load_testing_tools'
    return render_template(
        '/pie_chart_with_year.html',
        name='инструментов тестирования производительности',
        chart2019=get_data_with_year(cur(), 2019, chart),
        chart2020=get_data_with_year(cur(), 2020, chart),
        chart2021=get_data_with_year(cur(), 2021, chart),
    )


@app.route('/bdd_frameworks')
def bdd_frameworks():
    """BDD framework page"""
    chart = 'bdd_frameworks'
    return render_template(
        '/pie_chart_with_year.html',
        name='фреймворков BDD',
        chart2019=get_data_with_year(cur(), 2019, chart),
        chart2020=get_data_with_year(cur(), 2020, chart),
        chart2021=get_data_with_year(cur(), 2021, chart),
    )


@app.route('/web_ui_tools')
def web_ui_tools():
    """Web UI testing tools page"""
    chart = 'web_ui_tools'
    return render_template(
        '/pie_chart_with_year.html',
        name='средства тестирования Web UI',
        chart2019=get_data_with_year(cur(), 2019, chart),
        chart2020=get_data_with_year(cur(), 2020, chart),
        chart2021=get_data_with_year(cur(), 2021, chart),
    )


@app.route('/mobile_testing_frameworks')
def mobile_testing_frameworks():
    """Mobile app testing tools page"""
    chart = 'mobile_testing_frameworks'
    return render_template(
        '/pie_chart_with_year.html',
        name='инструментов тестирования мобильных приложений',
        chart2019=get_data_with_year(cur(), 2019, chart),
        chart2020=get_data_with_year(cur(), 2020, chart),
        chart2021=get_data_with_year(cur(), 2021, chart),
    )


@app.route('/bugtracking_n_tms')
def bugtracking_n_tms():
    """Mobile app testing tools page"""
    chart = 'bugtracking_n_tms'
    return render_template(
        '/pie_chart_with_year.html',
        name='cистем управления тестированием, bugtracking system и т.п.',
        chart2019=get_data_with_year(cur(), 2019, chart),
        chart2020=get_data_with_year(cur(), 2020, chart),
        chart2021=get_data_with_year(cur(), 2021, chart),
    )


@app.route('/cvs')
def cvs():
    """Mobile app testing tools page"""
    chart = 'cvs'
    return render_template(
        '/pie_chart_with_year.html',
        name='систем управления версиями',
        chart2019=get_data_with_year(cur(), 2019, chart),
        chart2020=get_data_with_year(cur(), 2020, chart),
        chart2021=get_data_with_year(cur(), 2021, chart),
    )


@app.route('/ci_cd')
def ci_cd():
    """Mobile app testing tools page"""
    chart = 'ci_cd'
    return render_template(
        '/pie_chart_with_year.html',
        name='средств CI/CD',
        chart2019=get_data_with_year(cur(), 2019, chart),
        chart2020=get_data_with_year(cur(), 2020, chart),
        chart2021=get_data_with_year(cur(), 2021, chart),
    )


@app.route('/')
def home_page():
    """Home page"""
    return render_template('/index.html')


@app.route('/word_cloud')
def word_cloud():
    """Chart page"""
    return render_template('/word_cloud.html')
