import re
import time
import platform
import requests
from enum import IntEnum
from datetime import datetime
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
from selenium import webdriver

SPAC_company = {'디비금융': 'DB금융', '아이비케이에스': 'IBKS', '에스케이': 'SK', 'NH': '엔에이치', 'KB': '케이비', '에이치엠씨아이비': '에이치엠씨'}


def convert_SPAC(company_name):
    company_name = company_name.replace('기업인수목적', '').replace('스팩', '')
    spac_num_pattern = re.search('제?([0-9]+호)', company_name)
    spac_num_full = spac_num_pattern.group(0)
    spac_num = spac_num_pattern.group(1)
    spac_underwriter = company_name.replace(spac_num_full, '')

    try:
        spac_underwriter = SPAC_company[spac_underwriter]
    except:
        #그대로 사용
        pass

    spac_name = ''
    if spac_underwriter in ['SK', '교보', '하나금융', '하나머스트', '한국']:
        spac_name = spac_underwriter + spac_num + '스팩'

    elif spac_underwriter in ['IBKS', '대신밸런스', '신한', '에이치엠씨', '유안타', '케이비', '하이', '한화플러스']:
        spac_name = spac_underwriter + '제' + spac_num + '스팩'

    else:
        spac_name = spac_underwriter + '스팩' + spac_num

    return spac_name


def check_bidding_status(date_diff_bidding_start, date_diff_bidding_finish):
    if date_diff_bidding_finish > 0:
        return BiddingStatus.ALREADY_FINISHED
    elif date_diff_bidding_start == -1:
        return BiddingStatus.START_TOMORROW
    elif date_diff_bidding_start == 0:
        return BiddingStatus.START_TODAY
    elif date_diff_bidding_start >= 1:
        if date_diff_bidding_finish == 0:
            return BiddingStatus.FINISH_TODAY
        else:
            return BiddingStatus.PROCEEDING
    else:
        return BiddingStatus.START_MORE_THAN_TWO_DAY_AFTER


def check_ipo_status(date_diff_ipo_start):
    if date_diff_ipo_start > 0:
        return IpoStatus.ALREADY_FINISHED
    elif date_diff_ipo_start == 0:
        return IpoStatus.START_TODAY
    elif date_diff_ipo_start == -1:
        return IpoStatus.START_TOMORROW
    else:
        return IpoStatus.START_MORE_THAN_TWO_DAY_AFTER


class BiddingStatus(IntEnum):
    FINISH_TODAY = 0
    START_TODAY = 1
    START_TOMORROW = 2
    START_MORE_THAN_TWO_DAY_AFTER = 3
    PROCEEDING = 1
    ALREADY_FINISHED = 5


class IpoStatus(IntEnum):
    START_TODAY = 0
    START_TOMORROW = 1
    ALREADY_FINISHED = 2
    START_MORE_THAN_TWO_DAY_AFTER = 3


class IpoDate:
    def __init__(self):
        self.bidding_start = None
        self.bidding_finish = None
        self.refund = None
        self.go_public = None


class IpoPrice:
    def __init__(self):
        self.band_price_low = None
        self.band_price_high = None
        self.offering_price = None
        self.offering_amount = None


class IpoNewStocksInfo:
    def __init__(self):
        self.total_num_of_new_stocks = None
        self.ratio_of_new_stocks = None


class IpoStockConditions:
    def __init__(self):
        self.total_num_of_stock_after_ipo = None
        self.num_of_stock_lockup = None
        self.num_of_stock_sale_available = None
        self.ratio_of_lockup = None
        self.ratio_of_sale_available = None


class IpoUnderwriter:
    def __init__(self):
        self.underwriter = None
        self.num_of_stock_allocated = None


class IpoDemandForecast:
    def __init__(self):
        self.competition_ratio = None
        self.commitment_ratio = None


class IpoBiddingResult:
    def __init__(self):
        self.num_of_equal_allocated_stocks = None
        self.num_of_investors = None
        self.final_competition_ratio = None
        self.final_commitment_ratio = None


