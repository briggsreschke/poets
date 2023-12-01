# Scrape wikipedia for World of Poets
# Slacker Design
# feature.frame at gmail dot com

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
from geopandas.tools import geocode

poets = []

# ---------------------------------------------------------------------------------------------
# make array of dicts (poet records) from html poet data

soup = BeautifulSoup(open("filtered.html"), 'html.parser')
object = soup.find(id="mw-content-text")
items = object.find_all('li')

for record in items:
    row = record.find('a')
    poet = {}
    poet['href'] = 'https://en.wikipedia.org' + row['href']
    poet['name'] = row.text
    poet["born"] = 0
    poet["died"] = 0
    poet['info'] = record.text
    poet['birthplace'] = ''
    poet['deathplace'] = ''
    poet['birth_lon'] = 0
    poet['birth_lat'] = 0
    poet['death_lon'] = 0
    poet['death_lat'] = 0
    poets.append(poet)

with open("./world-poets-g.json", 'w') as outfile:
    json.dump(poets, outfile)

# -----------------------------------------------------------------------------------------
# Get dates of birth/death with regular expressions

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
# Trim info/comment string

pattern = "\), (\D+)"

for poet in poets:
    data = poet['info']
    try:
        info = re.search(pattern, data).group(1)
        if info:
            poet["info"] = info
    except:
        poet["info"] = ""

with open("./world-poets-g.json", 'w') as outfile:
    json.dump(poets, outfile, indent=2)


# ---------------------------------------------------------------------------
# Get birthplace and deathplace from poet wikipage infobox

for poet in poets:
    page = requests.get(poet['href'])
    soup = BeautifulSoup(page.text, 'html.parser')

    try:
        first_div = soup.find('div', {'class': 'birthplace'})
        first_a = first_div.find('a')
        birthplace = first_a['title']

        poet['birthplace'] = birthplace
        print('birthplace: ', birthplace)
    except:
        pass

    try:
        first_div = soup.find('div', {'class': 'deathplace'})
        first_a = first_div.find('a')
        deathplace = first_a['title']

        poet['deathplace'] = deathplace
        print("deathplace: ", deathplace)
    except:
        pass

with open("./world-poets-g.json", 'w') as outfile:
    json.dump(poets, outfile, indent=2)

# ---------------------------------------------------------------------------
# Get birthplace and deathplace (old style infobox)

for poet in poets:

    if poet['birthplace'] or poet['deathplace']:
        continue

    page = requests.get(poet['href'])
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

    try:
        fifth_tr = infobox.find_all('tr')[4]
        bod = fifth_tr.find('th').text
        first_a = fifth_tr.find('a')['title']
        if bod == "Died":
            poet['deathplace'] = first_a
            print(poet['name'], bod, first_a)
        else:
            pass
    except:
        pass

with open("./world-poets-g.json", 'w') as outfile:
    json.dump(poets, outfile, indent=2)

# ----------------------------------------------------------------------------
# Geocode places of birth/death

for poet in poets:
    if poet['birthplace'] != '':
        try:
            df = geocode(poet['birthplace'], provider="nominatim",
                         user_agent="poetsgis", timeout=10)
            poet['birth_lon'] = round(df['geometry'][0].x, 5)
            poet['birth_lat'] = round(df['geometry'][0].y, 5)
            print(poet['name'], poet["birth_lon"], ", ", poet["birth_lat"])
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
