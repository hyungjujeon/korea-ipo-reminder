import requests
from datetime import datetime
from bs4 import BeautifulSoup
from enum import IntEnum
import pandas as pd

class UrlTypeIndex(IntEnum):
    PUBLIC_OFFERING = 0  # 공모정보
    SHARE_HOLDER = 1  # 주주구성
    DEMAND_FORECAST = 2  # 수요예측

def get_url_list(target_date):
    year = target_date.year
    month = target_date.month

    base_url = 'http://ipostock.co.kr'
    temp_url = f'http://ipostock.co.kr/sub03/ipo04.asp?str1={year}&str2={month}'
    response = requests.get(temp_url)
    temp_html = response.content.decode('utf-8', 'replace')
    temp_soup = BeautifulSoup(temp_html, 'lxml')

    company_name_a_tag_list = temp_soup.select("a[href^='/view_pg/']")
    offering_period_td_list = temp_soup.select("td[width^='88']")
    # 테이블 열이름 td[0:3] -> 환불일, 상장일, 경쟁률 없애기
    temp_date_td_list = temp_soup.select("td[width^='60']")[3:]

    offering_before_day_url_list = []
    offering_start_url_list = []
    offering_finish_url_list = []
    ipo_before_day_url_list = []
    ipo_d_day_url_list = []

    for idx in range(0, len(offering_period_td_list)):
        offering_start_temp, offering_fin_temp = offering_period_td_list[idx].text.strip().replace('\xa0', '').split('~')
        ipo_date = temp_date_td_list[1 + 2 * idx].text.strip().replace(' ', '')

        offering_start = datetime.strptime(str(year) + '.' + offering_start_temp, "%Y.%m.%d")
        date_diff_offering_start = (target_date - offering_start).days
        is_offering_ready = True if (date_diff_offering_start >= -1 and date_diff_offering_start <= 1) else False

        try:
            ipo_start = datetime.strptime(str(year) + '.' + ipo_date, "%Y.%m.%d")
            date_diff_ipo_start = (target_date - ipo_start).days
            is_ipo_ready = True if (date_diff_ipo_start == -1 or date_diff_ipo_start == 0) else False

            url = base_url + company_name_a_tag_list[idx].get('href')

            if (not is_offering_ready) and (not is_ipo_ready):
                continue
            elif date_diff_offering_start == -1:
                offering_before_day_url_list.append(url)
            elif date_diff_offering_start == 0:
                offering_start_url_list.append(url)
            elif date_diff_offering_start == 1:
                offering_finish_url_list.append(url)
            elif date_diff_ipo_start == -1:
                ipo_before_day_url_list.append(url)
            elif date_diff_ipo_start == 0:
                ipo_d_day_url_list.append(url)
        except:
            url = base_url + company_name_a_tag_list[idx].get('href')
            if (not is_offering_ready):
                continue
            elif date_diff_offering_start == -1:
                offering_before_day_url_list.append(url)
            elif date_diff_offering_start == 0:
                offering_start_url_list.append(url)
            elif date_diff_offering_start == 1:
                offering_finish_url_list.append(url)

    return [offering_before_day_url_list, offering_start_url_list, offering_finish_url_list, ipo_before_day_url_list, ipo_d_day_url_list]

def crawl_ipo_info(url):
    url_list = []
    url_list.append(url)  # 공모정보 탭

    for page_num in [2, 5]:  # 주주구성, 수요예측 탭
        search_required_url = url.replace('_04', f'_0{page_num}')
        url_list.append(search_required_url)

    bidding_info_df = get_bidding_info_df(url_list[UrlTypeIndex.PUBLIC_OFFERING])
    company_name = bidding_info_df['종목명']
    underwriter_df = get_underwriter_df(url_list[UrlTypeIndex.PUBLIC_OFFERING], company_name)

    shares_info_df = get_shareholder_info_df(url_list[UrlTypeIndex.SHARE_HOLDER], company_name)
    ipo_info_df = pd.merge(bidding_info_df, shares_info_df)

    try:
        demand_forecast_result_df = get_demand_forecast_result_df(url_list[UrlTypeIndex.DEMAND_FORECAST], company_name)
        demand_forecast_band_info_df = get_demand_forecast_band_info_df(url_list[UrlTypeIndex.DEMAND_FORECAST], company_name)
        ipo_info_df = pd.merge(ipo_info_df, demand_forecast_result_df)
    except IndexError:
        # 청약 전날에 수요예측 결과가 늦게 표기되는 경우가 종종 있음
        print("수요예측 결과 미표기")

    return ipo_info_df

