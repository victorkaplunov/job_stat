import re
import json

import pytest
from requests_html import HTMLSession
from requests import exceptions

from config import Config


@pytest.fixture
def charts_data():
    """Отдает результат запроса к заданному URL из которого выделяет данные
     для построения графиков."""
    def _get_charts_data(rout=f'{Config.LOCAL_HOST_BASE_URL}/', script_num=2):
        try:
            session = HTMLSession()
            response = session.get(f'{Config.LOCAL_HOST_BASE_URL}/{rout}')
            script = response.html.find('script')[script_num].text
        except exceptions.RequestException as exception:
            print(exception)

        try:
            finding_result = re.findall('arrayToDataTable\(((.+?))\);', script)
            output_data = dict()
            for n, i in enumerate(finding_result):
                substitution_result = re.sub("'", "\"", i[0])  # prepare data to json.loads
                output_data[n] = json.loads(substitution_result)
            return output_data
        except AttributeError:
            print('Data for chart not found.')
            return
    return _get_charts_data


@pytest.fixture
def scatter_charts_data():
    """Отдает результат запроса к заданному URL из которого выделяет данные
     для построения точечных графиков."""
    def _get_charts_data(rout=f'{Config.LOCAL_HOST_BASE_URL}/', script_num=2):
        try:
            session = HTMLSession()
            response = session.get(f'{Config.LOCAL_HOST_BASE_URL}/{rout}')
            script = response.html.find('script')[script_num].text
        except exceptions.RequestException as exception:
            print(exception)
        try:
            return re.findall('data.addRows\(((.+?))\);', script)
        except AttributeError:
            print('Data for chart not found.')
            return
    return _get_charts_data
