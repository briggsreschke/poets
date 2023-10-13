# Slacker Design feature.frame@github.com
import requests
import csv
import json
from bs4 import BeautifulSoup
from geopandas.tools import geocode

# -----------------------------------------------------------------------
# Scrape wiki pages and populate array of dicts containng poet data

url1 = "https://en.wikipedia.org/wiki/List_of_poets_from_the_United_States"
poets = []
poets_dates = []

page = requests.get(url1)
soup = BeautifulSoup(page.content, 'html.parser')
object = soup.find(id="mw-content-text")
divs = object.find_all(class_="div-col")

for tags in divs:

    # -------------------------------------------------------------------
    # get basic info (href to poet page and poet name)

    data = tags.findAll('a')
    for row in data:
        poet = {}
        poet['href'] = 'https://en.wikipedia.org' + row['href']
    
        poet['name'] = row['title']
        if poet['name'][0].isnumeric():
            continue
        print(poet)
        poets.append(poet)

    # --------------------------------------------------------------------
    # parse out years of birth and death

    for row in tags.findAll('li'):
        poet = {}
        poet['name'] = row.find('a')['title']

        years = row.text
        years = years[years.find("(")+1:years.find(")")]
        
        try:
            foo = years.split("–")
            poet['born'] = foo[0]
            poet['died'] = foo[1]
        except:
            pass
  
        try:               
            foo = years.split(" ")
            if foo[0] == "born":
                poet['born'] = foo[1]
                poet['died'] = ""   
        except:
            pass

        poets_dates.append(poet)

# ---------------------------------------------------------------------------
# mashup dates with poet data

npoets = len(poets)
i = 0
while (i < npoets):
    born = poets_dates[i]['born']
    try:
        died = poets_dates[i]['died']
    except:
        died = ""

    poets[i]['born'] = born
    poets[i]['died'] = died

    i += 1

with open("poets.json", "w") as ofile:
    json.dump(poets, ofile)


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

with open("poets.json", 'w') as outfile:
    json.dump(poets, outfile)


# --------------------------------------------------------------------------
# Get birth/death places from old style? infobox (<table>)

with open("poets.json") as infile:
    poets = json.load(infile)

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

        print(poet['name'], " ", bod, first_a)
        if bod == "Born":
            poet['birthplace'] = first_a
        elif bod == "Died":
            poet['deathplace'] = first_a
        else:
            pass
    except:
        pass

with open("poets.json.tmp", 'w') as outfile:
    json.dump(poets, outfile)

# ----------------------------------------------------------------------------
# Geocode data (lon/lat of birthplace and deathplace)

f = open("poets.json")
data = json.load(f)

for poet in data:
    if poet['birthplace'] != '':
        try:
            df = geocode(poet['birthplace'], provider="nominatim",
                         user_agent="poetsgis", timeout=10)
            poet['birth_lon'] = df['geometry'][0].x
            poet['birth_lat'] = df['geometry'][0].y
        except:
            continue
    else:
        poet['birth_lon'] = 0
        poet['birth_lat'] = 0

    if poet['deathplace'] != '':
        try:
            df = geocode(poet['deathplace'], provider="nominatim",
                         user_agent="poetsgis", timeout=10)
            poet['death_lon'] = df['geometry'][0].x
            poet['death_lat'] = df['geometry'][0].y
        except:
            continue
    else:
        poet['death_lon'] = 0
        poet['death_lat'] = 0

with open("poets.json.tmp", "w") as ofile:
    json.dump(data, ofile)

# ----------------------------------------------------------------------------
# Write to CSV

with open("poets.json.tmp") as infile:
    data = json.load(infile)

csv_file = open('poets.csv', 'w', newline='')
csv_writer = csv.writer(csv_file)

count = 0
for poet in data:
    if count == 0:
        header = poet.keys()
        csv_writer.writerow(header)
        count += 1
    csv_writer.writerow(poet.values())

csv_file.close()
