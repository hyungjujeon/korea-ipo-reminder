import os
import telegram
import requests
import src.column_description as cd
import src.utils as utils
from datetime import datetime, timedelta

def get_bot_id(bot):
    me = bot.getMe()
    bot_id = me['id']

    return bot_id

def get_bot_id_html():
    telegram_key = os.environ.get('TELEGRAM_KEY')
    url = 'https://api.telegram.org/bot' + telegram_key + '/getMe'

    response = requests.get(url, params='')
    if response.json()['ok'] == True:
        print('id 받아오기 성공')
        result = response.json()['result']
        bot_id = result['id']
        return bot_id
    else:
        print('id 받아오기 실패' + str(response.json()))

def get_chat_id_html():
    telegram_key = os.environ.get('TELEGRAM_KEY')
    url = 'https://api.telegram.org/bot' + telegram_key + '/getUpdates'

    response = requests.get(url, params='')
    if response.json()['ok'] == True:
        print('chat id 받아오기 성공')
        result = response.json()
    else:
        print('chat id 받아오기 실패' + str(response.json()))

def get_bid_parameter(ipo_data_list, target_date):
    weekdays = {0: '(월)', 1: '(화)', 2: '(수)', 3: '(목)', 4: '(금)', 5: '(토)', 6: '(일)'}
    today = target_date

    title = f'<b>💰{today.year}년 {today.month}월 {today.day}일{weekdays[today.weekday()]} 청약 정보💰</b>\n\n'

    contents = []
    for idx, ipo_data in enumerate(ipo_data_list):
        try:
            if ipo_data:
                day_info = ''
                if idx == 0:
                    day_info = f'📢오늘({today.month}/{today.day}) 청약 마감 : '
                elif idx == 1:
                    if len(contents) != 0:
                        contents.append('\n')
                    day_info = f'🔔오늘({today.month}/{today.day}) 청약 시작 : '
                else:
                    if len(contents) != 0:
                        contents.append('\n')
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
                    if competition_ratio is not None:
                        competition_ratio = format(int(competition_ratio), ',d') + ': 1'
                    else:
                        competition_ratio = '미표기'
                    if commitment_ratio is None:
                        commitment_ratio = '미표기'
                    else:
                        commitment_ratio = str(commitment_ratio) + '%'
                    underwriter = data[cd.IpoData.UNDERWRITER]
                    fee = [utils.get_bidding_fee(uw) for uw in underwriter]
                    allocated_share_list = data[cd.IpoData.ALLOCATED_SHARE_NUM]
                    underwriter_info = [(x[0] + '(수수료: ' + format(x[1], ',d') + '원, ' + format(x[2], ',d') + '주)') for x in list(zip(underwriter, fee, allocated_share_list))]
                    underwriter_info = ', '.join(underwriter_info)

                    if '스팩' in company_name:
                        minimum_bidding_price = offering_price * 10
                    else:
                        minimum_bidding_price = offering_price * 5

                    content = '<b>' + day_info + str(company_name) + '</b>\n'
                    content += f'💡균등 최소 청약증거금(10주) : ' + format(minimum_bidding_price, ',d') + '원\n'
                    content += f'📅공모 일정 : {bidding_start} ~ {bidding_finish}\n'
                    content += f'📅상장일 : {ipo_date}\n'
                    content += f'📅환불일 : {refund_date}\n'
                    content += f'💰희망공모가 : ' + format(band_price_low, ",d") + '원 ~ ' + format(band_price_high, ",d") + '원\n'
                    content += f'💰확정공모가 : ' + format(offering_price, ",d") + '원\n'
                    content += f'💰공모규모 : ' + format(offering_amount, ',d') + '억\n'
                    content += f'💰유통가능 금액(예상) : ' + format(sale_available_amount, ',d') + '억\n'
                    content += f'🧾유통가능 주식 비율(예상) : {sale_available_share_ratio}' + '%\n'
                    content += f'🏢수요예측 기관 경쟁률 : {competition_ratio}\n'
                    content += f'🏢의무보유 확약 비율(예상) : {commitment_ratio}' + '\n'
                    content += f'🚩주간사 : ' + underwriter_info + '\n'
                    content += '\n'
                    contents.append(content)
        except:
            pass

    contents = ''.join(contents)

    return title + contents

def get_ipo_parameter(ipo_data_list, target_date):
    weekdays = {0: '(월)', 1: '(화)', 2: '(수)', 3: '(목)', 4: '(금)', 5: '(토)', 6: '(일)'}
    today = target_date

    title = f'<b>💰{today.year}년 {today.month}월 {today.day}일{weekdays[today.weekday()]} 상장 정보💰</b>\n\n'

    contents = []
    for idx, ipo_data in enumerate(ipo_data_list):
        try:
            if ipo_data:
                day_info = ''
                if idx == 0:
                    day_info = f'🔔오늘({today.month}/{today.day}) 상장 : '
                else:
                    if len(contents) != 0:
                        contents.append('\n')
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
                        if competition_ratio is not None:
                            competition_ratio = format(int(competition_ratio), ',d') + ': 1'
                        else:
                            competition_ratio = '미표기'
                        if commitment_ratio is None:
                            commitment_ratio = '미표기'
                        else:
                            commitment_ratio = str(commitment_ratio) + '%'

                        content = '<b>' + day_info + str(company_name) + '</b>\n'
                        content += f'📅상장일 : {ipo_date}\n'
                        content += f'💰희망공모가 : ' + format(band_price_low, ",d") + '원 ~ ' + format(band_price_high, ",d") + '원\n'
                        content += f'💰확정공모가 : ' + format(offering_price, ",d") + '원\n'
                        content += f'💰공모규모 : ' + format(offering_amount, ',d') + '억\n'
                        content += f'💰유통가능 금액(확정) : ' + format(sale_available_amount, ',d') + '억\n'
                        content += f'🧾유통가능 주식 수(확정) : ' + format(sale_available_share_num, ',d') + '주\n'
                        content += f'🧾유통가능 주식 비율(확정) : {sale_available_share_ratio}' + '%\n'
                        content += f'🏢수요예측 기관 경쟁률 : {competition_ratio}\n'
                        content += f'🏢의무보유 확약 비율(확정) : {commitment_ratio}' + '\n'
                        content += '\n'
                        contents.append(content)
                except:
                    pass
        except:
            pass

    contents = ''.join(contents)

    return title + contents

def send_message_for_test(ipo_data_list, post_id, target_date):
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

    bot_token = os.environ.get('TELEGRAM_KEY')
    bot = telegram.Bot(token=bot_token)
    chat_id = os.environ.get('TELEGRAM_TEST_CHAT_ID')

    text = param_list
    text += '<a href="https://hzoo.tistory.com/' + str(post_id) + '">자세히 보기(블로그)</a>'
    bot.sendMessage(chat_id, text, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview = True)

def send_message(ipo_data_list, post_id, target_date):
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

    bot_token = os.environ.get('TELEGRAM_KEY')
    bot = telegram.Bot(token=bot_token)
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    text = param_list
    text += '<a href="https://hzoo.tistory.com/' + str(post_id) + '">자세히 보기(블로그)</a>'
    bot.sendMessage(chat_id, text, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview = True)