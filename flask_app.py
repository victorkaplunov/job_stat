import os
import json
from functools import lru_cache

from flask import Flask, send_from_directory, url_for, render_template
from flask_bootstrap import Bootstrap

import utils
from db.db_client import Database
from config import Config
from chart_generator import PieChart, PieChartWithTable, PieChartWithFilter, \
    HorizontalBarChart, StackedColumnChart, EChartStackedColumnChart

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


@app.route('/salary_by_category')
def salary_by_category():
    """Salary by category"""
    return render_template(
        '/candle.html',
        chart_data=utils.get_salary_by_category_data(),
        year=Config.YEARS[-1],
        title='Медианная зарплата в зависимости от упоминания языка.'
    )


@app.route('/top_employers')
def top_employers():
    """Employers by vacancies quantity page"""
    chart = HorizontalBarChart(
        chart_title='Топ 50 работодателей',
        chart_subtitle=f'по количеству вакансий в {Config.YEARS[-1]} году.',
        chart_name='top_employers')
    return render_template('/simple_chart.html',
                           package=chart.package,
                           title=chart.title,
                           subtitle=chart.subtitle,
                           charts_function=chart.generate_script(chart_name=chart.chart_name),
                           divs=chart.generate_divs())


@app.route('/schedule')
def schedule():
    """Schedule type popularity page"""
    chart = PieChart(chart_title='Популярность режимов работы',
                     chart_name='schedule')
    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Режимы работы.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/employment')
def employment():
    chart = PieChartWithTable(chart_title='Виды занятости',
                              chart_name='employment')
    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Виды занятости.',
        charts_function=chart.generate_script() + chart.generate_table_script(),
        divs=chart.generate_divs()
    )


@app.route('/experience')
def experience():
    """Experience popularity page"""
    chart = PieChart(chart_title='Требования к опыту ',
                     chart_name='experience')
    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Требуемый опыт работы.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/with_salary')
def with_salary():
    chart = PieChart(chart_title='Количество вакансий с указанной зарплатой',
                     chart_name='with_salary')
    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Количество вакансий с указанной зарплатой.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/key_skills')
def key_skills():
    """Key skills popularity page"""
    chart = HorizontalBarChart(
        chart_title='Ключевые навыки.',
        chart_subtitle=f'Пятьдесят наиболее популярных тегов в {Config.YEARS[-1]} году.',
        chart_name='key_skills')
    return render_template('/simple_chart.html',
                           package=chart.package,
                           title=chart.title,
                           subtitle=chart.subtitle,
                           charts_function=chart.generate_script(chart_name=chart.chart_name),
                           divs=chart.generate_divs())


@app.route('/programming_languages')
def programming_languages():
    """Programming languages page"""
    chart = PieChart(chart_title='Популярность языков программирования',
                     chart_name='languages')
    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Популярность языков программирования.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/unit_test_frameworks')
def unit_test_frameworks():
    """Unit test frameworks popularity page"""
    chart = PieChartWithFilter(chart_title='Популярность фреймворков для юнит-тестирования',
                               chart_name='frameworks')

    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Популярность фреймворков для юнит-тестирования.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/load_testing_and_monitoring_tools')
def load_testing_and_monitoring_tools():
    """Load testing tools page"""
    chart_1 = StackedColumnChart(chart_title='Инструменты тестирования производительности',
                                 chart_name='load_testing_tools')
    chart_2 = StackedColumnChart(chart_title='Популярность генераторов сетевого трафика',
                                 chart_name='traffic_generators')
    chart_3 = StackedColumnChart(chart_title='Системы трассировки',
                                 chart_name='tracing_system')
    chart_4 = StackedColumnChart(chart_title='Средства мониторинга',
                                 chart_name='monitoring')
    return render_template('4_charts.html',
                           package=chart_1.package,
                           title='Средства нагрузочного тестирования и мониторинга.',
                           charts_function_1=chart_1.generate_script(),
                           div_1=chart_1.generate_divs(),
                           charts_function_2=chart_2.generate_script(),
                           div_2=chart_2.generate_divs(),
                           charts_function_3=chart_3.generate_script(),
                           div_3=chart_3.generate_divs(),
                           charts_function_4=chart_4.generate_script(),
                           div_4=chart_4.generate_divs()
                           )


