import copy
import json
from operator import itemgetter

from db.db_client import Database
from config import Config


class BaseChartGenerator:
    """Базовый класс генерации JS-скриптов графиков."""
    def __init__(self, chart_name: str, chart_title: str, chart_subtitle=''):
        self.title = chart_title
        self.subtitle = chart_subtitle
        self.chart_name = chart_name
        self.package = []
        self.charts = ''
        self.divs = ''
        self.db = Database()
        self.config = Config
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
    def __init__(self, chart_name: str, chart_title: str, chart_subtitle=''):
        super().__init__(chart_name, chart_title, chart_subtitle)
        self.package = ['corechart']

    def generate_script(self):
        """Генерация функций JavaScript для отдельных графиков"""
        for year in self.reversed_years:
            chart_data = self.get_data_per_year(year, self.chart_name)
            self.charts = self.charts + f'''
                google.charts.setOnLoadCallback(drawChart{year});
                function drawChart{year}() {{
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
    def __init__(self, chart_name: str, chart_title: str, chart_subtitle=''):
        super().__init__(chart_name, chart_title, chart_subtitle)
        self.package = ['corechart', 'table']

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


class PieChartWithFilter(BaseChartGenerator):
    def __init__(self, chart_name: str, chart_title: str, chart_subtitle=''):
        super().__init__(chart_name, chart_title, chart_subtitle)
        self.package = ['corechart', 'controls']

    def get_data_per_year(self, year: int, chart_name: str, sort=True) -> list[list[str | int]]:
        """Формирует данные для графика популярности фреймворков юнит-тестирования по годам."""
        head = [['Framework', 'Popularity', 'Filter']]
        statistics_data = self.db.get_data_for_chart_per_year(year=year, chart_name=chart_name)
        data_list = []
        for i in statistics_data:
            data_list.append([i.data, i.popularity, i.parent])
        data_list.sort(reverse=True, key=itemgetter(1))
        return head + data_list

    def generate_script(self):
        """Генерация функций JavaScript для отдельных графиков"""
        for year in self.reversed_years:
            chart_data = self.get_data_per_year(year, self.chart_name)
            self.charts = self.charts + f"""
        google.charts.setOnLoadCallback(Chart{year});
        function Chart{year}() {{
        var data = google.visualization.arrayToDataTable({chart_data});
        
        var dashboard{year} = new google.visualization.Dashboard(
            document.getElementById('dashboard{year}_div'));
            
        var CategoryFilter{year} = new google.visualization.ControlWrapper({{
          'controlType': 'CategoryFilter',
          'containerId': 'filter_div{year}',
          'options': {{
            'filterColumnLabel': 'Filter',
            'ui': {{
                'caption': 'Выберите язык',
                'selectedValuesLayout': 'belowStacked',
                'label': 'Языки программирования',
                'labelStacking': 'vertical'
            }},
            'useFormattedValue': true
          }}
        }});
        
        // Create a pie chart, passing some options
        var pieChart{year} = new google.visualization.ChartWrapper({{
          'chartType': 'PieChart',
          'containerId': 'chart_div{year}',
          'options': {{
            'title':'{self.title} в {year} году.',
            chartArea:{{width:'100%',height:'75%'}},
            'height':500,
            'pieSliceText': 'value',
            'legend': 'right'
          }}
        }});

        dashboard{year}.bind(CategoryFilter{year}, pieChart{year});
        dashboard{year}.draw(data);
      }}"""
        return self.charts

    def generate_divs(self):
        """Генерация разделов в которые будут вставляться графики."""
        for year in self.reversed_years:
            self.divs = self.divs + f'''
        <div id="chart_div{year}"></div>
        <div id="filter_div{year}"></div>'''
        return self.divs


class HorizontalBarChart(BaseChartGenerator):
    def __init__(self, chart_name: str, chart_title: str, chart_subtitle=''):
        super().__init__(chart_name, chart_title, chart_subtitle)
        self.package = ['bar']

    def get_data_for_chart(self, chart_name: str) -> list[list[str | int]]:
        """Формирует данные для графика с горизонтальным столбцами."""
        statistics_data = self.db.get_data_for_chart(chart_name=chart_name)
        data_list = [[i.data, i.popularity] for i in statistics_data]
        for i in data_list:
            i.append(i[0])
        sorted_list = sorted(data_list, key=itemgetter(1), reverse=True)
        return sorted_list

    def generate_script(self, chart_name: str):
        """Генерация функций JavaScript для отдельных графиков"""
        chart_data = self.get_data_for_chart(chart_name=chart_name)
        self.charts = f"""
                google.charts.setOnLoadCallback(drawStuff);

              function drawStuff() {{
                var head = [['', 'количество', {{ role: 'annotation' }}]]
                head = head.concat({ chart_data});
                var data = new google.visualization.arrayToDataTable(head);
    
                var options = {{
                  title: '{self.title}',
                  width: '10%',
                  legend: {{ position: 'none' }},
                  chart: {{ title: '{self.title}',
                           subtitle: '{self.subtitle}' }},
                  bars: 'horizontal', // Required for Material Bar Charts.
                  hAxes: {{textPosition: 'in' }},
                  bar: {{ groupWidth: "90%" }}
               }};
        
                var chart = new google.charts.Bar(document.getElementById('chart'));
                chart.draw(data, options);
                }}"""
        return self.charts

    @staticmethod
    def generate_divs():
        """Генерация разделов в которые будут вставляться графики."""
        return '''<div id="chart" style="height: 1000px;"></div>'''


class StackedColumnChart(BaseChartGenerator):
    """Класс генерации столбчатой диаграммы."""

    def __init__(self, chart_name: str, chart_title: str, chart_subtitle=''):
        super().__init__(chart_name, chart_title, chart_subtitle)
        self.package = ['corechart']

    def get_data(self, chart_name: str) -> list[list[str | int]]:
        """Формирует данные для столбчатой диаграммы."""
        data_list = []
        tool_set = set()
        for year in Config.YEARS:
            year_data = [str(year)]
            data_per_year = self.db.get_sorted_data_for_chart_per_year(year=year,
                                                                       chart_name=chart_name)
            for i in data_per_year:
                year_data.append(i.popularity)
                tool_set.add(i.data)
            data_list.append(year_data)
        tool_list = list(tool_set)
        tool_list.sort()
        head = ['Год'] + tool_list
        data_list.insert(0, head)
        return data_list

    def generate_script(self):
        """Генерация функции JavaScript для Stacked столбчатой диаграммы."""
        chart_data = self.get_data(self.chart_name)
        self.charts = self.charts + f'''
            google.charts.setOnLoadCallback(drawChart{self.chart_name});
            function drawChart{self.chart_name}() {{
            var data = google.visualization.arrayToDataTable({chart_data});
            var options = {{
            title: '{self.title}',
                legend: {{position: 'top', maxLines: 10 }},
                isStacked: 'percent',
                vAxis: {{direction: 1}},
                chartArea: {{height: "55%"}}
            }};
            var {self.chart_name} = new google.visualization.ColumnChart(document.getElementById('{self.chart_name}'));
            {self.chart_name}.draw(data, options);
            }}'''
        return self.charts

    def generate_divs(self):
        """Генерация раздела в который будут вставляться график."""
        return f'''<div id="{self.chart_name}" style="height: 650px;"></div>'''


class EChartBaseChartGenerator(BaseChartGenerator):
    """Базовый класс генерации диаграмм на базе библиотеки ECharts."""
    def __init__(self, chart_name: str, chart_title: str, chart_subtitle=''):
        super().__init__(chart_name, chart_title, chart_subtitle)
        self.auto_font_size_function = f'''
            function autoFontSize() {{
              let width = document.getElementById('{self.chart_name}').offsetWidth;
              let newFontSize = Math.round(width /50);
              if (newFontSize < 12)
                newFontSize = 12
              if (newFontSize > 16)
                newFontSize = 16
              return newFontSize;
            }};'''
        self.add_event_listener_function = f"""
            window.addEventListener('resize', function() {{
            if (myChart_{self.chart_name} != null && myChart_{self.chart_name} != undefined) {{
             myChart_{self.chart_name}.resize({{width: 'auto', height: 'auto'}});
                myChart_{self.chart_name}.setOption({{
                  legend: {{textStyle: {{fontSize: autoFontSize()}},}},
                  tooltip: {{textStyle: {{fontSize: autoFontSize()}},}},
                  xAxis: {{axisLabel: {{fontSize: autoFontSize(),}},}},
                  yAxis: {{axisLabel: {{fontSize: autoFontSize(),}},}},
                  series: {{label: {{textStyle: {{fontSize: autoFontSize()}}}}}}
                    }})
                }}
            """
        self.script_header = f"""
            var chartDom_{self.chart_name} = document.getElementById('{self.chart_name}');
            var myChart_{self.chart_name} = echarts.init(document.querySelector('#{self.chart_name}'),
                                        null, {{ renderer: 'svg' }});
            """
        self.div = f'''
            <h4>{self.title}</h4>
            <div id="{self.chart_name}" class="collapse show" style="width:100%; height: 600px;"></div>
            <hr>'''
        self.legend_type = 'plain'


class EChartStackedColumnChart(EChartBaseChartGenerator):
    """Класс генерации столбчатой Stackable диаграммы на базе библиотеки ECharts."""
    def get_data(self) -> dict:
        """Формирует данные для столбчатой Stacked диаграммы в долях от 100%."""
        data_dict = dict(series='', category=[])
        obj_list = list()
        value_list = self.db.get_unic_values_for_chart(chart_name=self.chart_name)
        data_dict['category'] = Config.YEARS
        for value in value_list:
            data = self.db.get_percentage_ordered_by_years(chart_name=self.chart_name,
                                                           param_name=value)
            if self.chart_name in ['schedule', 'employment', 'experience', 'with_salary']:
                obj = dict(name=Config.TRANSLATIONS[value], stack='total', type='bar', data=data)
            else:
                obj = dict(name=value, stack='total', type='bar', data=data)
            obj_list.append(obj)
        data_dict['series'] = json.dumps(obj_list)
        return data_dict

    def set_chart_option(self) -> str:
        """Устанавливает опции столбчатой Stacked диаграммы."""
        chart_data = self.get_data()
        return f"""
        var option_{self.chart_name};
        option_{self.chart_name} = {{
            tooltip: {{
                confine: true,
                show: true,
                trigger: 'axis',
                triggerOn: 'mousemove',
                textStyle: {{fontSize: autoFontSize()}},
                valueFormatter: (value) => (value * 100).toFixed(1) + '%'
              }},
            legend: {{
                type: '{self.legend_type}',
                top: '76%',
                selectedMode: 'multiple',
                selectorPosition: 'start',
                textStyle: {{fontSize: autoFontSize()}},
                width: '90%',
                selector: [{{
                    type: 'inverse',
                    title: 'Inv'
                  }}]
              }},
            grid: {{
                left: 50,
                right: 20,
                top: 20,
                bottom: 175
                }},
            yAxis: {{
               type: 'value',
               splitNumber: 10,
               boundaryGap: ['0', '100%'],
               min:0,
               max:1,
               scale:true,
               splitArea : {{show : true}},
               axisLabel: {{
                    show: true,
                    fontSize: autoFontSize(),
                    fontStyle: 'bold',
                    formatter: value => value * 100 + '%'
                       }}
               }},
            xAxis: {{
                type: 'category',
                data: {chart_data['category']},
                axisLabel: {{
                      show: true,
                      fontSize: autoFontSize(),
                      fontStyle: 'bold',
                      formatter: value => value
                }},
              }},
            series: {chart_data['series']}
            }};
        myChart_{self.chart_name}.setOption(option_{self.chart_name});
            """

    def generate_script(self):
        """Генерация функции JavaScript для Stacked столбчатой диаграммы."""
        return f'''
        {self.script_header}
        {self.set_chart_option()}
        {self.add_event_listener_function }
        }});'''


class EchartSunburst(EChartBaseChartGenerator):
    """Класс генерации диаграммы типа Sunburst на базе библиотеки ECharts."""
    def __init__(self, chart_name: str, chart_title: str, chart_subtitle=''):
        super().__init__(chart_name, chart_title, chart_subtitle)

        self.add_event_listener_function = f"""
            window.addEventListener('resize', function() {{
            if (myChart_{self.chart_name} != null && myChart_{self.chart_name} != undefined) {{
             myChart_{self.chart_name}.resize({{width: 'auto', height: 'auto'}});
                myChart_{self.chart_name}.setOption({{
                  legend: {{textStyle: {{fontSize: autoFontSize()}},}},
                  tooltip: {{textStyle: {{fontSize: autoFontSize()}},}},
                  xAxis: {{axisLabel: {{fontSize: autoFontSize(),}},}},
                  yAxis: {{axisLabel: {{fontSize: autoFontSize(),}},}},
                  series: {{label: {{fontSize: autoFontSize()}}}}
                    }})
                }}
            """

    def get_data(self, year) -> list:
        """Формирует данные для графиков по годам на основе запроса в БД."""
        output_list = list()
        parents = self.db.get_unic_parents()
        for parent in parents:
            data_dict = dict()
            children_from_db = self.db.get_data_for_chart_per_year_by_parent(
                year=year, chart_name=self.chart_name,
                parent=parent)
            children = list()
            data_dict['name'] = parent
            for child in children_from_db:
                children.append(dict(name=child.data,
                                     value=child.percent,
                                     ))
            data_dict['children'] = children
            output_list.append(data_dict)
        return output_list

    def set_chart_option(self) -> str:
        """Устанавливает опции Sunburst диаграммы."""
        return f"""
            var option_{self.chart_name};
            option_{self.chart_name} = {{
                legend: {{
                    type: 'plain',
                    show: true,
                    data: [{{name: 'test', icon: 'circle',}}],
                    }},
                tooltip: {{
                    show: true,
                    alwaysShowContent: true,
                    triggerOn: 'mousemove',
                    confine: false,
                    valueFormatter: (value) => (value * 100).toFixed(1) + '%'
                    }},
                series: {{
                    type: 'sunburst',
                    data: {self.get_data('2024')},
                    sort: 'asc',
                    radius: [0, '90%'],
                    startAngle: 120,
                    label: {{rotate: 'radial'}},
                    labelLayout: {{hideOverlap: true}},
                    emphasis: {{
                        itemStyle: {{
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }}
                    }},
                    levels: [
                    {{}},
                    {{ r0: '15%', r: '60%', label: {{rotate: 'radial', align: 'right'}}}},
                    {{ r0: '60%', r: '70%', label: {{position: 'outside', show: true, rotate: 'radial'}}}},
                    ],
                }}
            }};
        myChart_{self.chart_name}.setOption(option_{self.chart_name});
        """

    def generate_script(self) -> str:
        """Генерация функции JavaScript для Sunburst диаграммы."""
        return f'''
        {self.script_header}
        {self.set_chart_option()}
        {self.add_event_listener_function }
        }});'''


class EChartTreeMapChart(EChartBaseChartGenerator):
    """Класс генерации TreeMap диаграммы."""
    def get_data(self, year) -> list:
        output_list = list()
        parents = self.db.get_unic_parents()
        for parent in parents:
            data_dict = dict()
            children_from_db = self.db.get_data_for_chart_per_year_by_parent(
                year=year, chart_name=self.chart_name,
                parent=parent)
            children = list()
            data_dict['name'] = parent
            for child in children_from_db:
                children.append(dict(name=child.data,
                                     value=child.percent,
                                     tooltip={'padding': 5},
                                     ))
            data_dict['children'] = children
            output_list.append(data_dict)
        return output_list

    def get_series(self, year, idx) -> str:
        """Generate series for option of TreeMap chart."""
        seria = f"""
            {{
                type: 'treemap',
                name: '{str(year)}',
                // visualDimension: {idx},
                data: {self.get_data(str(year))},
                //roam: 'zoom',
                zoomToNodeRatio: 0.7*0.7,
                tooltip: {{
                    valueFormatter: (value) => (value * 100).toFixed(1) + '%'
                    }},
                label: {{
                    show: true,
                    overflow: 'break',
                    formatter: function (params) {{
                      return `${{params.name}} ${{Number(params.value*100).toFixed(1)  + '%'}}`}}

                }},
                upperLabel: {{
                    show: true,
                    height: 30
                    }},
                itemStyle: {{borderColor: '#fff'}},
                levels: [{{
                    itemStyle: {{
                        borderColor: '#777',
                        borderWidth: 0,
                        gapWidth: 1
                        }},
                    upperLabel: {{show: false}}
                    }},
                    {{
                    itemStyle: {{
                        borderColor: '#555',
                        borderWidth: 5,
                        gapWidth: 1
                        }},
                    emphasis: {{
                        itemStyle: {{
                            borderColor: '#ddd'
                            }}
                        }}
                    }},
                    {{
                    //colorSaturation: [0.35, 0.5],
                    //colorAlpha: [1, 1],
                    itemStyle: {{
                        borderWidth: 5,
                        gapWidth: 1,
                        borderColorSaturation: 0.6
                        }}
                    }}],
            }},"""
        return seria

    def set_chart_option(self) -> str:
        """Set options for TreeMap chart."""
        series = ''
        for idx, year in enumerate(Config.YEARS[::-1]):
            series += self.get_series(year=str(year), idx=idx)
        print(f"{series=}")
        return f"""
            var option_{self.chart_name};
            option_{self.chart_name} = {{
                legend: {{data: {Config.YEARS[::-1]}, selectedMode: 'single',}},
                series: [{series}],
                tooltip: {{}},
                }};
        myChart_{self.chart_name}.setOption(option_{self.chart_name});
        """

    def generate_script(self) -> str:
        """Генерация функции JavaScript для Stacked столбчатой диаграммы."""
        return f'''
        {self.script_header}
        {self.set_chart_option()}
        {self.add_event_listener_function }
        }});'''
