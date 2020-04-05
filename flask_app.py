from flask import Flask, send_from_directory, url_for, render_template
import os
import sqlite3
import json

app = Flask(__name__)
id_list = []
l_host = "http://127.0.0.1:5000"


@app.route('/')
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
    <a href=" + url_for('chart') + " > " + "Популярность языков програмирования" + "</a><br>\
    </html>"



@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/vac/cal/<int:vac_id>')
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


@app.route('/vac/<int:vac_id>')
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


@app.route('/vac/last100id')
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


@app.route('/vac/last100data')
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


@app.route('/empl/<empl_name>')
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


@app.route('/statistics')
def chart():
    languages_list = ['Java', 'Python', 'JavaScript', 'C#', "PPH", 'C++', 'Ruby', 'Groovy']
    output = []
    for i in languages_list:
        con = sqlite3.connect("testdb.db")
        cur = con.cursor()
        sql = f"SELECT json FROM vacancies WHERE json LIKE '%{i}%';"
        cur.execute(sql)
        vac = cur.fetchall()
        output.append([i, len(vac)])
    frameworks_list = ['Pytest', 'Py.test', 'Unittest', 'xUnit', 'Mocha', 'Serenity', 'Robot Framework']
    output1 = []
    for i in frameworks_list:
        con = sqlite3.connect("testdb.db")
        cur = con.cursor()
        sql = f"SELECT json FROM vacancies WHERE json LIKE '%{i}%';"
        cur.execute(sql)
        vac = cur.fetchall()
        output1.append([i, len(vac)])
    con.close()
    return render_template('/chart.html', leng=output, frame=output1)
