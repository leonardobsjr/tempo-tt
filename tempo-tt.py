""" Tool to migrate tempo records to new timetracker """
from http import HTTPStatus
from typing import Dict, List
import json
from fake_useragent import UserAgent
import requests

TEMPO_LOGIN = '########'
TEMPO_PASSWORD = '#######'
TEMPO_API = 'https://#########/rest/tempo-timesheets/4/worklogs/search'
TEMPO_STARTING_DATE = '2022-08-02'
TEMPO_END_DATE = '2022-08-02'
TEMPO_USER = '##########'

TT_AUTH_TOKEN = '###########' # pylint: disable=line-too-long
TT_API_UPSERT = 'https://employees.bairesdev.com/api/v1/employees/timetracker-record-upsert'
TT_DATA_TEMPLATE = {
    "projectId": 1251, #SiriusXM - David Barker
    "date": None,
    "hours": None,
    "focalPointId": 14651, #Jose Lopez
    "descriptionId": 798, #Support
    "recordTypeId": 1, #Regular Hours
    "comments": "123123",
    "employeeId": None
}

USER_AGENT = UserAgent().random
TT_HEADERS = {
    'authorization': f"Bearer {TT_AUTH_TOKEN}",
    'Content-type': 'application/json',
    'User-Agent': USER_AGENT
}

def get_tempo_records() -> Dict:
    """ Get records from SXM Tempo """
    tempo_query = {"from": TEMPO_STARTING_DATE, "to": TEMPO_END_DATE, "worker": [TEMPO_USER]}
    print(tempo_query)
    response = requests.post(TEMPO_API, auth=(TEMPO_LOGIN, TEMPO_PASSWORD), json=tempo_query)
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        print('Check password!')
    elif response.status_code == HTTPStatus.OK:
        tempo_entries = response.json()
    return tempo_entries

def create_tt_records(sxm_tempo_records : List):
    """ Migrate SXM Tempo records to BDev new TT """
    for record in sxm_tempo_records:
        tt_record = TT_DATA_TEMPLATE.copy()
        tt_record['date'] = record['started']
        tt_record['hours'] = record['timeSpentSeconds']/3600
        tt_record['comments'] = record['issue']['key']
        date = tt_record['date'].split(' ')[0]
        if record['issue']['key'] == 'PTM-3': #Holiday
            print(f"Skipping { tt_record['hours'] }h on { date }. Motive: Holiday (PTM-3).")
            continue
        response = requests.put(TT_API_UPSERT, headers=TT_HEADERS, data=json.dumps(tt_record))
        if response.status_code == HTTPStatus.OK:
            print(f"{date} - {tt_record['hours']}hrs record for ticket "
                  f"{tt_record['comments']} created successfully.")
        else:
            print(f"{date} - Issue addind record for ticket { tt_record['comments'] }")
            print(response.status_code)
            print(response.content)

tempo_records = get_tempo_records()
create_tt_records(tempo_records)
