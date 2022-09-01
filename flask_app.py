from operator import itemgetter
from flask import Flask, send_from_directory, url_for, render_template
from flask_bootstrap import Bootstrap
import os
import sqlite3
import json
import utils
import copy
from functools import lru_cache

app = Flask(__name__)
bootstrap = Bootstrap(app)
id_list = []
l_host = "http://127.0.0.1:5000"


def cur():
    con = sqlite3.connect("testdb.db")
    return con.cursor()


@app.route('/')
def home_page():
    """Home page"""
    return render_template('/index.html')


@app.route('/api')
def api():
    return f"""
<html>
<a href="{url_for('show_vac_calendar', vac_id='14658327')}">{url_for('show_vac_calendar', vac_id='14658327')}</a>
<br>
<a href="{url_for('show_vac_description', vac_id='14658327')}">{url_for('show_vac_description', vac_id='14658327')}</a>
<br>
<a href="{url_for('show_vac_top_new_by_id')}">{url_for('show_vac_top_new_by_id')}"</a>
<br>
<a href="{url_for('show_vac_top_new_by_data')}">{url_for('show_vac_top_new_by_data')}"</a>
<br>
<a href="{url_for('search_vac', search_phrase='Python')}">{url_for('search_vac', search_phrase='Python')}"</a>
<br>
</html>"""


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/starter-template.css')
def starter_template():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'starter-template.css')


@app.route('/api/vac/cal/<int:vac_id>')
def show_vac_calendar(vac_id):
    """Show the publication data of vacancy with the given id"""
    con = sqlite3.connect("testdb.db")
    cursor = cur()
    sql = "SELECT data FROM calendar WHERE id = " + str(vac_id)
    cursor.execute(sql)
    vac = cursor.fetchall()
    con.close()
    data_list = []
    for i in vac:
        data_list.append(i[0])
    return str(data_list)


@app.route('/api/vac/<int:vac_id>')
def show_vac_description(vac_id):
    """Show the description of vacancy with the given id"""
    con = sqlite3.connect("testdb.db")
    cursor = con.cursor()
    sql = "SELECT * FROM vacancies WHERE id = " + str(vac_id)
    cursor.execute(sql)
    vac = cursor.fetchone()
    return str(
        json.loads(vac[1])['employer']["name"] + "\n" +
        json.loads(vac[1])["name"] + "\n" +
        json.loads(vac[1])['description'])


@app.route('/api/vac/last100id')
def show_vac_top_new_by_id():
    """Get last 100 vacancies sorted by id"""
    con = sqlite3.connect("testdb.db")
    cursor = con.cursor()
    sql = "SELECT * FROM calendar ORDER BY id DESC LIMIT 100;"
    cursor.execute(sql)
    vac = cursor.fetchall()
    con.close()
    data_list = []
    for i in vac:
        data_list.append('<a href="https://hh.ru/vacancy/' + str(i[0]) + '">' + str(i[0]) + '</a>')
    return str(data_list)


@app.route('/api/vac/last100data')
def show_vac_top_new_by_data():
    """Get last 100 vacancies sorted by last publication data"""
    con = sqlite3.connect("testdb.db")
    cursor = con.cursor()
    sql = "SELECT * FROM calendar ORDER BY data DESC LIMIT 100;"
    cursor.execute(sql)
    vac = cursor.fetchall()
    con.close()
    data_list = []
    for i in vac:
        data_list.append('<a href="https://hh.ru/vacancy/' + str(i[0]) + '">' + str(i[0]) + '</a>')
    return str(data_list)


@app.route('/api/search/<search_phrase>')
def search_vac(search_phrase):
    """Get vacancies with search phrase in JSON"""
    con = sqlite3.connect("testdb.db")
    cursor = con.cursor()
    sql = 'SELECT * FROM vacancies WHERE json LIKE "%{}%" ORDER BY id DESC LIMIT 100;'.format(search_phrase)
    cursor.execute(sql)
    vac = cursor.fetchall()
    con.close()
    data_list = []
    for i in vac:
        data_list.append('<a href="https://hh.ru/vacancy/' + str(i[0]) + '">' + str(i[0]) + '</a>')
    return str(data_list)


