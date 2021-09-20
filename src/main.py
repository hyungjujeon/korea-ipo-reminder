import requests
from datetime import datetime
from enum import IntEnum
import crawler.from_38com as crawler_38com
import crawler.from_ipostock as crawler_ipostock

class UrlDescription(IntEnum):
    OFFERING_BEFORE = 0
    OFFERING_START = 1
    OFFERING_FINISH = 2
    IPO_BEFORE = 3
    IPO_D_DAY = 4

if __name__ == '__main__':
    today = datetime.now()
    ipo_data_list = crawler_ipostock.get_ipo_data_list(today)
    print(ipo_data_list)