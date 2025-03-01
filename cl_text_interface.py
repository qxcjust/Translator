import logging
from translator import Translator

def main():
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 初始化翻译器
    translator = Translator()
    
    # 获取用户输入
    text = input("请输入要翻译的文本: ")
    source_lang = input("请输入源语言代码 (例如: 'en'): ")
    target_lang = input("请输入目标语言代码 (例如: 'zh'): ")
    
    # 调用translate_text方法进行翻译
    try:
        translated_text = translator.translate_text(text, source_lang, target_lang, task=None)
        print(f"翻译结果: {translated_text}")
    except Exception as e:
        print(f"翻译过程中出现错误: {e}")

if __name__ == "__main__":
    main()