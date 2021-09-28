from datetime import datetime
import crawler.from_ipostock as crawler_ipostock
import reminder.tistory as tistory
import reminder.kakao as kakao

if __name__ == '__main__':
    today = datetime.now()
    ipo_data_list = crawler_ipostock.get_ipo_data_list(today)
    bid_post_id = tistory.write_new_post(ipo_data_list[:3])
    ipo_post_id = tistory.write_new_post(ipo_data_list[3:])

    kakao.alarm_text_message(ipo_data_list[:3], bid_post_id)
    kakao.alarm_text_message(ipo_data_list[3:], ipo_post_id)