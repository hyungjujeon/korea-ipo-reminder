import re
import os
import gspread
import platform
from time import sleep
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from src.crawler.ipo_crawler import CrawlerIpoStock, IpoData
from oauth2client.service_account import ServiceAccountCredentials


class GoogleSpreadSheet:
    def __init__(self):
        self.spreadsheet_id = '19tH_v5zOzfuJVCxeOT3z7i2rQKJh6NqpxKVSmcs_HMQ'
        self.spreadsheet_url = 'https://docs.google.com/spreadsheets/d/' + self.spreadsheet_id + '/edit#gid=0'
        self.spreadsheet = None
        self.worksheet = None
        self.set_spreadsheet()
        self.set_worksheet_by_sheet_name('전체정보')

    # ref : https://docs.gspread.org/en/latest/oauth2.html
    def set_spreadsheet(self):
        if platform.system() == 'Linux':
            credentials = {
                "type": "service_account",
                "project_id": os.environ.get('GSPREAD_PROJECT_ID'),
                "private_key_id": os.environ.get('GSPREAD_PRIVATE_KEY_ID'),
                "private_key": os.environ.get('GSPREAD_PRIVATE_KEY'),
                "client_email": os.environ.get('GSPREAD_CLIENT_EMAIL'),
                "client_id": os.environ.get('GSPREAD_CLIENT_ID'),
                "auth_uri": os.environ.get('GSPREAD_AUTH_URI'),
                "token_uri": os.environ.get('GSPREAD_TOKEN_URI'),
                "auth_provider_x509_cert_url": os.environ.get('GSPREAD_AUTH_PROVIDER'),
                "client_x509_cert_url": os.environ.get('GSPREAD_CLIENT_CERT_URL')
            }
            gc = gspread.service_account_from_dict(credentials)
        else:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive',
            ]
            json_file_name = 'json/gspread_key.json'
            credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
            gc = gspread.authorize(credentials)

        spreadsheet = gc.open_by_url(self.spreadsheet_url)
        self.spreadsheet = spreadsheet

    def set_worksheet_by_sheet_name(self, sheet_name):
        self.worksheet = self.spreadsheet.worksheet(sheet_name)

    def convert_data_format(self, ipo_data: IpoData):
        row_data = [ipo_data.company_name]

        weekdays = {0: ' (월)', 1: ' (화)', 2: ' (수)', 3: ' (목)', 4: ' (금)', 5: ' (토)', 6: ' (일)'}

        bidding_start = ipo_data.bidding_start + weekdays[datetime.strptime(ipo_data.bidding_start, "%Y.%m.%d").weekday()]
        bidding_finish = ipo_data.bidding_finish + weekdays[datetime.strptime(ipo_data.bidding_finish, "%Y.%m.%d").weekday()]
        refund = ipo_data.refund + weekdays[datetime.strptime(ipo_data.refund, "%Y.%m.%d").weekday()]
        go_public = ipo_data.go_public + weekdays[datetime.strptime(ipo_data.go_public, "%Y.%m.%d").weekday()]
        competition_ratio = (ipo_data.competition_ratio if ipo_data.competition_ratio != 0 else '미표기')
        commitment_ratio = (ipo_data.commitment_ratio if ipo_data.commitment_ratio != 0 else '미표기')

        row_data.append(bidding_start)
        row_data.append(bidding_finish)
        row_data.append(refund)
        row_data.append(go_public)
        row_data.append(int(ipo_data.band_price_low))
        row_data.append(int(ipo_data.band_price_high))
        row_data.append(int(ipo_data.offering_price))
        row_data.append(int(ipo_data.offering_amount))
        row_data.append(int(ipo_data.total_num_of_new_stocks))
        row_data.append(int(ipo_data.total_num_of_stock_after_ipo))
        row_data.append(int(ipo_data.num_of_stock_sale_available))
        row_data.append(float(ipo_data.ratio_of_sale_available))
        row_data.append(int(ipo_data.num_of_stock_lockup))
        row_data.append(float(ipo_data.ratio_of_lockup))
        row_data.append(ipo_data.underwriter)
        row_data.append(ipo_data.num_of_stock_allocated)
        row_data.append(competition_ratio)
        row_data.append(commitment_ratio)

        return row_data

    def write_on_spreadsheet(self, ipo_data_list):
        for ipo_data in ipo_data_list:
            row_data = self.convert_data_format(ipo_data)
            self.worksheet.append_row(row_data)

    def create_worksheet(self, new_sheet_name, row_count: int, col_count: int):
        self.spreadsheet.add_worksheet(title=new_sheet_name, rows=str(row_count), cols=str(col_count))

    def delete_worksheet(self, worksheet: gspread.Worksheet):
        self.spreadsheet.del_worksheet(worksheet)

    def get_cell_value(self, row, col):
        value = self.worksheet.cell(row, col).value
        return value

    def get_cell_formula(self, row, col):
        cell = self.worksheet.cell(row, col, value_render_option='FORMULA').value
        return cell

    def get_all_values_from_row(self, row):
        row_values_list = self.worksheet.row_values(row)
        return row_values_list

    def get_all_values_from_col(self, col):
        col_values_list = self.worksheet.col_values(col)
        return col_values_list

    def get_all_values_from_worksheet(self):
        return self.worksheet.get_all_values()

    def find_cell_by_string(self, match_string: str):
        cell = self.worksheet.find(match_string)
        return cell

    def find_all_matched_cells(self, match_string: str):
        cell_list = self.worksheet.findall(match_string)
        return cell_list

    def update_cell(self, row: int, col: int, value):
        self.worksheet.update_cell(row, col, value)

    def update_after_ipo(self, company_name):
        cell = self.worksheet.find(company_name)
        company_data_row = cell.row

        offering_price = self.worksheet.cell(company_data_row, 8).value
        driver = webdriver.Chrome('../chromedriver.exe')
        default_url = 'https://finance.naver.com/'
        try:
            driver.get(default_url)
            driver.implicitly_wait(20)
            driver.find_element_by_class_name('snb_search_text').send_keys(company_name)
            driver.implicitly_wait(20)
            driver.find_element_by_class_name('snb_search_btn').click()
            sleep(3)
            company_code = re.compile(r"\S+\?code=").sub('', driver.current_url)
            page_to_crawl = 'https://finance.naver.com/item/sise_day.naver?code=' + str(company_code)

            driver.get(page_to_crawl)
            sleep(3)
            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            table = soup.find('table', {'summary': '페이지 네비게이션 리스트'})
            page = table.find_all('td')
            last_page_url = default_url + page[-1].find('a').get('href')

            driver.get(last_page_url)
            sleep(3)
            new_html = driver.page_source
            new_table = driver.find_element_by_class_name('type2')
            tr_list = new_table.text.split('\n')

            for j in range(-1, -len(tr_list) - 1, -1):
                if not str.isspace(tr_list[j]):
                    row_values = tr_list[j].split(' ')
                    finish_price = int(row_values[1].replace(',', ''))
                    finish_ratio = float((finish_price - offering_price) / offering_price)
                    start_price = int(row_values[3].replace(',', ''))
                    start_ratio = float((start_price - offering_price) / offering_price)
                    low_price = int(row_values[5].replace(',', ''))
                    low_ratio = float((low_price - offering_price) / offering_price)
                    high_price = int(row_values[4].replace(',', ''))
                    high_ratio = float((high_price - offering_price) / offering_price)
                    trading_volume = int(row_values[6].replace(',', ''))

                    update_list = [finish_price, finish_ratio, start_price, start_ratio, low_price, low_ratio]
                    update_list += [high_price, high_ratio, trading_volume]

                    self.worksheet.update('Z' + company_data_row, [update_list])
                    sleep(3)
                    break
        except Exception as e:
            print(company_name + ": 오류 발생, " + str(e))
            pass

    def update_monthly_after_ipo(self, year, month):
        crawler = CrawlerIpoStock()
        url_lists = crawler.get_monthly_ipo_url_list(year, month)

        data_lists = []
        for url in url_lists:
            if url:
                ipo_data = crawler.crawl_ipo_url(url)
                if ipo_data:
                    ipo_data.ref_url_ipo_stock = url
                    try:
                        data = self.convert_data_format(ipo_data)
                        data_lists.append(data)
                    except:
                        pass

        self.worksheet.add_rows(len(data_lists))
        self.worksheet.update('A' + str(self.worksheet.row_count + 1), data_lists)
