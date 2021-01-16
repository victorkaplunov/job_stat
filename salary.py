"""Подсчет средней зарплаты для вакансий с различным опытом.
Для вакансий с закрытым диапазоном берется среднее, для вакансий
с открытым диапазоном к началу диапазона прибавляется половина от
срденего разброса из вакансий с закрытым диапазоном."""

import json
import sqlite3
from pprint import pprint

exchange_rate = {'RUR': 1, 'EUR': 91, 'USD': 73, 'UAH': 2.58}
# {'between1And3', 'moreThan6', 'between3And6', 'noExperience'}
experience = 'between1And3'
print('experience: ', experience)


# Загружаем вакансии из БД
con = sqlite3.connect("testdb.db")
cur = con.cursor()
sql = "SELECT json FROM vacancies;"
cur.execute(sql)
vac = cur.fetchall()

# Отбираем вакансии с нужным опытом и собираем зарплаты в список
salary_list = []
for i in vac:
    # pprint(json.loads(i[0])['id'])
    if json.loads(i[0])['experience']['id'] == experience and json.loads(i[0])['salary'] is not None:
        salary = json.loads(i[0])['salary']
        salary.update({'id': json.loads(i[0])['id']})
        # print(salary)
        salary_list.append(salary)

# Подсчет зарплат с "чистой" и "грязной" зарплатой
net_list = []
gross_list = []
for i in salary_list:
    if i['gross'] is True:
        gross_list.append(i)
    else:
        net_list.append(i)
print('net: ', len(net_list))
print('gross: ', len(gross_list))

# Считаем средний разброс для вакансий с закрытым диапазоном
closed_salary = []
for i in salary_list:
    if i['from'] is None or i['to'] is None:
        pass
    else:
        closed_salary.append((i['to'] - i['from'])*exchange_rate[i['currency']])

closed_salary_sum = 0
for i in closed_salary:
    closed_salary_sum += i

average_delta_for_closed_salary = closed_salary_sum/len(closed_salary)
print('average_delta_for_closed_salary: ', average_delta_for_closed_salary)

# Считаем среднюю предполагаемую зарплату с учетом открытых диапазонов.
all_salary = []
for i in salary_list:
    # закрытый диапазон
    if (i['from'] is not None) and (i['to'] is not None):
        all_salary.append((i['to'] + (i['to'] - i['from'])/2) * exchange_rate[i['currency']])
    # открытый вверх
    elif i['to'] is None:
        all_salary.append((i['from'] + average_delta_for_closed_salary/2) * exchange_rate[i['currency']])
    # открытый вниз
    elif i['from'] is None:
        all_salary.append((i['to'] - average_delta_for_closed_salary/2) * exchange_rate[i['currency']])
    else:
        print(i)
salary_sum = 0
for i in all_salary:
    salary_sum += i

average_salary = salary_sum/len(all_salary)
print("average_salary: ", average_salary)
