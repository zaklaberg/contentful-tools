import json
import contentful
import os
from urllib.request import urlopen, Request
from dotenv import load_dotenv
import csv

env_vars = load_dotenv()

CONTENTFUL_SPACE_ID = os.getenv('CONTENTFUL_SPACE_ID')
CONTENTFUL_CDN_KEY = os.getenv('CONTENTFUL_CDN_KEY_GLOBAL_PREVIEW')
CONTENTFUL_ENVIRONMENT = os.getenv('CONTENTFUL_ENVIRONMENT')

client = contentful.Client(
    CONTENTFUL_SPACE_ID, CONTENTFUL_CDN_KEY, 'preview.contentful.com')
cf_voyages = client.entries({
    'content_type': 'voyage',
    'locale': 'en-GB',
    'select': 'sys.id,fields.slug,fields.bookable,fields.isPastOrCancelled,fields.destination',
    'include': 1,
    'limit': 500
}).items

cf_excursions = client.entries({
    'content_type': 'excursion',
    'locale': 'en-GB',
    'select': 'sys.id,fields.slug',
    'limit': 500
}).items

cf_programs = client.entries({
    'content_type': 'program',
    'locale': 'en-GB',
    'select': 'sys.id,fields.slug',
    'limit': 500
}).items

cf_activities = cf_excursions + cf_programs


def nellie_activity_url(id):
    for v in cf_activities:
        if (str(v.id) == str(id)):
            return 'https://www.hurtigruten.com/en-gb/expeditions/enhance-your-cruise/catalog/' + v.slug + '/'
    return 'https://www.hurtigruten.com/en-gb/expeditions/enhance-your-cruise/catalog/'


def nellie_voyage_url(id):
    for v in cf_voyages:
        if (str(v.id) == str(id)):
            if (v.fields('en-GB').get("bookable") and not v.fields('en-GB').get("isPastOrCancelled")):
                return 'https://www.hurtigruten.com/en-gb/expeditions/cruises/' + v.slug + '/'
            return 'https://www.hurtigruten.com/en-gb/expeditions/destinations/' + v.fields('en-GB').get('destination')[0].fields('en-GB').get('slug') + '/'
    return ''


voyage_base_url_epi = 'https://www.hurtigruten.co.uk/rest/b2b/voyages'
excursion_base_url_epi = 'https://www.hurtigruten.co.uk/rest/b2b/excursions'
program_base_url_epi = 'https://www.hurtigruten.co.uk/rest/b2b/programs'
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'User-Agent': 'ZBrowser'
}

req = Request(voyage_base_url_epi, headers=headers)
res = urlopen(req).read()
epi_voyages_raw = json.loads(res.decode('utf-8'))

req = Request(excursion_base_url_epi, headers=headers)
res = urlopen(req).read()
epi_excursions_raw = json.loads(res.decode('utf-8'))

req = Request(program_base_url_epi, headers=headers)
res = urlopen(req).read()
epi_programs_raw = json.loads(res.decode('utf-8'))

epi_voyages = {}
epi_excursions = {}
epi_programs = {}

for e in epi_voyages_raw:
    epi_voyages[e["url"]] = e["id"]
for e in epi_excursions_raw:
    epi_excursions[e["url"]] = e["id"]
for e in epi_programs_raw:
    epi_programs[e["url"]] = e["id"]


with open('epi-urls-v2.csv', 'r', encoding='UTF8', newline='') as f:
    reader = csv.reader(f, delimiter=',')
    header = next(reader)
    header.append('Nellie URL')

    rows = []
    for row in reader:

        row_vid = epi_voyages.get(row[0])
        row_eid = epi_excursions.get(row[0])
        row_pid = epi_programs.get(row[0])

        if (row_vid):
            row.append(nellie_voyage_url(row_vid))
        elif (row_eid):
            row.append(nellie_activity_url(row_eid))
        elif (row_pid):
            row.append(nellie_activity_url(row_pid))
        else:
            row.append('')
        rows.append(row)

with open('epi-urls-w-nellie.csv', 'w', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)
