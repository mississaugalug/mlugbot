import urllib2
from BeautifulSoup import BeautifulSoup
import re

url = 'http://mississaugalug.ca/'
soup = BeautifulSoup(urllib2.urlopen("%s" % url))

getEventTitles = soup.findAll(itemprop="name")

cnt = 0
for title in getEventTitles:
    thisTitle = title.getText()
    if thisTitle == "MLUG Monthly Meet":
        positionalP = cnt
	break
    cnt += 1


title = soup.findAll(itemprop="name")[positionalP].getText()
month = soup.findAll("div", {"class": "dp-upcoming-text-month"})[positionalP].getText()
day = soup.findAll("div", {"class": "dp-upcoming-text-day"})[positionalP].getText()
startDate = soup.findAll(itemprop="startDate")[positionalP].getText()
time = startDate.split('-', 1)[0].split(' ', 1)[1]
location = soup.findAll("meta", {"itemprop": "location"})[positionalP]['content']
spltLoc = location.rsplit(',', 2)[0]

msg = 'The next \"%s\" will be on %s %s, %sat %s' % (title, month, day, time, spltLoc)
print msg