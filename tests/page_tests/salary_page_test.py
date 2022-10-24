import pytest

import utils
from config_obj import ConfigObj

url = f"{ConfigObj().LOCAL_HOST_BASE_URL}/salary"
charts_data = utils.get_chart_data_from_route(url)


def test_salary_chart_data_type():
    """variable 'salary' in JS function 'salary' contains list."""
    print(charts_data)
    assert isinstance(charts_data, list)
    for i in charts_data:
        assert isinstance(charts_data, list)


def test_first_row_in_salary_chart_data():
    """Тне title row contain 'Range' and years value."""
    check_list = list(utils.years_tuple())
    string_check_list = []
    for i in check_list:
        string_check_list.append(str(i))
    assert charts_data[0][0][1:] == string_check_list
    assert charts_data[0][0][0] == 'Range'


def test_week_chart_legend_titles_data_type():
    assert isinstance(charts_data[0][0], list)
    assert isinstance(charts_data[0][0][0], str)


def test_week_chart_data_type():
    charts_data[0].pop(0)  # Remove title list
    for i in charts_data[0]:
        assert isinstance(i, list)
        assert isinstance(i[0], str)
        assert isinstance(i[1], int)
