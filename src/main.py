import time
from datetime import datetime, timedelta
from crawler.ipo_crawler import get_bidding_data_list, get_ipo_data_list
from reminder.tistory import TistoryPost
from reminder.telegram_bot import TelegramMessage

if __name__ == '__main__':
    today = datetime.utcnow() + timedelta(hours=9)
    if today.weekday() != 5:
        bidding_data_list = get_bidding_data_list(today)
        ipo_data_list = get_ipo_data_list(today)

        bid_message = TelegramMessage(bidding_data_list, today, 'public')
        ipo_message = TelegramMessage(ipo_data_list, today, 'public')

        now = datetime.utcnow()
        while (now.minute % 10) != 9:
            time.sleep(60)
            now = datetime.utcnow()

        while (now.minute % 10) != 0:
            time.sleep(1)
            now = datetime.utcnow()

        bid_message.send_message()
        ipo_message.send_message()
