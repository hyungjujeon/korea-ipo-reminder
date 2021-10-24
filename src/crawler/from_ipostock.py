import requests
from datetime import datetime
from bs4 import BeautifulSoup
from enum import IntEnum
import pandas as pd

class UrlTypeIndex(IntEnum):
    PUBLIC_OFFERING = 0  # 공모정보
    SHARE_HOLDER    = 1  # 주주구성
    DEMAND_FORECAST = 2  # 수요예측

def get_month_ipo_urls_list(year, month):
    url_list = []

    base_url = 'http://ipostock.co.kr'
    temp_url = f'http://ipostock.co.kr/sub03/ipo04.asp?str1={year}&str2={month}'
    response = requests.get(temp_url)
    temp_html = response.content.decode('utf-8', 'replace')
    temp_soup = BeautifulSoup(temp_html, 'lxml')

    company_a_tag_list = temp_soup.select("a[href^='/view_pg/']")
    for company_a_tag in company_a_tag_list:
        url_list.append(base_url + company_a_tag.get('href'))

    return url_list

def get_ipo_url_list(target_date):
    ipo_before_day_url_list = []
    ipo_d_day_url_list = []

    base_url = 'http://ipostock.co.kr'
    for page in range(1, 4):
        temp_url = f'http://www.ipostock.co.kr/sub03/05_7.asp?page={page}'
        response = requests.get(temp_url)
        temp_html = response.content.decode('utf-8', 'replace')
        temp_soup = BeautifulSoup(temp_html, 'lxml')

        company_name_a_tag_list = temp_soup.select("a[href^='/view_pg/']")
        ipo_period_td_list = temp_soup.select("td[width^='120']")[2: :2]

        latest_ipo_start_temp = ipo_period_td_list[0].text.strip().replace(' ', '')
        latest_ipo_start = datetime.strptime(latest_ipo_start_temp, "%Y.%m.%d")

        recent_ipo_start_temp = ipo_period_td_list[-1].text.strip().replace(' ', '')
        recent_ipo_start = datetime.strptime(recent_ipo_start_temp, "%Y.%m.%d")

        if recent_ipo_start > target_date:
            continue
        elif (target_date - latest_ipo_start).days > 1:
            break
        else:
            for idx in range(-1, -len(ipo_period_td_list), -1):
                ipo_start_temp = ipo_period_td_list[idx].text.strip().replace(' ', '')
                ipo_start = datetime.strptime(ipo_start_temp, "%Y.%m.%d")
                date_diff_ipo_start = (target_date - ipo_start).days

                url = base_url + company_name_a_tag_list[idx].get('href')

                if date_diff_ipo_start == -1:
                    ipo_before_day_url_list.append(url)
                elif date_diff_ipo_start == 0:
                    ipo_d_day_url_list.append(url)

    return [ipo_d_day_url_list, ipo_before_day_url_list]

