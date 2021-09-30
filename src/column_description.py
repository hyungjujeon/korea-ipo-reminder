from enum import IntEnum

class IpoDataList(IntEnum):
    OFFERING_FINISH         = 0
    OFFERING_START          = 1
    OFFERING_BEFORE         = 2
    IPO_D_DAY               = 3
    IPO_BEFORE              = 4

class IpoData(IntEnum):
    COMPANY_NAME = 0  # 종목명

    # bidding_info_list
    # date_info_list
    BIDDING_START = 1  # 공모시작
    BIDDING_FINISH = 2  # 공모마감
    REFUND_DATE = 3  # 환불일
    IPO_DATE = 4  # 상장일

    # offering_price_list
    BAND_PRICE_LOW = 5  # 공모가하단
    BAND_PRICE_HIGH = 6  # 공모가상단
    OFFERING_PRICE = 7  # 공모가격(원)
    OFFERING_AMOUNT = 8  # 공모규모(억)

    # total_share_num_list
    TOTAL_SHARE_NUM = 9  # 공모주식수
    NEW_SHARE_RATIO = 10  # 신주모집비율(%)

    # shares_info_list
    SHARE_NUM_AFTER_IPO = 11  # 공모후 상장주식수
    SHARE_RATIO_AFTER_IPO = 12  # 공모후 상장주식비율
    SALE_AVAILABLE_SHARE_NUM = 13  # 유통가능 주식수
    SALE_AVAILABLE_SHARE_RATIO = 14  # 유통가능 주식비율
    LOCK_UP_SHARE_NUM = 15  # 보호예수 물량 주식수
    LOCK_UP_SHARE_RATIO = 16  # 보호예수 물량 비율

    # underwriter_info_list
    UNDERWRITER = 17  # 주간사
    ALLOCATED_SHARE_NUM = 18  # 주간사별배정물량

    # demand_forecast_result_list
    COMPETITION_RATIO = 19  # 기관 경쟁률
    COMMITMENT_RATIO = 20  # 의무보유 확약 비율