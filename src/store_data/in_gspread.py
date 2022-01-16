import os
import gspread
import platform
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials


class GoogleSpreadSheet:
    def __init__(self):
        self.spreadsheet_id = '19tH_v5zOzfuJVCxeOT3z7i2rQKJh6NqpxKVSmcs_HMQ'
        self.spreadsheet_url = 'https://docs.google.com/spreadsheets/d/' + self.spreadsheet_id + '/edit#gid=0'
        self.spreadsheet = None
        self.worksheet = None
        self.set_spreadsheet()
        self.set_worksheet_by_sheet_name('전체정보')

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
            json_file_name = '../json/gspread_key.json'
            credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
            gc = gspread.authorize(credentials)

        spreadsheet = gc.open_by_url(self.spreadsheet_url)
        self.spreadsheet = spreadsheet

    def set_worksheet_by_sheet_name(self, sheet_name):
        self.worksheet = self.spreadsheet.worksheet(sheet_name)

    def convert_before_ipo_data_format(self, ipo_data):
        converted_data_list = [ipo_data.company_name]

        weekdays = {0: ' (월)', 1: ' (화)', 2: ' (수)', 3: ' (목)', 4: ' (금)', 5: ' (토)', 6: ' (일)'}

        bidding_start = ipo_data.bidding_start + weekdays[datetime.strptime(ipo_data.bidding_start, "%Y.%m.%d").weekday()]
        bidding_finish = ipo_data.bidding_finish + weekdays[datetime.strptime(ipo_data.bidding_finish, "%Y.%m.%d").weekday()]
        refund = ipo_data.refund + weekdays[datetime.strptime(ipo_data.refund, "%Y.%m.%d").weekday()]
        go_public = ipo_data.go_public + weekdays[datetime.strptime(ipo_data.go_public, "%Y.%m.%d").weekday()]
        competition_ratio = (ipo_data.competition_ratio if ipo_data.competition_ratio != 0 else '미표기')
        commitment_ratio = (ipo_data.commitment_ratio if ipo_data.commitment_ratio != 0 else '미표기')

        converted_data_list.append(bidding_start)
        converted_data_list.append(bidding_finish)
        converted_data_list.append(refund)
        converted_data_list.append(go_public)
        converted_data_list.append(int(ipo_data.band_price_low))
        converted_data_list.append(int(ipo_data.band_price_high))
        converted_data_list.append(int(ipo_data.offering_price))
        converted_data_list.append(int(ipo_data.offering_amount))
        converted_data_list.append(int(ipo_data.total_num_of_new_stocks))
        converted_data_list.append(int(ipo_data.total_num_of_stock_after_ipo))
        converted_data_list.append(int(ipo_data.num_of_stock_sale_available))
        converted_data_list.append(float(ipo_data.ratio_of_sale_available))
        converted_data_list.append(int(ipo_data.num_of_stock_lockup))
        converted_data_list.append(float(ipo_data.ratio_of_lockup))
        converted_data_list.append(ipo_data.underwriter)
        converted_data_list.append(ipo_data.num_of_stock_allocated)
        converted_data_list.append(competition_ratio)
        converted_data_list.append(commitment_ratio)

        return converted_data_list

    def convert_after_ipo_data_format(self, row_values, offering_price):
        finish_price = int(row_values[1].replace(',', ''))
        finish_ratio = float((finish_price - offering_price) / offering_price)
        start_price = int(row_values[3].replace(',', ''))
        start_ratio = float((start_price - offering_price) / offering_price)
        low_price = int(row_values[5].replace(',', ''))
        low_ratio = float((low_price - offering_price) / offering_price)
        high_price = int(row_values[4].replace(',', ''))
        high_ratio = float((high_price - offering_price) / offering_price)
        trading_volume = int(row_values[6].replace(',', ''))

        converted_data_list = [finish_price, finish_ratio, start_price, start_ratio, low_price, low_ratio]
        converted_data_list += [high_price, high_ratio, trading_volume]

        return converted_data_list

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

    def append_row_before_ipo(self, ipo_data_list):
        for ipo_data in ipo_data_list:
            row_data = self.convert_before_ipo_data_format(ipo_data)
            self.worksheet.append_row(row_data)

    def update_before_ipo(self, ipo_data):
        company_data_row = self.worksheet.find(ipo_data.company_name).row
        data = self.convert_before_ipo_data_format(ipo_data)
        self.worksheet.update('A' + str(company_data_row), [data])

    def update_after_ipo(self, company_name, tr_list):
        company_data_row = self.worksheet.find(company_name).row
        offering_price = int(self.worksheet.cell(company_data_row, 8).value)

        for j in range(-1, -len(tr_list) - 1, -1):
            if not str.isspace(tr_list[j]):
                row_values = tr_list[j].split(' ')
                update_list = self.convert_after_ipo_data_format(row_values, offering_price)

                self.worksheet.update('T' + str(company_data_row), [update_list])
                break
