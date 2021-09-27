from enum import IntEnum

class IpoDataList(IntEnum):
    OFFERING_BEFORE = 0
    OFFERING_START = 1
    OFFERING_FINISH = 2
    IPO_BEFORE = 3
    IPO_D_DAY = 4

class IpoData(IntEnum):
    COMPANY_NAME                = 0  # 종목명
    BIDDING_START               = 1  # 공모시작
    BIDDING_FINISH              = 2  # 공모마감
    REFUND_DATE                 = 3  # 환불일
    IPO_DATE                    = 4  # 상장일
    BAND_PRICE_LOW              = 5  # 공모가하단
    BAND_PRICE_HIGH             = 6  # 공모가상단
    OFFERING_PRICE              = 7  # 공모가격
    OFFERING_AMOUNT             = 8  # 공모규모
    TOTAL_SHARE_NUM             = 9  # 공모주식수
    INVESTOR_NUM                = 10 # 전문투자자(주식수)
    INVESTOR_RATIO              = 11 # 전문투자자(비율)
    EMPLOYEE_NUM                = 12 # 우리사주조합(주식수)
    EMPLOYEE_RATIO              = 13 # 우리사주조합(비율)
    PUBLIC_NUM                  = 14 # 일반청약자(주식수)
    PUBLIC_RATIO                = 15 # 일반청약자(비율)
    FOREIGNER_NUM               = 16 # 해외투자자(주식수)
    FOREIGNER_RATIO             = 17 # 해외투자자(비율)
    SHARE_NUM_AFTER_IPO         = 18 # 공모후 상장주식수
    SHARE_RATIO_AFTER_IPO       = 19 # 공모후 상장주식비율
    SALE_AVAILABLE_SHARE_NUM    = 20 # 유통가능 주식수
    SALE_AVAILABLE_SHARE_RATIO  = 21 # 유통가능 주식비율
    LOCK_UP_SHARE_NUM           = 22 # 보호예수 물량 주식수
    LOCK_UP_SHARE_RATIO         = 23 # 보호예수 물량 비율
    COMPETITION_RATIO           = 24 # 기관 경쟁률
    COMMITMENT_RATIO            = 25 # 의무보유 확약 비율
    UNDERWRITER                 = 26 # 주간사(배정물량)