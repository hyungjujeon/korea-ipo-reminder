from datetime import datetime, timedelta
import platform
import crawler.from_ipostock as crawler_ipostock
import reminder.tistory as tistory
import reminder.telegram_bot as telegram_bot

if __name__ == '__main__':
    today = datetime.utcnow() + timedelta(hours=9)
    if today.weekday() != 5: #토요일 제외
        ipo_data_list = crawler_ipostock.get_ipo_data_list(today)
        now = datetime.utcnow()
        print(now)
        print(platform.platform())

        print('테스트 메세지 입니다.')
        tomorrow = today + timedelta(days=1)
        bid_post_id = tistory.write_new_post(ipo_data_list[:3], tomorrow, 'test')
        ipo_post_id = tistory.write_new_post(ipo_data_list[3:], tomorrow, 'test')

        telegram_bot.send_message_for_test(ipo_data_list[:3], bid_post_id, tomorrow)
        telegram_bot.send_message_for_test(ipo_data_list[3:], ipo_post_id, tomorrow)