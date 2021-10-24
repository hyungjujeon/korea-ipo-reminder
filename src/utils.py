def get_bidding_fee(underwriter_name):
    if underwriter_name in ['미래에셋증권', '한국투자증권', '삼성증권', 'SK증권', '대신증권', '신영증권', '현대차증권']:
        return 2000
    elif underwriter_name == 'KB증권':
        return 1500
    elif underwriter_name in ['한화투자증권', '하이투자증권']:
        return 1000
    else:
        return 0