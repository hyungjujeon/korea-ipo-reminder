import requests
import json
import re
import yaml
from selenium import webdriver
from enum import IntEnum
from datetime import datetime, timedelta
import src.column_description as cd
import os

class AcceptCommentStatus(IntEnum):
    ALLOWANCE = 1
    DISALLOWANCE = 0

def get_authorization_code():
    CLIENT_ID = os.environ.get('TISTORY_API_ID')
    KAKAO_ID = os.environ.get('KAKAO_ID')
    KAKAO_PW = os.environ.get('KAKAO_PW')

    callback_url = 'https://hzoo.tistory.com/'
    oauth_url = 'https://www.tistory.com/oauth/authorize?client_id=' + CLIENT_ID + '&redirect_uri=' + callback_url + '&response_type=code'

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    driver.implicitly_wait(10)

    driver.get(oauth_url)
    driver.find_element_by_class_name('btn_login.link_kakao_id').click()
    driver.find_element_by_name('email').send_keys(KAKAO_ID)
    driver.find_element_by_name('password').send_keys(KAKAO_PW)

    driver.find_element_by_class_name('btn_g.btn_confirm.submit').click()
    driver.implicitly_wait(10)
    driver.find_element_by_class_name('confirm').click()

    authorization_code = driver.current_url

    authorization_code = re.compile("\S+\?code=").sub('', authorization_code)
    authorization_code = re.compile("\&\S+").sub('', authorization_code)

    driver.close()

    return authorization_code

def get_access_token():
    auth_code = get_authorization_code()

    CLIENT_ID = os.environ.get('TISTORY_API_ID')
    CLIENT_PW = os.environ.get('TISTORY_API_SECRET_KEY')

    url = 'https://www.tistory.com/oauth/access_token'
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_PW,
        'redirect_uri': 'https://hzoo.tistory.com/',
        'code': auth_code,
        'grant_type': 'authorization_code'
    }
    response = requests.get(url, params=data)
    access_token = response.text.split('=')[1]

    access_token_dic = {}
    access_token_dic['access_token'] = access_token

    with open('json/tistory_token.json', 'w') as json_file:
        json.dump(access_token_dic, json_file)

    return access_token

def get_post_list():
    access_token = get_access_token()
    url = 'https://www.tistory.com/apis/post/list'
    params = {
        'access_token': access_token,
        'output': 'json',
        #https://help.theatremanager.com/theatre-manager-online-help/rest-api-output-formats
        #https://taedi.net/26
        'blogName': 'hzoo',
        'page': 1
    }

    response = requests.get(url, params=params)
    json_data = response.json()

    with open('json/tistory_post_list.json', 'w') as json_file:
        json.dump(json_data, json_file)

    recent_post_title = json_data['tistory']['item']['posts'][0]['title']
    recent_post_url = json_data['tistory']['item']['posts'][0]['postUrl']

def get_category_id():
    try:
        TISTORY_CATEGORY_IPO = str(os.environ.get('TISTORY_CATEGORY_IPO'))
        TISTORY_CATEGORY_BID = str(os.environ.get('TISTORY_CATEGORY_BID'))
        category_dic = {'IPO': TISTORY_CATEGORY_IPO, 'BID': TISTORY_CATEGORY_BID}

        return category_dic

    except:
        access_token = get_access_token()

        url = 'https://www.tistory.com/apis/category/list'
        params = {
            'access_token': access_token,
            'output': 'json',
            'blogName': 'hzoo',
        }

        response = requests.get(url, params=params)
        json_data = response.json()

        category_dic = {}
        category_dic_list = json_data['tistory']['item']['categories']

        for i, category in enumerate(category_dic_list):
            if '공모주 알리미' in category['label']:
                if category['label'] == '공모주 알리미/상장 정보':
                    category_dic['IPO'] = category['id']
                elif category['label'] == '공모주 알리미/청약 정보':
                    category_dic['BID'] = category['id']

        with open('json/tistory_category.json', 'w') as json_file:
            json.dump(category_dic, json_file)

        return category_dic

