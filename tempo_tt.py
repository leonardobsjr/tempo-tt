""" Tool to migrate tempo records to new timetracker """
from http import HTTPStatus
from typing import Dict, List
import json
from fake_useragent import UserAgent
import requests
import sys

TEMPO_LOGIN = '########'
TEMPO_PASSWORD = '#########'
TEMPO_API = 'https://#########/rest/tempo-timesheets/4/worklogs/search'
TEMPO_STARTING_DATE = '2023-05-01'
TEMPO_END_DATE = '2023-05-14'
TEMPO_USER = 'JIRAUSER53826'

TT_AUTH_TOKEN = '#########' # pylint: disable=line-too-long
TT_API_UPSERT = 'https://employees.bairesdev.com/api/v1/employees/timetracker-record-upsert'

TT_DATA_TEMPLATE = {
    "projectId": 1251, #SiriusXM - David Barker
    "date": None,
    "hours": None,
    "focalPointId": 18120, #Jose de Castro
    "descriptionId": 798, #Support
    "recordTypeId": 1, #Regular Hours
    "comments": "123123",
    "employeeId": None
}

TT_HOLIDAY_TEMPLATE = {
   "projectId":1251,
   "date":"2022-11-02T00:00:00.000Z",
   "hours":8,
   "focalPointId":18120, #Jose de Castro
   "descriptionId":749, #Holiday
   "recordTypeId":1,
   "employeeId": None
}

TT_PTO_TEMPLATE = {
    "projectId":1251,
    "date":"2023-03-27T00:00:00.000Z",
    "hours":8,
    "focalPointId":18120, #Jose de Castro
    "descriptionId":751, #Vacations
    "recordTypeId":1,
    "comments":"TEMPO-1",
    "employeeId": None
}

USER_AGENT = UserAgent().random
TT_HEADERS = {
    'authorization': f"{TT_AUTH_TOKEN}",
    'Content-type': 'application/json',
    'User-Agent': USER_AGENT
}

def get_tempo_records() -> Dict:
    """ Get records from SXM Tempo """
    tempo_query = {"from": TEMPO_STARTING_DATE, "to": TEMPO_END_DATE, "worker": [TEMPO_USER]}
    print(tempo_query)
    response = requests.post(TEMPO_API, auth=(TEMPO_LOGIN, TEMPO_PASSWORD),
        json=tempo_query, timeout=60)
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        print('Check Tempo password!')
        sys.exit(1)
    elif response.status_code == HTTPStatus.OK:
        tempo_entries = response.json()
    else:
        print(response.content)
    print(f'Number of tempo records found: {len(tempo_entries)}')
    return tempo_entries

def create_tt_records(sxm_tempo_records : List):
    """ Migrate SXM Tempo records to BDev new TT """
    for record in sxm_tempo_records:
        tt_record = TT_DATA_TEMPLATE.copy()
        if record['issue']['key'] == 'TEMPO-1': #PTO/Holiday
            isholiday = record['comment'].lower().strip() == 'holiday'
            if isholiday:
                print(f'TEMPO-1 on {date} is a holiday.')
                tt_record = TT_HOLIDAY_TEMPLATE.copy()
            else:
                tt_record = TT_PTO_TEMPLATE.copy()
        tt_record['date'] = record['started']
        tt_record['hours'] = record['timeSpentSeconds']/3600
        tt_record['comments'] = record['issue']['key']
        date = tt_record['date'].split(' ')[0]
        #print(tt_record)
        response = requests.put(TT_API_UPSERT, headers=TT_HEADERS,
            data=json.dumps(tt_record), timeout=60)
        if response.status_code == HTTPStatus.OK:
            print(f"{date} - {tt_record['hours']}hrs record for ticket "
                  f"{tt_record['comments']} created successfully.")
        else:
            print(f"{date} - Issue adding record for ticket { tt_record['comments'] }:")
            print(f'Response code: {response.status_code}')
            print(f'Response content: {response.content}')

tempo_records = get_tempo_records()
#print(tempo_records)
create_tt_records(tempo_records)
