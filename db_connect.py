from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Vacancies, Calendar
from config_obj import ConfigObj


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

    def get_date_from_calendar_by_vacancy(self, vacancy_id: int) -> list[Calendar]:
        return self._session.query(Calendar.data).filter_by(id=vacancy_id).all()

    def get_vacancy_by_id(self, vacancy_id: int) -> list[Vacancies]:
        return self._session.query(Vacancies).filter_by(id=vacancy_id).one()

    def get_vacancy_ordered_by_id(self, limit=100) -> list[Vacancies]:
        return self._session.query(Vacancies).order_by(Vacancies.id.desc()).limit(limit).all()

    def get_vacancy_publication_ordered_by_date(self, limit=100) -> list[Calendar]:
        return self._session.query(Calendar).order_by(Calendar.data.desc()).limit(limit).all()

    def find_vacancy_by_substring(self, search_phrase: str, limit=150) -> list[Vacancies]:
        return self._session.query(Vacancies)\
            .filter(Vacancies.json.like(f'%{search_phrase}%'))\
            .order_by(Vacancies.published_at.desc())\
            .limit(limit).all()

    def get_vacancy_qty_by_day(self, day: date) -> int:
        return self._session.query(Calendar).distinct(Calendar.id) \
            .filter(Calendar.data.between(day, day + timedelta(days=1))).count()

    def get_vacancies_qty_by_period_of_time(self, start_day: date, end_day: date) -> int:
        """From start to finis, includes end date."""
        return self._session.query(Calendar.id.distinct()) \
            .filter(Calendar.data.between(start_day, end_day + timedelta(days=1))).count()




    # def execute_query(self, query):
    #     self._session.execute(query)
    #
    # def fetch_data(self, query):
    #     return self._session.execute(query).fetchall()
    #
    # def update_data(self, query):
    #     self._session.execute(query)
    #     self._session.commit()





# Execute a query
# database.execute_query("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")

# Fetch data
# data = database.fetch_data(text('SELECT * FROM vacancies ORDER BY id DESC LIMIT 100;'))
# print(f'{data[0]=}')
# Update data
# database.update_data("INSERT INTO users (name) VALUES ('John')")