def get_bid_parameter(ipo_data_list, target_date):
    weekdays = {0: '(월)', 1: '(화)', 2: '(수)', 3: '(목)', 4: '(금)', 5: '(토)', 6: '(일)'}
    today = target_date

    title = f'💰{today.year}년 {today.month}월 {today.day}일{weekdays[today.weekday()]} 청약 정보💰'
    tag_list = ['공모주', '공모주알리미', '공모주투자', '청약정보']
    category = get_category_id()['BID']

    contents = []
    for idx, ipo_data in enumerate(ipo_data_list):
        if ipo_data:
            day_info = ''
            if idx == 0:
                day_info = f'📢오늘({today.month}/{today.day}) 청약 마감 : '
            elif idx == 1:
                if len(contents) != 0:
                    contents.append('<hr contenteditable="false" data-ke-type="horizontalRule" data-ke-style="style2">')
                day_info = f'🔔오늘({today.month}/{today.day}) 청약 시작 : '
            else:
                if len(contents) != 0:
                    contents.append('<hr contenteditable="false" data-ke-type="horizontalRule" data-ke-style="style2">')
                tomorrow = today + timedelta(days=1)
                day_info = f'📋내일({tomorrow.month}/{tomorrow.day}) 청약 시작 : '

            for data in ipo_data:
                company_name = data[cd.IpoData.COMPANY_NAME]

                bidding_start = data[cd.IpoData.BIDDING_START]
                bidding_finish = data[cd.IpoData.BIDDING_FINISH]
                refund_date = data[cd.IpoData.REFUND_DATE]
                ipo_date = data[cd.IpoData.IPO_DATE]

                bidding_start += weekdays[datetime.strptime(bidding_start, "%Y.%m.%d").weekday()]
                bidding_finish += weekdays[datetime.strptime(bidding_finish, "%Y.%m.%d").weekday()]
                refund_date += weekdays[datetime.strptime(refund_date, "%Y.%m.%d").weekday()]
                ipo_date += weekdays[datetime.strptime(ipo_date, "%Y.%m.%d").weekday()] if ipo_date else "미정"

                band_price_low = data[cd.IpoData.BAND_PRICE_LOW]
                band_price_high = data[cd.IpoData.BAND_PRICE_HIGH]
                offering_price = data[cd.IpoData.OFFERING_PRICE]
                offering_amount = data[cd.IpoData.OFFERING_AMOUNT]
                sale_available_share_num = data[cd.IpoData.SALE_AVAILABLE_SHARE_NUM]
                sale_available_share_ratio = data[cd.IpoData.SALE_AVAILABLE_SHARE_RATIO]
                sale_available_amount = int(offering_price * sale_available_share_num // 100000000)
                competition_ratio = data[cd.IpoData.COMPETITION_RATIO]
                commitment_ratio = data[cd.IpoData.COMMITMENT_RATIO]
                underwriter = data[cd.IpoData.UNDERWRITER]
                allocated_share_list = data[cd.IpoData.ALLOCATED_SHARE_NUM]
                underwriter_info = [(x[0] + '(' + format(x[1], ',d') + '주)') for x in list(zip(underwriter, allocated_share_list))]
                underwriter_info = ', '.join(underwriter_info)
                if '스팩' in company_name:
                    minimum_bidding_price = offering_price * 10
                else:
                    minimum_bidding_price = offering_price * 5

                tag_list.append(company_name)
                p_tag_style = '<p data-ke-size="size14" style="margin: 0">'

                content = '<div class="article-view"><div class="tt_article_useless_p_margin contents_style">'
                content += '<h3><b>' + day_info + str(company_name) + '</b></h3>'
                content += p_tag_style + '<b>' + f'💡균등 최소 청약증거금(10주) : ' + format(minimum_bidding_price, ',d') + '원</b></p>'
                content += p_tag_style + f'📅공모 일정 : {bidding_start} ~ {bidding_finish}' + '</p>'
                content += p_tag_style + f'📅상장일 : {ipo_date}' + '</p>'
                content += p_tag_style + f'📅환불일 : {refund_date}' + '</p>'
                content += p_tag_style + f'💰희망공모가 : ' + format(band_price_low, ",d") + '원 ~ ' + format(band_price_high, ",d") + '원</p>'
                content += p_tag_style + f'💰확정공모가 : ' + format(offering_price, ",d") + '원</p>'
                content += p_tag_style + f'💰공모규모 : ' + format(offering_amount, ',d') + '억</p>'
                content += p_tag_style + f'💰유통가능 금액(예상) : ' + format(sale_available_amount, ',d') + '억</p>'
                content += p_tag_style + f'🧾유통가능 주식 비율(예상) : {sale_available_share_ratio}' + '%</p>'
                content += p_tag_style + f'🏢수요예측 기관 경쟁률 : ' + format(int(competition_ratio), ',d') + ': 1</p>'
                content += p_tag_style + f'🏢의무보유 확약 비율(예상) : {commitment_ratio}' + '%</p>'
                content += p_tag_style + f'🚩주간사 : ' + underwriter_info + '</p>'
                content += '<p>&nbsp;</p>' * 2
                content += '</div></div>'
                contents.append(content)

    tag = ', '.join(tag_list)
    contents = ''.join(contents)

    return [title, category, tag, contents]

def get_ipo_parameter(ipo_data_list, target_date):
    weekdays = {0: '(월)', 1: '(화)', 2: '(수)', 3: '(목)', 4: '(금)', 5: '(토)', 6: '(일)'}
    today = target_date

    title = f'💰{today.year}년 {today.month}월 {today.day}일{weekdays[today.weekday()]} 상장 정보💰'
    tag_list = ['공모주', '공모주알리미', '공모주투자', '상장정보']
    category = get_category_id()['IPO']

    contents = []
    for idx, ipo_data in enumerate(ipo_data_list):
        if ipo_data:
            day_info = ''
            if idx == 0:
                day_info = f'🔔오늘({today.month}/{today.day}) 상장 : '
            else:
                if len(contents) != 0:
                    contents.append('<hr contenteditable="false" data-ke-type="horizontalRule" data-ke-style="style2">')
                tomorrow = today + timedelta(days=1)
                day_info = f'📋내일 상장({tomorrow.month}/{tomorrow.day}) : '

            try:
                for data in ipo_data:
                    company_name = data[cd.IpoData.COMPANY_NAME]

                    ipo_date = data[cd.IpoData.IPO_DATE]
                    ipo_date += weekdays[datetime.strptime(ipo_date, "%Y.%m.%d").weekday()] if ipo_date else "미정"

                    band_price_low = data[cd.IpoData.BAND_PRICE_LOW]
                    band_price_high = data[cd.IpoData.BAND_PRICE_HIGH]
                    offering_price = data[cd.IpoData.OFFERING_PRICE]
                    offering_amount = data[cd.IpoData.OFFERING_AMOUNT]
                    sale_available_share_num = data[cd.IpoData.SALE_AVAILABLE_SHARE_NUM]
                    sale_available_share_ratio = data[cd.IpoData.SALE_AVAILABLE_SHARE_RATIO]
                    sale_available_amount = int(offering_price * sale_available_share_num // 100000000)
                    competition_ratio = data[cd.IpoData.COMPETITION_RATIO]
                    commitment_ratio = data[cd.IpoData.COMMITMENT_RATIO]

                    tag_list.append(company_name)
                    p_tag_style = '<p data-ke-size="size14" style="margin: 0">'

                    content = '<div class="article-view"><div class="tt_article_useless_p_margin contents_style">'
                    content += '<h3><b>' + day_info + str(company_name) + '</b></h3>'
                    content += p_tag_style + f'📅상장일 : {ipo_date}' + '</p>'
                    content += p_tag_style + f'💰희망공모가 : ' + format(band_price_low, ",d") + '원 ~ ' + format(band_price_high, ",d") + '원</p>'
                    content += p_tag_style + f'💰확정공모가 : ' + format(offering_price, ",d") + '원</p>'
                    content += p_tag_style + f'💰공모규모 : ' + format(offering_amount, ',d') + '억</p>'
                    content += p_tag_style + f'💰유통가능 금액(확정) : ' + format(sale_available_amount, ',d') + '억</p>'
                    content += p_tag_style + f'🧾유통가능 주식 수(확정) : ' + format(sale_available_share_num, ',d') + '주</p>'
                    content += p_tag_style + f'🧾유통가능 주식 비율(확정) : {sale_available_share_ratio}' + '%</p>'
                    content += p_tag_style + f'🏢수요예측 기관 경쟁률 : ' + format(int(competition_ratio), ',d') + ': 1</p>'
                    content += p_tag_style + f'🏢의무보유 확약 비율(확정) : {commitment_ratio}' + '%</p>'
                    content += '<p>&nbsp;</p>' * 2
                    content += '</div></div>'
                    contents.append(content)
            except:
                pass

    tag = ', '.join(tag_list)
    contents = ''.join(contents)

    return [title, category, tag, contents]

def write_new_post(ipo_data_list, target_date, post_type):
    access_token = get_access_token()
    url = 'https://www.tistory.com/apis/post/write'

    param_list = []
    if len(ipo_data_list) > 2:
        if len(ipo_data_list[0]) + len(ipo_data_list[1]) + len(ipo_data_list[2]) == 0:
            return
        else:
            param_list = get_bid_parameter(ipo_data_list, target_date)
    else:
        if len(ipo_data_list[0]) + len(ipo_data_list[1]) == 0:
            return
        else:
            param_list = get_ipo_parameter(ipo_data_list, target_date)

    contents = param_list.pop()
    tag = param_list.pop()
    category = param_list.pop()
    title = param_list.pop()

    data = {
        'access_token': access_token,
        'output': 'json',
        'blogName': 'hzoo',
        'title': title,
        'content': contents,
        'visibility': '3' if post_type=='main' else '0',
        'category': category,
        'tag': tag,
        'acceptComment': AcceptCommentStatus.ALLOWANCE
    }

    response = requests.post(url, data=data)
    new_post_json = response.json()
    new_post_id = new_post_json['tistory']['postId']

    return new_post_id