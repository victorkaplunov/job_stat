from datetime import date

import pytest

from db.db_client import Database
from config import ConfigObj

db = Database()
config = ConfigObj()


@pytest.mark.parametrize('test_input, expect',
                         [(date(2019, 3, 17), 12),
                          (date(2024, 2, 22), 200)],
                         ids=['2019-3-17', '2024-2-22'])
def test_get_vacancy_qty_by_day(test_input, expect):
    vacancies_qty = db.get_vacancy_qty_by_day(day=test_input)
    assert vacancies_qty == expect


@pytest.mark.parametrize('test_input, expect',
                         [((date(2022, 1, 1), date(2022, 1, 31)), 2321),
                          ((date(2024, 2, 21), date(2024, 2, 22)), 384)],
                         ids=['2022-1-1 - 2022-1-31',
                              '2024-2-21 - 2024-2-22'])
def test_get_vacancies_qty_by_period(test_input, expect):
    vacancies_qty = db.get_vacancies_qty_by_period(start_day=test_input[0],
                                                   end_day=test_input[1])
    assert vacancies_qty == expect
