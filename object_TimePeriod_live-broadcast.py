#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gspread
import csv
import os.path
import time
import json
import requests

from oauth2client.service_account import ServiceAccountCredentials
from shutil import copyfile
from os import system
from datetime import datetime,timedelta
from sys import exit


# accessing google docs via google API
feeds = ['https://spreadsheets.google.com/feeds']
access = ServiceAccountCredentials.from_json_keyfile_name('Ramowka-59cb424a8c77.json', feeds)
session = gspread.authorize(access)
doc = session.open_by_key('1JpW-bHNQ0TTcVvRNgeCYO7xeiVfvqgvpr83jUDuLi1c')
sheet = doc.get_worksheet(0)

# downloading spreadsheet in CSV format
sheet_csv_raw = sheet.export(format='csv').decode(encoding='UTF-8').replace('\r','')

# parsing CSV into python dictionary
sheet_csv = csv.DictReader(sheet_csv_raw.splitlines(), delimiter=',')

# creating maping of weekdays names from pl to en
week_day = {
    'piątek': "friday",
    'poniedziałek': 'monday',
    'sobota': 'saturday',
    'niedziela': 'sunday',
    'czwartek': 'thursday',
    'wtorek': 'tuesday',
    'środa': 'wednesday'
}

# defining empty dictionary
ranges = {}

# creating ranges of time when we expect to broadcast live
for show in sheet_csv:
    if show['Nagranie'] != 'Tak':
        continue

    show['Godzina rozp.'] = datetime.strptime(show['Godzina rozp.'],'%H:%M:%S')
    show['Godzina zako.'] = show['Godzina rozp.'] + timedelta(minutes=int(show['Czas trwania (min)']))

    if week_day[show['Dzień tygodnia']] in ranges:
        time_format = ',{}-{}'
        previous_times = ranges[week_day[show['Dzień tygodnia']]]
    else:
        time_format = '{}-{}'
        previous_times = ''


    ranges[week_day[show['Dzień tygodnia']]] = previous_times + time_format.format(
            show['Godzina rozp.'].strftime("%H:%M"),
            show['Godzina zako.'].strftime("%H:%M")
    )

# creating TimePeriod definition for icinga
data = {
    "display_name": "live-broadcast",
    "imports": [ "generic-time-period"],
    "object_name": "live-broadcast",
    "object_type": "object",
    "ranges": ranges,
    "update_method": "LegacyTimePeriod"
}

# sending settings to icinga via API
headers = {'Accept': 'application/json'}
target = {'name': 'live-broadcast'}
url = 'http://icinga2.radiouniwersytet.pl/icingaweb2/director'

# uploading new timeperiod
response = requests.put(url+'/timeperiod',headers=headers,params=target,data=json.dumps(data))
print(response.text)

# triggering deploy
response = requests.post(url+'/config/deploy',headers=headers)
print(response.text)
