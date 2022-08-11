import asyncio
import datetime
import json
import os.path
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import traceback
from config import SLEEP_TIME


class GoogleSheet:
    SPREADSHEET_ID = '1wOg0wUyBIQRVjLEbCr6BsaZBGlFxUTt7EmrJiBkjCtY'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    service = None

    def __init__(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print('flow')
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('sheets', 'v4', credentials=creds)

    def updateRangeValues(self, range, values):
        data = [{
            'range': range,
            'values': values
        }]
        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': data
        }
        result = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.SPREADSHEET_ID,
                                                                  body=body).execute()
        print('{0} cells updated.'.format(result.get('totalUpdatedCells')))


async def update_sheets():
    while True:
        print('Sheets start update at ', datetime.datetime.now().strftime('%H:%M:%S'))
        gs = GoogleSheet()

        try:
            with open('huobi.json', 'r') as huobi_file, open('binance.json', 'r') as binance_file:
                huobi_data = json.load(huobi_file)

                s = huobi_data
                rsh = 'Лист1!B51:G56'
                vsh = [
                    [1, '=1/B52', '=1/B53', '=1/B54', s['usdtrub'], '=1/B56'],
                    [s['btcusdt'], 1, '-', '=1/C54', s['btcrub'], '-'],
                    [s['bnbusdt'], '-', 1, '-', '-', '-'],
                    [s['ethusdt'], s['ethbtc'], '-', 1, '-', '-'],
                    ['=1/F51', '=1/F52', '-', '-', 1, '-'],
                    [s['shibusdt'], '-', '-', '-', '-', 1],
                ]

                binance_data = json.load(binance_file)
                s = binance_data
                rsb = 'Лист1!B29:H35'
                vsb = [
                    [1, '=1/B30', '-', '-', '=1/B33', s['USDTRUB'], '=1/B35'],
                    [s['BTCUSDT'], 1, s['BTCBUSD'], '=1/C32', '=1/C33', s['BTCRUB'], '-'],
                    ['-', '=1/D30', 1, '=1/D32', '=1/D33', s['BUSDRUB'], '=1/D35'],
                    ['-', s['BNBBTC'], s['BNBBUSD'], 1, s['BNBETH'], s['BNBRUB'], '-'],
                    [s['ETHUSDT'], s['ETHBTC'], s['ETHBUSD'], '=1/F32', 1, s['ETHRUB'], '-'],
                    ['=1/G29', '=1/G30', '=1/G31', '=1/G32', '=1/G33', 1, '-'],
                    [s['SHIBUSDT'], '-', s['SHIBBUSD'], '-', '-', '-', 1],
                ]

                gs.updateRangeValues(rsh, vsh)
                gs.updateRangeValues(rsb, vsb)

        except Exception:
            traceback.print_exc()

        print('Sheets end update at ', datetime.datetime.now().strftime('%H:%M:%S'))
        await asyncio.sleep(SLEEP_TIME+1)

# asyncio.run(update_sheets())
# from google_sheets import GoogleSheet, update_sheets
