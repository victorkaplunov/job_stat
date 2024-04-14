import pytest
from config import Config


rout = 'time_series'
chart_names = ['по неделям года', 'по месяцам', 'по дням недели']
chart_numbers = [0, 1, 2]  # Номера графиков на странице


@pytest.mark.parametrize('chart_number,expected_title',
                         [(0, 'Неделя'), (1, 'Месяц'), (2, 'Неделя за неделей')],
                         ids=chart_names)
def test_week_chart_legend_title(charts_data, chart_number, expected_title):
    assert charts_data(rout=rout)[chart_number][0][0] == expected_title,\
        'Заголовок легенды не совпадает с ожидаемым.'


@pytest.mark.parametrize('chart_number,subtitle',
                         [(0, 'количество вакансий'),
                          (1, '2020'), (2, 'текущая неделя')],
                         ids=chart_names)
def test_week_chart_legend_subtitle(charts_data, chart_number, subtitle):
    assert charts_data(rout=rout)[chart_number][0][1] == subtitle,\
        'Подзаголовок легенды не совпадает с ожидаемым.'


def test_week_by_week_data_types(charts_data):
    assert isinstance(charts_data(rout=rout)[0][0], list), \
        'Тип данных для легенды не совпадает с ожидаемым.'
    assert isinstance(charts_data(rout=rout)[0][0][0], str), \
        'Тип данных для элемента легенды не совпадает с ожидаемым.'
    assert isinstance(charts_data(rout=rout)[0][0][1], str), \
        'Тип данных для элемента легенды не совпадает с ожидаемым.'
    assert isinstance(charts_data(rout=rout)[0][0][2], dict), \
        'Тип данных для элемента легенды не совпадает с ожидаемым.'
    for i in charts_data(rout=rout)[0][1:]:
        assert isinstance(i[0], str), \
            'Тип данных для строки данных не совпадает с ожидаемым.'
        assert isinstance(i[1], int), \
            'Тип данных для строки данных не совпадает с ожидаемым.'
        assert isinstance(i[2], str), \
            'Тип данных для строки данных не совпадает с ожидаемым.'


def test_month_by_year_data_types(charts_data):
    assert isinstance(charts_data(rout=rout)[1][0], list),\
        'Тип данных для легенды не совпадает с ожидаемым.'
    for i in charts_data(rout=rout)[1][0]:
        assert isinstance(i, str),\
            'Тип данных для элемента легенды не совпадает с ожидаемым.'
    for n, i in enumerate(Config.YEARS):
        assert str(i) == charts_data(rout=rout)[1][0][1:][n], \
            "Год из заголовка графика не совпадает с годом из конфигурационного файла."
    for i in charts_data(rout=rout)[1][1:]:
        assert isinstance(i[0], str), \
            'Тип данных для первого элемента строки данных не совпадает с ожидаемым.'
        for i2 in i[1:]:
            assert isinstance(i2, int), \
                'Тип данных для второго и последующих элементов строки данных не ' \
                'совпадает с ожидаемым.'


def test_day_by_week_data_types(charts_data):
    assert isinstance(charts_data(rout=rout)[1][0], list),\
        'Тип данных для легенды не совпадает с ожидаемым.'
    for i in charts_data(rout=rout)[2][0]:
        assert isinstance(i, str),\
            'Тип данных для элемента легенды не совпадает с ожидаемым.'
    for i in charts_data(rout=rout)[2][1:]:
        assert isinstance(i[0], str), \
            'Тип данных для первого элемента строки данных не совпадает с ожидаемым.'
        for i2 in i[1:]:
            assert isinstance(i2, int), \
                'Тип данных для второго и последующих элементов строки данных не ' \
                'совпадает с ожидаемым.'