def get_bidding_info_df(url):
    response = requests.get(url)
    html = response.content.decode('utf-8', 'replace')
    soup = BeautifulSoup(html, 'lxml')
    tables = soup.select('table[class="view_tb"]')[0:3]

    company_name = soup.find('strong', {'class': 'view_tit'}).text.strip()

    date_table = tables[0]
    price_table = tables[1]
    allocation_ratio_table = tables[2]

    date_df = get_date_info_df(date_table, company_name)
    offering_price_df = get_offering_price_info_df(price_table, company_name)
    allocation_ratio_df = get_allocation_ratio_df(allocation_ratio_table, company_name)

    bidding_info_df = pd.merge(date_df, offering_price_df)
    bidding_info_df = pd.merge(bidding_info_df, allocation_ratio_df)

    return bidding_info_df

def get_date_info_df(date_table, company_name):
    date_table_rows = date_table.find_all('tr')[2:]
    del date_table_rows[-2]

    temp_ipo_date_info = date_table_rows[0].find_all('td')[1].text.strip().replace('\xa0', '').replace(" ", "")
    offering_start = temp_ipo_date_info[:10]
    offering_finish = temp_ipo_date_info[:5] + temp_ipo_date_info[-5:]
    refund_date = date_table_rows[1].find_all('td')[1].text.strip().replace('\xa0', '').replace(" ", "")
    ipo_date = date_table_rows[2].find_all('td')[1].text.strip().replace('\xa0', '').replace(" ", "")
    date_info_df = pd.DataFrame({'종목명': company_name,
                                 '공모시작': offering_start,
                                 '공모마감': offering_finish,
                                 '환불일': refund_date,
                                 '상장일': ipo_date}, index=[0])

    return date_info_df

def get_offering_price_info_df(price_table, company_name):
    price_table_rows = price_table.find_all('tr')[:-2]
    del price_table_rows[1]

    offering_price_band = price_table_rows[0].find_all('td')[1].text.strip().replace('\xa0', '').replace(' ', '').replace('원', '')
    offering_price_band_low, offering_price_band_high = offering_price_band.split('~')
    offering_price = price_table_rows[1].find_all('td')[1].text.strip().replace('\xa0', '').replace(' ', '').replace('원', '')
    offering_amount = price_table_rows[2].find_all('td')[1].text.strip().replace('\xa0', '').replace(' ', '').replace('원', '')

    offering_price_info_df = pd.DataFrame({'종목명': company_name,
                                           '공모가하단': offering_price_band_low,
                                           '공모가상단': offering_price_band_high,
                                           '공모가격': offering_price,
                                           '공모규모': offering_amount}, index=[0])

    return offering_price_info_df

def get_allocation_ratio_df(allocation_ratio_table, company_name):
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

