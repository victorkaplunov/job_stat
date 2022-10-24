import pytest
from utils import get_chart_data_from_route
from config_obj import ConfigObj

url = f"{ConfigObj().LOCAL_HOST_BASE_URL}/time_series"
chart_names = ['по неделям года', 'по месяцам', 'по дням недели']
chart_numbers = [0, 1, 2]  # Номера графиков на странице

charts_data = get_chart_data_from_route(url)


@pytest.mark.parametrize('chart_number,title',
                         [(0, 'Неделя'), (1, 'Месяц'), (2, 'Неделя')],
                         ids=chart_names)
def test_week_chart_legend_title(chart_number, title):
    assert charts_data[chart_number][0][0] == title


@pytest.mark.parametrize('chart_number,subtitle',
                         [(0, 'количество вакансий'),
                          (1, '2019'), (2, 'текущая неделя')],
                         ids=chart_names)
def test_week_chart_legend_subtitle(chart_number, subtitle):
    assert charts_data[chart_number][0][1] == subtitle


@pytest.mark.parametrize('chart_number', chart_numbers,
                         ids=chart_names)
def test_week_chart_legend_titles_data_type(chart_number):
    assert isinstance(charts_data[chart_number][0], list)
    assert isinstance(charts_data[chart_number][0][0], str)


@pytest.mark.parametrize('chart_number', chart_numbers,
                         ids=chart_names)
def test_week_chart_data_type(chart_number):
    charts_data[chart_number].pop(0)  # Remove title list
    for i in charts_data[chart_number]:
        assert isinstance(i, list)
        assert isinstance(i[0], str)
        assert isinstance(i[1], int)



