from flask import Flask, send_from_directory, url_for, render_template
import os
import sqlite3
import json

app = Flask(__name__)
id_list = []
l_host = "http://127.0.0.1:5000"


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


@app.route('/')
def chart():
    """"""
    con = sqlite3.connect("testdb.db")
    cur = con.cursor()
    sql = 'SELECT data, popularity FROM charts WHERE chart_name="languages";'
    cur.execute(sql)
    languages_statistics = cur.fetchall()
    # Convert list of tuples to list of lists
    # print(languages_statistics)
    languages_list = []
    for i in languages_statistics:
        # print(i)
        languages_list.append(list(i))
    print(languages_list)

    sql = 'SELECT data, popularity FROM charts WHERE chart_name="frameworks";'
    cur.execute(sql)
    frameworks_statistics = cur.fetchall()
    # print(frameworks_statistics)
    # Convert list of tuples to list of lists
    frameworks_list = []
    for i in frameworks_statistics:
        # print(i)
        frameworks_list.append(list(i))
    print(frameworks_list)

    sql = 'SELECT data, popularity FROM charts WHERE chart_name="lt_frameworks";'
    cur.execute(sql)
    lt_frameworks = cur.fetchall()
    # print(frameworks_statistics)
    # Convert list of tuples to list of lists
    lt_frameworks_list = []
    for i in lt_frameworks:
        # print(i)
        lt_frameworks_list.append(list(i))
    print(lt_frameworks_list)

    con.close()
    return render_template('/chart.html', languages=languages_list,
                           frameworks=frameworks_list,
                           lt_frameworks=lt_frameworks_list
                           )
