from datetime import datetime, timedelta
from crawler.ipo_crawler import CrawlerIpoStock
from reminder.tistory import TistoryPost
from reminder.telegram_bot import TelegramMessage

if __name__ == '__main__':
    today = datetime.utcnow() + timedelta(hours=9)
    tomorrow = today + timedelta(days=1)
    if tomorrow.weekday() < 5:
        crawler = CrawlerIpoStock()
        crawler.set_target_date(tomorrow)

        bidding_data_list = crawler.get_bidding_data_list_of_lists()
        ipo_data_list = crawler.get_ipo_data_list_of_lists()

        bid_post = TistoryPost(bidding_data_list, tomorrow, 'private')
        ipo_post = TistoryPost(ipo_data_list, tomorrow, 'private')
        bid_post.write_new_post()
        ipo_post.write_new_post()

        bid_message = TelegramMessage(bidding_data_list, tomorrow, 'private', bid_post.new_post_id)
        ipo_message = TelegramMessage(ipo_data_list, tomorrow, 'private', ipo_post.new_post_id)
        bid_message.send_message()
        ipo_message.send_message()

        # db = database.Query()
        # db.create_schema('ipo_reminder')
        # db.create_table('ipo_reminder', '')
        # del db