class IpoData(IpoDate, IpoPrice, IpoNewStocksInfo, IpoStockConditions, IpoUnderwriter, IpoDemandForecast):
    def __init__(self, company_name):
        self.company_name = company_name
        self.public_offering_page_url = None
        self.stock_holder_page_url = None
        self.demand_forecast_page_url = None
        self.ref_url_ipo_stock = None
        self.ref_url_38com = None
        self.is_from_KONEX = False
        self.market_type = None
        IpoDate.__init__(self)
        IpoPrice.__init__(self)
        IpoNewStocksInfo.__init__(self)
        IpoStockConditions.__init__(self)
        IpoUnderwriter.__init__(self)
        IpoDemandForecast.__init__(self)

    def set_public_offering_page_url(self, url):
        self.public_offering_page_url = url
        self.stock_holder_page_url = self.public_offering_page_url.replace('_04', f'_02')
        self.demand_forecast_page_url = self.public_offering_page_url.replace('_04', f'_05')

    def set_ipo_date(self, ipo_date: IpoDate):
        self.bidding_start = ipo_date.bidding_start
        self.bidding_finish = ipo_date.bidding_finish
        self.refund = ipo_date.refund
        self.go_public = ipo_date.go_public

    def set_ipo_price(self, ipo_price: IpoPrice):
        self.band_price_low = ipo_price.band_price_low
        self.band_price_high = ipo_price.band_price_high
        self.offering_price = ipo_price.offering_price
        self.offering_amount = ipo_price.offering_amount

    def set_ipo_new_stocks_info(self, ipo_new_stocks_info: IpoNewStocksInfo):
        self.total_num_of_new_stocks = ipo_new_stocks_info.total_num_of_new_stocks
        self.ratio_of_new_stocks = ipo_new_stocks_info.ratio_of_new_stocks

    def set_ipo_stock_conditions(self, ipo_stock_conditions: IpoStockConditions):
        self.total_num_of_stock_after_ipo = ipo_stock_conditions.total_num_of_stock_after_ipo
        self.num_of_stock_lockup = ipo_stock_conditions.num_of_stock_lockup
        self.num_of_stock_sale_available = ipo_stock_conditions.num_of_stock_sale_available
        self.ratio_of_lockup = ipo_stock_conditions.ratio_of_lockup
        self.ratio_of_sale_available = ipo_stock_conditions.ratio_of_sale_available

    def set_ipo_underwriter(self, ipo_underwriter: IpoUnderwriter):
        self.underwriter = ipo_underwriter.underwriter
        self.num_of_stock_allocated = ipo_underwriter.num_of_stock_allocated

    def set_ipo_demand_forecast(self, ipo_demand_forecast: IpoDemandForecast):
        self.competition_ratio = ipo_demand_forecast.competition_ratio
        self.commitment_ratio = ipo_demand_forecast.commitment_ratio

    def get_ipo_price(self):
        ipo_price = IpoPrice()

        ipo_price.band_price_low = self.band_price_low
        ipo_price.band_price_high = self.band_price_high
        ipo_price.offering_price = self.offering_price
        ipo_price.offering_amount = self.offering_amount

        return ipo_price

    def get_ipo_date(self):
        ipo_date = IpoDate()

        ipo_date.bidding_start = self.bidding_start
        ipo_date.bidding_finish = self.bidding_finish
        ipo_date.refund = self.refund
        ipo_date.go_public = self.go_public

        return ipo_date

    def get_ipo_new_stocks_info(self):
        ipo_new_stocks_info = IpoNewStocksInfo()

        ipo_new_stocks_info.total_num_of_new_stocks = self.total_num_of_new_stocks
        ipo_new_stocks_info.ratio_of_new_stocks = self.ratio_of_new_stocks

        return ipo_new_stocks_info

    def get_ipo_stock_conditions(self):
        ipo_stock_conditions = IpoStockConditions()

        ipo_stock_conditions.total_num_of_stock_after_ipo = self.total_num_of_stock_after_ipo
        ipo_stock_conditions.num_of_stock_lockup = self.num_of_stock_lockup
        ipo_stock_conditions.num_of_stock_sale_available = self.num_of_stock_sale_available
        ipo_stock_conditions.ratio_of_lockup = self.ratio_of_lockup
        ipo_stock_conditions.ratio_of_sale_available = self.ratio_of_sale_available

        return ipo_stock_conditions

    def get_ipo_underwriter(self):
        ipo_underwriter = IpoUnderwriter()

        ipo_underwriter.underwriter = self.underwriter
        ipo_underwriter.num_of_stock_allocated = self.num_of_stock_allocated

        return ipo_underwriter

    def get_ipo_demand_forecast(self):
        ipo_demand_forecast = IpoDemandForecast()

        ipo_demand_forecast.competition_ratio = self.competition_ratio
        ipo_demand_forecast.commitment_ratio = self.commitment_ratio

        return ipo_demand_forecast


class BiddingUrlList:
    def __init__(self):
        self.start_tomorrow = []
        self.start_today = []
        self.finish_today = []

    def __getitem__(self, index):
        if index == BiddingStatus.START_TOMORROW:
            return self.start_tomorrow
        elif index == BiddingStatus.START_TODAY:
            return self.start_today
        elif index == BiddingStatus.PROCEEDING:  # REITs Exception(REITS bidding for 3 days)
            return self.start_today
        elif index == BiddingStatus.FINISH_TODAY:
            return self.finish_today


class IpoUrlList:
    def __init__(self):
        self.start_tomorrow = []
        self.start_today = []

    def __getitem__(self, index):
        if index == IpoStatus.START_TOMORROW:
            return self.start_tomorrow
        elif index == IpoStatus.START_TODAY:
            return self.start_today


class IpoCrawler:
    def __init__(self):
        self.bidding_url_list = BiddingUrlList()
        self.ipo_url_list = IpoUrlList()
        self.bidding_data_list_of_lists = [[], [], []]
        self.ipo_data_list_of_lists = [[], []]
        self.target_date = None
        self.company_name = None

    def get_bidding_finish_today_data(self):
        return self.bidding_data_list_of_lists[BiddingStatus.FINISH_TODAY]

    def get_bidding_start_today_data(self):
        return self.bidding_data_list_of_lists[BiddingStatus.START_TODAY]

    def get_bidding_start_tomorrow_data(self):
        return self.bidding_data_list_of_lists[BiddingStatus.START_TOMORROW]

    def get_ipo_start_today_data(self):
        return self.ipo_data_list_of_lists[IpoStatus.START_TODAY]

    def get_ipo_start_tomorrow_data(self):
        return self.ipo_data_list_of_lists[IpoStatus.START_TOMORROW]

    def set_target_date(self, target_date):
        self.target_date = target_date


