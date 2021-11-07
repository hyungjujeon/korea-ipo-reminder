import requests
from enum import IntEnum
from datetime import datetime
from bs4 import BeautifulSoup


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


class IpoData(IpoDate, IpoPrice, IpoNewStocksInfo, IpoStockConditions, IpoUnderwriter, IpoDemandForecast):
    def __init__(self, company_name):
        self.company_name = company_name
        self.__public_offering_page_url = None
        self.stock_holder_page_url = None
        self.demand_forecast_page_url = None
        self.ref_url_ipo_stock = None
        self.ref_url_38com = None
        IpoDate.__init__(self)
        IpoPrice.__init__(self)
        IpoNewStocksInfo.__init__(self)
        IpoStockConditions.__init__(self)
        IpoUnderwriter.__init__(self)
        IpoDemandForecast.__init__(self)

    @property
    def public_offering_page_url(self):
        return self.__public_offering_page_url

    @public_offering_page_url.setter
    def public_offering_page_url(self, url):
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
        self.base_bidding_url = 'http://www.38.co.kr/html/fund/index.htm?o=k&page='
        self.base_ipo_url = 'http://www.38.co.kr/html/fund/index.htm?o=nw&page='
        self.soup = None

    def parsing_html(self, url):
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = response.text
        self.soup = BeautifulSoup(html, 'lxml')


class CrawlerIpoStock(IpoCrawler):
    def __init__(self):
        super().__init__()
        self.base_url = 'http://ipostock.co.kr'
        self.base_bidding_url = 'http://www.ipostock.co.kr/sub03/05_6.asp?page='
        self.base_ipo_url = 'http://www.ipostock.co.kr/sub03/05_7.asp?page='
        self.soup = None

    def parsing_html(self, url):
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

            if (first_bidding_start_date_of_page - self.target_date).days > 1:
                continue
            elif (last_bidding_finish_date_of_page - self.target_date).days < -1:
                break
            else:
                for idx in range(-1, -len(bidding_period_td_list) - 1, -1):
                    bidding_start = self.convert_bidding_td_to_datetime(bidding_period_td_list[idx], 'start')
                    bidding_finish = self.convert_bidding_td_to_datetime(bidding_period_td_list[idx], 'finish')
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

        new_stocks_info = self.convert_ipo_tr_to_string(new_stocks_info_table_rows[0]).replace(',', '').replace('(',
                                                                                                                '').replace(
            ')', '')
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
                allocated_stock_num = underwriter_row.find_all('td')[1].text.strip().replace(' ', '').replace('주',
                                                                                                              '').replace(
                    ',', '')
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

    def crawl_ipo_url(self, url):
        self.parsing_html(url)
        self.crawl_company_name(url)
        ipo_data = IpoData(self.company_name)
        ipo_data.public_offering_page_url = url
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

        return ipo_data
        # ipo_demand_forecast_band = crawl_ipo_demand_forecast_band(url)
        # ipo_allocation_detail = crawl_ipo_allocation_detail(url, ipo_tables[2])

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
                    if str(ipo_data.offering_price) != '0':
                        ipo_data.ref_url_ipo_stock = url
                        self.bidding_data_list_of_lists[i].append(ipo_data)

        return self.bidding_data_list_of_lists

    def get_ipo_data_list_of_lists(self):
        self.set_ipo_url_list()
        for i in range(2):
            for url in self.ipo_url_list[i]:
                if url:
                    print(url)
                    ipo_data = self.crawl_ipo_url(url)
                    if str(ipo_data.offering_price) != '0':
                        ipo_data.ref_url_ipo_stock = url
                        self.ipo_data_list_of_lists[i].append(ipo_data)

        return self.ipo_data_list_of_lists

    # Not use yet
    # def crawl_demand_forecast_band(url):
    #     crawler = CrawlerIpoStock()
    #     crawler.parsing_html(url)
    #
    #     table = crawler.select_tables_by_class('view_tb')[1]
    #     band_rows = table.find_all('tr')[2:]
    #
    #     price_list = []  # 가격
    #     registration_num_list = []  # 건수
    #     registration_ratio_list = []  # 건수비중
    #     amount_list = []  # 참여수량
    #     amount_ratio_list = []  # 참여수량비중
    #
    #     for result_row in band_rows:
    #         tds = result_row.find_all('td')
    #         price_list.append(tds[0].text.strip())
    #         registration_num_list.append(tds[1].text.strip())
    #         registration_ratio_list.append(tds[2].text.strip())
    #         amount_list.append(tds[3].text.strip())
    #         amount_ratio_list.append(tds[4].text.strip())
    #
    #     return [price_list, registration_num_list, registration_ratio_list, amount_list, amount_ratio_list]

    # def crawl_allocation_detail(url, table=None):
    #     if table is None:
    #         crawler = CrawlerIpoStock()
    #         crawler.parsing_html(url)
    #         table = crawler.select_tables_by_class('view_tb')[2]

    # allocation_ratio_table_rows = table.find_all('tr')
    #
    # investor_num = allocation_ratio_table_rows[1].find_all('td')[2].text.strip().replace(" ", "")  # 1: 전문투자자
    # investor_ratio = allocation_ratio_table_rows[1].find_all('td')[3].text.strip().replace(" ", "")
    #
    # employee_num = allocation_ratio_table_rows[2].find_all('td')[1].text.strip().replace(" ", "")  # 2: 우리사주조합
    # employee_ratio = allocation_ratio_table_rows[2].find_all('td')[2].text.strip().replace(" ", "")
    #
    # public_num = allocation_ratio_table_rows[3].find_all('td')[1].text.strip().replace(" ", "")  # 3: 일반청약자
    # public_ratio = allocation_ratio_table_rows[3].find_all('td')[2].text.strip().replace(" ", "")
    #
    # foreigner_num = allocation_ratio_table_rows[4].find_all('td')[1].text.strip().replace(" ", "")  # 4: 해외투자자
    # foreigner_ratio = allocation_ratio_table_rows[4].find_all('td')[2].text.strip().replace(" ", "")
