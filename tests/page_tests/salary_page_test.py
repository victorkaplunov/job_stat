from config import ConfigObj

config = ConfigObj()
rout = 'salary'


def test_salary_chart_data_type(charts_data):
    """variable 'salary' in JS function 'salary' contains list."""
    testing_data = charts_data(rout=rout)[0]
    assert isinstance(testing_data, list), 'Данные графика не являются списком.'
    for i in testing_data:
        assert isinstance(i, list), 'В данных графика использован не список.'
        assert i != [], 'В данных графика обнаружен пустой список.'


def test_annotation_row_in_salary_chart_data(charts_data):
    """Тне annotation row contain 'Range' and years value."""
    title_row = charts_data(rout=rout)[0][0]
    assert title_row[0] == 'Range', 'Первый элемент аннотации имеет неверное значение.'
    for n, i in enumerate(config.YEARS):
        assert str(i) == title_row[1:][n],\
            "Год из заголовка графика не совпадает с годом из конфигурационного файла."
