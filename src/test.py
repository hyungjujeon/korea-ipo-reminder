from datetime import datetime
import crawler.from_ipostock as crawler_ipostock
import reminder.tistory as tistory
import reminder.kakao as kakao
import reminder.telegram_bot as telegram_bot

if __name__ == '__main__':
    today = datetime.now()
    ipo_data_list = crawler_ipostock.get_ipo_data_list(today)
    bid_post_id = tistory.write_new_post(ipo_data_list[:3], today, 'test')
    ipo_post_id = tistory.write_new_post(ipo_data_list[3:], today, 'test')

    telegram_bot.send_message_for_test(ipo_data_list[:3], 96, today)
    telegram_bot.send_message_for_test(ipo_data_list[3:], 97, today)