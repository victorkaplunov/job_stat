import statistics
from distutils.command.config import config

from pyecharts import options as opts
from pyecharts.charts import TreeMap, Bar, Boxplot
from pyecharts.commons import utils

from config import Config
from db.db_client import Database


class BaseChart:
    def __init__(self, name: str, title: str):
        self.title = title
        self.name = name
        self.db = Database()

    def get_div(self, height=600) -> str:
        """Make chart`s div."""
        return f'''
        <h4>{self.title}</h4>
        <div id="{self.name}" style="height: {height}px;"></div>
        <hr>'''

    def _get_options(self) -> str:
        raise NotImplementedError('Не определен метод _get_options')

    def get_script(self) -> str:
        """Get chart script."""
        return f"""
        <script src="/static/echarts.js"></script>
        <script type="text/javascript">
        var chartDom_{self.name} = document.getElementById('{self.name}');
        var {self.name} = echarts.init(document.querySelector('#{self.name}'),
                                        null, {{ renderer: 'svg' }});
        var option = {self._get_options()}
        {self.name}.setOption(option);
        </script>
        """


class EchartStackedColumn(BaseChart):
    def _get_data(self) -> list:
        """Get data for Stacked Column chart."""
        value_list = self.db.get_unic_values_for_chart_sorted_by_last_year_percent(chart_name=self.name)
        output_list = []
        for value in value_list:
            data = self.db.get_percentage_ordered_by_years(chart_name=self.name,
                                                           param_name=value)
            if self.name in ['schedule', 'employment', 'experience', 'with_salary']:
                obj = dict(name=Config.TRANSLATIONS[value], data=data)
            else:
                obj = dict(name=value, data=data)
            output_list.append(obj)
        return output_list

    def _get_options(self) -> str:
        chart = Bar(init_opts=opts.InitOpts(width="100%"))
        chart.set_global_opts(title_opts=opts.TitleOpts(is_show=False),
                              legend_opts=opts.LegendOpts(selector_position='start',
                                                          pos_top='76%', pos_left='center',
                                                          selector=[{'type': 'inverse'}],
                                                          selector_button_gap=5),
                              yaxis_opts=opts.AxisOpts(
                                  axislabel_opts=opts.LabelOpts(
                                      formatter=utils.JsCode("value => value * 100 + '%'"))),
                              tooltip_opts=opts.TooltipOpts(
                                  is_show=True, trigger_on='mousemove',
                                  trigger='axis', is_confine=True,
                                  value_formatter=utils.JsCode(
                                      "(value) => (value * 100).toFixed(1) + '%'")),
                              )
        chart.add_xaxis(self.db.get_years_for_chart(self.name))
        series = self._get_data()
        for seria in series:
            chart.add_yaxis(seria['name'], seria['data'], stack="stack1")
        chart.options['grid'] = {'left': 50, 'right': 20, 'top': 20, 'bottom': 175}
        chart.options['legend'][0]['width'] = '90%'
        chart.set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        return chart.dump_options()


class EchartTreeMap(BaseChart):
    def _get_data(self, year) -> list:
        """Get data for TreeMap chart."""
        output_list = list()
        parents = self.db.get_unic_parents()
        for parent in parents:
            data_dict = dict()
            children_from_db = self.db.get_data_for_chart_per_year_by_parent(
                year=year, chart_name=self.name,
                parent=str(parent))
            children = list()
            data_dict['name'] = parent
            for child in children_from_db:
                children.append(dict(name=child.data, value=child.percent))
            data_dict['children'] = children
            output_list.append(data_dict)
        return output_list

    def _get_options(self) -> str:
        chart = TreeMap().set_global_opts(title_opts=opts.TitleOpts(is_show=False),
                                          legend_opts=opts.LegendOpts(selected_mode='single', ),
                                          tooltip_opts=opts.TooltipOpts(is_show=True))

        fn = "function (params) {return `${params.name} ${Number(params.value*100).toFixed(1)  + '%'}`}"
        for year in Config.YEARS[::-1]:
            chart.add(
                series_name=year, data=self._get_data(year=year), roam='zoom',
                leaf_depth=1,
                label_opts=opts.LabelOpts(formatter=utils.JsCode(fn)),
                upper_label_opts=opts.LabelOpts(is_show=True),
                levels=[
                    opts.TreeMapLevelsOpts(upper_label_opts=opts.LabelOpts(is_show=False)),
                    opts.TreeMapLevelsOpts(upper_label_opts=opts.LabelOpts(is_show=True)),
                    opts.TreeMapLevelsOpts(
                        upper_label_opts=opts.LabelOpts(is_show=True),
                        treemap_itemstyle_opts=opts.TreeMapItemStyleOpts(
                            border_color='#ddd',
                            border_width=1
                        )
                    )
                ],
                tooltip_opts=opts.TooltipOpts(
                    value_formatter=utils.JsCode("(value) => (value * 100).toFixed(1) + '%'"),
                    trigger_on='mousemove'
                ),
            )
        del chart.options['legend'][0]['data']
        return chart.dump_options()