@app.route('/time_series')
@lru_cache(maxsize=32)
def time_series():
    """Time series page"""
    return render_template(
        '/time_series.html',
        title='Количество вакансий по месяцам и неделям.',
        vacancy_count_week_by_week=utils.vacancy_count_week_by_week(cur()),
        vacancy_rate_by_year=utils.get_vacancy_count_by_year(cur()),
        vacancy_count_day_by_week=utils.vacancy_count_day_by_week(cur()),
           )


@app.route('/salary')
def salary():
    """Time series page"""
    return render_template(
        '/salary.html',
        title='Заработная плата в зависимости от опыта.',
        salary=utils.get_salary_data_with_year(cur()),
        no_experience_salary=utils.get_vac_with_salary(cur(), 'noExperience'),
        between1And3_salary=utils.get_vac_with_salary(cur(), 'between1And3'),
        between3And6_salary=utils.get_vac_with_salary(cur(), 'between3And6'),
        moreThan6e_salary=utils.get_vac_with_salary(cur(), 'moreThan6'))


@app.route('/salary_by_category')
def salary_by_category():
    """Salary by category"""
    chart = 'frameworks'
    title = 'Медианная зарплата в зависимости от упоминания языка.'
    result = utils.render_salary_by_category_charts(title, chart)
    return render_template(
        '/tmp.html',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/schedule_type')
def schedule_type():
    """Schedule type popularity page"""
    chart = 'schedule_type'
    title = 'Популярность режимов работы'
    result = utils.render_pie_charts(utils.reversed_years(), title, chart, cur())
    return render_template(
        '/pie_chart_with_year.html',
        title='Режимы работы.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/employment_type')
def employment_type():
    """Employment type popularity page"""
    title = 'Популярность видов найма '
    charts = ''
    divs = ''
    for year in utils.reversed_years():
        data = utils.get_data_with_year(cur(), year, 'employment_type')  # Данные для графика

        # Данные для таблицы
        table_data = copy.deepcopy(data)
        table_data.remove(['Type', 'Popularity'])
        sum_vac = 0
        for i in table_data:
            sum_vac += i[1]
        for i in table_data:
            percent = str(round(i[1] / sum_vac * 100, 1))
            i.append(percent)

        # Генерация функция JavaScript для отдельных графиков
        charts = charts + f'''

        google.charts.setOnLoadCallback(drawScheduleTypeChart{year});
        function drawScheduleTypeChart{year}() {{
        var data = google.visualization.arrayToDataTable({data});
        var options = {{'title':'{title} в {year} году.',
        chartArea:{{width:'90%',height:'80%'}},
        pieSliceTextStyle: {{fontSize: 11}}
        }};
        var chart = new google.visualization.PieChart(document.getElementById('chart_for_{year}'));
        chart.draw(data, options);
        }}
        
        google.charts.setOnLoadCallback(draw{year}Table);
        function draw{year}Table() {{
            var data = new google.visualization.DataTable();
            data.addColumn('string', 'Вид');
            data.addColumn('number', 'Количество вакансий');
            data.addColumn('string', 'Доля, %');
            data.addRows({ table_data });

            var table = new google.visualization.Table(document.getElementById('table{year}div'));

            table.draw(data, {{width: '100%', height: '100%'}});
          }}
        '''
        # Генерация разделов в которые будут вставляться графики.
        divs = divs + f'''
        
        <div id="chart_for_{year}" style="height: 300px;"></div>
        <div id="table{year}div"></div>
        <p>
        <hr>
        <p>
        '''
    return render_template(
        '/employment_type.html',
        title='Виды занятости.',
        charts_function=charts,
        divs=divs
    )


@app.route('/experience')
def experience():
    """Experience popularity page"""
    chart = 'experience'
    title = 'Требования к опыту '
    result = utils.render_pie_charts(utils.reversed_years(), title, chart, cur())
    return render_template(
        '/pie_chart_with_year.html',
        title='Требуемый опыт работы.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/with_salary')
def with_salary():
    chart = 'with_salary'
    title = 'Количество вакансий с указанной зарплатой '
    result = utils.render_pie_charts(utils.reversed_years(), title, chart, cur())
    return render_template(
        '/pie_chart_with_year.html',
        title='Количество вакансий с указанной зарплатой.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/key_skills')
def key_skills():
    """Key skills popularity page"""
    key_skills_list = utils.get_key_skills_data('key_skills', cur())
    for i in key_skills_list:
        i.append(i[0])
    sorted_key_skills_list = sorted(key_skills_list, key=itemgetter(1), reverse=True)
    return render_template(
        '/key_skills.html',
        title='50 наиболее популярных тегов раздела "Ключевые навыки".',
        key_skills=sorted_key_skills_list[:50]
    )


@app.route('/programming_languages')
def programming_languages():
    """Programming languages page"""
    chart = 'languages'
    title = 'Популярность языков программирования'
    result = utils.render_pie_charts(utils.reversed_years(), title, chart, cur())
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность языков программирования.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/unit_test_frameworks')
def unit_test_frameworks():
    """Unit test frameworks popularity page"""
    chart = 'frameworks'
    title = 'Популярность фреймворков для юнит-тестирования'
    result = utils.render_framework_charts(title, chart, cur())
    return render_template(
        '/unittesting_frameworks_chart.html',
        title='Популярность фреймворков для юнит-тестирования.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/load_testing_tools')
def load_testing_tool():
    """Load testing tools page"""
    chart = 'load_testing_tools'
    title = 'Популярность инструментов тестирования производительности'
    result = utils.render_pie_charts(utils.reversed_years(), title, chart, cur())
    return render_template(
        '/pie_chart_with_year.html',
        title='Средства нагрузочного тестирования.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/monitoring_tools')
def monitoring_tools():
    """ Monitoring tools page"""
    chart = 'monitoring'
    title = 'Популярность различных средств мониторинга'
    result = utils.render_pie_charts(utils.reversed_years(), title, chart, cur())
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность различных средств мониторинга.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/bdd_frameworks')
def bdd_frameworks():
    """BDD framework page"""
    chart = 'bdd_frameworks'
    title = 'Популярность фреймворков BDD'
    result = utils.render_pie_charts(utils.reversed_years(), title, chart, cur())
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность фреймворков BDD.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/web_ui_tools')
def web_ui_tools():
    """Web UI testing tools page"""
    chart = 'web_ui_tools'
    title = 'Популярность средства тестирования Web UI'
    result = utils.render_pie_charts(utils.reversed_years(), title, chart, cur())
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность средства тестирования Web UI.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/mobile_testing_frameworks')
def mobile_testing_frameworks():
    """Mobile app testing tools page"""
    chart = 'mobile_testing_frameworks'
    title = 'Популярность инструментов тестирования мобильных приложений'
    result = utils.render_pie_charts(utils.reversed_years(), title, chart, cur())
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность инструментов тестирования мобильных приложений.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/bugtracking_n_tms')
def bugtracking_n_tms():
    """Mobile app testing tools page"""
    chart = 'bugtracking_n_tms'
    title = 'Популярность систем управления тестированием, bugtracking system и т.п.'
    result = utils.render_pie_charts(utils.reversed_years(), title, chart, cur())
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность систем управления тестированием, bugtracking system и т.п.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/cvs')
def cvs():
    """Mobile app testing tools page"""
    chart = 'cvs'
    title = 'Популярность систем управления версиями'
    result = utils.render_pie_charts(utils.reversed_years(), title, chart, cur())
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность систем управления версиями.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/ci_cd')
def ci_cd():
    """Mobile app testing tools page"""
    chart = 'ci_cd'
    title = 'Популярность средств CI/CD'
    result = utils.render_pie_charts(utils.reversed_years(), title, chart, cur())
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность средств CI/CD.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/word_cloud')
def word_cloud():
    """Chart page"""
    return render_template('/word_cloud.html',
                           title='"Облако слов" на основе текстов вакансий.'
                           )
