import os
import json

from flask import Flask, send_from_directory, url_for, render_template, redirect
from flask_bootstrap import Bootstrap

import utils
from db.db_client import Database
from echarts import EchartStackedColumn, EchartTreeMap, EchartHorizontalBar, EchartBoxplot,\
    EchartHorizontalBarByCategory

db = Database()


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
<a href="{url_for('show_vac_calendar', vacancy_id='101279526')}">
        {url_for('show_vac_calendar', vacancy_id='101279526')}</a>
<br>
<a href="{url_for('show_vac_description', vacancy_id='101279526')}">
        {url_for('show_vac_description', vacancy_id='101279526')}</a>
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
def time_series():
    """Time series page"""
    return render_template(
        '/time_series.html',
        title='Количество вакансий по месяцам и неделям',
        vacancy_count_week_by_week=utils.get_vacancies_qty_week_by_week(),
        vacancy_rate_by_year=utils.get_vacancies_qty_by_month_of_year(),
        vacancy_count_day_by_week=utils.get_vacancies_qty_by_day_of_week(),
    )


@app.route('/salary')
def salary():
    """Time series page"""
    return render_template(
        '/salary.html',
        title='Заработная плата в зависимости от опыта',
        salary=utils.get_salary_data_per_year(),
        no_experience_salary=utils.get_vacancies_with_salary(experience='noExperience'),
        between1And3_salary=utils.get_vacancies_with_salary(experience='between1And3'),
        between3And6_salary=utils.get_vacancies_with_salary(experience='between3And6'),
        moreThan6e_salary=utils.get_vacancies_with_salary(experience='moreThan6'))


@app.route('/salary_by_category')
def salary_by_category():
    """Salary by category"""
    chart_1 = EchartBoxplot(name='languages',
                            title='...упоминания языка программирования.')
    chart_2 = EchartBoxplot(name='frameworks',
                            title='...тестового фреймворка.')
    chart_3 = EchartBoxplot(name='web_ui_tools',
                            title='...средства тестирования web UI.')
    chart_4 = EchartBoxplot(name='load_testing_tools',
                            title='...инструмента нагрузочного тестирования.')
    return render_template(
        '4_charts.html',
        title='Зарплаты в зависимости от...',
        description='В российских рублях, в месяц, за вычетом 13% НДФЛ.',
        chart_function_1=chart_1.get_script(),
        div_1=chart_1.get_div(),
        chart_function_2=chart_2.get_script(),
        div_2=chart_2.get_div(),
        chart_function_3=chart_3.get_script(),
        div_3=chart_3.get_div(),
        chart_function_4=chart_4.get_script(),
        div_4=chart_4.get_div()
    )


@app.route('/top_employers')
def top_employers():
    """Employers by vacancies quantity page"""
    chart = EchartHorizontalBar(name='top_employers',
                                title='Топ 50 работодателей по количеству публикаций вакансий')
    return render_template(
        'pyechart.html',
        chart_script=chart.get_script(),
        div=chart.get_div(height=2500)
    )


@app.route('/employment_and_schedule')
def employment_and_schedule():
    chart1 = EchartStackedColumn(name='employment',
                                 title='Виды занятости')
    chart2 = EchartStackedColumn(name='schedule',
                                 title='Популярность режимов работы')
    return render_template(
        '2_charts.html',
        chart_script1=chart1.get_script(),
        div1=chart1.get_div(),
        chart_script2=chart2.get_script(),
        div2=chart2.get_div(),
    )


@app.route('/experience_and_salary_mention')
def experience_and_salary_mention():
    """Experience and salary mention page"""
    chart1 = EchartStackedColumn(name='experience',
                                 title='Требования к опыту')
    chart2 = EchartStackedColumn(name='with_salary',
                                 title='Доля вакансий с указанной зарплатой')
    return render_template(
        '2_charts.html',
        chart_script1=chart1.get_script(),
        div1=chart1.get_div(),
        chart_script2=chart2.get_script(),
        div2=chart2.get_div(),
    )


@app.route('/key_skills')
def key_skills():
    """Key skills popularity page"""
    chart = EchartHorizontalBar(name='key_skills',
                                title='Наиболее популярные ключевые навыки')
    return render_template(
        'pyechart.html',
        chart_script=chart.get_script(),
        div=chart.get_div(height=2000)
    )


@app.route('/load_testing_and_monitoring_tools')
def load_testing_and_monitoring_tools():
    """Load testing tools page"""
    chart_1 = EchartStackedColumn(title='Инструменты тестирования производительности',
                                  name='load_testing_tools')
    chart_2 = EchartStackedColumn(title='Популярность генераторов сетевого трафика',
                                  name='traffic_generators')
    chart_3 = EchartStackedColumn(title='Системы трассировки',
                                  name='tracing_system')
    chart_4 = EchartStackedColumn(title='Средства мониторинга',
                                  name='monitoring')
    return render_template('4_charts.html',
                           title='Средства нагрузочного тестирования и мониторинга',
                           chart_function_1=chart_1.get_script(),
                           div_1=chart_1.get_div(),
                           chart_function_2=chart_2.get_script(),
                           div_2=chart_2.get_div(),
                           chart_function_3=chart_3.get_script(),
                           div_3=chart_3.get_div(),
                           chart_function_4=chart_4.get_script(),
                           div_4=chart_4.get_div()
                           )


@app.route('/web_ui_and_api_tools')
def web_ui_and_api_tools():
    """Web UI and API testing tools page"""
    chart1 = EchartStackedColumn(name='api_testing_tools',
                                 title='Популярность инструментов тестирования Web API')
    chart2 = EchartStackedColumn(name='web_ui_tools',
                                 title='Популярность средства тестирования Web UI')
    return render_template(
        '2_charts.html',
        chart_script1=chart1.get_script(),
        div1=chart1.get_div(),
        chart_script2=chart2.get_script(),
        div2=chart2.get_div(),
    )


