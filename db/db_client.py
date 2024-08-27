import os
from datetime import date, timedelta
from typing import Type, Sequence, Any, NoReturn

from sqlalchemy import create_engine, and_, select, Row, RowMapping, exc, func, text
from sqlalchemy.orm import sessionmaker

from db.models import Vacancies, Calendar, Charts, VacWithSalary
from config import Config


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
        self._db_engine = create_engine(
            'sqlite:///' + str(os.path.join(Config.basedir, Config.DB_FILE_NAME)))
        self._session = sessionmaker(bind=self._db_engine)()

    def get_date_from_calendar_by_vacancy(
            self, vacancy_id: int) -> Sequence[Row[Any] | RowMapping]:
        return self._session.scalars(select(Calendar.data)
                                     .filter(Calendar.id == vacancy_id)).all()

    def get_vacancy_by_id(self, vacancy_id: int) -> Type[Vacancies]:
        return self._session.query(Vacancies).filter_by(id=vacancy_id).one()

    def get_vacancy_ordered_by_id(self, limit=100) -> list[Type[Vacancies]]:
        return self._session.query(Vacancies)\
            .order_by(Vacancies.id.desc()).limit(limit).all()

    def get_vacancy_publication_ordered_by_date(
            self, limit=100) -> list[Type[Calendar]]:
        return self._session.query(Calendar)\
            .order_by(Calendar.data.desc()).limit(limit).all()

    def find_vacancy_by_substring(
            self, search_phrase: str, limit=150) -> list[Type[Vacancies]]:
        return self._session.query(Vacancies) \
            .filter(Vacancies.json.like(f'%{search_phrase}%')) \
            .order_by(Vacancies.published_at.desc()) \
            .limit(limit).all()

    def find_vacancy_with_salary_by_substring(
            self, search_phrase: str) -> list[Type[VacWithSalary]]:
        return ((self._session.query(VacWithSalary)
                 .filter(VacWithSalary.description.like(f'%{search_phrase}%')))
                .order_by(VacWithSalary.published_at.desc()).all())

    def find_vacancy_with_salary_by_substring_per_period(
            self, experience: str, start_day: date, end_day: date
    ) -> list[Type[VacWithSalary]]:
        return (self._session.query(VacWithSalary)
                .filter(VacWithSalary.experience == experience)
                .filter(VacWithSalary.published_at.between(start_day, end_day))
                .order_by(VacWithSalary.published_at.asc())
                .all())

    def get_vacancy_qty_by_day(self, day: date) -> int:
        return self._session.query(Calendar).distinct(Calendar.id) \
            .filter(Calendar.data.between(day, day + timedelta(days=1))).count()

    def get_vacancies_qty_by_period(self, start_day: date, end_day: date) -> int:
        """From start to finis, includes end date."""
        return self._session.query(Calendar.id.distinct()) \
            .filter(Calendar.data.between(start_day,
                                          end_day + timedelta(days=1))).count()

    def get_all_vacancies_ids(self) -> Sequence[Row[Any] | RowMapping]:
        return self._session.scalars(select(Vacancies.id)).all()

    def get_all_vacancies_jsons(self):
        return self._session.scalars(select(Vacancies.json)).all()

    def count_vacancy_by_search_phrase_and_year(
            self, search_phrase: str, year: int) -> int:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        return self._session.query(Vacancies) \
            .filter(and_(Vacancies.json.like(f'%{search_phrase}%'),
                         Vacancies.published_at.between(start_date, end_date))) \
            .count()

    def get_json_from_vacancies_by_year(
            self, year: int) -> Sequence[Row[Any] | RowMapping]:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        return self._session.scalars(
            select(Vacancies.json)
            .filter(Vacancies.published_at.between(start_date, end_date))).all()

    def get_json_from_filtered_vacancies_by_year(
            self, search_phrase: str, year: int) -> Sequence[Row[Any] | RowMapping]:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        return self._session.scalars(
            select(Vacancies.json)
            .filter(Vacancies.published_at.between(start_date, end_date))
            .filter(Vacancies.json.like(f'%{search_phrase}%'))
        ).all()

    def get_data_for_chart(self, chart_name: str) -> list[Type[Charts]]:
        return self._session.query(Charts).filter_by(chart_name=chart_name).all()

    def get_sorted_data_for_chart(self, chart_name: str) -> list[Type[Charts]]:
        return self._session.query(Charts).order_by(Charts.popularity.desc()).filter_by(chart_name=chart_name).all()

    def get_data_for_chart_per_year(
            self, year: int, chart_name: str) -> list[Type[Charts]]:
        return self._session.query(Charts).filter(
            and_(Charts.year == year, Charts.chart_name == chart_name)).all()

    def get_data_for_chart_per_year_by_parent(
            self, year: int, chart_name: str, parent: str) -> list[Type[Charts]]:
        return self._session.query(Charts).filter(
            and_(Charts.year == year, Charts.chart_name == chart_name,
                 Charts.parent == parent)).all()

    def get_sorted_data_for_chart_per_year(
            self, year: int, chart_name: str) -> list[Type[Charts]]:
        return self._session.query(Charts).order_by(Charts.data).filter(
            and_(Charts.year == year, Charts.chart_name == chart_name)).all()

    def get_pytest_data(self, year: int) -> int:
        return self._session.scalars(
            select(Charts.popularity).filter(and_(
                Charts.year == year,
                Charts.chart_name == 'frameworks',
                Charts.data == 'pytest'
            ))
        ).one()

    def get_unic_chart_names(self) -> Sequence[Row[Any] | RowMapping]:
        return self._session.scalars(select(Charts.chart_name)
                                     .distinct()).all()

    def get_unic_parents(self) -> Sequence[Row[Any] | RowMapping]:
        return self._session.scalars(select(Charts.parent).where(Charts.parent.is_not(None))
                                     .distinct()).all()

    def get_unic_values_for_chart_sorted_by_last_year_percent(
            self, chart_name: str) -> Sequence[Row[Any] | RowMapping]:
        return self._session.scalars(select(Charts.data)
                                     .filter(and_(Charts.chart_name == chart_name,
                                                  Charts.year == Config.YEARS[-1]))
                                     .order_by(Charts.percent.desc())
                                     .distinct()).all()

    def get_sum_for_chart_per_year(self, year: int,  chart_name:  Sequence[Row[Any] | RowMapping]) -> int:
        return self._session.query(func.sum(Charts.popularity)).filter(
            and_(Charts.chart_name == chart_name, Charts.year == year)).scalar()

    def get_percentage_ordered_by_years(
            self, chart_name:  str, param_name:  Sequence[Row[Any] | RowMapping]) -> Sequence[Row[Any] | RowMapping]:
        return self._session.scalars(select(Charts.percent)
                                     .filter(and_(Charts.chart_name == chart_name,
                                                  Charts.data == param_name))
                                     .order_by(Charts.year)).all()

    def insert_vacancy(self, vac_id, json, published_at) -> NoReturn:
        vacancy = Vacancies(id=vac_id, json=json, published_at=published_at)
        self._session.add(vacancy)
        self._session.commit()

    def insert_vac_id_to_calendar(self, vac_id: int, published_at: str) -> NoReturn:
        vacancy = Calendar(id=vac_id, data=published_at)
        try:
            self._session.add(vacancy)
            self._session.commit()
        except exc.IntegrityError:
            self._session.rollback()

    def update_charts(self, chart_name: str, data: str, popularity: int,
                      year: [int, None], parent: [str, None] = None) -> NoReturn:
        row = self._session.query(Charts).filter(
            and_(Charts.year == year, Charts.chart_name == chart_name,
                 Charts.parent == parent, Charts.data == data)).one()
        row.popularity = popularity
        self._session.commit()

    def update_percentage(self,  chart_name:  Sequence[Row[Any] | RowMapping],
                          data: str, percent: float, year: [int, None],
                          ) -> NoReturn:
        row = self._session.query(Charts).filter(
            and_(Charts.year == year, Charts.chart_name == chart_name,
                 Charts.data == data)).one()
        row.percent = percent
        self._session.commit()

    def insert_in_charts(self, chart_name: str, data: str, popularity: int,
                         year: [int, None], parent: [str, None] = None) -> NoReturn:
        row = Charts(chart_name=chart_name, parent=parent,
                     popularity=popularity, year=year, data=data)
        self._session.add(row)
        self._session.commit()

    def insert_in_vac_with_salary(self, item: dict, salary: float) -> NoReturn:
        row = VacWithSalary(id=item['id'], published_at=str(item['published_at']),
                            calc_salary=salary, experience=item['experience'],
                            url=item['alternate_url'], description=item['description'])
        self._session.add(row)
        self._session.commit()

    def delete_vacancy_with_json_like(self, word: str) -> NoReturn:
        vacancies = self._session.query(Vacancies)\
            .filter(Vacancies.json.like(f'%{word}%'))
        vacancies.delete()
        self._session.commit()

    def delete_chart_data(self, chart_name: str) -> NoReturn:
        chart_data = self._session.query(Charts)\
            .filter(Charts.chart_name == chart_name)
        chart_data.delete()
        self._session.commit()

    def drop_and_recreate_vac_with_salary_table(self) -> NoReturn:
        VacWithSalary.__table__.drop(bind=self._db_engine)
        VacWithSalary.__table__.create(bind=self._db_engine)

    def drop_and_recreate_charts_table(self) -> NoReturn:
        Charts.__table__.drop(bind=self._db_engine)
        Charts.__table__.create(bind=self._db_engine)

    def vacuum_db(self) -> NoReturn:
        """ Очистка БД, для уменьшения ее размера."""
        self._session.execute(text('VACUUM'))

    def close_session(self) -> NoReturn:
        self._session.close()
        self._db_engine.dispose()
