"""Подсчет средней зарплаты для вакансий с различным опытом.
Для вакансий с закрытым диапазоном берется среднее, для вакансий
с открытым диапазоном к началу диапазона прибавляется половина от
средней разницы из вакансий с закрытым диапазоном."""

import json
import sqlite3
import statistics

exchange_rate = {'RUR': 1, 'EUR': 91, 'USD': 73, 'UAH': 2.58}
# {'between1And3', 'moreThan6', 'between3And6', 'noExperience'}
experience = 'noExperience'
print('experience: ', experience)


# Загружаем вакансии из БД
con = sqlite3.connect("testdb.db")
cur = con.cursor()
sql = """SELECT v.json
FROM vacancies v
INNER JOIN calendar c
ON v.id = c.id
WHERE c.data LIKE "2021%";"""
cur.execute(sql)
vac = cur.fetchall()

# Отбираем вакансии с нужным опытом и собираем зарплаты в список
salary_list = []
for i in vac:
    if json.loads(i[0])['experience']['id'] == experience and json.loads(i[0])['salary'] is not None:
        salary_obj = json.loads(i[0])['salary']
        salary_obj.update({'id': json.loads(i[0])['id']})
        salary_list.append(salary_obj)

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

# Считаем среднюю предполагаемую зарплату с учетом открытых диапазонов и НДФЛ.
all_salary = []
for i in salary_list:
    # "Чистая" зарплата
    if i['gross'] is False:
        # закрытый диапазон
        if (i['from'] is not None) and (i['to'] is not None):
            all_salary.append((i['to'] + (i['to'] - i['from'])/2) * exchange_rate[i['currency']])
        # открытый вверх
        elif i['to'] is None:
            all_salary.append(i['from'] * exchange_rate[i['currency']] + average_delta_for_closed_salary/2)
        # открытый вниз
        elif i['from'] is None:
            all_salary.append(i['to'] * exchange_rate[i['currency']] - average_delta_for_closed_salary/2)
        else:
            print('!!!', i)
    # "Грязная" зарплата
    elif i['gross'] is True:
        # закрытый диапазон
        if (i['from'] is not None) and (i['to'] is not None):
            gross_salary = (i['to'] + (i['to'] - i['from']) / 2) * exchange_rate[i['currency']]
            all_salary.append(gross_salary - gross_salary * 0.13)
        # открытый вверх
        elif i['to'] is None:
            gross_salary = (i['from'] * exchange_rate[i['currency']] + average_delta_for_closed_salary / 2)
            all_salary.append(gross_salary - gross_salary * 0.13)
        # открытый вниз
        elif i['from'] is None:
            gross_salary = (i['to'] * exchange_rate[i['currency']] - average_delta_for_closed_salary / 2)
            all_salary.append(gross_salary - gross_salary * 0.13)
        else:
            print('!!', i)
    # else:
        # Зарплаты без указания "чистоты" в расчете не учитываются
        # print('!', i)
salary_sum = 0
for i in all_salary:
    salary_sum += i

average_salary = salary_sum/len(all_salary)
print("average_salary: ", average_salary)
print("median: ", statistics.median(all_salary))
# print(all_salary)

import csv


with open('GFG.csv', 'w', newline='') as f:
    # using csv.writer method from CSV package
    write = csv.writer(f)
    for i in all_salary:
        write.writerow([i])