class Crawler38Communication(IpoCrawler):
    def __init__(self):
        super().__init__()
        self.base_url = 'http://www.38.co.kr'
        self.base_bidding_url = 'http://www.38.co.kr/html/fund/index.htm?o=k'
        self.bidding_table_summary = '공모주 청약일정'
        self.base_ipo_url = 'http://www.38.co.kr/html/fund/index.htm?o=nw'
        self.ipo_table_summary = '신규상장종목'
        self.soup = None

    def parsing_html(self, url):
        if platform.system() == 'Linux':
            proxy_url = 'https://free-proxy-list.net/'
            proxy_res = requests.get(proxy_url)
            print(f'free proxy url response : {proxy_res.status_code}')
            proxy_html = proxy_res.content.decode('utf-8', 'replace')
            soup = BeautifulSoup(proxy_html, 'lxml')
            tbody = soup.select('table[class="table table-striped table-bordered"]')[0].contents[1]
            rows = tbody.find_all('tr')
            country = 'Korea'
            port = '80'

            for row in rows:
                tds = row.find_all('td')
                if tds[3].text == country and tds[1].text == port:
                    free_proxy = tds[0].text
                    proxy = {"https": free_proxy, "http": free_proxy}
                    try:
                        response = requests.get(url, proxies=proxy)
                        print(f'38com url response : {response.status_code}')
                        html = response.content.decode('euc-kr', 'replace')
                        self.soup = BeautifulSoup(html, 'lxml')
                        break
                    except Exception as e:
                        print(f'error occurred : {e}')
                        self.parsing_html(url)
        else:
            response = requests.get(url)
            html = response.content.decode('euc-kr', 'replace')
            self.soup = BeautifulSoup(html, 'lxml')
        return

    def get_company_tr_list(self, data_type):
        if data_type == 'bid':
            company_tr_list = self.find_table_by_summary(self.bidding_table_summary)
        else:
            company_tr_list = self.find_table_by_summary(self.ipo_table_summary)
        company_tr_list = company_tr_list.find('tbody').find_all('tr')
        return company_tr_list

    def convert_bidding_td_to_datetime(self, td, time):
        temp_date_list = td.text.strip().replace(' ', '').split('~')
        year = temp_date_list[0][:4]
        if time == 'start':
            return datetime.strptime(temp_date_list[0], "%Y.%m.%d")
        elif time == 'finish':
            return datetime.strptime(str(year) + '.' + temp_date_list[1], "%Y.%m.%d")

    def convert_ipo_td_to_datetime(self, td):
        temp_datetime = td.text.strip().replace(' ', '')
        return datetime.strptime(temp_datetime, "%Y/%m/%d")

    def set_bidding_url_list(self):
        self.parsing_html(self.base_bidding_url)
        company_tr_list = self.get_company_tr_list('bid')

        for idx in range(-1, -len(company_tr_list) - 1, -1):
            company_td_list = company_tr_list[idx].find_all('td')
            company_a_tag = company_td_list[0].select('a')
            company_href = company_a_tag[0].get('href')

            bidding_start = self.convert_bidding_td_to_datetime(company_td_list[1], 'start')
            bidding_finish = self.convert_bidding_td_to_datetime(company_td_list[1], 'finish')

            date_diff_bidding_start = (self.target_date - bidding_start).days
            date_diff_bidding_finish = (self.target_date - bidding_finish).days

            result_url = self.base_url + company_href
            bidding_status = check_bidding_status(date_diff_bidding_start, date_diff_bidding_finish)

            if bidding_status == BiddingStatus.ALREADY_FINISHED:
                continue
            elif bidding_status == BiddingStatus.START_MORE_THAN_TWO_DAY_AFTER:
                break
            else:
                self.bidding_url_list[bidding_status].append(result_url)

    def set_ipo_url_list(self):
        self.parsing_html(self.base_ipo_url)
        company_tr_list = self.get_company_tr_list('ipo')

        for idx in range(-1, -len(company_tr_list) - 1, -1):
            company_td_list = company_tr_list[idx].find_all('td')
            company_a_tag = company_td_list[0].select('a')
            company_href = company_a_tag[0].get('href')

            ipo_start_date = self.convert_ipo_td_to_datetime(company_td_list[1])

            date_diff_ipo_start = (self.target_date - ipo_start_date).days

            result_url = self.base_url + '/html/fund' + company_href[1:]
            ipo_status = check_ipo_status(date_diff_ipo_start)

            if ipo_status == IpoStatus.ALREADY_FINISHED:
                continue
            elif ipo_status == IpoStatus.START_MORE_THAN_TWO_DAY_AFTER:
                break
            else:
                self.ipo_url_list[ipo_status].append(result_url)

    def find_table_by_summary(self, summary):
        table = self.soup.find('table', {'summary': summary})
        return table

    def crawl_company_name(self):
        company_summary = self.find_table_by_summary('기업개요')
        company_summary_tr = company_summary.find_all('td')[1]
        company_name = company_summary_tr.text.strip()
        self.company_name = company_name
        return company_summary

    def crawl_market_type(self):
        company_summary = self.find_table_by_summary('기업개요')
        market_type_tr = company_summary.find_all('tr')[1]
        market_type_td = market_type_tr.find_all('td')[1]
        market_type = market_type_td.text.strip()
        market_type = 'KOSDAQ' if market_type == '코스닥' else 'KOSPI'

        return market_type

    def crawl_ipo_date(self):
        ipo_date = IpoDate()
        table = self.find_table_by_summary('공모청약일정')
        date_tr_list = table.find_all('tr')[1:6]
        del date_tr_list[1:3]
        date_td_list = [tr.find_all('td')[1].text.replace('\xa0', '').replace(' ', '') for tr in date_tr_list]

        ipo_date.bidding_start, ipo_date.bidding_finish = date_td_list[0].split('~')
        ipo_date.refund = date_td_list[1]
        ipo_date.go_public = date_td_list[2]

        return ipo_date

    def crawl_ipo_price(self):
        ipo_price = IpoPrice()
        table = self.find_table_by_summary('공모정보')
        price_tr_list = table.find_all('tr')[2:4]

        band_price_range_td = price_tr_list[0].find_all('td')[1].text
        band_price_range = band_price_range_td.replace('\xa0', '').replace(' ', '').replace('원', '').replace(',', '')

        band_price_low, band_price_high = band_price_range.split('~')

        public_competition_rate_td = price_tr_list[0].find_all('td')[3].text
        public_competition_rate = public_competition_rate_td.replace('\xa0', '').replace(' ', '').replace(':1', '')

        offering_price_td = price_tr_list[1].find_all('td')[1].text.replace('-', '0')
        offering_price = offering_price_td.replace('\xa0', '').replace(' ', '').replace('원', '').replace(',', '')

        offering_amount_td = price_tr_list[1].find_all('td')[3].text
        offering_amount = offering_amount_td.replace('\xa0', '').replace(' ', '').replace('(백만원)', '').replace(',', '')

        ipo_price.band_price_low = band_price_low
        ipo_price.band_price_high = band_price_high
        ipo_price.offering_price = offering_price
        ipo_price.offering_amount = str(int(offering_amount) // 100)

        return ipo_price

    def crawl_ipo_new_stocks_info(self):
        ipo_new_stocks_info = IpoNewStocksInfo()
        table = self.find_table_by_summary('공모정보')
        new_stock_info_tr_list = table.find_all('tr')[:2]

        total_num_of_new_stocks_td = new_stock_info_tr_list[0].find_all('td')[1].text
        total_num_of_new_stocks = total_num_of_new_stocks_td.replace('주', '').replace(' ', '').replace(',', '').strip()

        temp_td = new_stock_info_tr_list[1].find_all('td')[1].text.split('/')[0]
        ratio_of_new_stocks = temp_td.split('(')[1]
        ratio_of_new_stocks = ratio_of_new_stocks.replace(' ', '').replace('%)', '').strip()

        ipo_new_stocks_info.total_num_of_new_stocks = total_num_of_new_stocks
        ipo_new_stocks_info.ratio_of_new_stocks = ratio_of_new_stocks

        return ipo_new_stocks_info

    def crawl_ipo_demand_forecast(self):
        ipo_demand_forecast = IpoDemandForecast()

        table = self.find_table_by_summary('공모청약일정')
        demand_forecast_rows_tr = table.select('table > tr')[19].find_all('td')[1::2]
        competition_ratio = demand_forecast_rows_tr[0].text.replace(':1', '').strip()
        commitment_ratio = demand_forecast_rows_tr[1].text.replace('0.00%', '').replace('%', '').strip()

        ipo_demand_forecast.competition_ratio = competition_ratio if any(competition_ratio) else 0
        ipo_demand_forecast.commitment_ratio = commitment_ratio if any(commitment_ratio) else 0

        return ipo_demand_forecast

    def crawl_ipo_url(self, url):
        self.parsing_html(url)
        self.crawl_company_name()
        ipo_data = IpoData(self.company_name)
        ipo_data.market_type = self.crawl_market_type()

        ipo_date = self.crawl_ipo_date()
        ipo_data.set_ipo_date(ipo_date)
        del ipo_date

        ipo_price = self.crawl_ipo_price()
        ipo_data.set_ipo_price(ipo_price)
        del ipo_price

        ipo_new_stocks_info = self.crawl_ipo_new_stocks_info()
        ipo_data.set_ipo_new_stocks_info(ipo_new_stocks_info)
        del ipo_new_stocks_info

        ipo_demand_forecast = self.crawl_ipo_demand_forecast()
        ipo_data.set_ipo_demand_forecast(ipo_demand_forecast)
        del ipo_demand_forecast

        company_name = ipo_data.company_name

        if '스팩' in company_name or '기업인수' in company_name:
            ipo_data.company_name = convert_SPAC(company_name)
            ipo_data.offering_price = '2000'

        return ipo_data

    def get_bidding_data_list_of_lists(self):
        self.set_bidding_url_list()
        for i in range(3):
            for url in self.bidding_url_list[i]:
                if url:
                    ipo_data = self.crawl_ipo_url(url)
                    if ipo_data:
                        ipo_data.ref_url_38com = url
                        self.bidding_data_list_of_lists[i].append(ipo_data)

        return self.bidding_data_list_of_lists

    def get_ipo_data_list_of_lists(self):
        self.set_ipo_url_list()
        for i in range(2):
            for url in self.ipo_url_list[i]:
                if url:
                    ipo_data = self.crawl_ipo_url(url)
                    if ipo_data:
                        ipo_data.ref_url_38com = url
                        self.ipo_data_list_of_lists[i].append(ipo_data)

        return self.ipo_data_list_of_lists


class CrawlerIpoStock(IpoCrawler):
    def __init__(self):
        super().__init__()
        self.base_url = 'http://ipostock.co.kr'
        self.base_bidding_url = 'http://www.ipostock.co.kr/sub03/05_6.asp?page='
        self.base_ipo_url = 'http://www.ipostock.co.kr/sub03/05_7.asp?page='
        self.soup = None

    def parsing_html(self, url):
        try:
            response = requests.get(url)
            html = response.content.decode('utf-8', 'replace')
            self.soup = BeautifulSoup(html, 'lxml')
        except Exception as e:
            print(f'IpoStock Parsing Error : {e}')
            time.sleep(5)
            response = requests.get(url)
            html = response.content.decode('utf-8', 'replace')
            self.soup = BeautifulSoup(html, 'lxml')

    def convert_bidding_td_to_datetime(self, td, time):
        year = self.target_date.year
        temp_datetime = td.text.strip().replace(' ', '').split('~')
        if time == 'start':
            return datetime.strptime(str(year) + '.' + temp_datetime[0], "%Y.%m.%d")
        elif time == 'finish':
            return datetime.strptime(str(year) + '.' + temp_datetime[1], "%Y.%m.%d")

    def convert_ipo_td_to_datetime(self, td):
        temp_datetime = td.text.strip().replace(' ', '')
        return datetime.strptime(temp_datetime, "%Y.%m.%d")

    def convert_ipo_tr_to_string(self, tr):
        return tr.find_all('td')[1].text.strip().replace('\xa0', '').replace(" ", "")

    def select_tables_by_class(self, class_name):
        tables = self.soup.select('table[class="' + class_name + '"]')
        return tables

    def select_a_tags_by_href_value(self, href_value):
        a_tags = self.soup.select('a[href^="' + href_value + '"]')
        return a_tags

    def select_tds_by_attribute_value(self, attribute, value):
        tds = self.soup.select('td[' + attribute + '^="' + value + '"]')
        return tds

    def crawl_company_name(self, url):
        if self.soup is None:
            self.parsing_html(url)

        self.company_name = self.soup.find('strong', {'class': 'view_tit'}).text.strip()
        return self.company_name

    def crawl_market_type(self, url):
        if self.soup is None:
            self.parsing_html(url)

        try:
            kosdaq_img = self.soup.select('img[src^="/image/contents/co.gif"]')[0]
            print(f'{self.company_name} : will list in KOSDAQ')
            return 'KOSDAQ'
        except IndexError:
            pass

        try:
            kospi_img = self.soup.select('img[src^="/image/contents/u.gif"]')[0]
            print(f'{self.company_name} : will list in KOSPI')
            return 'KOSPI'
        except IndexError:
            pass

        try:
            konex_img = self.soup.select('img[src^="/image/contents/f.jpg"]')[0]
            print(f'{self.company_name} : from KONEX, will list in KOSDAQ')
            return 'KONEX'
        except IndexError:
            pass

    def get_stock_conditions(self, stock_condition_trs):
        stock_conditions = []
        idx = -1
        while len(stock_conditions) < 6:
            tds = stock_condition_trs[idx].find_all('td')
            idx = idx - 1
            target_text = tds[0].text.strip().replace('\t', '').replace('\r\n', '')

            if target_text in ['공모후 상장주식수', '유통가능주식합계', '보호예수물량합계']:
                number_of_stocks = int(tds[1].text.strip().replace('주', '').replace(',', ''))
                stock_conditions.append(number_of_stocks)

                ratio_of_stocks = float(tds[3].text.strip().replace(' ', '').replace('%', ''))
                stock_conditions.append(ratio_of_stocks)

        return stock_conditions

    def set_bidding_url_list(self):
        for page in range(1, 4):
            bidding_url = self.base_bidding_url + str(page)
            self.parsing_html(bidding_url)

            company_name_a_tag_list = self.select_a_tags_by_href_value('/view_pg/')
            bidding_period_td_list = self.select_tds_by_attribute_value('width', '105')[2:]

            first_bidding_start_date_of_page = self.convert_bidding_td_to_datetime(bidding_period_td_list[-1], 'start')
            last_bidding_finish_date_of_page = self.convert_bidding_td_to_datetime(bidding_period_td_list[0], 'finish')

            if last_bidding_finish_date_of_page.month < first_bidding_start_date_of_page.month:
                first_bidding_start_date_of_page -= relativedelta(years=1)

            if (first_bidding_start_date_of_page - self.target_date).days > 1:
                continue
            elif (last_bidding_finish_date_of_page - self.target_date).days < -1:
                break
            else:
                for idx in range(-1, -len(bidding_period_td_list) - 1, -1):
                    bidding_start = self.convert_bidding_td_to_datetime(bidding_period_td_list[idx], 'start')
                    bidding_finish = self.convert_bidding_td_to_datetime(bidding_period_td_list[idx], 'finish')
                    if bidding_start.month > self.target_date.month:
                        bidding_start -= relativedelta(years=1)
                    if bidding_finish.month > self.target_date.month:
                        bidding_finish -= relativedelta(years=1)
                    date_diff_bidding_start = (self.target_date - bidding_start).days
                    date_diff_bidding_finish = (self.target_date - bidding_finish).days

                    result_url = self.base_url + company_name_a_tag_list[idx].get('href')
                    bidding_status = check_bidding_status(date_diff_bidding_start, date_diff_bidding_finish)

                    if bidding_status == BiddingStatus.ALREADY_FINISHED:
                        continue
                    elif bidding_status == BiddingStatus.START_MORE_THAN_TWO_DAY_AFTER:
                        break
                    else:
                        self.bidding_url_list[bidding_status].append(result_url)

    def set_ipo_url_list(self):
        for page in range(1, 4):
            base_ipo_url = self.base_ipo_url + str(page)
            self.parsing_html(base_ipo_url)

            company_name_a_tag_list = self.select_a_tags_by_href_value('/view_pg/')
            ipo_period_td_list = self.select_tds_by_attribute_value('width', '120')[2::2]

            first_ipo_start_date_of_page = self.convert_ipo_td_to_datetime(ipo_period_td_list[-1])
            last_ipo_start_date_of_page = self.convert_ipo_td_to_datetime(ipo_period_td_list[0])

            if (self.target_date - first_ipo_start_date_of_page).days < 0:
                continue
            elif (self.target_date - last_ipo_start_date_of_page).days > 0:
                break
            else:
                for idx in range(-1, -len(ipo_period_td_list) - 1, -1):
                    ipo_start_date = self.convert_ipo_td_to_datetime(ipo_period_td_list[idx])
                    date_diff_ipo_start = (self.target_date - ipo_start_date).days

                    result_url = self.base_url + company_name_a_tag_list[idx].get('href')
                    ipo_status = check_ipo_status(date_diff_ipo_start)

                    if ipo_status == IpoStatus.ALREADY_FINISHED:
                        continue
                    elif ipo_status == IpoStatus.START_MORE_THAN_TWO_DAY_AFTER:
                        break
                    else:
                        self.ipo_url_list[ipo_status].append(result_url)

    def crawl_ipo_date(self, url, table=None):
        ipo_date = IpoDate()

        if table is None:
            self.parsing_html(url)
            table = self.select_tables_by_class('view_tb')[0]

        date_table_rows = table.find_all('tr')[2:]
        del date_table_rows[-2]

        bidding_period = self.convert_ipo_tr_to_string(date_table_rows[0])

        ipo_date.bidding_start = bidding_period[:10]
        ipo_date.bidding_finish = bidding_period[:5] + bidding_period[-5:]
        ipo_date.refund = self.convert_ipo_tr_to_string(date_table_rows[1])
        ipo_date.go_public = self.convert_ipo_tr_to_string(date_table_rows[2])

        return ipo_date

    def crawl_ipo_price(self, url, table=None):
        ipo_price = IpoPrice()

        if table is None:
            self.parsing_html(url)
            table = self.select_tables_by_class('view_tb')[1]

        price_table_rows = table.find_all('tr')[:-2]
        del price_table_rows[1]

        bidding_price_band_list = self.convert_ipo_tr_to_string(price_table_rows[0]).replace('원', '').replace(',',
                                                                                                              '').split(
            '~')

        ipo_price.band_price_low = bidding_price_band_list.pop(0)
        ipo_price.band_price_high = bidding_price_band_list.pop(0)
        ipo_price.offering_price = self.convert_ipo_tr_to_string(price_table_rows[1]).replace('원', '').replace(',', '')
        ipo_price.offering_amount = self.convert_ipo_tr_to_string(price_table_rows[2]).replace('억원', '').replace(',',
                                                                                                                 '')

        return ipo_price

    def crawl_ipo_new_stocks_info(self, url, table=None):
        ipo_new_stocks_info = IpoNewStocksInfo()

        if table is None:
            self.parsing_html(url)
            table = self.select_tables_by_class('view_tb')[2]

        new_stocks_info_table_rows = table.find_all('tr')

        new_stocks_info = self.convert_ipo_tr_to_string(new_stocks_info_table_rows[0]).replace(',', '')
        new_stocks_info = new_stocks_info.replace('(', '').replace(')', '')
        total_num_of_new_stocks, ratio_of_new_stocks = new_stocks_info.split('주')
        ratio_of_new_stocks = int(ratio_of_new_stocks.replace('모집', '').replace('%', ''))

        ipo_new_stocks_info.total_num_of_new_stocks = total_num_of_new_stocks
        ipo_new_stocks_info.ratio_of_new_stocks = ratio_of_new_stocks

        return ipo_new_stocks_info

    def crawl_ipo_underwriter(self, url, table=None):
        ipo_underwriter = IpoUnderwriter()

        if table is None:
            self.parsing_html(url)
            table = self.select_tables_by_class('view_tb')[3]

        underwriter_rows = table.find_all('tr')[1:]
        underwriter_list = []
        allocated_stock_num_list = []

        for underwriter_row in underwriter_rows:
            underwriter = underwriter_row.find_all('td')[0].text.strip().replace(' ', '')
            if underwriter:
                allocated_stock_num = underwriter_row.find_all('td')[1].text.strip()
                allocated_stock_num = allocated_stock_num.replace(' ', '').replace('주', '').replace(',', '')
                underwriter_list.append(underwriter)
                allocated_stock_num_list.append(allocated_stock_num)

        ipo_underwriter.underwriter = ', '.join(underwriter_list)
        ipo_underwriter.num_of_stock_allocated = ', '.join(allocated_stock_num_list)

        return ipo_underwriter

    def crawl_ipo_stock_conditions(self, url):
        ipo_stock_conditions = IpoStockConditions()

        self.parsing_html(url)
        table = self.select_tables_by_class('view_tb')[2]

        stock_conditions_table_rows = table.find_all('tr')
        stock_conditions = self.get_stock_conditions(stock_conditions_table_rows)

        ipo_stock_conditions.total_num_of_stock_after_ipo = stock_conditions[0]
        ipo_stock_conditions.num_of_stock_sale_available = stock_conditions[2]
        ipo_stock_conditions.ratio_of_sale_available = stock_conditions[3]
        ipo_stock_conditions.num_of_stock_lockup = stock_conditions[4]
        ipo_stock_conditions.ratio_of_lockup = stock_conditions[5]

        return ipo_stock_conditions

    def crawl_ipo_demand_forecast(self, url):
        ipo_demand_forecast = IpoDemandForecast()

        self.parsing_html(url)
        try:
            table = self.select_tables_by_class('view_tb2')[1]
            demand_forecast_rows = table.find_all('tr')
            del demand_forecast_rows[1]
        except Exception as e:
            print(f'{self.company_name} - 크롤링중 오류 : {e}')
            print("demand forecast table doesn't exist")
            competition_ratio = 0
            commitment_ratio = 0

            ipo_demand_forecast.competition_ratio = competition_ratio
            ipo_demand_forecast.commitment_ratio = commitment_ratio

            return ipo_demand_forecast

        try:
            competition_ratio = self.convert_ipo_tr_to_string(demand_forecast_rows[0])
            competition_ratio = float(competition_ratio.replace(',', '').replace(':1', ''))
        except Exception as e:
            print(f'{self.company_name} - 크롤링중 오류 : {e}')
            print("competition ratio doesn't exist")
            competition_ratio = 0

        try:
            commitment_ratio = self.convert_ipo_tr_to_string(demand_forecast_rows[1])
            commitment_ratio = float(commitment_ratio.replace('%', ''))
        except Exception as e:
            print(f'{self.company_name} - 크롤링중 오류 : {e}')
            print("commitment ratio doesn't exist")
            commitment_ratio = 0

        ipo_demand_forecast.competition_ratio = competition_ratio
        ipo_demand_forecast.commitment_ratio = commitment_ratio

        return ipo_demand_forecast

    def is_ipo_canceled(self):
        title_tr = self.soup.find('strong', {'class': 'view_tit'}).parent.parent
        ipo_status = title_tr.find_all('td')[1].text
        if '철회' in ipo_status:
            return True
        else:
            return False

    def crawl_ipo_url(self, url):
        self.parsing_html(url)
        if self.is_ipo_canceled():
            return None
        else:
            self.crawl_company_name(url)
            ipo_data = IpoData(self.company_name)
            ipo_data.market_type = self.crawl_market_type(url)
            ipo_data.is_from_KONEX = True if ipo_data.market_type == 'KONEX' else False
            ipo_data.set_public_offering_page_url(url)
            ipo_tables = self.select_tables_by_class('view_tb')[:4]

            ipo_date = self.crawl_ipo_date(url, ipo_tables[0])
            ipo_data.set_ipo_date(ipo_date)
            del ipo_date

            ipo_price = self.crawl_ipo_price(url, ipo_tables[1])
            ipo_data.set_ipo_price(ipo_price)
            del ipo_price

            ipo_new_stocks_info = self.crawl_ipo_new_stocks_info(url, ipo_tables[2])
            ipo_data.set_ipo_new_stocks_info(ipo_new_stocks_info)
            del ipo_new_stocks_info

            ipo_underwriter = self.crawl_ipo_underwriter(url, ipo_tables[3])
            ipo_data.set_ipo_underwriter(ipo_underwriter)
            del ipo_underwriter

            ipo_stock_conditions = self.crawl_ipo_stock_conditions(ipo_data.stock_holder_page_url)
            ipo_data.set_ipo_stock_conditions(ipo_stock_conditions)
            del ipo_stock_conditions

            ipo_demand_forecast = self.crawl_ipo_demand_forecast(ipo_data.demand_forecast_page_url)
            ipo_data.set_ipo_demand_forecast(ipo_demand_forecast)
            del ipo_demand_forecast

            company_name = ipo_data.company_name

            if '스팩' in company_name or '기업인수' in company_name:
                ipo_data.company_name = convert_SPAC(company_name)
                ipo_data.offering_price = '2000'

            return ipo_data

    def get_monthly_ipo_url_list(self, year, month):
        monthly_url_list = []
        url = f'http://ipostock.co.kr/sub03/ipo04.asp?str1={year}&str2={month}'
        self.parsing_html(url)

        company_a_tag_list = self.select_a_tags_by_href_value('/view_pg/')
        for company_a_tag in company_a_tag_list:
            result_url = self.base_url + company_a_tag.get('href')
            monthly_url_list.append(result_url)

        return monthly_url_list

    def get_bidding_data_list_of_lists(self):
        self.set_bidding_url_list()
        for i in range(3):
            for url in self.bidding_url_list[i]:
                if url:
                    ipo_data = self.crawl_ipo_url(url)
                    if ipo_data:
                        ipo_data.ref_url_ipo_stock = url
                        self.bidding_data_list_of_lists[i].append(ipo_data)

        return self.bidding_data_list_of_lists

    def get_ipo_data_list_of_lists(self):
        self.set_ipo_url_list()
        for i in range(2):
            for url in self.ipo_url_list[i]:
                if url:
                    ipo_data = self.crawl_ipo_url(url)
                    if ipo_data:
                        ipo_data.ref_url_ipo_stock = url
                        self.ipo_data_list_of_lists[i].append(ipo_data)

        return self.ipo_data_list_of_lists


def is_empty(value, value_type):
    if value_type == 'date':
        return True if not value else False

    elif value_type == 'price':
        return True if value == '0' else False

    else:
        return True if value == 0 else False


def double_check_data(data_from_38_com, data_from_ipo_stock):
    for i in range(len(data_from_38_com)):
        for ipo_data_38_com in data_from_38_com[i]:
            if ipo_data_38_com:
                for j, ipo_data_ipo_stock in enumerate(data_from_ipo_stock[i]):
                    if ipo_data_ipo_stock.company_name == ipo_data_38_com.company_name:
                        if not is_empty(ipo_data_38_com.go_public, 'date'):
                            if is_empty(ipo_data_ipo_stock.go_public, 'date'):
                                data_from_ipo_stock[i][j].go_public = ipo_data_38_com.go_public

                        if not is_empty(ipo_data_38_com.offering_price, 'price'):
                            if is_empty(ipo_data_ipo_stock.offering_price, 'price'):
                                data_from_ipo_stock[i][j].offering_price = ipo_data_38_com.offering_price

                        if not is_empty(ipo_data_38_com.offering_amount, 'price'):
                            if is_empty(ipo_data_ipo_stock.offering_amount, 'price'):
                                data_from_ipo_stock[i][j].offering_amount = ipo_data_38_com.offering_amount

                        if not is_empty(ipo_data_38_com.competition_ratio, 'ratio'):
                            if is_empty(ipo_data_ipo_stock.competition_ratio, 'ratio'):
                                data_from_ipo_stock[i][j].competition_ratio = ipo_data_38_com.competition_ratio

                        if not is_empty(ipo_data_38_com.commitment_ratio, 'ratio'):
                            if is_empty(ipo_data_ipo_stock.commitment_ratio, 'ratio'):
                                data_from_ipo_stock[i][j].commitment_ratio = ipo_data_38_com.commitment_ratio

                        data_from_ipo_stock[i][j].ref_url_38com = ipo_data_38_com.ref_url_38com
                        break

    return data_from_ipo_stock


def get_bidding_data_list(target_date):
    crawler_38com = Crawler38Communication()
    crawler_38com.set_target_date(target_date)

    crawler_ipo_stock = CrawlerIpoStock()
    crawler_ipo_stock.set_target_date(target_date)

    bidding_data_list_38com = crawler_38com.get_bidding_data_list_of_lists()
    bidding_data_list_ipo_stock = crawler_ipo_stock.get_bidding_data_list_of_lists()

    bidding_data_list = double_check_data(bidding_data_list_38com, bidding_data_list_ipo_stock)

    return bidding_data_list


def get_ipo_data_list(target_date):
    crawler_38com = Crawler38Communication()
    crawler_ipo_stock = CrawlerIpoStock()

    crawler_38com.set_target_date(target_date)
    crawler_ipo_stock.set_target_date(target_date)

    ipo_data_list_38com = crawler_38com.get_ipo_data_list_of_lists()
    ipo_data_list_ipo_stock = crawler_ipo_stock.get_ipo_data_list_of_lists()

    ipo_data_list = double_check_data(ipo_data_list_38com, ipo_data_list_ipo_stock)

    return ipo_data_list


def get_ipo_after_data(company_name):
    driver = webdriver.Chrome('../chromedriver')
    default_url = 'https://finance.naver.com/'
    driver.get(default_url)
    driver.implicitly_wait(20)
    driver.find_element_by_class_name('snb_search_text').send_keys(company_name)
    driver.implicitly_wait(20)
    driver.find_element_by_class_name('snb_search_btn').click()
    time.sleep(3)
    company_code = None

    try:
        company_code = int(re.compile(r"\S+\?code=").sub('', driver.current_url))
    except ValueError as e:
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        a_tags = soup.select('a[href^="/item/main.naver?"]')
        for a_tag in a_tags:
            if a_tag.text == company_name:
                company_code = int(re.compile(r"\S+\?code=").sub('', a_tag.get('href')))
                break
    finally:
        page_to_crawl = 'https://finance.naver.com/item/sise_day.naver?code=' + str(company_code)

        driver.get(page_to_crawl)
        time.sleep(3)
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        table = soup.find('table', {'summary': '페이지 네비게이션 리스트'})
        page = table.find_all('td')
        last_page_url = default_url + page[-1].find('a').get('href')

        driver.get(last_page_url)
        time.sleep(3)
        new_table = driver.find_element_by_class_name('type2')
        tr_list = new_table.text.split('\n')

        return tr_list
