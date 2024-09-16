from config import Config

rout = 'salary'


def test_salary_chart_data_type(charts_data):
    """variable 'salary' in JS function 'salary' contains list."""
    testing_data = charts_data(rout=rout)[0]
    assert isinstance(testing_data, list), 'Данные графика не являются списком.'
    for i in testing_data:
        assert isinstance(i, list), 'В данных графика использован не список.'
        assert i != [], 'В данных графика обнаружен пустой список.'


def test_annotation_row_in_salary_chart_data(charts_data):
    """Тне annotation row contains 'Range' and years value."""
    title_row = charts_data(rout=rout)[0][0]
    assert title_row[0] == 'Range', 'Первый элемент аннотации имеет неверное значение.'
    for n, i in enumerate(Config.YEARS):
        assert str(i) == title_row[1:][n],\
            "Год из заголовка графика не совпадает с годом из конфигурационного файла."


def test_salary_chart_values_qty(charts_data):
    """Длина списка со значениями совпадает с длинной списка заголовка."""
    testing_data = charts_data(rout=rout)[0]
    for exp_range in testing_data[1:-1]:
        assert len(exp_range) == len(testing_data[0]),\
            "Год из заголовка графика не совпадает с годом из конфигурационного файла."


def test_scatter_chart(scatter_charts_data):
    """Проверка данных для точечных диаграмм."""
    testing_data = scatter_charts_data(rout=rout)
    assert len(testing_data) == 4, 'Данные для точечных графиков не найдены или найдены не полностью.'
    assert isinstance(testing_data, list), 'Тип данных для точечных графиков не совпадает с ожидаемым.'
    for i in testing_data:
        assert isinstance(i, tuple), 'Тип данных для точечных графиков не совпадает с ожидаемым.'