@app.route('/mobile_testing_frameworks')
def mobile_testing_frameworks():
    """Mobile app testing frameworks page"""
    chart = EchartStackedColumn(title='Популярность фреймворков тестирования мобильных приложений',
                                name='mobile_testing_frameworks')
    return render_template(
        'pyechart.html',
        chart_script=chart.get_script(),
        div=chart.get_div(),
    )


@app.route('/sniffers')
def sniffers():
    """Sniffers"""
    chart1 = EchartStackedColumn(name='sniffers',
                                 title='Популярность анализаторов трафика (сниферов)')
    return render_template(
        '1_echart.html',
        chart_script1=chart1.get_script(),
        div1=chart1.get_div(),
    )


@app.route('/programming_languages')
def programming_languages():
    """Programming languages page"""
    chart = EchartStackedColumn(name='languages',
                                title='Популярность языков программирования')
    return render_template(
        'pyechart.html',
        chart_script=chart.get_script(),
        div=chart.get_div(),
    )


@app.route('/test_frameworks')
def test_frameworks():
    """Unit test frameworks popularity page"""
    chart1 = EchartTreeMap(title='Популярность тестовых фреймворков',
                           name='frameworks')
    chart2 = EchartStackedColumn(name='bdd_frameworks',
                                 title='Популярность фреймворков BDD')

    return render_template(
        '2_charts.html',
        chart_script1=chart1.get_script(),
        div1=chart1.get_div(),
        chart_script2=chart2.get_script(),
        div2=chart2.get_div(),
    )


@app.route('/unit_test_frameworks')
def unit_test_frameworks():
    """BDD framework page"""
    return redirect("https://clingon.pythonanywhere.com/test_frameworks", code=302)


@app.route('/bdd_frameworks')
def bdd_frameworks():
    """BDD framework page"""
    return redirect("https://clingon.pythonanywhere.com/unit_test_frameworks", code=302)


@app.route('/bugtracking_n_tms')
def bugtracking_n_tms():
    """Mobile app testing tools page"""
    chart_title = 'Популярность систем управления тестированием, bugtracking system и т.п.'
    chart = EchartStackedColumn(title=chart_title,
                                name='bugtracking_n_tms')
    return render_template(
        'pyechart.html',
        chart_script=chart.get_script(),
        div=chart.get_div(),
    )


@app.route('/cvs_and_ci_cd')
def cvs_and_ci_cd():
    """CVS and CI/CD page"""
    chart1 = EchartStackedColumn(name='ci_cd',
                                 title='Популярность средств <br> CI/CD.')
    chart2 = EchartStackedColumn(name='cvs',
                                 title='Популярность систем управления версиями.')
    return render_template(
        '2_charts.html',
        chart_script1=chart1.get_script(),
        div1=chart1.get_div(),
        chart_script2=chart2.get_script(),
        div2=chart2.get_div(),
    )


@app.route('/word_cloud')
def word_cloud():
    """Chart page"""
    return render_template('/word_cloud.html',
                           title='"Облако слов" на основе текстов вакансий.')


@app.route('/tmp')
def tmp():
    """Temporary chart page."""
    chart_1 = EchartBoxplot(name='languages',
                            title='...упоминания языка программирования.')
    chart_2 = EchartBoxplot(name='frameworks',
                            title='...тестового фреймворка.')
    chart_3 = EchartBoxplot(name='web_ui_tools',
                            title='...средства тестирования web UI.')
    chart_4 = EchartBoxplot(name='load_testing_tools',
                            title='...инструмента нагрузочного тестирования.')
    return render_template(
        '4_charts.html',
        title='Зарплаты в зависимости от...',
        chart_function_1=chart_1.get_script(),
        div_1=chart_1.get_div(),
        chart_function_2=chart_2.get_script(),
        div_2=chart_2.get_div(),
        chart_function_3=chart_3.get_script(),
        div_3=chart_3.get_div(),
        chart_function_4=chart_4.get_script(),
        div_4=chart_4.get_div()
    )


@app.route('/tmp_1')
def tmp_1():
    """Temporary chart page."""
    chart1 = EchartTreeMap(name='frameworks',
                           title='Популярность фреймворков для unit-тестирования')
    chart2 = EchartStackedColumn(name='cvs',
                                 title='Популярность систем управления версиями.')
    return render_template(
        '2_charts.html',
        chart_script1=chart1.get_script(),
        div1=chart1.get_div(),
        chart_script2=chart2.get_script(),
        div2=chart2.get_div(),
    )


@app.route('/tmp_2')
def tmp_2():
    chart_1 = EchartHorizontalBarByCategory(name='salary',
                                            title='Без опыта, ₽, net',
                                            category='noExperience')
    chart_2 = EchartHorizontalBarByCategory(name='salary',
                                            title='От года до трех лет, ₽, net',
                                            category='between1And3')
    chart_3 = EchartHorizontalBarByCategory(name='salary',
                                            title='От трех до шести лет, ₽, net',
                                            category='between3And6')
    chart_4 = EchartHorizontalBarByCategory(name='salary',
                                            title='Больше шести лет, ₽, net',
                                            category='moreThan6')
    return render_template(

        '4_charts.html',
        title='Медианная заработная плата в зависимости от опыта',
        chart_function_1=chart_1.get_script(),
        div_1=chart_1.get_div(height=300),
        chart_function_2=chart_2.get_script(),
        div_2=chart_2.get_div(),
        chart_function_3=chart_3.get_script(),
        div_3=chart_3.get_div(),
        chart_function_4=chart_4.get_script(),
        div_4=chart_4.get_div()
    )
