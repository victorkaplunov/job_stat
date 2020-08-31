import json
import re
import sqlite3
from wordcloud import WordCloud
from PIL import Image
import numpy as np


con = sqlite3.connect("testdb.db")
cur = con.cursor()
sql = 'SELECT json FROM vacancies'
# sql = 'SELECT json FROM vacancies LIMIT 1000'
cur.execute(sql)
vac = cur.fetchall()
cleaner = re.compile('<.*?>')  # Remove HTML tags
text = ''
# Create a list of word
f = open("word_cloud.txt", "a", encoding="utf-8")
for i in vac:
    description = json.loads(i[0])['description']
    json_dump = re.sub(cleaner, '', description)
    json_dump = json_dump.replace('й', 'й')
    json_dump = json_dump.replace('&quot;', '')
    print(json_dump)
    f.write(json_dump)
    text += json_dump
f.close()

f = open("word_cloud.txt", "r", encoding="utf-8")
text = f.read()
mask = np.array(Image.open("alfa_channel.png"))
# Create the wordcloud object
wordcloud = WordCloud(background_color="white",
                      max_words=1000,
                      mask=mask,
                      # contour_width=3, contour_color='steelblue',
                      width=800, height=600, margin=0
                      ).generate(text)

image = wordcloud.to_image()
# image.show()
wordcloud.to_file('w_cloud.png')
f.close()
