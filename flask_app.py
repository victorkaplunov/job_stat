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
def index():
    return "<html> \
    <a href=" + url_for('show_vac_calendar', vac_id='30962151') + ">" + url_for('show_vac_calendar',
vac_id='30962151') + "</a><br> \
    <a href = " + url_for('show_vac_description', vac_id='30962151') + " > " + url_for('show_vac_description',
vac_id='30962151') + "</a><br>\
    <a href = " + url_for('show_vac_top_new_by_id') + " > " + url_for('show_vac_top_new_by_id') + "</a><br>\
    <a href = " + url_for('show_vac_top_new_by_data') + " > " + url_for('show_vac_top_new_by_data') + "</a><br>\
    <a href=" + url_for('show_vac_of_employer', empl_name='СофтПро') + ">" + url_for('show_vac_of_employer',
empl_name='СофтПро') + "</a><br> \
    <a href=" + url_for('chart') + " > " + "Статистика" + "</a><br>\
    </html>"


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/starter-template.css')
def starter_template():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'starter-template.css')  #, mimetype='image/vnd.microsoft.icon')


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


@app.route('/api/empl/<empl_name>')
def show_vac_of_employer(empl_name):
    """Get vacancies of given employer"""
    con = sqlite3.connect("testdb.db")
    cur = con.cursor()
    sql = 'SELECT * FROM vacancies WHERE json LIKE "%{}%";'.format(empl_name)
    cur.execute(sql)
    vac = cur.fetchall()
    con.close()
    data_list = []
    for i in vac:
        data_list.append('<a href="https://hh.ru/vacancy/' + str(i[0]) + '">' + str(i[0]) + '</a>')
    return str(data_list)


def get_statistics_data(chart_name, cursor):
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


@app.route('/')
def chart():
    """Chart page"""

    con = sqlite3.connect("testdb.db")
    cur = con.cursor()

    sql = 'SELECT COUNT(*) FROM vacancies;'
    cur.execute(sql)
    vacancies_qty = (cur.fetchone()[0])

    schedule_type_list = get_statistics_data('schedule_type', cur)
    languages_list = get_statistics_data('languages', cur)

    lt_frameworks_list = get_statistics_data('lt_frameworks', cur)
    bdd_frameworks_list = get_statistics_data('bdd_frameworks', cur)
    web_ui_tools_list = get_statistics_data('web_ui_tools', cur)
    mobile_testing_frameworks_list = get_statistics_data('mobile_testing_frameworks', cur)
    bugtracking_n_tms_list = get_statistics_data('bugtracking_n_tms', cur)
    cvs_list = get_statistics_data('cvs', cur)

    con.close()
    return render_template('/chart.html',
                           vacancies_qty=vacancies_qty,
                           schedule_type=sorted(schedule_type_list, key=itemgetter(1), reverse=True),
                           languages=sorted(languages_list, key=itemgetter(1), reverse=True),
                           lt_frameworks=sorted(lt_frameworks_list, key=itemgetter(1), reverse=True),
                           bdd_frameworks=sorted(bdd_frameworks_list, key=itemgetter(1), reverse=True),
                           web_ui_tools=sorted(web_ui_tools_list, key=itemgetter(1), reverse=True),
                           mobile_testing_frameworks=sorted(mobile_testing_frameworks_list,
                                                            key=itemgetter(1), reverse=True),
                           bugtracking_n_tms=sorted(bugtracking_n_tms_list, key=itemgetter(1), reverse=True),
                           cvs=sorted(cvs_list, key=itemgetter(1), reverse=True)
                           )


@app.route('/unit_test_frameworks')
def unit_test_frameworks():
    """Unit test frameworks popularity page"""
    con = sqlite3.connect("testdb.db")
    cur = con.cursor()
    frameworks_list = get_statistics_data('frameworks', cur)
    frameworks_list = sorted(frameworks_list, key=itemgetter(1), reverse=True)
    frameworks_list.insert(0, ['Framework', 'Popularity', 'Language'])
    return render_template(
        '/unit_test_frameworks.html',
        frameworks=frameworks_list

    )


@app.route('/schedule_type')
def schedule_type():
    """Schedule type popularity page"""
    con = sqlite3.connect("testdb.db")
    cur = con.cursor()
    schedule_type_list = get_statistics_data('schedule_type', cur)
    return render_template(
        '/chart_schedule_type.html',
        schedule_type=sorted(schedule_type_list, key=itemgetter(1), reverse=True)

    )


@app.route('/programming_languages')
def programming_languages():
    """Schedule type popularity page"""
    con = sqlite3.connect("testdb.db")
    cur = con.cursor()
    languages_list = get_statistics_data('languages', cur)
    return render_template(
        '/programming_languages.html',
        languages=sorted(languages_list, key=itemgetter(1), reverse=True)

    )


@app.route('/load_testing_tool')
def load_testing_tool():
    """Schedule type popularity page"""
    lt_frameworks_list = get_statistics_data('lt_frameworks', cur())
    return render_template(
        '/load_testing_tool.html',
        lt_frameworks=sorted(lt_frameworks_list, key=itemgetter(1), reverse=True)
    )


@app.route('/index')
def index_boot():
    """Chart page"""

    con = sqlite3.connect("testdb.db")
    cur = con.cursor()

    sql = 'SELECT COUNT(*) FROM vacancies;'
    cur.execute(sql)
    vacancies_qty = (cur.fetchone()[0])

    schedule_type_list = get_statistics_data('schedule_type', cur)
    languages_list = get_statistics_data('languages', cur)

    lt_frameworks_list = get_statistics_data('lt_frameworks', cur)
    bdd_frameworks_list = get_statistics_data('bdd_frameworks', cur)
    web_ui_tools_list = get_statistics_data('web_ui_tools', cur)
    mobile_testing_frameworks_list = get_statistics_data('mobile_testing_frameworks', cur)
    bugtracking_n_tms_list = get_statistics_data('bugtracking_n_tms', cur)
    cvs_list = get_statistics_data('cvs', cur)
    return render_template('/index.html',
                           vacancies_qty=vacancies_qty,
                           schedule_type=sorted(schedule_type_list, key=itemgetter(1), reverse=True),
                           languages=sorted(languages_list, key=itemgetter(1), reverse=True),
                           lt_frameworks=sorted(lt_frameworks_list, key=itemgetter(1), reverse=True),
                           bdd_frameworks=sorted(bdd_frameworks_list, key=itemgetter(1), reverse=True),
                           web_ui_tools=sorted(web_ui_tools_list, key=itemgetter(1), reverse=True),
                           mobile_testing_frameworks=sorted(mobile_testing_frameworks_list,
                                                            key=itemgetter(1), reverse=True),
                           bugtracking_n_tms=sorted(bugtracking_n_tms_list, key=itemgetter(1), reverse=True),
                           cvs=sorted(cvs_list, key=itemgetter(1), reverse=True)
                           )

