import time
from datetime import datetime, timedelta
from crawler.ipo_crawler import get_bidding_data_list, get_ipo_data_list
from reminder.tistory import TistoryPost
from reminder.telegram_bot import TelegramMessage

if __name__ == '__main__':
    today = datetime.utcnow() + timedelta(hours=9)
    if today.weekday() < 5:
        bidding_data_list = get_bidding_data_list(today)
        ipo_data_list = get_ipo_data_list(today)

        # now = datetime.utcnow()
        # while (now.minute % 10) != 9:
        #     time.sleep(60)
        #     now = datetime.utcnow()
        #
        # while (now.minute % 10) != 0:
        #     time.sleep(1)
        #     now = datetime.utcnow()

        bid_post = TistoryPost(bidding_data_list, today, 'public')
        ipo_post = TistoryPost(ipo_data_list, today, 'public')

        bid_post.write_new_post()
        ipo_post.write_new_post()

        bid_message = TelegramMessage(bidding_data_list, today, 'private', bid_post.new_post_id)
        ipo_message = TelegramMessage(ipo_data_list, today, 'private', ipo_post.new_post_id)

        bid_message.send_message()
        ipo_message.send_message()
