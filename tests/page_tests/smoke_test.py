import pytest
import requests

from config import Config
from flask_app import app


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)


def all_routs():
    links = []
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and has_no_empty_params(rule):
            print(f'{rule.endpoint=}')
            links.append(rule.endpoint)
    print(links)
    return links


exceptions_list = ['favicon', 'starter_template', 'show_vac_top_new_by_id',
                   'show_vac_top_new_by_date', 'home_page']


@pytest.mark.parametrize('rout', all_routs())
def test_routs_status_code(charts_data, rout):
    """Request all routs and check status code."""
    print(rout)
    response = requests.get(url=Config.LOCAL_HOST_BASE_URL + '/' + rout)
    if rout in exceptions_list:
        assert response.status_code == 404
    else:
        assert response.status_code == 200
