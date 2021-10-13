from datetime import datetime, timedelta
import time
import crawler.from_ipostock as crawler_ipostock
import reminder.tistory as tistory
import reminder.kakao as kakao
import reminder.telegram_bot as telegram_bot

if __name__ == '__main__':
    today = datetime.utcnow() + timedelta(hours=9)
    if today.weekday() != 5: #토요일 제외
        ipo_data_list = crawler_ipostock.get_ipo_data_list(today)
        now = datetime.utcnow()

        while now.minute != 39:
            time.sleep(60)
            now = datetime.utcnow()

        while now.minute != 40:
            time.sleep(1)
            now = datetime.utcnow()

        if today.hour == 8: #한국 08시 40분 : 본 메세지
            print('본 메세지 입니다.')
            bid_post_id = tistory.write_new_post(ipo_data_list[:3], today, 'main')
            ipo_post_id = tistory.write_new_post(ipo_data_list[3:], today, 'main')

            telegram_bot.send_message(ipo_data_list[:3], bid_post_id, today)
            telegram_bot.send_message(ipo_data_list[3:], ipo_post_id, today)
        else: #한국 21시 40분 : test
            print('테스트 메세지 입니다.')
            tomorrow = today + timedelta(days=1)
            bid_post_id = tistory.write_new_post(ipo_data_list[:3], tomorrow, 'test')
            ipo_post_id = tistory.write_new_post(ipo_data_list[3:], tomorrow, 'test')

            telegram_bot.send_message_for_test(ipo_data_list[:3], bid_post_id, tomorrow)
            telegram_bot.send_message_for_test(ipo_data_list[3:], ipo_post_id, tomorrow)