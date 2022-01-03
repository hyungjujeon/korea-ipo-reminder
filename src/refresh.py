from datetime import datetime, timedelta
from crawler.ipo_crawler import get_bidding_data_list, get_ipo_data_list, get_ipo_after_data, BiddingStatus, IpoStatus
from reminder.tistory import TistoryPost
from reminder.telegram_bot import TelegramMessage
from src.store_data.in_gspread import GoogleSpreadSheet
from src.store_data.in_database import Query


def gs_to_postgresql(row_range):
    query = Query()
    for i in row_range:
        row_data = gs.get_all_values_from_row(i)
        for j in range(1, 5):
            row_data[j] = row_data[j][:10]
        for k in range(20, 27, 2):
            row_data[k] = row_data[k].replace('%', '')

        before_offering_data = "'" + "', '".join(row_data[:19]) + "'"
        after_ipo_data = "'" + "', '".join(row_data[19:]) + "'"

        query.insert_data('ipo_reminder', 'before_offering', before_offering_data)
        query.insert_data('ipo_reminder', 'after_ipo', after_ipo_data)

if __name__ == '__main__':
    today = datetime.utcnow() + timedelta(hours=9) - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    gs = GoogleSpreadSheet()

    tomorrow_bidding_data_list = get_bidding_data_list(tomorrow)
    tomorrow_ipo_data_list = get_ipo_data_list(tomorrow)

    today_bidding_data_list = get_bidding_data_list(today)
    today_ipo_data_list = get_ipo_data_list(today)

    try:
        gs.append_row_before_ipo(tomorrow_bidding_data_list[BiddingStatus.START_TOMORROW])
    except Exception as e:
        print(f'내일 모레 청약시작 종목 없음 : {e}')

    for i, bidding_data_list in enumerate(today_bidding_data_list):
        if bidding_data_list:
            try:
                for bidding_data in bidding_data_list:
                    gs.update_before_ipo(bidding_data)
            except Exception as e:
                if i == BiddingStatus.FINISH_TODAY:
                    print(f'오늘 청약 마감 종목 없음 : {e}')
                elif i == BiddingStatus.START_TODAY:
                    print(f'오늘 청약 시작 종목 없음 : {e}')
                else:
                    print(f'내일 청약 시작 종목 없음 : {e}')

    try:
        for today_ipo_data in today_ipo_data_list[IpoStatus.START_TODAY]:
            company_name = today_ipo_data.company_name
            ipo_result_tr_list = get_ipo_after_data(company_name)
            gs.update_after_ipo(company_name, ipo_result_tr_list)
    except Exception as e:
        print(f'오늘 상장 종목 없음 : {e}')