@app.route('/api_testing_tools')
def api_testing_tools():
    """Load testing tools page"""
    chart = PieChart(chart_title='Популярность инструментов тестирования Web API',
                     chart_name='api_testing_tools')
    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Средства тестирования Web API.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/bdd_frameworks')
def bdd_frameworks():
    """BDD framework page"""
    chart = PieChart(chart_title='Популярность фреймворков BDD',
                     chart_name='bdd_frameworks')
    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Популярность фреймворков BDD.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/web_ui_tools')
def web_ui_tools():
    """Web UI testing tools page"""
    chart = PieChart(chart_title='Популярность средства тестирования Web UI',
                     chart_name='web_ui_tools')
    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Популярность средства тестирования Web UI.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/mobile_testing_frameworks')
def mobile_testing_frameworks():
    """Mobile app testing tools page"""
    chart = PieChart(chart_title='Популярность инструментов тестирования мобильных приложений',
                     chart_name='mobile_testing_frameworks')
    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Популярность инструментов тестирования мобильных приложений.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/bugtracking_n_tms')
def bugtracking_n_tms():
    """Mobile app testing tools page"""
    chart = PieChart(chart_title='Популярность систем управления тестированием, bugtracking system и т.п.',
                     chart_name='bugtracking_n_tms')
    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Популярность систем управления тестированием, bugtracking system и т.п.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/cvs')
def cvs():
    """CVS page"""
    chart = PieChart(chart_title='Популярность систем управления версиями',
                     chart_name='cvs')
    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Популярность систем управления версиями.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/ci_cd')
def ci_cd():
    """Mobile app testing tools page"""
    chart = PieChart(chart_title='Популярность средств CI/CD',
                     chart_name='ci_cd')
    return render_template(
        '/simple_chart.html',
        package=chart.package,
        title='Популярность средств CI/CD.',
        charts_function=chart.generate_script(),
        divs=chart.generate_divs()
    )


@app.route('/word_cloud')
def word_cloud():
    """Chart page"""
    return render_template('/word_cloud.html',
                           title='"Облако слов" на основе текстов вакансий.')


@app.route('/tmp')
def tmp():
    """Temporary chart page."""
    chart = EChartStackedColumnChart(chart_name='load_testing_tools',
                                     chart_title='Популярность средств CI/CD.')
    return render_template(
        'tmp.html',
        auto_font_size_function=chart.auto_font_size_function,
        chart_function=chart.generate_script(),
        div=chart.generate_divs(),
        )


@app.route('/tmp_1')
def tmp_1():
    """Temporary chart page."""
    chart1 = EChartStackedColumnChart(chart_name='ci_cd',
                                      chart_title='Популярность средств CI/CD.')
    chart2 = EChartStackedColumnChart(chart_name='cvs',
                                      chart_title='Популярность систем управления версиями.')
    chart3 = EChartStackedColumnChart(chart_name='bugtracking_n_tms',
                                      chart_title='Популярность систем управления тестированием, bugtracking system и т.п.')
    return render_template(
        '3_charts.html',
        chart_title_button_1=chart1.title_button,
        chart_title_button_2=chart2.title_button,
        chart_title_button_3=chart3.title_button,
        auto_font_size_function=chart1.auto_font_size_function,
        chart_function1=chart1.generate_script(),
        div1=chart1.div,
        chart_function2=chart2.generate_script(),
        div2=chart2.div,
        chart_function3=chart3.generate_script(),
        div3=chart3.div,
        )
