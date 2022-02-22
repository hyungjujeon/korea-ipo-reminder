from crawler.ipo_crawler import IpoData
from datetime import datetime, timedelta

weekdays = {0: '(월)', 1: '(화)', 2: '(수)', 3: '(목)', 4: '(금)', 5: '(토)', 6: '(일)'}
quote_range_KOSPI = {}

def get_bidding_fee(underwriter_name):
    if underwriter_name in ['미래에셋증권', '한국투자증권', '하나금융투자', '삼성증권', 'SK증권', '대신증권', '신영증권', '현대차증권', '하이투자증권']:
        return 2000
    elif underwriter_name in ['KB증권', 'KB투자증권']:
        return 1500
    elif underwriter_name in ['한화투자증권', '교보증권']:
        return 1000
    else:
        return 0


def get_stock_quote(stock_price: int, market_type: str):
    quote = 0

    if market_type == 'KOSDAQ':
        if stock_price >= 50000:
            quote = 100
            return quote

    price_level = stock_price / (5 * 10**(len(str(stock_price)) - 1))
    price_level += 2 * (len(str(stock_price)) - 4)
    price_level = min(int(price_level), 5)

    quote = 5 * ((price_level % 2) + 1) * 10**(price_level // 2)

    return quote


def check_is_upper_limit_price(price_changed: int, closing_price: int, market_type: str):
    is_upper_limit_price = False

    change_ratio = price_changed / (closing_price - price_changed)
    if change_ratio == 0.3:
        is_upper_limit_price = True
    elif change_ratio >= 0.295:
        tick = get_stock_quote(closing_price, market_type)
        change_ratio = (price_changed + tick) / (closing_price - price_changed)
        if change_ratio > 0.3:
            is_upper_limit_price = True

    return is_upper_limit_price


class ConvertIpoDataType:
    def __init__(self, ipo_data: IpoData):
        self.content_list = []

        self.company_name = ipo_data.company_name
        self.is_from_KONEX = ipo_data.is_from_KONEX

        self.bidding_start = ipo_data.bidding_start + weekdays[
            datetime.strptime(ipo_data.bidding_start, "%Y.%m.%d").weekday()]
        self.bidding_finish = ipo_data.bidding_finish + weekdays[
            datetime.strptime(ipo_data.bidding_finish, "%Y.%m.%d").weekday()]
        self.refund_date = ipo_data.refund + weekdays[datetime.strptime(ipo_data.refund, "%Y.%m.%d").weekday()]
        self.ipo_date = ipo_data.go_public + weekdays[
            datetime.strptime(ipo_data.go_public, "%Y.%m.%d").weekday()] if ipo_data.go_public else "미정"

        self.band_price_low = int(ipo_data.band_price_low)
        self.band_price_high = int(ipo_data.band_price_high)
        self.offering_price = int(ipo_data.offering_price)
        self.offering_amount = int(ipo_data.offering_amount)

        self.num_of_stock_sale_available = int(ipo_data.num_of_stock_sale_available)
        self.ratio_of_sale_available = ipo_data.ratio_of_sale_available
        self.amount_of_sale_available = int(self.offering_price * self.num_of_stock_sale_available // 100000000)

        self.underwriter_list = ipo_data.underwriter

        underwriter = ipo_data.underwriter.split(', ')
        fee = [get_bidding_fee(uw) for uw in underwriter]
        num_of_stock_allocated = ipo_data.num_of_stock_allocated.split(', ')

        self.competition_ratio = ipo_data.competition_ratio
        self.commitment_ratio = ipo_data.commitment_ratio

        self.underwriter_info = [(x[0] + '(수수료: ' + format(x[1], ',d') + '원, ' + format(int(x[2]), ',d') + '주)') for x
                                 in list(zip(underwriter, fee, num_of_stock_allocated))]
        self.underwriter_info = ', '.join(self.underwriter_info)
        self.minimum_bidding_price = (
            self.offering_price * 10 if '스팩' in self.company_name else self.offering_price * 5)

    def to_content_list(self):
        self.content_list.append(f'💡균등 최소 청약증거금(10주) : ' + format(self.minimum_bidding_price, ',d') + '원')
        self.content_list.append(f'📅공모 일정 : {self.bidding_start} ~ {self.bidding_finish}')
        self.content_list.append(f'📅상장일 : {self.ipo_date}')
        self.content_list.append(f'📅환불일 : {self.refund_date}')
        self.content_list.append(
            f'💰희망공모가 : ' + format(self.band_price_low, ",d") + '원 ~ ' + format(self.band_price_high, ",d") + '원')
        self.content_list.append(f'💰확정공모가 : ' + format(self.offering_price, ",d") + '원')
        self.content_list.append(f'💰공모규모 : ' + format(self.offering_amount, ',d') + '억')
        self.content_list.append(f'💰유통가능 금액(예상) : ' + format(self.amount_of_sale_available, ',d') + '억')
        self.content_list.append(f'🧾유통가능 주식 수(예상) : ' + format(self.num_of_stock_sale_available, ',d') + '주')
        self.content_list.append(f'🧾유통가능 주식 비율(예상) : {self.ratio_of_sale_available}' + '%')
        self.content_list.append(f'🏢수요예측 기관 경쟁률 : (' + format(self.competition_ratio, '.2f') + ' : 1)')
        self.content_list.append(f'🏢의무보유 확약 비율(예상) : {self.commitment_ratio}' + '%')
        self.content_list.append(f'🚩주간사(수수료, 배정물량) : ' + self.underwriter_info)
        self.content_list.append(f'🚩주간사 : ' + self.underwriter_list)


class ConvertBiddingData(ConvertIpoDataType):
    def __init__(self, ipo_data: IpoData):
        super().__init__(ipo_data)

    def get_tistory_content(self):
        super().to_content_list()
        p_tag_style = '<p data-ke-size="size14" style="margin: 0">'

        del self.content_list[-1]

        self.content_list[0] = '<b>' + self.content_list[0] + '</b>'
        self.content_list = [p_tag_style + content + '</p>' for content in self.content_list]
        if self.is_from_KONEX:
            self.content_list.insert(0, p_tag_style + f'<b>❗❗코넥스→코스닥 이전상장 종목</b></p>')

        return ''.join(self.content_list)

    def get_telegram_content(self):
        super().to_content_list()

        del self.content_list[-1]

        self.content_list = [content + '\n' for content in self.content_list]
        if self.is_from_KONEX:
            self.content_list.insert(0, f'<b>❗❗코넥스→코스닥 이전상장 종목</b>\n')

        return '\n' + ''.join(self.content_list)


class ConvertIpoReadyData(ConvertIpoDataType):
    def __init__(self, ipo_data: IpoData):
        super().__init__(ipo_data)

    def get_tistory_content(self):
        super().to_content_list()
        p_tag_style = '<p data-ke-size="size14" style="margin: 0">'

        del self.content_list[:2]
        del self.content_list[1]
        del self.content_list[-2]

        self.content_list[-6:] = [content.replace('예상', '확정') for content in self.content_list[-6:]]
        self.content_list = [p_tag_style + content + '</p>' for content in self.content_list]

        if self.is_from_KONEX:
            self.content_list.insert(0, p_tag_style + f'<b>❗❗코넥스→코스닥 이전상장 종목</b></p>')

        return ''.join(self.content_list)

    def get_telegram_content(self):
        super().to_content_list()

        del self.content_list[:2]
        del self.content_list[1]
        del self.content_list[-2]

        self.content_list[-6:] = [content.replace('예상', '확정') for content in self.content_list[-6:]]
        self.content_list = [content + '\n' for content in self.content_list]
        if self.is_from_KONEX:
            self.content_list.insert(0, f'<b>❗❗코넥스→코스닥 이전상장 종목</b>\n')

        return '\n' + ''.join(self.content_list)


class TextContent:
    def __init__(self, ipo_data_list_of_lists, target_date, post_type):
        self.post_type = post_type
        self.target_date = target_date
        self.ipo_data_list_of_lists = ipo_data_list_of_lists

        self.title = None
        self.content = None
        self.category = None
        self.subtitle_list = []

    def set_title(self):
        self.title = f'💰{self.target_date.year}년 {self.target_date.month}월 {self.target_date.day}일'
        self.title += f'{weekdays[self.target_date.weekday()]} {self.category} 정보💰'

    def set_subtitle_list(self):
        if self.category == '청약':
            self.subtitle_list.append(f'📢오늘({self.target_date.month}/{self.target_date.day}) 청약 마감 : ')
            self.subtitle_list.append(f'🔔오늘({self.target_date.month}/{self.target_date.day}) 청약 시작 : ')
            tomorrow = self.target_date + timedelta(days=1)
            self.subtitle_list.append(f'📋내일({tomorrow.month}/{tomorrow.day}) 청약 시작 : ')

        elif self.category == '상장':
            self.subtitle_list.append(f'📢오늘({self.target_date.month}/{self.target_date.day}) 상장 : ')
            tomorrow = self.target_date + timedelta(days=1)
            self.subtitle_list.append(f'📋내일({tomorrow.month}/{tomorrow.day}) 상장 : ')
