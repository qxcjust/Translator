from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
import re
import logging
from acronym_manager import AcronymManager
import os
import datetime
import csv
from langdetect import detect, LangDetectException

# 导入配置文件
from gl_config import LOG_LEVEL, MODEL_NAME, ENDPOINT_URL, TEMPERATURE, MAX_RETRY, USE_REFLECTION, API_KEY

# 配置日志记录
logging.basicConfig(level=LOG_LEVEL)


class AcronymManager:
    """管理行业缩写和特殊字符"""
    def __init__(self):
        # 定义汽车行业常见缩写和允许的字符
        self.industry_abbreviations = {'ECU', 'ABS', 'ESP', 'CAN', 'LIN', 'OTA'}
        self.alphanumeric_chars = r'a-zA-Z0-9'  # 大小写字母和数字
        # 压缩后的正则表达式模式（带注释）
        self.special_characters = r'\s\.,„;:!?\(\)\[\]{}<>\-–—‒=+\±/\\|@#%^&*~$€£¥Ψ¢"“”\'‘’`«»‹›…¤‚•·∙'


class TranslationCore:
    def __init__(self, model_name=MODEL_NAME, endpoint_url=ENDPOINT_URL, temperature=TEMPERATURE):
        # Initialize model
        self.llm = ChatOpenAI(model=model_name, base_url=endpoint_url, api_key=API_KEY, temperature=temperature)
        
        self.acronym_manager = AcronymManager()

        # 配置语言检测映射
        self.lang_code_map = {
            'Chinese': 'zh',
            'Japanese': 'ja',
            'English': 'en'
        }
        
    def translate_text(self, text, source_lang, target_lang, use_reflection=USE_REFLECTION):
        """核心翻译方法"""
        original_text = text

        # 前置检查流程
        check_result = self._pre_translation_checks(original_text, target_lang)
        if check_result is not None:
            return check_result


        # 翻译流程
        initial_result = self.initial_translation_with_lang(original_text, source_lang, target_lang)
        
        if use_reflection:
            feedback_result = self.reflect_translation(initial_result, target_lang)
            finally_result = self.improve_translation(initial_result, feedback_result, target_lang)
        else:
            finally_result = initial_result

        logging.info(f"{original_text} → {initial_result} → {finally_result} Translating from {source_lang} to {target_lang}")
        return finally_result

    def _pre_translation_checks(self, text, target_lang):
        """执行所有前置检查的集成方法"""
        # 空值检查
        if not text or text.strip() == "":
            return text
        
        # 技术内容检查（包含最新特殊字符）
        if self._is_technical_content(text):
            logging.debug(f"技术内容保留: {text}")
            return text
            
        # 目标语言验证（增强版）
        if self._is_effective_target_language(text, target_lang):
            logging.info(f"目标语言内容保留: {text}")
            return text
            
        # 单字符/无效输入检查
        if not self._is_translatable(text):
            return self._get_context_required_message(target_lang)
            
        return None


    def _is_effective_target_language(self, text, target_lang):
        """增强版语言有效性检测"""
        try:
            # 使用加权检测算法
            lang_score = self._detect_language_with_confidence(text)
            target_code = self.lang_code_map[target_lang]
            
            # 判断条件：置信度>60% 或 包含目标语言特征字符
            if lang_score[target_code] > 0.6:
                return True
                
            # 中日文特有字符检查
            if target_code == 'zh' and self._contains_chinese_char(text):
                return True
            if target_code == 'ja' and self._contains_japanese_char(text):
                return True
                
            return False
        except Exception as e:
            logging.error(f"语言检测异常: {str(e)}")
            return False

    def _detect_language_with_confidence(self, text):
        """带置信度的语言检测（示例实现）"""
        # 这里可以集成更专业的语言检测服务
        from langdetect import detect_langs
        try:
            results = detect_langs(text)
            return {lang.lang: lang.prob for lang in results}
        except:
            return {'unknown': 0.0}

    def _contains_chinese_char(self, text):
        """检查是否包含中文字符"""
        return re.search(r'[\u4e00-\u9fff]', text)

    def _contains_japanese_char(self, text):
        """检查是否包含日文字符"""
        return re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text)

    def _is_translatable(self, text):
        """检查是否需要进入翻译流程"""
        if len(text.strip()) <= 1 and not text.isdigit():
            return False
        return True

    def _is_technical_content(self, text):
        """检测是否是纯技术内容（缩写/符号）"""
        # 匹配行业缩写
        if text.strip().upper() in self.acronym_manager.industry_abbreviations:
            return True
            
        # 匹配技术格式（大写字母、数字、符号）
        pattern = rf'^[{self.acronym_manager.alphanumeric_chars}{self.acronym_manager.special_characters}]*$'
        return re.match(pattern, text, re.ASCII) is not None


    def initial_translation_with_lang(self, processed_text, source_lang, target_lang):
        """初步翻译方法"""
        system_prompt = (
            f"You are a automotive software localization expert. "
            f"Translate from {source_lang} to {target_lang} preserving: "
            "1. Original formatting and punctuation\n"
            "2. Industry terms (ECU, ABS, CAN, etc.)\n"
            "3. Mixed language context\n\n"
            "Output ONLY the translated text."
        )

        user_prompts = {
            "Chinese": "翻译到中文，保留英文术语：\n{input}",
            "Japanese": "日本語に翻訳（アルファベット略語はそのまま）：\n{input}",
            "English": "Translate to English preserving technical terms:\n{input}"
        }
        user_prompt = user_prompts.get(target_lang, "Translate:\n{input}")

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])

        chain = prompt_template | self.llm | StrOutputParser()
        return chain.invoke({"input": processed_text})

    def reflect_translation(self, translation, target_lang):
        """翻译质量反馈"""
        system_prompt = {
            "Chinese": "您是中国汽车行业的本地化专家，请用中文指出以下翻译问题：",
            "Japanese": "自動車ソフトウェアの専門家として日本語でフィードバック：",
            "English": "As automotive localization expert, provide English feedback:"
        }[target_lang]

        user_prompt = (
            "请检查：\n"
            "1. 术语一致性（ECU/ABS等是否保留）\n"
            "2. 混合语言处理\n"
            "3. 标点格式\n"
            "4. 技术准确性\n\n"
            "翻译内容：\n{translation}"
        )

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        
        return prompt_template | self.llm | StrOutputParser() | self._clean_feedback

    def improve_translation(self, translation, feedback, target_lang):
        """迭代改进翻译"""
        system_prompt = {
            "Chinese": "您是中国汽车行业的资深译员，请根据反馈改进翻译：",
            "Japanese": "自動車分野のプロ翻訳者として改善してください：",
            "English": "Refine this automotive translation per feedback:"
        }[target_lang]

        user_prompt = (
            "反馈：\n{feedback}\n\n"
            "改进要求：\n"
            "1. 严格保留技术术语\n"
            "2. 维持标点格式\n"
            "3. 准确处理混合内容\n\n"
            "待改进文本：\n{translation}"
        )

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])

        chain = prompt_template | self.llm | StrOutputParser()
        return chain.invoke({"feedback": feedback, "translation": translation})

    def _clean_feedback(self, text):
        """清理反馈中的冗余内容"""
        return text.split("改进建议：")[-1].split("---")[0].strip()  
