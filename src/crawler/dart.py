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

def crawl_bidding_result(url):
    driver = webdriver.Chrome('../../chromedriver')
    driver.get(url)
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