def get_shareholder_info_df(url, company_name):
    response = requests.get(url)
    html = response.content.decode('utf-8', 'replace')
    soup = BeautifulSoup(html, 'lxml')
    table = soup.select('table[class="view_tb"]')[2]  # 유통 가능 정보 테이블
    table_rows = table.find_all('tr')

    shares_info = []

    idx = -1
    while len(shares_info) < 3:
        tds = table_rows[idx].find_all('td')
        idx = idx - 1
        target_text = tds[0].text.strip().replace('\t', '').replace('\r\n', '')

        if target_text in ['공모후 상장주식수', '유통가능주식합계', '보호예수물량합계']:
            number_of_shares = int(tds[1].text.strip().replace('주', '').replace(',', ''))
            ratio_of_shares = tds[3].text.strip().replace(' ', '')
            shares_info.append([number_of_shares, ratio_of_shares])

    shareholder_info_df = pd.DataFrame({'종목명': company_name,
                                        '공모후 상장주식수(주식수)': shares_info[0][0],
                                        '공모후 상장주식수(비율)': shares_info[0][1],
                                        '유통가능주식합계(주식수)': shares_info[1][0],
                                        '유통가능주식합계(비율)': shares_info[1][1],
                                        '보호예수물량합계(주식수)': shares_info[2][0],
                                        '보호예수물량합계(비율)': shares_info[2][1]}, index=[0])
    return shareholder_info_df

def get_demand_forecast_result_df(url, company_name):
    response = requests.get(url)
    html = response.content.decode('utf-8', 'replace')
    soup = BeautifulSoup(html, 'lxml')

    additional_info_table = soup.select('table[class="view_tb2"]')[1]
    additional_info_rows = additional_info_table.find_all('tr')
    del additional_info_rows[1]

    competition_ratio = additional_info_rows[0].find_all('td')[1].text.strip().replace(' ', '').replace('\xa0', '')
    commitment_ratio = additional_info_rows[1].find_all('td')[1].text.strip().replace(' ', '')

    demand_forecast_df = pd.DataFrame({'종목명': company_name,
                                       '기관경쟁률': competition_ratio,
                                       '의무보유확약비율': commitment_ratio}, index=[0])
    return demand_forecast_df

def get_underwriter_df(url, company_name):
    response = requests.get(url)
    html = response.content.decode('utf-8', 'replace')
    soup = BeautifulSoup(html, 'lxml')

    underwriter_table = soup.select('table[class="view_tb"]')[3]
    underwriter_rows = underwriter_table.find_all('tr')[1:]

    # 주간사 별 배정수량
    underwriter_name_list = []
    underwriter_quantity_list = []

    for underwriter_row in underwriter_rows:
        underwriter_name_list.append(underwriter_row.find_all('td')[0].text.strip().replace(" ", ""))
        underwriter_quantity_list.append(underwriter_row.find_all('td')[1].text.strip().replace(" ", ""))

    return pd.DataFrame({'종목명': [company_name] * len(underwriter_rows), '주간사': underwriter_name_list, '배정수량': underwriter_quantity_list})

def get_demand_forecast_band_info_df(url, company_name):
    response = requests.get(url)
    html = response.content.decode('utf-8', 'replace')
    soup = BeautifulSoup(html, 'lxml')
    demand_forecast_result_table = soup.select('table[class="view_tb"]')[1]
    demand_forecast_info_rows = demand_forecast_result_table.find_all('tr')[2:]

    price_list = []
    registration_num_list = []
    registration_ratio_list = []
    amount_list = []
    amount_ratio_list = []

    for result_row in demand_forecast_info_rows:
        tds = result_row.find_all('td')
        price_list.append(tds[0].text.strip())
        registration_num_list.append(tds[1].text.strip())
        registration_ratio_list.append(tds[2].text.strip())
        amount_list.append(tds[3].text.strip())
        amount_ratio_list.append(tds[4].text.strip())

    demand_forecast_band_info_df = pd.DataFrame({'종목명': [company_name] * len(price_list),
                                                 '가격': price_list,
                                                 '건수': registration_num_list,
                                                 '건수비중': registration_ratio_list,
                                                 '참여수량': amount_list,
                                                 '참여수량비중': amount_ratio_list, })
    return demand_forecast_band_info_df

def get_ipo_data_list(date):
    url_list = get_url_list(date)
    ipo_data_list = []
    for urls in url_list:
        returned_data_list = []
        for url in urls:
            if url:
                returned_data_list.append(crawl_ipo_info(url))
        ipo_data_list.append(returned_data_list)

    return ipo_data_list