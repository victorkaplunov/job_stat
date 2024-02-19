import re
import json

import pytest
from requests_html import HTMLSession
from requests import exceptions

from config_obj import ConfigObj


@pytest.fixture
def charts_data():
    """Отдает результат запроса к заданному URL из которого выделяет данные
     для построения графиков"""
    try:
        session = HTMLSession()
        response = session.get(f"{ConfigObj().LOCAL_HOST_BASE_URL}/salary")

    except exceptions.RequestException as e:
        print(e)

    script = response.html.find('script')[2].text

    try:
        finding_result = re.findall('arrayToDataTable\(((.+?))\);', script)
    except AttributeError:
        print('Data for chart not found.')

    test_data_list = list()
    for i in finding_result:
        substitution_result = re.sub("'", "\"", i[0])
        list_ = json.loads(substitution_result)
        test_data_list.append(list_)
    return test_data_list
