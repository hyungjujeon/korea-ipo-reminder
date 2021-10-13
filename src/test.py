from datetime import datetime
import crawler.from_ipostock as crawler_ipostock
import reminder.tistory as tistory
import reminder.kakao as kakao
import reminder.telegram_bot as telegram_bot

if __name__ == '__main__':
    today = datetime.now()
    print('heroku 시간', today.hour)
    ipo_data_list = crawler_ipostock.get_ipo_data_list(today)
    bid_post_id = tistory.write_new_post(ipo_data_list[:3], today, 'test')
    ipo_post_id = tistory.write_new_post(ipo_data_list[3:], today, 'test')

    telegram_bot.send_message_for_test(ipo_data_list[:3], bid_post_id, today)
    telegram_bot.send_message_for_test(ipo_data_list[3:], ipo_post_id, today)

    # if today.hour == 8:
    #     ipo_data_list = crawler_ipostock.get_ipo_data_list(today)
    #     bid_post_id = tistory.write_new_post(ipo_data_list[:3], today, 'test')
    #     ipo_post_id = tistory.write_new_post(ipo_data_list[3:], today, 'test')
    #
    #     telegram_bot.send_message_for_test(ipo_data_list[:3], bid_post_id, today)
    #     telegram_bot.send_message_for_test(ipo_data_list[3:], ipo_post_id, today)
    # else:
    #     ipo_data_list = crawler_ipostock.get_ipo_data_list(today)
    #     bid_post_id = tistory.write_new_post(ipo_data_list[:3], today, 'main')
    #     ipo_post_id = tistory.write_new_post(ipo_data_list[3:], today, 'main')
    #
    #     telegram_bot.send_message(ipo_data_list[:3], bid_post_id, today)
    #     telegram_bot.send_message(ipo_data_list[3:], ipo_post_id, today)
