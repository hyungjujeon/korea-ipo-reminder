import requests
import json
import re
import yaml
from selenium import webdriver
from enum import IntEnum
from datetime import datetime, timedelta
import src.column_description as cd

class AcceptCommentStatus(IntEnum):
    ALLOWANCE = 1
    DISALLOWANCE = 0

def get_authorization_code():
    with open('../config.yaml') as f:
        TISTORY_INFO = yaml.load(f, Loader=yaml.FullLoader)
        CLIENT_ID = TISTORY_INFO['TISTORY_API_ID']
        KAKAO_ID = TISTORY_INFO['KAKAO_ID']
        KAKAO_PW = TISTORY_INFO['KAKAO_PW']

    callback_url = 'https://hzoo.tistory.com/'
    oauth_url = 'https://www.tistory.com/oauth/authorize?client_id=' + CLIENT_ID + '&redirect_uri=' + callback_url + '&response_type=code'
    driver = webdriver.Chrome('../../chromedriver')
    driver.implicitly_wait(3)

    driver.get(oauth_url)
    driver.find_element_by_class_name('btn_login.link_kakao_id').click()
    driver.find_element_by_name('email').send_keys(KAKAO_ID)
    driver.find_element_by_name('password').send_keys(KAKAO_PW)

    driver.find_element_by_class_name('btn_g.btn_confirm.submit').click()
    driver.find_element_by_class_name('confirm').click()

    authorization_code = driver.current_url

    authorization_code = re.compile("\S+\?code=").sub('', authorization_code)
    authorization_code = re.compile("\&\S+").sub('', authorization_code)

    driver.close()

    return authorization_code

def get_access_token():
    try:
        with open('json/tistory_token.json', 'r') as f:
            json_data = json.load(f)

        access_token = json_data['access_token']
        return access_token

    except:
        auth_code = get_authorization_code()

        with open('../config.yaml') as f:
            TISTORY_INFO = yaml.load(f, Loader=yaml.FullLoader)
            CLIENT_ID = TISTORY_INFO['TISTORY_API_ID']
            CLIENT_PW = TISTORY_INFO['TISTORY_API_SECRET_KEY']

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
        with open('json/tistory_category.json', 'r') as f:
            category_dic = json.load(f)

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

