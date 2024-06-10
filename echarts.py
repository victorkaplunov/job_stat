from pyecharts import options as opts
from pyecharts.charts import TreeMap
from pyecharts.commons import utils

from config import Config
from db.db_client import Database


class EchartTreeMap(TreeMap):
    def __init__(self, name: str, title: str):
        super().__init__()
        self.title = title
        self.name = name
        self.db = Database()

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

    def get_options(self):
        chart = TreeMap().set_global_opts(title_opts=opts.TitleOpts(is_show=False),
                                          legend_opts=opts.LegendOpts(selected_mode='single', ),
                                          tooltip_opts=opts.TooltipOpts(is_show=True))

        for year in Config.YEARS[::-1]:
            chart.add(
                series_name=year, data=self.get_data(year=year), roam='zoom',
                leaf_depth=1,
                label_opts=opts.LabelOpts(
                    formatter=utils.JsCode(
                        """function (params) {return `${params.name} ${Number(params.value*100).toFixed(1)  + '%'}`}"""
                    ),
                ),
                upper_label_opts=opts.LabelOpts(is_show=False),
                tooltip_opts=opts.TooltipOpts(
                    value_formatter=utils.JsCode("(value) => (value * 100).toFixed(1) + '%'"),
                ),
            )
        del chart.options['legend'][0]['data']
        return chart.dump_options()

    def get_div(self):
        """Make chart`s div."""
        return f'''
        <h4>{self.title}</h4>
        <div id="{self.name}" style="height: 600px;"></div>
        <hr>'''

    def get_script(self):
        """Make complete chart script."""
        return f"""
        <script src="/static/echarts.js"></script>
        <script type="text/javascript">
        var chartDom_{self.name} = document.getElementById('{self.name}');
        var myChart_{self.name} = echarts.init(document.querySelector('#{self.name}'),
                                        null, {{ renderer: 'svg' }});
        var option = {self.get_options()}
        myChart_{self.name}.setOption(option);
    </script>
        """
