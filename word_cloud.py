import json
import re
import sqlite3
from wordcloud import WordCloud
from PIL import Image
import numpy as np

con = sqlite3.connect("testdb.db")
cur = con.cursor()

# Get descriptions from all vacancies
year = '2024'
sql = f"""SELECT json FROM vacancies WHERE published_at
              BETWEEN '{year}-01-01T00:00:00+0300' AND '{year}-12-31T11:59:59+0300';"""
cur.execute(sql)
vacancies = cur.fetchall()
cleaner = re.compile('<.*?>')  # This is RegExp for removing HTML tags
text = ''
f = open("word_cloud.txt", "a", encoding="utf-8")
f.truncate(0)

# Create a list of word and filter some content
for i in vacancies:
    description = json.loads(i[0])['description']
    json_dump = re.sub(cleaner, '', description)  # Remove HTML tags
    json_dump = json_dump.replace('й', 'й')
    json_dump = json_dump.replace('Й', 'Й')
    json_dump = json_dump.replace('&quot;', '')
    stop_list = [
        'Mail.ru Group', 'Group IB', 'looking',
    ]
    for word in stop_list:
        json_dump = json_dump.replace(word, '')

    result = re.sub(u'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]', u'', json_dump)
    f.write(result)
f.close()

f = open("word_cloud.txt", "r", encoding="utf-8")
text = f.read()
# mask = np.array(Image.open("alfa_channel.png"))

# Create the wordcloud object
wordcloud = WordCloud(background_color="white",
                      max_words=100,
                      # mask=mask,
                      contour_width=3, contour_color='steelblue',
                      min_word_length=2,
                      # width=800, height=600, margin=0,
                      width=350, height=550, margin=0
                      ).generate(text)

image = wordcloud.to_image()
wordcloud.to_file('w_cloud.png')
f.close()