def get_bidding_url_list(target_date):
    year = target_date.year
    month = target_date.month

    bidding_before_day_url_list = []
    bidding_start_url_list = []
    bidding_finish_url_list = []

    base_url = 'http://ipostock.co.kr'
    for page in range(1, 4):
        temp_url = f'http://www.ipostock.co.kr/sub03/05_6.asp?page={page}'
        response = requests.get(temp_url)
        temp_html = response.content.decode('utf-8', 'replace')
        temp_soup = BeautifulSoup(temp_html, 'lxml')

        company_name_a_tag_list = temp_soup.select("a[href^='/view_pg/']")
        bidding_period_td_list = temp_soup.select("td[width^='105']")[2:]
        latest_bidding_start_temp = bidding_period_td_list[0].text.strip().replace(' ', '').split('~')[0]
        latest_bidding_start = datetime.strptime(str(year) + '.' + latest_bidding_start_temp, "%Y.%m.%d")

        recent_bidding_start_temp = bidding_period_td_list[-1].text.strip().replace(' ', '').split('~')[0]
        recent_bidding_start = datetime.strptime(str(year) + '.' + recent_bidding_start_temp, "%Y.%m.%d")

        if recent_bidding_start > target_date:
            continue
        elif (target_date - latest_bidding_start).days > 4:
            break
        else:
            for idx in range(-1, -len(bidding_period_td_list) - 1, -1):
                bidding_start_temp, bidding_fin_temp = bidding_period_td_list[idx].text.strip().replace(' ', '').split('~')
                bidding_start = datetime.strptime(str(year) + '.' + bidding_start_temp, "%Y.%m.%d")
                bidding_finish = datetime.strptime(str(year) + '.' + bidding_fin_temp, "%Y.%m.%d")
                date_diff_bidding_start = (target_date - bidding_start).days
                date_diff_bidding_finish = (target_date - bidding_finish).days

                url = base_url + company_name_a_tag_list[idx].get('href')

                if date_diff_bidding_finish > 0:
                    continue
                elif date_diff_bidding_start == -1:
                    bidding_before_day_url_list.append(url)
                elif date_diff_bidding_start == 0:
                    bidding_start_url_list.append(url)
                elif date_diff_bidding_start >= 1 and date_diff_bidding_start <= 4:
                    if date_diff_bidding_finish == 0:
                        bidding_finish_url_list.append(url)
                    else: #리츠의 경우 청약일이 3일 -> 2틀차는 시작일로 치려고 함
                        bidding_start_url_list.append(url)
                else:
                    break

    return [bidding_finish_url_list, bidding_start_url_list, bidding_before_day_url_list]

def crawl_ipo_info(url):
    url_list = []
    url_list.append(url)  # 공모정보 탭
    total_list = []

    for page_num in [2, 5]:  # 주주구성, 수요예측 탭
        search_required_url = url.replace('_04', f'_0{page_num}')
        url_list.append(search_required_url)
    try:
        bidding_info_list = get_bidding_info_list(url_list[UrlTypeIndex.PUBLIC_OFFERING])
        shares_info_list = get_shares_info_list(url_list[UrlTypeIndex.SHARE_HOLDER])
        underwriter_info_list = get_underwriter_info_list(url_list[UrlTypeIndex.PUBLIC_OFFERING])

        total_list = bidding_info_list + shares_info_list + underwriter_info_list

        demand_forecast_result_list = get_demand_forecast_result_list(url_list[UrlTypeIndex.DEMAND_FORECAST])
        total_list += demand_forecast_result_list

        return total_list

    except Exception as e:
        print(e)
        # 도중 오류나면, 안읽어옴 : null return 해버리게 됨.
        pass

def get_bidding_info_list(url):
    response = requests.get(url)
    html = response.content.decode('utf-8', 'replace')
    soup = BeautifulSoup(html, 'lxml')
    tables = soup.select('table[class="view_tb"]')[0:3]

    company_name = soup.find('strong', {'class': 'view_tit'}).text.strip()

    date_table = tables[0]
    price_table = tables[1]
    allocation_ratio_table = tables[2]

    date_info_list = get_date_info_list(date_table)
    bidding_price_list = get_bidding_price_info_list(price_table)
    total_share_num_list = get_total_share_num_list(allocation_ratio_table)

    return [company_name] + date_info_list + bidding_price_list + total_share_num_list

def get_date_info_list(date_table):
    weekdays = {0: '(월)', 1: '(화)', 2: '(수)', 3: '(목)', 4: '(금)', 5: '(토)', 6: '(일)'}
    date_table_rows = date_table.find_all('tr')[2:]
    del date_table_rows[-2]

    temp_ipo_date_info = date_table_rows[0].find_all('td')[1].text.strip().replace('\xa0', '').replace(" ", "")
    bidding_start = temp_ipo_date_info[:10]
    bidding_finish = temp_ipo_date_info[:5] + temp_ipo_date_info[-5:]
    refund_date = date_table_rows[1].find_all('td')[1].text.strip().replace('\xa0', '').replace(" ", "")
    ipo_date = date_table_rows[2].find_all('td')[1].text.strip().replace('\xa0', '').replace(" ", "")

    # offering_start = offering_start.strftime('%Y.%m.%d') + f'({weekdays[offering_start.weekday()]})'
    # offering_finish = offering_finish.strftime('%Y.%m.%d') + f'({weekdays[offering_finish.weekday()]})'
    # refund_date = refund_date.strftime('%Y.%m.%d') + f'({weekdays[refund_date.weekday()]})'
    # ipo_date = ipo_date.strftime('%Y.%m.%d') + f'({weekdays[ipo_date.weekday()]})'

    return [bidding_start, bidding_finish, refund_date, ipo_date]

