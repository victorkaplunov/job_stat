from datetime import date, timedelta
from typing import Type, List

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

from models import Vacancies, Calendar, Charts, VacWithSalary
from config import ConfigObj


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Database(metaclass=SingletonMeta):
    _db_engine = None
    _session = None

    def __init__(self):
        self._db_engine = create_engine(f"sqlite:///{ConfigObj.DB_FILE_NAME}")
        self._session = sessionmaker(bind=self._db_engine)()

    def get_date_from_calendar_by_vacancy(self, vacancy_id: int) -> list[Calendar.data]:
        return self._session.query(Calendar.data).filter_by(id=vacancy_id).all()

    def get_vacancy_by_id(self, vacancy_id: int) -> Type[Vacancies]:
        return self._session.query(Vacancies).filter_by(id=vacancy_id).one()

    def get_vacancy_ordered_by_id(self, limit=100) -> list[Type[Vacancies]]:
        return self._session.query(Vacancies).order_by(Vacancies.id.desc()).limit(limit).all()

    def get_vacancy_publication_ordered_by_date(self, limit=100) -> list[Type[Calendar]]:
        return self._session.query(Calendar).order_by(Calendar.data.desc()).limit(limit).all()

    def find_vacancy_by_substring(self, search_phrase: str, limit=150) -> list[Type[Vacancies]]:
        return self._session.query(Vacancies)\
            .filter(Vacancies.json.like(f'%{search_phrase}%'))\
            .order_by(Vacancies.published_at.desc())\
            .limit(limit).all()

    def find_vacancy_with_salary_by_substring(self, search_phrase: str) -> list[Type[VacWithSalary]]:
        return self._session.query(VacWithSalary)\
            .filter(VacWithSalary.description.like(f'%{search_phrase}%'))\
            .order_by(VacWithSalary.published_at.desc()).all()

    def get_vacancy_qty_by_day(self, day: date) -> int:
        return self._session.query(Calendar).distinct(Calendar.id) \
            .filter(Calendar.data.between(day, day + timedelta(days=1))).count()

    def get_vacancies_qty_by_period(self, start_day: date, end_day: date) -> int:
        """From start to finis, includes end date."""
        return self._session.query(Calendar.id.distinct()) \
            .filter(Calendar.data.between(start_day, end_day + timedelta(days=1))).count()

    def get_all_vacancies_ids(self) -> list:
        return [i[0] for i in self._session.query(Vacancies.id)]

    def count_vacancy_by_search_phrase_and_year(self, search_phrase: str, year: int) -> int:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        return self._session.query(Vacancies) \
            .filter(and_(Vacancies.json.like(f'%{search_phrase}%'),
                         Vacancies.published_at.between(start_date, end_date)))\
            .count()

    def get_json_from_vacancies_per_year(self, year: int) -> list[str]:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        result = self._session.query(Vacancies.json) \
            .filter(Vacancies.published_at.between(start_date, end_date)).all()
        return [i[0] for i in result]

    def get_data_for_chart(self, chart_name: str) -> list[Type[Charts]]:
        return self._session.query(Charts).filter_by(chart_name=chart_name).all()

    def get_data_for_chart_per_year(self, year: int, chart_name: str) -> list[Type[Charts]]:
        return self._session.query(Charts).filter(
            and_(Charts.year == year, Charts.chart_name == chart_name)).all()

    # def execute_query(self, query):
    #     self._session.execute(query)
    #
    # def fetch_data(self, query):
    #     return self._session.execute(query).fetchall()
    #
    # def update_data(self, query):
    #     self._session.execute(query)
    #     self._session.commit()

