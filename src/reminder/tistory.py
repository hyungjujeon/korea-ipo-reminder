import os
import re
import json
import yaml
import platform
import requests
from selenium import webdriver
from src.utils import ConvertBiddingData, ConvertIpoReadyData, TextContent

weekdays = {0: '(월)', 1: '(화)', 2: '(수)', 3: '(목)', 4: '(금)', 5: '(토)', 6: '(일)'}


class RequiredParam:
    def __init__(self):
        self.access_token = get_access_token()
        self.url = 'https://www.tistory.com/apis/'


class WritePostParam(RequiredParam):
    def __init__(self, post_type):
        super().__init__()
        self.url += 'post/write'
        self.output_type = 'json'
        self.blog_name = 'hzoo'
        self.title = None
        self.content = None
        self.visibility = Visibility.public if post_type == 'public' else Visibility.private
        self.category = None
        self.tag = None
        self.accept_comment = AcceptComment.allow


def get_authorization_code():
    driver = None

    if platform.system() == 'Linux':
        client_id = os.environ.get('TISTORY_API_ID')
        kakao_id = os.environ.get('KAKAO_ID')
        kakao_pw = os.environ.get('KAKAO_PW')

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    else:
        with open('../config.yaml') as f:
            tistory_info = yaml.load(f, Loader=yaml.FullLoader)
            client_id = tistory_info['TISTORY_API_ID']
            kakao_id = tistory_info['KAKAO_ID']
            kakao_pw = tistory_info['KAKAO_PW']

        driver = webdriver.Chrome('../../chromedriver')

    callback_url = 'https://hzoo.tistory.com/'
    oauth_url = 'https://www.tistory.com/oauth/authorize?client_id=' + client_id + '&redirect_uri=' + callback_url + '&response_type=code'

    driver.implicitly_wait(10)
    driver.get(oauth_url)
    driver.find_element_by_class_name('btn_login.link_kakao_id').click()
    driver.find_element_by_name('email').send_keys(kakao_id)
    driver.find_element_by_name('password').send_keys(kakao_pw)

    driver.find_element_by_class_name('btn_g.btn_confirm.submit').click()
    driver.implicitly_wait(10)
    driver.find_element_by_class_name('confirm').click()

    authorization_code = driver.current_url

    authorization_code = re.compile(r"\S+\?code=").sub('', authorization_code)
    authorization_code = re.compile(r"\&\S+").sub('', authorization_code)

    driver.close()

    return authorization_code


def get_access_token():
    try:
        if platform.system() == 'Linux':
            access_token = os.environ.get('TISTORY_ACCESS_TOKEN')
            return access_token
        else:
            with open('json/tistory_token.json', 'r') as f:
                json_data = json.load(f)
            access_token = json_data['access_token']

            return access_token
    except Exception as e:
        print(f'error occurred when get access token : {e}')
        auth_code = get_authorization_code()

        if platform.system() == 'Linux':
            client_id = os.environ.get('TISTORY_API_ID')
            client_pw = os.environ.get('TISTORY_API_SECRET_KEY')
        else:
            with open('../config.yaml') as f:
                tistory_info = yaml.load(f, Loader=yaml.FullLoader)
                client_id = tistory_info['TISTORY_API_ID']
                client_pw = tistory_info['TISTORY_API_SECRET_KEY']

        url = 'https://www.tistory.com/oauth/access_token'
        data = {
            'client_id': client_id,
            'client_secret': client_pw,
            'redirect_uri': 'https://hzoo.tistory.com/',
            'code': auth_code,
            'grant_type': 'authorization_code'
        }
        response = requests.get(url, params=data)
        access_token = response.text.split('=')[1]

        access_token_dic = {'access_token': access_token}

        with open('json/tistory_token.json', 'w') as json_file:
            json.dump(access_token_dic, json_file)

        return access_token


# not yet developed
def get_post_list():
    access_token = get_access_token()
    url = 'https://www.tistory.com/apis/post/list'
    params = {
        'access_token': access_token,
        'output': 'json',
        'blogName': 'hzoo',
        'page': 1
    }

    response = requests.get(url, params=params)
    json_data = response.json()

    with open('json/tistory_post_list.json', 'w') as json_file:
        json.dump(json_data, json_file)

    recent_post_title = json_data['tistory']['item']['posts'][0]['title']
    recent_post_url = json_data['tistory']['item']['posts'][0]['postUrl']


