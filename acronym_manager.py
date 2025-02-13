

class AcronymManager:
    def __init__(self):
        # 固定保护的术语
        self.protected_terms = {
            'IEM': "IEM",
            'TSAP': "TSAP"
        }