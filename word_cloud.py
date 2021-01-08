import json
import re
import sqlite3
from wordcloud import WordCloud
from PIL import Image
import numpy as np

con = sqlite3.connect("testdb.db")
cur = con.cursor()

# Get descriptions from all vacancies
sql = 'SELECT json FROM vacancies'
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
    print(json_dump)
    f.write(json_dump)
f.close()

f = open("word_cloud.txt", "r", encoding="utf-8")
text = f.read()
mask = np.array(Image.open("C:\\Users\\User\\PycharmProjects\\job_stat\\alpha_channel_1.png"))

# Create the wordcloud object
wordcloud = WordCloud(background_color="white",
                      max_words=300,
                      mask=mask,
                      # contour_width=3, contour_color='steelblue',
                      width=600, height=800, margin=0
                      ).generate(text)

image = wordcloud.to_image()
wordcloud.to_file('w_cloud.png')
f.close()
