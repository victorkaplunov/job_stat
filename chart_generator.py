import copy
from operator import itemgetter

from db_client import Database
from config import ConfigObj


class BaseChartGenerator:
    """Базовый класс генерации JS-скриптов графиков."""
    def __init__(self, chart_name: str, chart_title: str):
        self.title = chart_title
        self.chart_name = chart_name
        self.charts = ''
        self.divs = ''
        self.db = Database()
        self.config = ConfigObj()
        self.translations = self.config.TRANSLATIONS
        self.years = self.config.YEARS
        self.reversed_years = self.config.YEARS[::-1]

    def get_data_per_year(self, year: int, chart_name: str, sort=True) -> list[list[str | int]]:
        """Формирует данные для графиков по годам на основе запроса в БД."""
        head = [['Type', 'Popularity']]
        statistics_data = self.db.get_data_for_chart_per_year(year=year, chart_name=chart_name)
        data_list = []
        for i in statistics_data:
            # Переводим параметры для перечисленных видов графиков
            if chart_name in ['schedule', 'employment', 'experience', 'with_salary']:
                row = [self.translations[i.data], i.popularity]
                data_list.append(row)
            else:  # Для остальных не переводим
                data_list.append([i.data, i.popularity])
        data_list.sort(reverse=sort, key=itemgetter(1))
        return head + data_list


class PieChart(BaseChartGenerator):
    """Класс генерации JS функций и данных для круговой диаграммы."""
    def generate_script(self):
        """Генерация функций JavaScript для отдельных графиков"""
        for year in self.reversed_years:
            chart_data = self.get_data_per_year(year, self.chart_name)
            self.charts = self.charts + f'''
                google.charts.setOnLoadCallback(drawScheduleTypeChart{year});
                function drawScheduleTypeChart{year}() {{
                var data = google.visualization.arrayToDataTable({chart_data});
                var options = {{'title':'{self.title} в {year} году.',
                chartArea:{{width:'90%',height:'80%'}},
                pieSliceTextStyle: {{fontSize: 11}}
                }};
                var chart = new google.visualization.PieChart(document.getElementById('chart_for_{year}'));
                chart.draw(data, options);
                }}'''
        return self.charts

    def generate_divs(self):
        """Генерация разделов в которые будут вставляться графики."""
        for year in self.reversed_years:
            self.divs = self.divs + f'<div id="chart_for_{year}" style="height: 300px;"></div>'
        return self.divs


class PieChartWithTable(PieChart):
    """Класс генерации JS функций и данных для круговой диаграммы с таблицей данных."""
    def generate_table_script(self):
        table = ''
        for year in self.reversed_years:
            table_data = self.get_data_per_year(year, self.chart_name)
            table_data = copy.deepcopy(table_data)
            table_data.remove(['Type', 'Popularity'])
            sum_vac = 0
            for i in table_data:
                sum_vac += i[1]
            for i in table_data:
                percent = str(round(i[1] / sum_vac * 100, 1))
                i.append(percent)

            table = table + f'''
                google.charts.setOnLoadCallback(draw{year}Table);
                function draw{year}Table() {{
                var data = new google.visualization.DataTable();
                data.addColumn('string', 'Вид');
                data.addColumn('number', 'Количество вакансий');
                data.addColumn('string', 'Доля, %');
                data.addRows({ table_data });
    
                var table = new google.visualization.Table(document.getElementById('table{year}div'));
    
                table.draw(data, {{width: '100%', height: '100%'}});
              }}
            '''
        return table

    def generate_divs(self):
        """Генерация разделов в которые будут вставляться графики и таблицы."""
        for year in self.reversed_years:
            self.divs = self.divs + f'''
                     <div id="chart_for_{year}" style="height: 300px;"></div>
                     <div id="table{year}div"></div>
                     <p>
                     <hr>
                     <p>'''
        return self.divs
