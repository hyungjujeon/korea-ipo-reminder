import yaml
import telegram
import requests

def get_telegram_api_key():
    with open('../../config.yaml') as f:
        KEY_INFO = yaml.load(f, Loader=yaml.FullLoader)
        telegram_key = KEY_INFO['TELEGRAM_KEY']

    return telegram_key

def get_bot_id():
    bot_token = get_telegram_api_key()
    bot = telegram.Bot(token=bot_token)
    me = bot.getMe()
    bot_id = me['id']

    return bot_id

def get_bot_id_html():
    url = 'https://api.telegram.org/bot' + get_telegram_api_key() + '/getMe'

    response = requests.get(url, params='')
    if response.json()['ok'] == True:
        print('id 받아오기 성공')
        result = response.json()['result']
        bot_id = result['id']
        return bot_id
    else:
        print('id 받아오기 실패' + str(response.json()))

def main():
    chat_id1 = get_bot_id()
    chat_id2 = get_bot_id_html()
    print('id 동일') if chat_id1 == chat_id2 else print('id 인식 못하거나, 다름')

main()