def get_bidding_price_info_list(price_table):
    price_table_rows = price_table.find_all('tr')[:-2]
    del price_table_rows[1]

    bidding_price_band = price_table_rows[0].find_all('td')[1].text.strip().replace('\xa0', '').replace(' ', '').replace('원', '').replace(',', '')
    bidding_price_band_low, bidding_price_band_high = bidding_price_band.split('~') #공모가 하단, 상단
    bidding_price = price_table_rows[1].find_all('td')[1].text.strip().replace('\xa0', '').replace(' ', '').replace('원', '').replace(',', '') #공모가격(원)
    bidding_amount = price_table_rows[2].find_all('td')[1].text.strip().replace('\xa0', '').replace(' ', '').replace('억원', '').replace(',', '') #공모규모(억)

    return [int(bidding_price_band_low), int(bidding_price_band_high), int(bidding_price), int(bidding_amount)]

def get_total_share_num_list(allocation_ratio_table):
    allocation_ratio_table_rows = allocation_ratio_table.find_all('tr')

    total_share_num = allocation_ratio_table_rows[0].find_all('td')[1].text.strip().replace('\xa0', '').replace(' ', '').replace(',', '').replace('(', '').replace(')', '')
    total_share_num, bidding_ratio = total_share_num.split('주')             #공모주식수
    bidding_ratio = int(bidding_ratio.replace('모집', '').replace('%', ''))  #신주매출 비율(%)

    return [total_share_num, bidding_ratio]

def get_shares_info_list(url):
    response = requests.get(url)
    html = response.content.decode('utf-8', 'replace')
    soup = BeautifulSoup(html, 'lxml')
    table = soup.select('table[class="view_tb"]')[2]  # 유통 가능 정보 테이블
    table_rows = table.find_all('tr')

    shares_info = []

    idx = -1
    while len(shares_info) < 6:
        tds = table_rows[idx].find_all('td')
        idx = idx - 1
        target_text = tds[0].text.strip().replace('\t', '').replace('\r\n', '')

        if target_text in ['공모후 상장주식수', '유통가능주식합계', '보호예수물량합계']:
            number_of_shares = int(tds[1].text.strip().replace('주', '').replace(',', ''))
            shares_info.append(number_of_shares)
            ratio_of_shares = float(tds[3].text.strip().replace(' ', '').replace('%', ''))
            shares_info.append(ratio_of_shares)

    # 0:주식수, 1:비율
    return shares_info

def get_demand_forecast_result_list(url):
    response = requests.get(url)
    html = response.content.decode('utf-8', 'replace')
    soup = BeautifulSoup(html, 'lxml')

    additional_info_table = soup.select('table[class="view_tb2"]')[1]
    additional_info_rows = additional_info_table.find_all('tr')
    del additional_info_rows[1]

    try:
        competition_ratio = float(additional_info_rows[0].find_all('td')[1].text.strip().replace(' ', '').replace('\xa0', '').replace(',', '').replace(':1', ''))
    except:
        print("기관 경쟁률 미표기")
        competition_ratio = 0

    try:
        commitment_ratio = float(additional_info_rows[1].find_all('td')[1].text.strip().replace(' ', '').replace('%', ''))
    except:
        print("의무보유 확약 비율 미표기")
        commitment_ratio = 0

    return [competition_ratio, commitment_ratio]

