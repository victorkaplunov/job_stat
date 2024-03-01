import os
import copy
from operator import itemgetter
import json
from functools import lru_cache

from flask import Flask, send_from_directory, url_for, render_template
from flask_bootstrap import Bootstrap

import utils
from db_client import Database
from config import ConfigObj
from chart_generator import PieChartGen

db = Database()
config = ConfigObj()


def create_app():
    application = Flask(__name__)
    Bootstrap(application)
    return application


app = create_app()


@app.route('/')
def home_page():
    """Home page"""
    return render_template('/index.html')


@app.route('/api')
def api():
    return f"""
<html>
<a href="{url_for('show_vac_calendar', vacancy_id='14658327')}">
        {url_for('show_vac_calendar', vacancy_id='14658327')}</a>
<br>
<a href="{url_for('show_vac_description', vacancy_id='14658327')}">
        {url_for('show_vac_description', vacancy_id='14658327')}</a>
<br>
<a href="{url_for('show_vac_top_new_by_id')}">{url_for('show_vac_top_new_by_id')}"</a>
<br>
<a href="{url_for('show_vac_top_new_by_date')}">{url_for('show_vac_top_new_by_date')}"</a>
<br>
<a href="{url_for('search_vac', search_phrase='Python')}">
    {url_for('search_vac', search_phrase='Python')}"</a>
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


@app.route('/api/vac/cal/<int:vacancy_id>')
def show_vac_calendar(vacancy_id):
    """Show the publication data of vacancy with the given id"""
    return db.get_date_from_calendar_by_vacancy(vacancy_id=vacancy_id)


@app.route('/api/vac/<int:vacancy_id>')
def show_vac_description(vacancy_id):
    """Show the description of vacancy with the given id"""
    vacancy_json = db.get_vacancy_by_id(vacancy_id=vacancy_id).json
    return json.loads(vacancy_json)


@app.route('/api/vac/last100id')
def show_vac_top_new_by_id():
    """Get last 100 vacancies sorted by id"""
    vacancies = db.get_vacancy_ordered_by_id()
    data_list = [f'<a href="https://hh.ru/vacancy/{v.id}">{v.id}</a>' for v in vacancies]
    return str(data_list)


@app.route('/api/vac/last100date')
def show_vac_top_new_by_date():
    """Get last 100 vacancies sorted by last publication data"""
    publications = db.get_vacancy_publication_ordered_by_date()
    output = [f'<a href="https://hh.ru/vacancy/{v.id}">{v.id}</a>' for v in publications]
    return str(output)


@app.route('/api/search/<search_phrase>')
def search_vac(search_phrase):
    """Find vacancies by search phrase in JSON"""
    vacancies = db.find_vacancy_by_substring(search_phrase)
    output = [f'<a href="https://hh.ru/vacancy/{v.id}">{v.id}</a>' for v in vacancies]
    return str(output)


@app.route('/time_series')
@lru_cache(maxsize=None)
def time_series():
    """Time series page"""
    return render_template(
        '/time_series.html',
        title='Количество вакансий по месяцам и неделям.',
        vacancy_count_week_by_week=utils.get_vacancies_qty_week_by_week(),
        vacancy_rate_by_year=utils.get_vacancies_qty_by_month_of_year(),
        vacancy_count_day_by_week=utils.get_vacancies_qty_by_day_of_week(),
           )


@app.route('/salary')
def salary():
    """Time series page"""
    return render_template(
        '/salary.html',
        title='Заработная плата в зависимости от опыта.',
        salary=utils.get_salary_data_per_year(),
        no_experience_salary=utils.get_vacancies_with_salary(experience='noExperience'),
        between1And3_salary=utils.get_vacancies_with_salary(experience='between1And3'),
        between3And6_salary=utils.get_vacancies_with_salary(experience='between3And6'),
        moreThan6e_salary=utils.get_vacancies_with_salary(experience='moreThan6'))


@app.route('/top_employers')
def top_employers():
    """Employers by vacancies quantity page"""
    key_skills_list = utils.get_data_for_horizontal_bar_chart('top_employers')
    print(f'{key_skills_list=}')
    for i in key_skills_list:
        i.append(i[0])
    sorted_key_skills_list = sorted(key_skills_list, key=itemgetter(1), reverse=True)
    current_year = config.YEARS[-1]
    return render_template(
        '/horizontal_bar.html',
        title='Топ 50 работодателей',
        subtitle=f'по количеству вакансий в {current_year} году.',
        chart_data=sorted_key_skills_list
    )


@app.route('/salary_by_category')
def salary_by_category():
    """Salary by category"""
    return render_template(
        '/tmp.html',
        chart_data=utils.get_salary_by_category_data(),
        title='Медианная зарплата в зависимости от упоминания языка.'
    )


@app.route('/schedule_type')
def schedule_type():
    """Schedule type popularity page"""
    chart = PieChartGen(chart_title='Популярность режимов работы',
                        chart_name='schedule_type')
    return render_template(
        '/pie_chart_with_year.html',
        title='Режимы работы.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/employment_type')
def employment_type():
    """Employment type popularity page"""
    title = 'Популярность видов найма '
    charts = ''
    divs = ''
    for year in utils.reversed_years():
        data = utils.get_data_per_year(year=year, chart_name='employment_type')

        # Данные для таблицы
        table_data = copy.deepcopy(data)
        table_data.remove(['Type', 'Popularity'])
        sum_vac = 0
        for i in table_data:
            sum_vac += i[1]
        for i in table_data:
            percent = str(round(i[1] / sum_vac * 100, 1))
            i.append(percent)

        # Генерация функций JavaScript для отдельных графиков
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
    chart = PieChartGen(chart_title='Требования к опыту ',
                        chart_name='experience')
    return render_template(
        '/pie_chart_with_year.html',
        title='Требуемый опыт работы.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/with_salary')
def with_salary():
    chart = PieChartGen(chart_title='Количество вакансий с указанной зарплатой',
                        chart_name='with_salary')
    return render_template(
        '/pie_chart_with_year.html',
        title='Количество вакансий с указанной зарплатой.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/key_skills')
def key_skills():
    """Key skills popularity page"""
    key_skills_list = utils.get_data_for_horizontal_bar_chart('key_skills')
    for i in key_skills_list:
        i.append(i[0])
    sorted_key_skills_list = sorted(key_skills_list, key=itemgetter(1), reverse=True)
    return render_template(
        '/horizontal_bar.html',
        title='Ключевые навыки.',
        subtitle='Пятьдесят наиболее популярных тегов',
        chart_data=sorted_key_skills_list[:50]
    )


@app.route('/programming_languages')
def programming_languages():
    """Programming languages page"""
    chart = PieChartGen(chart_title='Популярность языков программирования',
                        chart_name='languages')
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность языков программирования.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/unit_test_frameworks')
def unit_test_frameworks():
    """Unit test frameworks popularity page"""
    chart = 'frameworks'
    title = 'Популярность фреймворков для юнит-тестирования'
    result = utils.render_framework_charts(title, chart)
    return render_template(
        '/unittesting_frameworks_chart.html',
        title='Популярность фреймворков для юнит-тестирования.',
        charts_function=result[0],
        divs=result[1]
    )


@app.route('/load_testing_tools')
def load_testing_tool():
    """Load testing tools page"""
    chart = PieChartGen(chart_title='Популярность инструментов тестирования производительностия',
                        chart_name='load_testing_tools')
    return render_template(
        '/pie_chart_with_year.html',
        title='Средства нагрузочного тестирования.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/monitoring_tools')
def monitoring_tools():
    """ Monitoring tools page"""
    chart = PieChartGen(chart_title='Популярность различных средств мониторинга',
                        chart_name='monitoring')
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность различных средств мониторинга.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/bdd_frameworks')
def bdd_frameworks():
    """BDD framework page"""
    chart = PieChartGen(chart_title='Популярность фреймворков BDD',
                        chart_name='bdd_frameworks')
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность фреймворков BDD.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/web_ui_tools')
def web_ui_tools():
    """Web UI testing tools page"""
    chart = PieChartGen(chart_title='Популярность средства тестирования Web UI',
                        chart_name='web_ui_tools')
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность средства тестирования Web UI.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/mobile_testing_frameworks')
def mobile_testing_frameworks():
    """Mobile app testing tools page"""
    chart = PieChartGen(chart_title='Популярность инструментов тестирования мобильных приложений',
                        chart_name='mobile_testing_frameworks')
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность инструментов тестирования мобильных приложений.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/bugtracking_n_tms')
def bugtracking_n_tms():
    """Mobile app testing tools page"""
    chart = PieChartGen(chart_title='Популярность систем управления тестированием, bugtracking system и т.п.',
                        chart_name='bugtracking_n_tms')
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность систем управления тестированием, bugtracking system и т.п.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/cvs')
def cvs():
    """CVS page"""
    chart = PieChartGen(chart_title='Популярность систем управления версиями',
                        chart_name='cvs')
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность систем управления версиями.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/ci_cd')
def ci_cd():
    """Mobile app testing tools page"""
    chart = PieChartGen(chart_title='Популярность средств CI/CD',
                        chart_name='ci_cd')
    return render_template(
        '/pie_chart_with_year.html',
        title='Популярность средств CI/CD.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/word_cloud')
def word_cloud():
    """Chart page"""
    return render_template('/word_cloud.html',
                           title='"Облако слов" на основе текстов вакансий.'
                           )
