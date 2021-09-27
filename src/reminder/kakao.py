import time
import requests
import json
import os
import yaml
from datetime import datetime
from datetime import timedelta
import pandas as pd
import numpy as np
import src.crawler.from_ipostock as crawler_ipostock

# def get_response_code(login_info):
#     with open('../../config.yaml') as f:
#         CLIENT_ID = yaml.load(f, Loader=yaml.FullLoader)['KAKAO_REST_API_KEY']
#     driver = webdriver.Chrome('../../chromedriver.exe'))
#     driver.implicitly_wait(3)
#     driver.get('https://kauth.kakao.com/oauth/authorize?client_id=' + CLIENT_ID + '&redirect_uri=https://hzoo.tistory.com&response_type=code')
#
#     driver.find_element_by_name('email').send_keys(KAKAO_ID)
#     driver.find_element_by_name('password').send_keys(KAKAO_PW)
#
#     requests = driver.find_element_by_class_name('btn_g.btn_confirm.submit').click()
#
#     for request in requests:
#         if request.response
#
#     button = driver.find_element_by_xpath("//*[@id='login-form']/fieldset/div[8]/button[1]")
#     # button.click()

def create_token(code):
        with open('../../config.yaml') as f:
            CLIENT_ID = yaml.load(f, Loader=yaml.FullLoader)['KAKAO_REST_API_KEY']

        url = 'https://kauth.kakao.com/oauth/token'
        data = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'redirect_uri': 'https://hzoo.tistory.com',
            'code': code
        }
        response = requests.post(url, data=data)
        tokens = response.json()

        with open('../../kakao_token.json', 'w') as fp:
            json.dump(tokens, fp)

def refresh_token():
    with open('../../kakao_token.json', 'r') as kt_json:
        kakao_token = json.load(kt_json)
    with open('../../config.yaml') as f:
        CLIENT_ID = yaml.load(f, Loader=yaml.FullLoader)['KAKAO_REST_API_KEY']

    refresh_token = kakao_token['refresh_token']
    url = 'https://kauth.kakao.com/oauth/token'
    data = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'refresh_token': refresh_token,
    }

    response = requests.post(url, data=data)
    refresh_kakao_token = response.json()

    with open('../../refresh_kakao_token.json', 'w') as fp:
        json.dump(refresh_kakao_token, fp)

def print_hello_world():
    refresh_token()

    with open('../../refresh_kakao_token.json', 'r') as tk:
        kakao_token = json.load(tk)

    url = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'
    headers = {'Authorization': 'Bearer ' + kakao_token['access_token']}
    data = {'template_object': json.dumps({'object_type': 'text',
                                           'text': 'Hello, world!',
                                           'link': {'web_url': 'https://hzoo.tistory.com/m'}})}

    response = requests.post(url, headers=headers, data=data)
    if response.json().get('result_code') == 0:
        print('메시지를 성공적으로 보냈습니다.')
    else:
        print('메시지를 성공적으로 보내지 못했습니다. 오류메시지 : ' + str(response.json()))

def send_template_message():
    refresh_token()

    with open('../../refresh_kakao_token.json', 'r') as tk:
        kakao_token = json.load(tk)

    url = 'https://kapi.kakao.com/v2/api/talk/memo/send'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Bearer ' + kakao_token['access_token']}
    data = 'template_id=59335'

    print(data)

    response = requests.post(url, headers=headers, data=data)
    if response.json().get('result_code') == 0:
        print('메시지를 성공적으로 보냈습니다.')
    else:
        print('메시지를 성공적으로 보내지 못했습니다. 오류메시지 : ' + str(response.json()))


def get_header_title_text(index):
    header_title_dict = {
        0 : '<내일 청약 예정 종목>',
        1  : '<오늘 청약 시작 종목>',
        2 : '<오늘 청약 마감 종목>',
        3 : '<내일 상장 예정 종목>',
        4 : '<오늘 상장 종목>'
    }
    try:
        header_text = header_title_dict[index]
        return header_text
    except Exception as e:
        print(e)
        print("Wrong Index")

def alarm_message(ipo_data_list):
    refresh_token()
    with open('../../refresh_kakao_token.json', 'r') as tk:
        kakao_token = json.load(tk)

    url = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'

    for idx, ipo_data in enumerate(ipo_data_list):
        if ipo_data:
            contents = []
            for data in ipo_data:
                data = data.values.tolist()[0]
                content = {
                    "title": data[0],
                    "description": "청약시작" + data[1],
                    "image_url": '',
                    "link": {
                        "web_url": "https://hzoo.tistory.com",
                        "mobile_web_url": "https://hzoo.tistory.com/m"
                    }
                }
                contents.append(content)

            title = get_header_title_text(idx)

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': 'Bearer ' + kakao_token['access_token']}
            template_object = {
                "object_type": "list",
                "header_title": title,
                "header_link": {
                    "web_url": "https://hzoo.tistory.com",
                    "mobile_web_url": "https://hzoo.tistory.com/m"
                },
                "contents": contents,
                "buttons": [
                    {
                        "title": "자세히 보기",
                        "link": {
                            "web_url": "https://hzoo.tistory.com",
                            "mobile_web_url": "https://hzoo.tistory.com/m"
                        }
                    }
                ],
            }

            data = {
                "template_object" : json.dumps(template_object)
            }

            print(data)
            response = requests.post(url, headers=headers, data=data)
            if response.json().get('result_code') == 0:
                print('메시지를 성공적으로 보냈습니다.')
            else:
                print('메시지를 성공적으로 보내지 못했습니다. 오류메시지 : ' + str(response.json()))

            time.sleep(5)

# response_code = get_response_code()
# response_code = 'abc'

#create_token(response_code)
#refresh_token()
#print_hello_world()

#send_template_message()

#Test when 21/09/13
# today = datetime.now()
# target = today + timedelta(days=-11)
# ipo_data_list = crawler_ipostock.get_ipo_data_list(target)
# alarm_message(ipo_data_list)