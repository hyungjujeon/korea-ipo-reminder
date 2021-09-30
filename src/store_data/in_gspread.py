from datetime import datetime
from time import sleep
import gspread
import src.column_description as cd
from oauth2client.service_account import ServiceAccountCredentials
import src.crawler.from_ipostock as crawler_ipostock

def get_google_spreadsheet(sheet_name):
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]
    json_file_name = '../json/gspread_key.json'
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/19tH_v5zOzfuJVCxeOT3z7i2rQKJh6NqpxKVSmcs_HMQ/edit#gid=0'

    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
    gc = gspread.authorize(credentials)

    doc = gc.open_by_url(spreadsheet_url)
    worksheet = doc.worksheet(sheet_name)

    return worksheet

def convert_data_format(row_data):
    weekdays = {0: ' (월)', 1: ' (화)', 2: ' (수)', 3: ' (목)', 4: ' (금)', 5: ' (토)', 6: ' (일)'}
    row_data[cd.BidData.BIDDING_START] += weekdays[
        datetime.strptime(row_data[cd.BidData.BIDDING_START], "%Y.%m.%d").weekday()]
    row_data[cd.BidData.BIDDING_FINISH] += weekdays[
        datetime.strptime(row_data[cd.BidData.BIDDING_FINISH], "%Y.%m.%d").weekday()]
    row_data[cd.BidData.REFUND_DATE] += weekdays[
        datetime.strptime(row_data[cd.BidData.REFUND_DATE], "%Y.%m.%d").weekday()]
    row_data[cd.BidData.IPO_DATE] += weekdays[datetime.strptime(row_data[cd.BidData.IPO_DATE], "%Y.%m.%d").weekday()]

    row_data[cd.BidData.UNDERWRITER] = ', '.join(row_data[cd.BidData.UNDERWRITER])
    row_data[cd.BidData.ALLOCATED_SHARE_NUM] = ', '.join(map(str, row_data[cd.BidData.ALLOCATED_SHARE_NUM]))
    if row_data[cd.BidData.COMPETITION_RATIO] == 0:
        row_data[cd.BidData.COMPETITION_RATIO] = '미표기'
    if row_data[cd.BidData.COMMITMENT_RATIO] == 0:
        row_data[cd.BidData.COMMITMENT_RATIO] = '미표기'

    return row_data

def write_on_spreadsheet(spreadsheet, ipo_data_list):
    for ipo_data in ipo_data_list:
        ipo_data = convert_data_format(ipo_data)
        spreadsheet.append_row(ipo_data)

def write_on_spreadsheet_per_month(year, start, end):
    for i in range(start, end+1):
        url_list = crawler_ipostock.get_month_ipo_urls_list(year, i)
        ipo_data_list = []
        for url in url_list:
            ipo_data = crawler_ipostock.crawl_ipo_info(url)
            if ipo_data:
                ipo_data_list.append(ipo_data)

        ipo_spreadsheet = get_google_spreadsheet('전체정보')
        write_on_spreadsheet(ipo_spreadsheet, ipo_data_list)
        print('API Write Request 제한을 위해, 40초 휴식합니다.')
        sleep(40)

#write_on_spreadsheet_per_month('2021', 9, 9)