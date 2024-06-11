import json

from pyecharts import options as opts
from pyecharts.charts import TreeMap, Bar, Grid
from pyecharts.commons import utils
from pyecharts.globals import RenderType

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

    def get_options(self) -> str:
        return ''

    def get_script(self) -> str:
        """Get chart script."""
        return f"""
        <script src="/static/echarts.js"></script>
        <script type="text/javascript">
        var chartDom_{self.name} = document.getElementById('{self.name}');
        var {self.name} = echarts.init(document.querySelector('#{self.name}'),
                                        null, {{ renderer: 'svg' }});
        var option = {self.get_options()}
        {self.name}.setOption(option);
        </script>
        """


class EchartStackedColumn(BaseChart):
    def get_data(self) -> list:
        """Get data for Stacked Column chart."""
        value_list = self.db.get_unic_values_for_chart(chart_name=self.name)
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

    def get_options(self) -> str:
        chart = Bar(init_opts=opts.InitOpts(width="100%"))
        chart.set_global_opts(title_opts=opts.TitleOpts(is_show=False),
                              legend_opts=opts.LegendOpts(selector_position='start',
                                                          pos_top='76%', pos_left=5,
                                                          selector=[{'type': 'inverse'}],
                                                          selector_button_gap=5),
                              tooltip_opts=opts.TooltipOpts(
                                  is_show=True, trigger_on='mousemove', trigger='axis',
                                  value_formatter=utils.JsCode(
                                      "(value) => (value * 100).toFixed(1) + '%'")),
                              )
        chart.add_xaxis(Config.YEARS)
        series = self.get_data()
        for seria in series:
            chart.add_yaxis(seria['name'], seria['data'], stack="stack1")
        chart.options['grid'] = {'left': 50, 'right': 20, 'top': 20, 'bottom': 175}
        chart.options['legend'][0]['width'] = '90%'
        chart.set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        return chart.dump_options()


class EchartTreeMap(BaseChart):
    def get_data(self, year) -> list:
        """Get data for TreeMap chart."""
        output_list = list()
        parents = self.db.get_unic_parents()
        for parent in parents:
            data_dict = dict()
            children_from_db = self.db.get_data_for_chart_per_year_by_parent(
                year=year, chart_name=self.name,
                parent=parent)
            children = list()
            data_dict['name'] = parent
            for child in children_from_db:
                children.append(dict(name=child.data, value=child.percent))
            data_dict['children'] = children
            output_list.append(data_dict)
        return output_list

    def get_options(self) -> str:
        chart = TreeMap().set_global_opts(title_opts=opts.TitleOpts(is_show=False),
                                          legend_opts=opts.LegendOpts(selected_mode='single', ),
                                          tooltip_opts=opts.TooltipOpts(is_show=True))

        js_fnc = "function (params) {return `${params.name} ${Number(params.value*100).toFixed(1)  + '%'}`}"
        for year in Config.YEARS[::-1]:
            chart.add(
                series_name=year, data=self.get_data(year=year), roam='zoom',
                leaf_depth=1,
                label_opts=opts.LabelOpts(formatter=utils.JsCode(js_fnc)),
                upper_label_opts=opts.LabelOpts(is_show=True),
                levels=[
                    opts.TreeMapLevelsOpts(upper_label_opts=opts.LabelOpts(is_show=False)),
                    opts.TreeMapLevelsOpts(upper_label_opts=opts.LabelOpts(is_show=True),),
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
