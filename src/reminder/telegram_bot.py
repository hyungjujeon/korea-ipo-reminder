import os
import yaml
import platform
import telegram
import requests
from src.utils import ConvertBiddingData, ConvertIpoReadyData, TextContent


class TelegramAPI:
    def __init__(self):
        self.api_key = None
        self.main_chat_id = None
        self.test_chat_id = None
        self.set_api_key()
        self.set_main_chat_id()
        self.set_test_chat_id()

    def set_api_key(self):
        if platform.system() == 'Linux':
            self.api_key = os.environ.get('TELEGRAM_KEY')
        else:
            with open('../config.yaml') as f:
                key_info = yaml.load(f, Loader=yaml.FullLoader)
                telegram_key = key_info['TELEGRAM_KEY']

            self.api_key = telegram_key

    def get_bot(self):
        return telegram.Bot(token=self.api_key)

    def get_bot_id(self, bot: telegram.Bot):
        me = bot.getMe()
        bot_id = me['id']

        return bot_id

    def get_bot_id_by_rest_api(self):
        url = 'https://api.telegram.org/bot' + self.api_key + '/getMe'

        response = requests.get(url, params='')
        if response.json()['ok']:
            print('id 받아오기 성공')
            result = response.json()['result']
            bot_id = result['id']
            return bot_id
        else:
            print('id 받아오기 실패' + str(response.json()))

    # not yet developed
    def get_chat_id(self, bot: telegram.Bot):
        me = bot.getUpdates()
        print(me)

    # not yet developed
    def get_chat_id_by_rest_api(self):
        url = 'https://api.telegram.org/bot' + self.api_key + '/getUpdates'

        response = requests.get(url, params='')
        if response.json()['ok']:
            print('chat id 받아오기 성공')
            result = response.json()
            print(result)
        else:
            print('chat id 받아오기 실패' + str(response.json()))

    def set_main_chat_id(self):
        if platform.system() == 'Linux':
            self.main_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        else:
            with open('../config.yaml') as f:
                key_info = yaml.load(f, Loader=yaml.FullLoader)
                self.main_chat_id = key_info['TELEGRAM_CHAT_ID']

    def set_test_chat_id(self):
        if platform.system() == 'Linux':
            self.test_chat_id = os.environ.get('TELEGRAM_TEST_CHAT_ID')
        else:
            with open('../config.yaml') as f:
                key_info = yaml.load(f, Loader=yaml.FullLoader)
                self.test_chat_id = key_info['TELEGRAM_TEST_CHAT_ID']


class TelegramMessage(TextContent):
    def __init__(self, ipo_data_list_of_lists, target_date, post_type, post_id):
        super().__init__(ipo_data_list_of_lists, target_date, post_type)
        if len(ipo_data_list_of_lists) == 3:
            self.category = '청약'
        elif len(ipo_data_list_of_lists) == 2:
            self.category = '상장'

        self.post_id = post_id
        self.set_title()
        self.set_subtitle_list()
        self.set_content()

    def set_title(self):
        super().set_title()
        self.title = '<b>' + self.title + '</b>\n\n'

    def set_content(self):
        data_type_separator = '\n'
        subtitle_style_open_tag = ''
        subtitle_style_close_tag = ''
        subtitle_text_style_open_tag = '<b>'
        subtitle_text_style_close_tag = '</b>'
        content_separator = '\n'

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
                            content += ConvertBiddingData(ipo_data).get_telegram_content()
                        elif self.category == '상장':
                            content += ConvertIpoReadyData(ipo_data).get_telegram_content()

                        content += f'🖥️ipostock에서 자세히 보기 : '
                        content += f'<a href="{ipo_data.ref_url_ipo_stock}">링크</a>\n'
                        #TODO : Connection Timeout 해결 후 주석 해제
                        # content += f'🖥️38com에서 자세히 보기 : '
                        # content += f'<a href="{ipo_data.ref_url_38com}">링크</a>\n'

                        content += subtitle_style_close_tag + content_separator
                        content_list.append(content)

            except Exception as e:
                print(f'Telegram text 생성 중 오류 : {e}')

        self.content = ''.join(content_list)

    def get_content(self):
        return self.content

    def send_message(self):
        telegram_api = TelegramAPI()
        text = self.title + '\n'
        chat_id = None

        if any(self.ipo_data_list_of_lists):
            if self.post_type == 'private':
                chat_id = telegram_api.test_chat_id
            elif self.post_type == 'public':
                chat_id = telegram_api.main_chat_id
        else:
            return

        text += self.get_content()
        text += f'📝블로그에서 자세히 보기 : <a href="https://hzoo.tistory.com/{str(self.post_id)}">링크</a>'

        bot = telegram_api.get_bot()
        del telegram_api

        bot.sendMessage(chat_id, text, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)