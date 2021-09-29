import time
import requests
import json
import yaml
from datetime import datetime
import src.column_description as cd

def create_token(code):
        with open('../config.yaml') as f:
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

        with open('json/kakao_token.json', 'w') as fp:
            json.dump(tokens, fp)

def refresh_token():
    with open('json/kakao_token.json', 'r') as kt_json:
        kakao_token = json.load(kt_json)
    with open('../config.yaml') as f:
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

    with open('json/refresh_kakao_token.json', 'w') as fp:
        json.dump(refresh_kakao_token, fp)

def print_hello_world():
    refresh_token()

    with open('json/refresh_kakao_token.json', 'r') as tk:
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

def get_bid_contents(ipo_data_list):
    today = datetime.now()

    contents = f'📢청약정보📢\n'
    contents += f'🗓️{today.year}년 {today.month}월 {today.day}일🗓\n'

    for idx, ipo_data in enumerate(ipo_data_list):
        if ipo_data:
            if idx == 0:
                contents += '\n🔥오늘 청약 마감 종목'
            elif idx == 1:
                contents += '\n🔥오늘 청약 시작 종목'
            elif idx == 2:
                contents += '\n🔥내일 청약 예정 종목'
            for data in ipo_data:
                data = data.values.tolist()[0]
                company_name = data[cd.IpoData.COMPANY_NAME]
                offering_price = data[cd.IpoData.OFFERING_PRICE]

                contents += '\n  📊 ' + company_name + f'(공모가: {offering_price})'

            contents += '\n'

    return contents

def get_ipo_contents(ipo_data_list):
    today = datetime.now()

    contents = f'📢상장정보📢\n'
    contents += f'🗓️{today.year}년 {today.month}월 {today.day}일🗓\n'

    for idx, ipo_data in enumerate(ipo_data_list):
        if ipo_data:
            if idx == 0:
                contents += '\n🔥오늘 상장 종목'
            elif idx == 1:
                contents += '\n🔥내일 상장 종목'
            for data in ipo_data:
                data = data.values.tolist()[0]
                company_name = data[cd.IpoData.COMPANY_NAME]
                offering_price = data[cd.IpoData.OFFERING_PRICE]

                contents += '\n  📊 ' + company_name + f'(공모가: {offering_price})'

            contents += '\n'

    return contents

def alarm_text_message(ipo_data_list, post_id):
    contents = ''
    if len(ipo_data_list) > 2:
        if len(ipo_data_list[0]) + len(ipo_data_list[1]) + len(ipo_data_list[2]) == 0:
            return
        else:
            contents = get_bid_contents(ipo_data_list)
    else:
        if len(ipo_data_list[0]) + len(ipo_data_list[1]) == 0:
            return
        else:
            contents = get_ipo_contents(ipo_data_list)

    refresh_token()

    with open('json/refresh_kakao_token.json', 'r') as tk:
        kakao_token = json.load(tk)

    url = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'
    headers = {'Authorization': 'Bearer ' + kakao_token['access_token']}
    data = {'template_object': json.dumps({'object_type': 'text',
                                           'text': contents,
                                           'link': {'web_url': 'https://hzoo.tistory.com/' + str(post_id),
                                                    'mobile_web_url': 'https://hzoo.tistory.com/m/' + str(post_id)
                                                    },
                                           'button_title': '더 자세한 정보'
                                           })}

    response = requests.post(url, headers=headers, data=data)
    if response.json().get('result_code') == 0:
        print('메시지를 성공적으로 보냈습니다.')
    else:
        print('메시지를 성공적으로 보내지 못했습니다. 오류메시지 : ' + str(response.json()))

def send_template_message():
    refresh_token()

    with open('json/refresh_kakao_token.json', 'r') as tk:
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
    with open('json/refresh_kakao_token.json', 'r') as tk:
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