# Scrape wikipedia for World Poets\
# Slacker Design
# feature.frame at gmail dot com

import requests
import json
from bs4 import BeautifulSoup
import re
import csv
from geopandas.tools import geocode

poets = []

soup = BeautifulSoup(open("filtered.html"), 'html.parser')
object = soup.find(id="mw-content-text")
items = object.find_all('li')

# ---------------------------------------------------------------------------------------------

for tag in items:
    for row in tag.findAll('a'):
        poet = {}
        poet['href'] = 'https://en.wikipedia.org' + row['href']
        poet['name'] = row.text
        poet["born"] = 0
        poet["died"] = 0
        poet['info'] = tag.text
        poets.append(poet)

# print(poets)

with open("./world-poets-g.json", 'w') as outfile:
    json.dump(poets, outfile)


# -----------------------------------------------------------------------------------------
# Dates of Birth/Death

pattern = "\(\d+\u2013\d+\)" + "|" + "\(born \d+\)" + "|" + "\(died \d+\)"

for poet in poets:
    data = poet['info']

    try:
        dates = re.search(pattern, data).group(0)

        years = re.search("(\d+)\u2013(\d+)", dates)
        if years:
            poet["born"] = int(years.group(1))
            poet['died'] = int(years.group(2))
            continue

        years = re.search("born (\d+)", dates)
        if years:
            poet["born"] = int(years.group(1))
            continue

        years = re.search("died (\d+)", dates)
        if years:
            poet["died"] = int(years.group(1))
            continue
    except:
        continue

with open("./world-poets-g.json", 'w') as outfile:
    json.dump(poets, outfile, indent=2)

# ---------------------------------------------------------------------------------------------
# Info/comment string

pattern = "\), (\D+)"

for poet in poets:
    data = poet['info']
    try:
        info = re.search(pattern, data).group(1)
        if info:
            poet["info"] = str(info)
    except:
        poet["info"] = ""

with open("./world-poets-g.json", 'w') as outfile:
    json.dump(poets, outfile, indent=2)

# ---------------------------------------------------------------------------------------------
# del dups

tmp = []
foo = count = 0
for poet in poets:
    if count == 0:
        pb = poet["born"]
        pd = poet["died"]
        info = poet["info"]
        count += 1
    elif poet["born"] == pb and poet["died"] == pd and poet["info"] == info:
        poets.remove(poet)
        foo += 1
        count = 0
    else:
        pb = poet["born"]
        pd = poet["died"]
        info = poet["info"]

print(foo)

with open("./world-poets-g.json", 'w') as outfile:
    json.dump(poets, outfile, indent=2)

# ---------------------------------------------------------------------------
# Get birthplace and deathplace

for poet in poets:
    url2 = poet['href']
    page = requests.get(url2)
    soup = BeautifulSoup(page.text, 'html.parser')

    try:
        first_div = soup.find('div', {'class': 'birthplace'})
        first_a = first_div.find('a')
        birthplace = first_a['title']

        poet['birthplace'] = birthplace
        print('birthplace: ', birthplace)
    except:
        poet['birthplace'] = ""
        pass

    try:
        first_div = soup.find('div', {'class': 'deathplace'})
        first_a = first_div.find('a')
        deathplace = first_a['title']

        poet['deathplace'] = deathplace
        print("deathplace: ", deathplace)
    except:
        poet['deathplace'] = ""
        pass

with open("./world-poets-g.json", 'w') as outfile:
    json.dump(poets, outfile, indent=2)

# ---------------------------------------------------------------------------
# Get birthplace and deathplace - old style infobox

for poet in poets:
    if poet['birthplace'] or poet['deathplace']:
        continue

    url2 = poet['href']
    page = requests.get(url2)
    soup = BeautifulSoup(page.content, 'html.parser')

    try:
        infobox = soup.find('table', {'class': 'infobox'})
        # print(infobox)
        third_tr = infobox.find_all('tr')[2]
        # print(third_tr)
        bod = third_tr.find('th').text
        first_a = third_tr.find('a')['title']
        if(len(first_a) < 30):
            print(poet['name'], " ", bod, first_a)
            if bod == "Born":
                poet['birthplace'] = first_a
            elif bod == "Died":
                poet['deathplace'] = first_a
            else:
                pass
    except:
        pass

    try:
        fourth_tr = infobox.find_all('tr')[3]
        bod = fourth_tr.find('th').text
        first_a = fourth_tr.find('a')['title']

        if(len(first_a) < 30):
            print(poet['name'], " ", bod, first_a)
            if bod == "Born":
                poet['birthplace'] = first_a
            elif bod == "Died":
                poet['deathplace'] = first_a
            else:
                pass
    except:
        pass

with open("./world-poets-g.json", 'w') as outfile:
    json.dump(poets, outfile, indent=2)

# ----------------------------------------------------------------------------
# Geocode places of birth/death

for poet in poets:
    poet['birth_lon'] = 0
    poet['birth_lat'] = 0
    poet['death_lon'] = 0
    poet['death_lat'] = 0

    if poet['birthplace'] != '':
        try:
            df = geocode(poet['birthplace'], provider="nominatim",
                         user_agent="poetsgis", timeout=10)
            poet['birth_lon'] = round(df['geometry'][0].x, 5)
            poet['birth_lat'] = round(df['geometry'][0].y, 5)
        except:
            continue

    if poet['deathplace'] != '':
        try:
            df = geocode(poet['deathplace'], provider="nominatim",
                         user_agent="poetsgis", timeout=10)
            poet['death_lon'] = round(df['geometry'][0].x, 5)
            poet['death_lat'] = round(df['geometry'][0].y, 5)
        except:
            continue

with open("world-poets-g.json", 'w') as outfile:
    json.dump(poets, outfile, indent=2)

# ----------------------------------------------------------------------------
# Write to CSV

with open("world-poets-g.json") as infile:
    data = json.load(infile)

csv_file = open('world-poets.csv', 'w', newline='')
csv_writer = csv.writer(csv_file)

count = 0
for poet in data:
    if count == 0:
        header = poet.keys()
        csv_writer.writerow(header)
        count += 1
    csv_writer.writerow(poet.values())

csv_file.close()