def get_underwriter_info_list(url):
    response = requests.get(url)
    html = response.content.decode('utf-8', 'replace')
    soup = BeautifulSoup(html, 'lxml')

    underwriter_table = soup.select('table[class="view_tb"]')[3]
    underwriter_rows = underwriter_table.find_all('tr')[1:]

    # 주간사 별 배정수량
    underwriter_list = []
    allocated_share_num_list = []

    for underwriter_row in underwriter_rows:
        underwriter = underwriter_row.find_all('td')[0].text.strip().replace(' ', '')
        allocated_share_num = int(underwriter_row.find_all('td')[1].text.strip().replace(' ', '').replace('주', '').replace(',', ''))

        underwriter_list.append(underwriter)
        allocated_share_num_list.append(allocated_share_num)

    return [underwriter_list, allocated_share_num_list]

def get_ipo_data_list(date):
    url_list = get_bidding_url_list(date)
    url_list += get_ipo_url_list(date)
    ipo_data_list = []
    for urls in url_list:
        returned_data_list = []
        for url in urls:
            if url:
                ipo_info = crawl_ipo_info(url)
                # null returned when ipo canceled
                if ipo_info:
                    returned_data_list.append(ipo_info)
        ipo_data_list.append(returned_data_list)

    return ipo_data_list

#Not used yet
def get_demand_forecast_band_info_list(url):
    response = requests.get(url)
    html = response.content.decode('utf-8', 'replace')
    soup = BeautifulSoup(html, 'lxml')
    demand_forecast_result_table = soup.select('table[class="view_tb"]')[1]
    demand_forecast_info_rows = demand_forecast_result_table.find_all('tr')[2:]

    price_list = []                             # 가격
    registration_num_list = []                  # 건수
    registration_ratio_list = []                # 건수비중
    amount_list = []                            # 참여수량
    amount_ratio_list = []                      # 참여수량비중

    for result_row in demand_forecast_info_rows:
        tds = result_row.find_all('td')
        price_list.append(tds[0].text.strip())
        registration_num_list.append(tds[1].text.strip())
        registration_ratio_list.append(tds[2].text.strip())
        amount_list.append(tds[3].text.strip())
        amount_ratio_list.append(tds[4].text.strip())

    return [price_list, registration_num_list, registration_ratio_list, amount_list, amount_ratio_list]

def get_allocation_detail_df(allocation_ratio_table, company_name):
    allocation_ratio_table_rows = allocation_ratio_table.find_all('tr')

    total_share_num = allocation_ratio_table_rows[0].find_all('td')[1].text.strip().replace('\xa0', '').replace(" ", "")  # 0: 공모주식수
    investor_num = allocation_ratio_table_rows[1].find_all('td')[2].text.strip().replace(" ", "")  # 1: 전문투자자
    investor_ratio = allocation_ratio_table_rows[1].find_all('td')[3].text.strip().replace(" ", "")
    employee_num = allocation_ratio_table_rows[2].find_all('td')[1].text.strip().replace(" ", "")  # 2: 우리사주조합
    employee_ratio = allocation_ratio_table_rows[2].find_all('td')[2].text.strip().replace(" ", "")
    public_num = allocation_ratio_table_rows[3].find_all('td')[1].text.strip().replace(" ", "")  # 3: 일반청약자
    public_ratio = allocation_ratio_table_rows[3].find_all('td')[2].text.strip().replace(" ", "")
    foreigner_num = allocation_ratio_table_rows[4].find_all('td')[1].text.strip().replace(" ", "")  # 4: 해외투자자
    foreigner_ratio = allocation_ratio_table_rows[4].find_all('td')[2].text.strip().replace(" ", "")

    allocation_ratio_df = pd.DataFrame({'종목명': company_name,
                                        '공모주식수': total_share_num,
                                        '전문투자자(주식수)': investor_num,
                                        '전문투자자(비율)': investor_ratio,
                                        '우리사주조합(주식수)': employee_num,
                                        '우리사주조합(비율)': employee_ratio,
                                        '일반청약자(주식수)': public_num,
                                        '일반청약자(비율)': public_ratio,
                                        '해외투자자(주식수)': foreigner_num,
                                        '해외투자자(비율)': foreigner_ratio}, index=[0])

    return allocation_ratio_df