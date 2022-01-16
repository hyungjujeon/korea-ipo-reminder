import re
import time
import platform
import requests
from enum import IntEnum
from datetime import datetime
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
from selenium import webdriver


def get_report_url(company_name):
    driver = webdriver.Chrome('../../chromedriver')
    default_url = 'https://dart.fss.or.kr'
    driver.get(default_url + '/main.do')
    driver.implicitly_wait(20)
    driver.find_element_by_id('li_03').click()
    driver.find_element_by_id('totalChoice_03').click()
    driver.find_element_by_id('textCrpNm2').send_keys(company_name)
    driver.find_element_by_class_name('btnSearch').click()
    time.sleep(1)

    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    tbody = soup.find('tbody', {'id': 'tbody'})
    trs = tbody.find_all('tr')
    for tr in trs:
        target_td = tr.find_all('td')[2]
        report_name = target_td.find('a').text.strip()
        if report_name == '증권발행실적보고서':
            report_url = default_url + target_td.find('a').get('href').strip()
            driver.quit()
            return report_url


def get_target_subtitle_url(report_url):
    driver = webdriver.Chrome('../../chromedriver')
    target_subtitle_url = []
    driver.get(report_url)
    leaves = driver.find_elements_by_class_name('jstree-anchor')
    for leaf in leaves:
        if leaf.text.strip() == 'Ⅰ. 발행개요' or leaf.text.strip() == 'Ⅱ. 청약 및 배정에 관한 사항':
            leaf.click()
            html_overview = driver.page_source
            soup = BeautifulSoup(html_overview, 'lxml')
            src = soup.find('iframe', {'id': 'ifrm'}).get('src')
            target_subtitle_url.append('https://dart.fss.or.kr' + src)
        else:
            if len(target_subtitle_url) >= 2:
                driver.quit()
                return target_subtitle_url


def crawl_overview(url):
    driver = webdriver.Chrome('../../chromedriver')
    driver.get(url)

    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('table')

    tds = table.find_all('td')
    data = [td.text for td in tds]

    driver.quit()
    return data


def crawl_underwriter_table(table):
    rows = table.find('tbody').find_all('tr')
    underwriter_list = []
    allocated_stock_num_list = []
    allocated_stock_ratio_list = []
    total_stock_num = int(rows[-1].find_all('td')[1].text.replace(',', ''))

    for i in range(len(rows) - 1):
        tds = rows[i].find_all('td')
        underwriter = tds[0].text.replace('(주)', '').strip()
        allocated_stock_num = int(tds[1].text.replace(',', ''))

        underwriter_list.append(underwriter)
        allocated_stock_num_list.append(allocated_stock_num)
        allocated_stock_ratio_list.append(allocated_stock_num / total_stock_num)

    return [', '.join(underwriter_list), ', '.join(allocated_stock_num_list), ', '.join(allocated_stock_ratio_list)]


def crawl_bidding_result_table(table):
    rows = table.find('tbody').find_all('tr')
    # 구분
    institution_list = []
    # 최초 배정
    initial_allocated_stock_num_list = []
    # 최종 배정
    final_allocated_stock_num_list = []
    public_bidding_result = None

    for i in range(len(rows) - 1):
        tds = rows[i].find_all('td')
        institution = tds[0].text.replace('(주)', '').strip()
        initial_allocated_stock_num = int(tds[1].text.replace(',', ''))
        final_allocated_stock_num = int(tds[8].text.replace(',', ''))

        if '일반' in institution:
            public_bidding_num = int(tds[3].text.replace(',', '')) # 일반 투자자 청약 건수
            public_bidding_quantity = int(tds[4].text.replace(',', '')) # 일반 투자자 청약 수량
            public_ratio = public_bidding_quantity / final_allocated_stock_num # 비례 경쟁률
            public_bidding_result = [public_bidding_num, public_bidding_quantity, public_ratio]

        institution_list.append(institution)
        initial_allocated_stock_num_list.append(initial_allocated_stock_num)
        final_allocated_stock_num_list.append(final_allocated_stock_num)

    return [', '.join(institution_list), ', '.join(initial_allocated_stock_num_list),
            ', '.join(final_allocated_stock_num_list)] + public_bidding_result


def crawl_bidding_result(url):
    driver = webdriver.Chrome('../../chromedriver')
    driver.get(url)

    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    tables = soup.find_all('table', {'border': '1'})

    underwriter_table_data = crawl_underwriter_table(tables[1])
    bidding_result_table_data = crawl_bidding_result_table(tables[2])

    for table in tables:
        try:
            cols = [col.text for col in table.find_all('th')]
            print(cols)
        except:
            pass

    driver.quit()
    # html = driver.page_source
    # soup = BeautifulSoup(html, 'lxml')
    # tbody = soup.find('tbody', {'id': 'tbody'})


def crawl_after_bid(company_name):
    report_url = get_report_url(company_name)
    subtitle_url_list = get_target_subtitle_url(report_url)
    overview_data = crawl_overview(subtitle_url_list[0])
    bidding_result_data = crawl_bidding_result(subtitle_url_list[1])


# company = '모비릭스'
company = 'SK바이오사이언스'
crawl_after_bid(company)