class Visibility:
    private = '0'
    protected = '1'
    public = '3'


class AcceptComment:
    prohibit = '0'
    allow = '1'


class TistoryPost(TextContent):
    def __init__(self, ipo_data_list_of_lists, target_date, post_type):
        super().__init__(ipo_data_list_of_lists, target_date, post_type)

        self.new_post_id = None
        self.tag_list = None
        self.tistory_category_id = None

        self.set_init_tag()
        self.access_token = get_access_token()

        if len(ipo_data_list_of_lists) == 3:
            self.category = '청약'
            self.add_tag('청약정보')
        elif len(ipo_data_list_of_lists) == 2:
            self.category = '상장'
            self.add_tag('상장정보')

        self.set_title()
        self.set_tistory_category_id()
        self.set_subtitle_list()
        self.set_content()

    def set_init_tag(self):
        self.tag_list = ['공모주', '공모주알리미', '공모주투자']

    def add_tag(self, tag_name):
        self.tag_list.append(tag_name)

    def set_tistory_category_id(self):
        if platform.system() == 'Linux':
            tistory_category_ipo = str(os.environ.get('TISTORY_CATEGORY_IPO'))
            tistory_category_bid = str(os.environ.get('TISTORY_CATEGORY_BID'))
            category_dic = {'상장': tistory_category_ipo, '청약': tistory_category_bid}

            self.tistory_category_id = category_dic[self.category]
        else:
            try:
                with open('json/tistory_category.json', 'r') as f:
                    category_dic = json.load(f)

                    self.tistory_category_id = category_dic[self.category]

            except Exception as e:
                print(f'error occurred when load tistory category json : {e}')
                access_token = self.access_token

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
                            category_dic['상장'] = category['id']
                        elif category['label'] == '공모주 알리미/청약 정보':
                            category_dic['청약'] = category['id']

                with open('json/tistory_category.json', 'w') as json_file:
                    json.dump(category_dic, json_file)

                self.tistory_category_id = category_dic[self.category]

    def write_new_post(self):
        param = WritePostParam(self.post_type)

        if any(self.ipo_data_list_of_lists):
            param.content = self.get_content()
            param.tag = self.get_tag()
            param.category = self.get_post_category()
            param.title = self.title

        else:
            return

        data = {
            'access_token': param.access_token,
            'output': param.output_type,
            'blogName': param.blog_name,
            'title': param.title,
            'content': param.content,
            'visibility': param.visibility,
            'category': param.category,
            'tag': param.tag,
            'acceptComment': param.accept_comment
        }

        response = requests.post(param.url, data=data)
        new_post_json = response.json()
        self.new_post_id = new_post_json['tistory']['postId']

    def set_content(self):
        data_type_separator = '<hr contenteditable="false" data-ke-type="horizontalRule" data-ke-style="style2">'
        subtitle_style_open_tag = '<div class="article-view"><div class="tt_article_useless_p_margin contents_style">'
        subtitle_style_close_tag = '</div></div>'
        subtitle_text_style_open_tag = '<h3><b>'
        subtitle_text_style_close_tag = '</b></h3>'
        content_separator = '<p>&nbsp;</p>'

        content_list = []
        for idx, ipo_data_list in enumerate(self.ipo_data_list_of_lists):
            try:
                if ipo_data_list:
                    if len(content_list) != 0:
                        content_list.append(data_type_separator)
                    subtitle = self.subtitle_list[idx]

                    for ipo_data in ipo_data_list:
                        content = subtitle_style_open_tag
                        content += subtitle_text_style_open_tag + subtitle
                        content += ipo_data.company_name + subtitle_text_style_close_tag

                        if self.category == '청약':
                            content += ConvertBiddingData(ipo_data).get_tistory_content()
                        elif self.category == '상장':
                            content += ConvertIpoReadyData(ipo_data).get_tistory_content()

                        content += subtitle_style_close_tag + content_separator
                        self.tag_list.append(ipo_data.company_name)
                        content_list.append(content)

            except Exception as e:
                print(f'Tistory content 생성 중 오류 : {e}')

        self.content = ''.join(content_list)

    def get_content(self):
        return self.content

    def get_tag(self):
        return ', '.join(self.tag_list)

    def get_post_category(self):
        return self.tistory_category_id