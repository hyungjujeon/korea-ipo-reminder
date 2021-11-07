from datetime import datetime
from time import sleep
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from src.crawler.ipo_crawler import CrawlerIpoStock

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

def convert_data_format(ipo_data):
    row_data = [ipo_data.company_name]

    weekdays = {0: ' (월)', 1: ' (화)', 2: ' (수)', 3: ' (목)', 4: ' (금)', 5: ' (토)', 6: ' (일)'}

    bidding_start = weekdays[datetime.strptime(ipo_data.bidding_start, "%Y.%m.%d").weekday()]
    bidding_finish = weekdays[datetime.strptime(ipo_data.bidding_finish, "%Y.%m.%d").weekday()]
    refund = weekdays[datetime.strptime(ipo_data.refund, "%Y.%m.%d").weekday()]
    go_public = weekdays[datetime.strptime(ipo_data.go_public, "%Y.%m.%d").weekday()]
    competition_ratio = (ipo_data.competition_ratio if ipo_data.competition_ratio != 0 else '미표기')
    commitment_ratio = (ipo_data.commitment_ratio if ipo_data.commitment_ratio != 0 else '미표기')

    row_data.append(bidding_start)
    row_data.append(bidding_finish)
    row_data.append(refund)
    row_data.append(go_public)
    row_data.append(ipo_data.band_price_low)
    row_data.append(ipo_data.band_price_high)
    row_data.append(ipo_data.offering_price)
    row_data.append(ipo_data.offering_amount)
    row_data.append(ipo_data.total_num_of_new_stocks)
    row_data.append(ipo_data.ratio_of_new_stocks)
    row_data.append(ipo_data.total_num_of_stock_after_ipo)
    row_data.append(ipo_data.num_of_stock_sale_available)
    row_data.append(ipo_data.ratio_of_sale_available)
    row_data.append(ipo_data.num_of_stock_lockup)
    row_data.append(ipo_data.ratio_of_lockup)
    row_data.append(ipo_data.underwriter)
    row_data.append(ipo_data.num_of_stock_allocated)
    row_data.append(competition_ratio)
    row_data.append(commitment_ratio)

    return row_data

def write_on_spreadsheet(spreadsheet, ipo_data_list):
    for ipo_data in ipo_data_list:
        row_data = convert_data_format(ipo_data)
        spreadsheet.append_row(row_data)

def write_on_spreadsheet_per_month(year, start, end):
    for month in range(start, end+1):
        crawler = CrawlerIpoStock()
        ipo_url_list = crawler.get_monthly_ipo_url_list(year, month)

        ipo_data_list = []
        for url in ipo_url_list:
            if url:
                ipo_data = crawler.crawl_ipo_url(url)
                ipo_data_list.append(ipo_data)

        ipo_spreadsheet = get_google_spreadsheet('전체정보')
        write_on_spreadsheet(ipo_spreadsheet, ipo_data_list)
        print('Considering the api write request limit, sleep for 40 seconds')
        sleep(40)