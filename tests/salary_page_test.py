import requests
from requests_html import HTMLSession
import re
import json
import utils

url = "http://127.0.0.1:5000/salary"

try:
    session = HTMLSession()
    response = session.get(url)

except requests.exceptions.RequestException as e:
    print(e)

script = response.html.find('script')[1].text

try:
    string_list = re.search('arrayToDataTable\(((.+?))\);', script).group(1)
except AttributeError:
    print('Data for "salary" chart not found.')

string_list = re.sub("'", "\"", string_list)
data_list = json.loads(string_list)
print(type(data_list))


def test_salary_chart_data_type():
    """var data in function 'salary' contains list."""
    assert isinstance(data_list, list)


def test_first_row_in_salary_chart_data():
    """Тне title row contain 'Range' and years value."""
    assert data_list[0][0] == 'Range'
    check_list = list(utils.years_tuple())
    string_check_list = []
    for i in check_list:
        i = str(i)
        string_check_list.append(i)
    assert data_list[0][1:] == string_check_list


