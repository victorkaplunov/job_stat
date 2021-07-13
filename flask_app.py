from operator import itemgetter
from flask import Flask, send_from_directory, url_for, render_template
from flask_bootstrap import Bootstrap
import os
import sqlite3
import json

app = Flask(__name__)
bootstrap = Bootstrap(app)
id_list = []
l_host = "http://127.0.0.1:5000"


def cur():
    con = sqlite3.connect("testdb.db")
    return con.cursor()


@app.route('/api')
def api():
    return "<html> \
    <a href=" + url_for('show_vac_calendar', vac_id='14658327') + ">" + url_for('show_vac_calendar',
                                                                                vac_id='14658327') + "</a><br> \
    <a href = " + url_for('show_vac_description', vac_id='14658327') + " > " + url_for('show_vac_description',
                                                                                       vac_id='14658327') + "</a><br>\
    <a href = " + url_for('show_vac_top_new_by_id') + " > " + url_for('show_vac_top_new_by_id') + "</a><br>\
    <a href = " + url_for('show_vac_top_new_by_data') + " > " + url_for('show_vac_top_new_by_data') + "</a><br>\
    <a href=" + url_for('search_vac', search_phrase='Python') + ">" + url_for('search_vac',
                                                                              search_phrase='Python') + "</a><br> \
    </html>"


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

    year_tuple = ('2019', '2020', '2021')

    head_time_series = [['Месяц']]
    output_list = []
    for y in year_tuple:
        head_time_series[0].append(y)
        for n, month in enumerate(month_tuples):
            # Запрашиваем количество вакансий за месяц
            sql = f'SELECT DISTINCT id ' \
                  f'FROM calendar ' \
                  f'WHERE data ' \
                  f'BETWEEN "{y}-{month[0]}-01T00:00:00+03:00" and "{y}-{month[0]}-{month[2]}T23:59:59+03:00";'
            cursor.execute(sql)
            vacancies_tuple = (cursor.fetchall())
            if y == '2019':
                # Данные за февраль неполные, поэтому вместо них пишем ноль
                if month[1] == 'февраль':
                    output_list.append([month[1], 0])
                else:
                    output_list.append([month[1], len(vacancies_tuple)])
            else:
                output_list[n].append(len(vacancies_tuple))
    output_list = head_time_series + output_list
    return output_list


def get_data_with_year(cursor, year, chart_name):
    request = f'SELECT data, popularity ' \
              f'FROM charts ' \
              f'WHERE chart_name="{chart_name}" AND year={str(year)};'
    head = [['Type', 'Popularity']]
    cursor.execute(request)
    statistics_data = cursor.fetchall()
    data_list = []
    for i in statistics_data:
        data_list.append(list(i))
    data_list.sort(reverse=True, key=itemgetter(1))
    return head + data_list


@app.route('/unit_test_frameworks')
def unit_test_frameworks():
    """Unit test frameworks popularity page"""
    frameworks_list = get_statistics_data('frameworks', cur())
    frameworks_list = sorted(frameworks_list, key=itemgetter(1), reverse=True)
    frameworks_list.insert(0, ['Framework', 'Popularity', 'Language'])
    return render_template(
        '/unit_test_frameworks.html',
        frameworks=frameworks_list
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
    """Schedule type popularity page"""
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
    return render_template(
        '/employment_type.html',
        employment_type_chart_2019=employment_type2019,
        employment_type_table_2019=employment_table2019,
        employment_type_chart_2020=employment_type2020,
        employment_type_table_2020=employment_table2020
    )


@app.route('/experience')
def experience():
    """Schedule type popularity page"""
    experience_list = get_statistics_data('experience', cur())
    return render_template(
        '/chart_experience.html',
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
        with_salary2020=get_data_with_year(cur(), 2020, 'with_salary')
    )


@app.route('/time_series')
def time_series():
    """Time series page"""
    print(get_time_series_data(cur()))
    return render_template(
        '/time_series.html',
        time_series=get_time_series_data(cur())
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
    """Schedule type popularity page"""
    print(get_data_with_year(cur(), 2019, 'languages'))
    return render_template(
        '/programming_languages.html',
        languages2019=get_data_with_year(cur(), 2019, 'languages'),
        languages2020=get_data_with_year(cur(), 2020, 'languages'),
        languages2021=get_data_with_year(cur(), 2021, 'languages'),
    )


@app.route('/load_testing_tool')
def load_testing_tool():
    """Schedule type popularity page"""
    lt_frameworks_list = get_statistics_data('load_testing_tools', cur())
    return render_template(
        '/load_testing_tool.html',
        lt_frameworks=sorted(lt_frameworks_list, key=itemgetter(1), reverse=True)
    )


@app.route('/bdd_frameworks')
def bdd_frameworks():
    """Schedule type popularity page"""
    bdd_frameworks_list = get_statistics_data('bdd_frameworks', cur())
    return render_template(
        '/bdd_frameworks.html',
        bdd_frameworks=sorted(bdd_frameworks_list, key=itemgetter(1), reverse=True)
    )


@app.route('/web_ui_tools')
def web_ui_tools():
    """Schedule type popularity page"""
    web_ui_tools_list = get_statistics_data('web_ui_tools', cur())
    return render_template(
        '/web_ui_tools.html',
        web_ui_tools=sorted(web_ui_tools_list, key=itemgetter(1), reverse=True)
    )


@app.route('/mobile_testing_frameworks')
def mobile_testing_frameworks():
    """Schedule type popularity page"""
    mobile_testing_frameworks_list = get_statistics_data('mobile_testing_frameworks', cur())
    return render_template('/mobile_testing_frameworks.html',
                           mobile_testing_frameworks=sorted(mobile_testing_frameworks_list,
                                                            key=itemgetter(1), reverse=True))


@app.route('/bugtracking_n_tms')
def bugtracking_n_tms():
    """Schedule type popularity page"""
    bugtracking_n_tms_list = get_statistics_data('bugtracking_n_tms', cur())
    return render_template(
        '/bugtracking_n_tms.html',
        bugtracking_n_tms=sorted(bugtracking_n_tms_list,
                                 key=itemgetter(1), reverse=True))


@app.route('/cvs')
def cvs():
    """CVS popularity page"""
    cvs_list = get_statistics_data('cvs', cur())
    return render_template('/cvs.html', cvs=sorted(cvs_list, key=itemgetter(1), reverse=True))


@app.route('/ci_cd')
def ci_cd():
    """CI/CD system popularity page"""
    ci_cd = get_statistics_data('ci_cd', cur())
    return render_template('/ci_cd.html', ci_cd=sorted(ci_cd, key=itemgetter(1), reverse=True))


@app.route('/')
def home_page():
    """Home page"""
    con = sqlite3.connect("testdb.db")
    cur = con.cursor()
    sql = 'SELECT COUNT(*) FROM vacancies;'
    cur.execute(sql)
    vacancies_qty = (cur.fetchone()[0])
    return render_template('/index.html', vacancies_qty=vacancies_qty)


@app.route('/word_cloud')
def word_cloud():
    """Chart page"""
    return render_template('/word_cloud.html')
