from sqlalchemy import Column, Integer, String, Numeric, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Vacancies(Base):
    __tablename__ = "vacancies"
    id = Column(Integer, primary_key=True)
    json = Column(String)
    published_at = Column(String)


class Calendar(Base):
    __tablename__ = "calendar"
    id = Column(Integer, primary_key=True)
    data = Column(String)


class Charts(Base):
    __tablename__ = "charts"
    id = Column(Integer, primary_key=True)
    chart_name = Column(String)
    data = Column(String)
    popularity = Column(Integer)
    percent = Column(Float)
    parent = Column(String)
    year = Column(Integer)


class HorizontalBarCharts(Base):
    __tablename__ = "h_bar_charts"
    chart_name = Column(String, primary_key=True)
    category = Column(String)
    value = Column(Integer)
    date_start = Column(String)
    date_end = Column(String)


class VacWithSalary(Base):
    __tablename__ = "vac_with_salary"
    id = Column(Integer, primary_key=True)
    published_at = Column(String)
    calc_salary = Column(Float)
    experience = Column(String)
    url = Column(String)
    description = Column(String)
