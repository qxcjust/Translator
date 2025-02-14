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
            'SoP': "SoP",
            'VIN': "VIN"       
        }
        # 添加特殊字符
        self.special_characters = r'↑↓←→↗↙'
        
        # 添加字母数字字符和特殊符号
        self.alphanumeric_chars = r'a-zA-Z0-9\s.,!?()-'

        # 幻覚パターン検出用正規表現
        self.hallucination_patterns = [
            # 中文常见模式
            re.compile(r'注：.*'),
            re.compile(r'※.*'),
            re.compile(r'\(Note:.*\)', re.I),
            re.compile(r'^【.*】', re.M),
            re.compile(r'注意：'),
            re.compile(r'建议：'),
            re.compile(r'提示：'),
            re.compile(r'提醒：'),
            re.compile(r'备注：'),
            re.compile(r'译注：'),
            # 英文常见模式
            re.compile(r'Suggestion:', re.I),
            re.compile(r'explanation:', re.I),
            re.compile(r'Disclaimer:', re.I),
            re.compile(r'Warning:', re.I),
            re.compile(r'Tip:', re.I),
            # 日文常见模式
            re.compile(r'提案：', re.I),
            re.compile(r'説明：', re.I),
            re.compile(r'免責事項：', re.I),
            re.compile(r'警告：', re.I),
            re.compile(r'ヒント：', re.I),
            re.compile(r'補足：'),
            re.compile(r'備考：')
        ]

        # ZH -> JP
        self.term_mapping = {
            "议题": "議題",
            '空间': '空間',    
            '背景': '背景',    
            '不具合': '不具合'
            # 可根据需求继续扩充映射词典
            # "示例词": "正確表記",
        }