import re
class AcronymManager:
    def __init__(self):
        # 添加特殊字符
        self.special_characters = r'↑↓←→↗↙'
        # 添加字母数字字符和特殊符号
        self.alphanumeric_chars = r'a-zA-Z0-9\s.,!?()-'