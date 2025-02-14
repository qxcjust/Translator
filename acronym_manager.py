import re
class AcronymManager:
    def __init__(self):
        # 固定保护的术语
        self.protected_terms = {
            'IEM': "IEM",
            'TSAP': "TSAP",
            'iAUTO': "iAUTO",
            'VDM': "VDM",
            'TTRS': "TTRS",
            'ZCU': "ZCU",
            'ZCU_FR': "ZCU_FR",
            'ZCU_FL': "ZCU_FL",
            'ZCU_R': "ZCU_R",
            'HPC': "HPC",
            'NTC': "NTC",
            'Benz': "Benz",
            'MB': "MB",
            'PoC': "PoC",
            'SoP': "SoP"                    
        }
        # 添加特殊字符
        self.special_characters = r'↑↓←→↗↙'
        
        # 添加字母数字字符和特殊符号
        self.alphanumeric_chars = r'a-zA-Z0-9\s.,!?()-'

        # 幻覚パターン検出用正規表現
        self.hallucination_patterns = [
            re.compile(r'注：.*'),
            re.compile(r'※.*'),
            re.compile(r'\(Note:.*\)', re.I),
            re.compile(r'^【.*】', re.M),
            re.compile(r'Suggestion:', re.I),
            re.compile(r'explanation:', re.I),
            re.compile(r'注意：'),
            re.compile(r'建议：')
        ]