import json
import re
import sqlite3
from wordcloud import WordCloud
from PIL import Image
import numpy as np

con = sqlite3.connect("testdb.db")
cur = con.cursor()

# Get descriptions from all vacancies
year = '2020'
sql = f"""SELECT json FROM vacancies WHERE published_at
              BETWEEN '{year}-01-01T00:00:00+0300' AND '{year}-12-31T11:59:59+0300';"""
cur.execute(sql)
vac = cur.fetchall()
cleaner = re.compile('<.*?>')  # This is RegExp for removing HTML tags
text = ''
f = open("word_cloud.txt", "a", encoding="utf-8")
f.truncate(0)

# Create a list of word and filter some content
for i in vac:
    description = json.loads(i[0])['description']
    json_dump = re.sub(cleaner, '', description)  # Remove HTML tags
    json_dump = json_dump.replace('й', 'й')
    json_dump = json_dump.replace('Й', 'Й')
    json_dump = json_dump.replace('&quot;', '')
    stop_list = [
        'Опыт', 'опыт', "от года", "от одного года", 'тестирования', 'тестовой', 'тест планов', 'тест-планов',
        'тестовой документации', 'тест кейсы', "тест-кейсы", 'тест кейсов', "тест-кейсов",
        "тест-кейсы", 'чек листов', 'чек-листов', 'чек листы', 'чек-листы', 'тестовых сценариев',
        'тестирования ПО', "тестирование программного обеспечения", "по тестированию",
        'Мы ищем', 'мы ищем', "Мы ждем", "Мы ожидаем", "Чем предстоит", "Вам предстоит", "Вы будете",
        "Что нужно", 'Будет плюсом', 'будет плюсом', "плюсом будет",
        "Требования", "Базовые знания", "базовые знания", "Знания", "Знание", "принципов работы",
        "Навыки работы", "Умение работать", "умение работать",
        'Мы предлагаем', "Мы предлагаем:", "Что мы", "для сотрудников", "скидки от", "скидки на",
        "ДМС после", "счет компании", "со стоматологией", "доступности от", "чай", "кофе",
        "возможности для", "возможности для профессионального роста", "интересные задачи",
        "есть возможность",
        "Комфортный офис", "комфортный офис", "уютный офис", "современный офис", "от метро",
        "центре Москвы",
        "гибкое начало рабочего дня", 'График работы', 'график работы', "гибкий график",
        'Оформление по ТК РФ', "Официальное оформление", 'по ТК', "ТК РФ",
        'по результатам', 'на уровне', "заработная плата", "по итогам", "с первого дня",
        "испытательного срока",
        "для нас", "от вас", "если вы", "если ты", "для этого", "мы не", "том числе", "один из",
        "одного из", "не менее", "не только", "на базе", "на основе"
    ]
    for word in stop_list:
        json_dump = json_dump.replace(word, '')
    print(json_dump)
    f.write(json_dump)
f.close()

f = open("word_cloud.txt", "r", encoding="utf-8")
text = f.read()
# mask = np.array(Image.open("C:\\Users\\User\\PycharmProjects\\job_stat\\alpha_channel_1.png"))

# Create the wordcloud object
wordcloud = WordCloud(background_color="white",
                      max_words=300,
                      # mask=mask,
                      # contour_width=3, contour_color='steelblue',
                      width=600, height=800, margin=0
                      ).generate(text)

image = wordcloud.to_image()
wordcloud.to_file('w_cloud.png')
f.close()
