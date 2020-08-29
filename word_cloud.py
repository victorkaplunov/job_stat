import json
import re
import sqlite3
from wordcloud import WordCloud

con = sqlite3.connect("testdb.db")
cur = con.cursor()
sql = 'SELECT json FROM vacancies'
# sql = 'SELECT json FROM vacancies LIMIT 1000'
cur.execute(sql)
vac = cur.fetchall()
cleaner = re.compile('<.*?>')  # Remove HTML tags
text = ''
# Create a list of word

for i in vac:
    description = json.loads(i[0])['description']
    json_dump = re.sub(cleaner, '', description)
    json_dump = json_dump.replace('&quot;', '')
    text += json_dump
print(text)

# Create the wordcloud object
wordcloud = WordCloud(background_color="white", width=600, height=800, margin=0).generate(text)

image = wordcloud.to_image()
# image.show()
wordcloud.to_file('w_cloud.png')