def get_bid_parameter(ipo_data_list):
    today = datetime.now()

    title = f'💰{today.year}년 {today.month}월 {today.day}일 청약 정보💰'
    tag_list = ['공모주', '공모주알리미', '공모주투자', '청약정보']
    category = get_category_id()['BID']

    contents = []
    for idx, ipo_data in enumerate(ipo_data_list):
        if ipo_data:
            day_info = ''
            if idx == 0:
                tomorrow = today + timedelta(days=1)
                day_info = f'📢오늘({today.month}/{today.day}) 청약 마감 : '
            elif idx == 1:
                if len(contents) != 0:
                    contents.append('<hr contenteditable="false" data-ke-type="horizontalRule" data-ke-style="style2">')
                day_info = f'🔔오늘({today.month}/{today.day}) 청약 시작 : '
            else:
                if len(contents) != 0:
                    contents.append('<hr contenteditable="false" data-ke-type="horizontalRule" data-ke-style="style2">')
                day_info = f'📋내일({tomorrow.month}/{tomorrow.day}) 청약 시작 : '

            try:
                for data in ipo_data:
                    data = data.values.tolist()[0]
                    company_name = data[cd.IpoData.COMPANY_NAME]
                    bidding_start = data[cd.IpoData.BIDDING_START]
                    bidding_finish = data[cd.IpoData.BIDDING_FINISH]
                    refund_date = data[cd.IpoData.REFUND_DATE]
                    ipo_date = data[cd.IpoData.IPO_DATE]
                    ipo_date = ipo_date if ipo_date else "미정"
                    band_price_low = data[cd.IpoData.BAND_PRICE_LOW]
                    band_price_high = data[cd.IpoData.BAND_PRICE_HIGH]
                    offering_price = data[cd.IpoData.OFFERING_PRICE]
                    offering_amount = data[cd.IpoData.OFFERING_AMOUNT]
                    sale_available_share_num = data[cd.IpoData.SALE_AVAILABLE_SHARE_NUM]
                    sale_available_share_ratio = data[cd.IpoData.SALE_AVAILABLE_SHARE_RATIO]
                    sale_available_amount = int(int(offering_price.replace(',', '')) * sale_available_share_num // 100000000)
                    competition_ratio = data[cd.IpoData.COMPETITION_RATIO]
                    commitment_ratio = data[cd.IpoData.COMMITMENT_RATIO]
                    underwriter = data[cd.IpoData.UNDERWRITER]
                    minimum_bidding_price = int(offering_price.replace(',', '')) * 5

                    tag_list.append(company_name)
                    content = '<div class="article-view"><div class="tt_article_useless_p_margin contents_style">'
                    content += '<h3><b>' + day_info + str(company_name) + '</b></h3>'
                    content += '<p data-ke-size="size14" style="margin: 0"><b>' + f'💡균등 최소 청약증거금(10주) : ' + format(minimum_bidding_price, ',d') + '원</b></p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'📅공모 일정 : {bidding_start}~{bidding_finish}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'📅상장일 : {ipo_date}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'📅환불일 : {refund_date}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'💰희망공모가 : {band_price_low}~{band_price_high}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'💰확정공모가 : {offering_price}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'💰공모규모 : {offering_amount}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'💰유통가능 금액(예상) : ' + format(sale_available_amount, ',d') + '억</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'🧾유통가능 주식 비율(예상) : {sale_available_share_ratio}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'🏢수요예측 기관 경쟁률 : {competition_ratio}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'🏢의무보유 확약 비율(예상) : {commitment_ratio}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'🚩주간사 : {underwriter}' + '</p>'
                    content += '<p>&nbsp;</p>' * 2
                    content += '</div></div>'
                    contents.append(content)
            except:
                pass

    tag = ', '.join(tag_list)
    contents = ''.join(contents)

    return [title, category, tag, contents]

def get_ipo_parameter(ipo_data_list):
    today = datetime.now()

    title = f'💰{today.year}년 {today.month}월 {today.day}일 상장 정보💰'
    tag_list = ['공모주', '공모주알리미', '공모주투자', '상장정보']
    category = get_category_id()['IPO']

    contents = []
    for idx, ipo_data in enumerate(ipo_data_list):
        if ipo_data:
            day_info = ''
            if idx == 0:
                tomorrow = today + timedelta(days=1)
                day_info = f'🔔오늘({today.month}/{today.day}) 상장 : '
            else:
                if len(contents) != 0:
                    contents.append('<hr contenteditable="false" data-ke-type="horizontalRule" data-ke-style="style2">')
                day_info = f'📋내일 상장({tomorrow.month}/{tomorrow.day}) : '

            try:
                for data in ipo_data:
                    data = data.values.tolist()[0]
                    company_name = data[cd.IpoData.COMPANY_NAME]
                    ipo_date = data[cd.IpoData.IPO_DATE]
                    ipo_date = ipo_date if ipo_date else "미정"
                    band_price_low = data[cd.IpoData.BAND_PRICE_LOW]
                    band_price_high = data[cd.IpoData.BAND_PRICE_HIGH]
                    offering_price = data[cd.IpoData.OFFERING_PRICE]
                    offering_amount = data[cd.IpoData.OFFERING_AMOUNT]
                    sale_available_share_num = data[cd.IpoData.SALE_AVAILABLE_SHARE_NUM]
                    sale_available_share_ratio = data[cd.IpoData.SALE_AVAILABLE_SHARE_RATIO]
                    sale_available_amount = int(int(offering_price.replace(',', '')) * sale_available_share_num // 100000000)
                    competition_ratio = data[cd.IpoData.COMPETITION_RATIO]
                    commitment_ratio = data[cd.IpoData.COMMITMENT_RATIO]

                    tag_list.append(company_name)
                    content = '<div class="article-view"><div class="tt_article_useless_p_margin contents_style">'
                    content += '<h3><b>' + day_info + str(company_name) + '</b></h3>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'📅상장일 : {ipo_date}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'💰희망공모가 : {band_price_low}~{band_price_high}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'💰확정공모가 : {offering_price}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'💰공모규모 : {offering_amount}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'💰유통가능 금액(확정) : ' + format(sale_available_amount, ',d') + '억</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'🧾유통가능 주식 수(확정) : ' + format(sale_available_share_num, ',d') + '주</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'🧾유통가능 주식 비율(확정) : {sale_available_share_ratio}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'🏢수요예측 기관 경쟁률 : {competition_ratio}' + '</p>'
                    content += '<p data-ke-size="size14" style="margin: 0">' + f'🏢의무보유 확약 비율(확정) : {commitment_ratio}' + '</p>'
                    content += '<p>&nbsp;</p>' * 2
                    content += '</div></div>'
                    contents.append(content)
            except:
                pass

    tag = ', '.join(tag_list)
    contents = ''.join(contents)

    return [title, category, tag, contents]

def write_new_post(ipo_data_list):
    access_token = get_access_token()
    url = 'https://www.tistory.com/apis/post/write'

    param_list = []
    if len(ipo_data_list) > 2:
        param_list = get_bid_parameter(ipo_data_list)
    else:
        param_list = get_ipo_parameter(ipo_data_list)

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
        'visibility': '3',
        'category': category,
        'tag': tag,
        'acceptComment': AcceptCommentStatus.ALLOWANCE
    }

    response = requests.post(url, data=data)
    new_post_json = response.json()
    new_post_id = new_post_json['tistory']['postId']

    return new_post_id