def overflow(name_list: list) -> list:
    """Clean up strings for horizontal bar charts"""
    output_list = list()
    for name in name_list:
        name = name.replace('(JSC «OTP Bank»)', '')
        name = name.replace('-специализированный застройщик', '')
        if len(name) > 20:
            name = name.replace(' ', '\n')
        output_list.append(name)
    return output_list


class EchartHorizontalBar(BaseChart):
    def _get_data(self) -> dict:
        """Get data for Horizontal Bar chart."""
        statistics_data = self.db.get_sorted_data_for_chart(chart_name=self.name)
        name_list = [i.data for i in statistics_data]
        name_list = overflow(name_list=name_list)
        data_list = [i.popularity for i in statistics_data]
        output_dict = dict(name_list=name_list[::-1], data_list=data_list[::-1])
        return output_dict

    def _get_options(self) -> str:
        """Get options for Horizontal Bar chart."""
        chart_data = self._get_data()
        chart = (((Bar(init_opts=opts.InitOpts(width="100%"))
                 .add_xaxis(chart_data['name_list'], ))
                 .add_yaxis(Config.YEARS[-1], chart_data['data_list'],
                            label_opts=opts.LabelOpts(
                    overflow='break', position='insideRight')))
                 .reversal_axis()
                 .set_global_opts(
            xaxis_opts=opts.AxisOpts(type_='value'),
            yaxis_opts=opts.AxisOpts(type_='category')
        ).set_series_opts(label_opts=opts.LabelOpts(is_show=False),
                          tooltip_opts=opts.TooltipOpts(formatter='{c}'), position='inside'))
        chart.options['grid'] = {'left': 140, 'right': 20, 'top': 30, 'bottom': 175}
        return chart.dump_options()


class EchartHorizontalBarByCategory(BaseChart):
    def __init__(self, name: str, title: str, category: str):
        self.title = title
        self.name = name
        self.category = category
        self.db = Database()

    def _get_data(self) -> list:
        """Get data for Horizontal Bar chart."""
        data = self.db.get_data_for_chart_per_year_by_category(chart_name=self.name,
                                                               category=self.category)
        return [i.popularity for i in data]

    def _get_options(self) -> str:
        """Get options for Horizontal Bar chart."""
        chart = Bar(init_opts=opts.InitOpts(width="100%", page_title='fgfdgfd'))
        chart.add_xaxis(Config.YEARS)
        chart.add_yaxis(series_name=self.category, y_axis=self._get_data(),
                        label_opts=opts.LabelOpts(
                            overflow='break', position='insideRight'))

        chart.reversal_axis()
        chart.set_global_opts(
            title_opts=opts.TitleOpts(title=self.title),
            xaxis_opts=opts.AxisOpts(type_='value',
                                     max_=300000,
                                     split_number=3,
                                     axislabel_opts=opts.LabelOpts(
                                         is_show=True,
                                         formatter=utils.JsCode(
                                             "value => '₽' +(value / 1000).toFixed(0) + ' тыс.'"))
                                     ),
            yaxis_opts=opts.AxisOpts(type_='category',

                                     axislabel_opts=opts.LabelOpts(
                                         is_show=True,
                                         formatter=utils.JsCode(
                                             "value => value + ' г.'"))
                                     ),
            legend_opts=opts.LegendOpts(is_show=False),
        )
        chart.add_xaxis(self.db.get_years_for_chart(self.name))
        chart.options['grid'] = {'left': 76, 'right': 25, 'top': 40}
        return chart.dump_options()

    def get_div(self, height=600) -> str:
        """Make chart`s div."""
        return f'''
        <div id="{self.name}" style="height: {height}px;"></div>
        '''


class EchartBoxplot(BaseChart):
    def get_data(self) -> (list[list], list):
        """Get data for Boxplot chart."""
        param_list = self.db.get_unic_values_for_chart(self.name)
        tmp_dict = dict()
        for param in param_list:
            salary_list = self.db.find_salary_by_substring_in_description(search_phrase=str(param))
            if len(salary_list) < 10:
                continue
            if param == 'Robot_Framework':
                param = 'Robot\nFramework'
            tmp_dict[str(param)] = salary_list
        # Сортируем по медиане для списка зарплат.
        sorted_dict = dict(sorted(tmp_dict.items(), key=lambda item: statistics.median(item[1])))
        return sorted_dict

    def _get_options(self) -> str:
        """Get options for Boxplot chart."""
        chart_data = self.get_data()
        chart = (Boxplot(init_opts=opts.InitOpts(width="100%")))
        chart.add_xaxis(list(chart_data.keys()))
        chart.add_yaxis(Config.YEARS[-1], chart.prepare_data(chart_data.values()))
        chart.set_global_opts(xaxis_opts=opts.AxisOpts(type_='value', split_number=2),
                              yaxis_opts=opts.AxisOpts(type_='category'),
                              tooltip_opts=opts.TooltipOpts(trigger_on='mousemove')
                              )
        chart.reversal_axis()
        chart.options['grid'] = {'left': 76, 'right': 25, 'top': 40}
        return chart.dump_options()
