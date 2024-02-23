class ConfigObj:
    LOCAL_HOST_BASE_URL = 'http://127.0.0.1:5000'
    BASE_URL = 'http://api.hh.ru/vacancies/'
    DB_FILE_NAME = 'testdb.db'
    YEARS = [2019, 2020, 2021, 2022, 2023, 2024]
    STOP_LIST = ['Формовщик теста', 'тестомес', 'Тестомес',
                 'Key Account Manager']
    EXCHANGE_RATES = {'RUR': 1, 'EUR': 86,
                      'USD': 73, 'UAH': 2.58,
                      'KZT': 0.2, 'AZN': 53.03}
    EXPERIENCE_GRADES = ['noExperience', 'between1And3',
                         'between3And6', 'moreThan6']
