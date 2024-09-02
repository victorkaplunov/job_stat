import os


class Config:
    basedir = os.path.abspath(os.path.dirname(__file__))
    # PythonAnywhere params
    PA_USERNAME = 'clingon'
    PA_APP_DIR = 'job_stat'

    LOCAL_HOST_BASE_URL = 'http://127.0.0.1:5000'

    BASE_URL = 'http://api.hh.ru/vacancies/'

    SEARCH_STRING = u'?text=QA OR Qa OR QА OR Qа Q.A. тест* OR Тест* OR ТЕСТ* ' \
                    u' OR SDET OR test* OR Test* OR TEST* OR Quality OR quality&' \
                    'no_magic=true&order_by=publication_time&' \
                    'area=1&specialization=1.117&' \
                    'search_field=name&' \
                    'page=0'

    PAGES_QTY = 12

    DB_FILE_NAME = 'testdb.db'

    YEARS = [2020, 2021, 2022, 2023, 2024]

    STOP_LIST = ['Формовщик теста', 'тестомес', 'Тестомес', 'Тестовод',
                 'Пекарь-тестомес', 'Пекарь/тестовод', 'Тестодел',
                 'тестоприготовления', 'тесторазделочных',
                 'Key Account Manager', 'Комплектовщик-Тестировщик',
                 'Специалист по подбору материалов для учебных курсов',
                 'Составитель теста и фарша', '(Ввод в гражданский оборот)',
                 'Менеджер по качеству и пищевой безопасности',
                 'Materials Operations Intern',
                 'Тестировщик бытовой техники', 'Тестировщик женских сумок',
                 'мастер-тестировщик',
                 'Начинающий специалист в отдел тестирование крупной техники',
                 'Начинающий специалист в отдел тестирование крупной техники',
                 'Начинающий специалист в отдел тестирования крупной техники',
                 'Начинающий специалист в отдел тестирования крупной техники',
                 'Стажер в центр сборки и тестирования техники',
                 'Сотрудник на тестирование ИИ (нейросетей)',
                 'Тестировщик Чат Ботов ИИ(Нейросетей)',
                 'Тестировщик крупно-бытовой техники',
                 'FixItRight', 'Тестировщик устройств Apple',
                 'Тестировщик компьютерной техники/ Оптимизация и ремонт',
                 'Начинающий тестировщик компьютерной техники',
                 'Тестировщик игровых приставок', 'Тестировщик-установщик оборудования',
                 'Тестировщик мобильных телефонов',
                 'Мастер по ремонту оборудования, техники',
                 'ИП Дмитриев Александр Петрович'
                 ]
    # ToDo: Запрашивать в API, включая обменный курс.
    EXCHANGE_RATES = {'RUR': 1, 'EUR': 86,
                      'USD': 73, 'UAH': 2.58,
                      'KZT': 0.2, 'AZN': 53.03}

    MROT = 13890  # Минимальный размер оплаты труда

    TRANSLATIONS = dict(noExperience="Без опыта",
                        between1And3="От года до трех",
                        between3And6="От трех до шести лет",
                        moreThan6="Более шести лет",
                        fullDay='Полный день', flexible='Гибкий график',
                        shift='Сменный график', remote='Удаленная работа',
                        full='Полная занятость', part='Частичная занятость',
                        project="Проектная работа", probation='Стажировка',
                        volunteer="Волонтер",
                        without_salary='Зарплата не указана',
                        closed='Закрытый диапазон',
                        open_up='Зарплата от...',
                        open_down='Зарплата до...',
                        flyInFlyOut='Вахтовый метод')

    PROGRAM_LANGUAGES = ['Java', 'Python', 'JavaScript', 'C#', "PHP", 'C++',
                         'Ruby', 'Groovy', ' Go ', 'Scala', 'Swift',
                         'Kotlin', 'TypeScript', 'VBScript', 'tcl', 'Perl',
                         'AutoIT']

    BDD_FRAMEWORKS = ['Cucumber', 'Robot_Framework', 'SpecFlow', 'TestLeft',
                      'RSpec', 'JBehave', 'HipTest', "Jasmine", 'Behat',
                      'behave', 'Fitnesse', 'Cucumber-JVM',
                      'pytest-bdd', 'NSpec', 'Serenity BDD']

    LOAD_TESTING_TOOLS = ['JMeter', 'LoadRunner', 'Performance Center', 'K6',
                          'Locust', 'Gatling', 'Grinder', 'Yandex.Tank',
                          'IBM Rational Performance']

    TRAFFIC_GENERATORS = ['TRex', 'IXIA', 'pktgen']

    TRACING_SYSTEM = ['DynaTrace', 'Jaeger', 'Zipkin']

    MONITORING = ['CloudWatch', 'Grafana', 'Zabbix', 'Tabix',
                  'Prometheus', 'VictoriaMetrics',
                  'InfluxDB', 'Graphite', 'ClickHouse']

    API_TESTING_TOOLS = ['Postman', 'Insomnia', 'SoapUI', 'cURL', 'Swagger']

    SNIFFERS = ['Fiddler', 'Charles', 'Burp', 'Proxyman', 'mitmproxy', 'Wireshark',
                # 'Reqable', 'PCAPdroid', 'Packet Capture', 'HTTP Catcher'
                ]

    CI_CD = ['GitLab', 'GitHub', 'Bitbucket', 'Jenkins',
             'Cirlce CI', 'Travis CI', 'Bamboo', 'TeamCity']

    WEB_UI_TOOLS = ['Selenium', 'Ranorex', 'Selenide', 'Selenoid', 'Selene',
                    'Cypress', 'Splinter', 'Puppeteer', 'WebDriverIO', 'Galen',
                    'Playwright', 'Protractor', 'TestCafe']

    MOBILE_TESTING_FRAMEWORKS = ['Appium', 'Selendroid', 'Espresso', 'Detox',
                                 'robotium', 'Calabash', 'UI Automation',
                                 'UIAutomator', 'XCTest', 'Kobiton']

    BUGTRACKING_N_TMS = ['Youtrack', 'TestRail', 'TestLink', 'TestLodge',
                         'Jira', 'Confluence', 'Redmine', 'TFS', 'Zephyr',
                         'Hiptest', 'Xray', 'PractiTest', 'Testpad',
                         'Deviniti', 'Qase', 'IBM Rational Quality Manager',
                         'HP Quality Center', 'HP ALM', 'TestIt']

    CVS = ['git', 'SVN', 'Subversion', 'Mercurial']

    UNIT_FRAMEWORKS = [['pytest', 'Python'], ['py.test', 'Python'],
                       ['Unittest', 'Python'], ['Nose', 'Python'],
                       ['Robot_Framework', 'Python'],
                       ['JUnit', 'Java'], ['TestNG', 'Java'],
                       ['PHPUnit', 'PHP'], ['Codeception', 'PHP'],
                       ['RSpec', 'Ruby'], ['Capybara', 'Ruby'],
                       ['Spock', 'C#'], ['NUnit', 'C#'],
                       ['Mocha', 'JavaScript'], ['Serenity', 'JavaScript'],
                       ['Jest', 'JavaScript'], ['Jasmine', 'JavaScript'],
                       ['Nightwatch', 'JavaScript'], ['Karma', 'JavaScript'],
                       ['CodeceptJS', 'JavaScript']]

    SCHEDULE = ['fullDay', 'flexible', 'shift', 'remote', 'flyInFlyOut']
     
    EXPERIENCE = ['noExperience', 'between1And3', 'between3And6', 'moreThan6']
    
    EMPLOYMENT = ['full', 'part', 'project', 'probation', 'volunteer']
    
    WITH_SALARY = ['without_salary', 'closed', 'open_up', 'open_down']
