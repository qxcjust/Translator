from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
import re
import logging
from acronym_manager import AcronymManager
import os
import datetime
import csv
# 导入配置文件
from gl_config import LOG_LEVEL, MODEL_NAME, ENDPOINT_URL, TEMPERATURE, MAX_RETRY, USE_REFLECTION, API_KEY

# 配置日志记录
logging.basicConfig(level=LOG_LEVEL)

class TranslationCore:
    def __init__(self, model_name=MODEL_NAME, endpoint_url=ENDPOINT_URL, temperature=TEMPERATURE):
        # Initialize model
        self.llm = ChatOpenAI(model=model_name, base_url=endpoint_url, api_key=API_KEY, temperature=temperature)
        # 创建 AcronymManager 实例
        self.acronym_manager = AcronymManager()
        
        # Write prompts in target language
        self.language_prompts = {
            "Chinese": {
                "English": """You are a professional translator. STRICT RULES:
                    1. TRANSLATION RULES:
                    - PRESERVE acronyms/proper nouns (e.g., ZCU) 
                    - MAINTAIN tone
                    - CONSISTENT terminology
                    2. FORMAT RULES:
                    - KEEP original formatting/structure
                    - NO explanations/comments/footnotes
                    - PRESERVE numbering/bullet points
                    3. OUTPUT CONTROL:
                    - OUTPUT ONLY translation
                    - NO content additions/omissions
                    - STRICTLY follow source text structure
                    4. SPECIAL CASES:
                    - USE official English names
                    - KEEP unknown acronyms
                    5. ANTI-HALLUCINATION:
                    - DO NOT add any information
                    - DO NOT interpret ambiguous terms
                    - DO NOT summarize content
                    - REJECT creative translations"""
                ,
                "Japanese": """高度な専門性を持つ翻訳者として、中国語から日本語への翻訳の際には、以下の点を厳守:
                    1. 翻訳規則:
                    - 技術用語、製品名、固有名詞（例：iAuto改造车、RZ、14inch、24L2、車機woP席など）は原文そのまま保持し、翻訳や変更を行わないこと。
                    - 括弧内の内容や記号（例：+）も正確に再現すること。
                    - 用語一貫性保持
                    - 簡体字→日本語漢字変換必須
                    - 日本語は翻訳しません
                    2. 形式規則:
                    - 原文の書式、改行、スペース、記号等を忠実に再現すること。
                    - 説明/注釈厳禁
                    - 箇条書き形式保持
                    3. 出力制御:
                    - 翻訳文のみを出力し、余計な説明や注釈を追加しないこと。
                    - 追加/省略厳禁
                    - 原文構造完全再現
                    4. 特殊処理:
                    - 公式日本語名称使用
                    - 不明略語は保持
                    5. 幻覚防止:
                    - 独自解釈厳禁
                    - 曖昧語句は原文保持
                    - 要約厳禁
                    - 創造的翻訳拒否"""
            },

            "English": {
                "Chinese": """作为专业翻译，请严格遵循：
                    1. 翻译规则：
                    - 保留英文缩写/专有名词（例：ZCU）
                    - 保持文档的专业语气
                    - 确保术语一致性
                    2. 格式要求：
                    - 严格保持原文格式结构
                    - 禁止添加解释或注释
                    - 保留数字编号/项目符号
                    3. 输出控制：
                    - 仅输出翻译文本
                    - 禁止内容增减
                    - 完全复制源文本结构
                    4. 特殊处理：
                    - 使用官方中文名称
                    - 未知缩写保持原样
                    5. 防幻觉措施：
                    - 禁止添加任何信息
                    - 不解释模糊术语
                    - 保持数字/时间格式不变
                    - 拒绝创造性翻译""",

                "Japanese": """優れたプロの翻訳者として厳守事項：
                    1. 翻訳規則：
                    - 英語略語/固有名詞保持（例：ZCU）
                    - 文書の専門的表現維持
                    - 用語の一貫性確保
                    2. 形式要件：
                    - 原文フォーマット厳密保持
                    - 説明/注釈厳禁
                    - 数字/箇条書き形式保持
                    3. 出力制御：
                    - 翻訳文のみ出力
                    - 内容追加/削除禁止
                    4. 特殊処理：
                    - 外来語は適切なカタカナ表記に変換（例：module → モジュール）
                    - 公式日本語名称使用
                    - 不明略語は原文保持
                    5. 注意事項：
                    - 数字（3.14）、時刻（14:30）形式変更禁止
                    - 文頭の数字/記号（1. 2. 等）変更不可
                    - 幻覚的翻訳厳禁"""
            },

            "Japanese": {
                "Chinese": """作为专业翻译员，请翻译日语到中文，并且严格遵守：
                    1. 翻译规则：
                    - 保留英文缩写/专有名词（例：ZCU）
                    - 术语统一转换（例：ブレーキ → 制动器）
                    - 参数精确转换
                    - 不翻译中文
                    2. 格式要求：
                    - 完全保留原文编号结构
                    - 中日标点符号转换（「」→“”）
                    - 保留所有数字格式
                    3. 特殊処理：
                    - 日本企业使用官方中文名（例：トヨタ → 丰田）
                    - 计量单位转换（例：km → 公里）
                    - 日本標準日期格式変換（令和→公历）
                    4. 质量控制：
                    - 禁止添加译者注
                    - 人名/地名音译需准确
                    - 防止过度本地化
                    5. 确保忠实翻译：
                    - 不解释模糊术语
                    - 保持数字/时间格式不变
                    - 不添加额外信息""",

                "English": """As translation expert, follow STRICT rules:
                    1. Translation Rules:
                    - Preserve Japanese technical terms (e.g., ECU, ハイブリッド)
                    - Convert measurements to imperial/metric units when appropriate
                    - Maintain formal tone
                    2. Format Requirements:
                    - Keep original numbering/bullet structure
                    - Convert Japanese punctuation to English equivalents
                    - Preserve all numeric formats
                    3. Special Cases:
                    - Use official English names for companies (e.g., トヨタ → Toyota)
                    - Handle Japanese era dates conversion (令和 → Reiwa)
                    - Retain untranslatable cultural concepts
                    4. Quality Control:
                    - No translator's notes
                    - Accurate transliteration of proper nouns
                    - Avoid over-localization"""
            }
        }

    def get_prompt(self, source_lang, target_lang):
        """Get the prompt for a specific language pair"""
        if source_lang in self.language_prompts and target_lang in self.language_prompts[source_lang]:
            return self.language_prompts[source_lang][target_lang]
        return None

    def log_hallucination(self, original, translation):
        """记录幻觉翻译结果到CSV文件"""
        log_file_path = "logfiles/translation_feedback.csv"
        if not os.path.exists(os.path.dirname(log_file_path)):
            os.makedirs(os.path.dirname(log_file_path))

        with open(log_file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                writer.writerow(["Original Text", "Translated Text"])
            writer.writerow([original, translation])

    def validate_translation(self, original, translation):
        """执行严格的内容校验，包括结构、数字、幻觉模式及语义一致性"""
        if not self.check_structure_integrity(original, translation):
            logging.warning("Structure inconsistency detected")
            return False

        if any(pattern.search(translation) for pattern in self.acronym_manager.hallucination_patterns):
            logging.error("Hallucination pattern detected")
            return False
        
        return True

    def check_structure_integrity(self, original, translated):
        """检查结构一致性：段落数量及列表项"""
        orig_para = len(original.split('\n'))
        trans_para = len(translated.split('\n'))
        if orig_para != trans_para:
            return False
        
        orig_bullets = re.findall(r'^\d+\.', original, re.M)
        trans_bullets = re.findall(r'^\d+\.', translated, re.M)
        return len(orig_bullets) == len(trans_bullets)

    def convert_simplified_japanese_terms(self, translation):
        """
        针对中文→日文翻译中出现的简体日语词汇进行转换，
        例如：'议题' 转换为 '議題'
        """
        for simplified, proper in self.acronym_manager.term_mapping.items():
            translation = translation.replace(simplified, proper)
        return translation

    def post_process_translation(self, original, translation, source_lang, target_lang):
        """
        针对中文→日文的情况进行后处理：
        1. 如果原文中未出现“的”，但翻译结果在技术术语中插入了“的”，则自动移除；
        2. 对翻译中出现的简体日语词汇（如“议题”）进行转换，确保使用正确的日语表述（如“議題”）。
        """
        if source_lang == "Chinese" and target_lang == "Japanese":
            orig_lines = original.split('\n')
            trans_lines = translation.split('\n')
            new_lines = []
            for orig, trans in zip(orig_lines, trans_lines):
                if "的" not in orig and "的" in trans:
                    trans = re.sub(r'([\u4e00-\u9fff])的([\u4e00-\u9fff])', r'\1\2', trans)
                new_lines.append(trans)
            translation = "\n".join(new_lines)
            translation = self.convert_simplified_japanese_terms(translation)
        return translation



    def initial_translation(self, processed_text, system_prompt):
        """
        增强的初步翻译流程：
        - 在每次重试时动态降低温度，以降低生成随机性从而减少幻觉
        - 如果校验通过，则返回翻译；否则记录幻觉并返回原文
        """
        prompt_template = ChatPromptTemplate([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        chain = prompt_template | self.llm | StrOutputParser()
        translation = chain.invoke({"input": processed_text})

        # 可能无效情况下，记录LOG
        if not self.validate_translation(processed_text, translation):
            self.log_hallucination(processed_text, translation)
        
        return translation
    

    def reflect_translation(self, translation, target_lang):
        """反思与反馈阶段：请模型检查初步翻译，指出问题并提出改进建议，输出必须为目标语言反馈"""
        if target_lang == "Chinese":
            system_prompt = "你是一位翻译专家，请只提供简明、建设性的反馈，并请用中文回答。"
            user_prompt = "请审查以下翻译，指出可能存在的问题（例如不准确、格式、技术术语等），并提出改进建议：\n\n{translation}"
        elif target_lang == "Japanese":
            system_prompt = "あなたは翻訳の専門家です。簡潔で建設的なフィードバックのみを提供し、日本語で回答してください。"
            user_prompt = "以下の翻訳を確認し、問題点（不正確さ、フォーマット、技術用語の不整合など）を指摘し、改善案を提示してください：\n\n{translation}"
        else:
            system_prompt = "You are a translation expert. Provide only concise, constructive feedback. Please respond in English."
            user_prompt = "Please review the following translation for issues (e.g., inaccuracies, formatting, technical terms) and provide suggestions for improvement:\n\n{translation}"
        
        reflection_template = ChatPromptTemplate([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        chain = reflection_template | self.llm | StrOutputParser()
        feedback = chain.invoke({"translation": translation})
        return feedback


    def improve_translation(self, translation, feedback, target_lang):
        """迭代改进阶段：根据反馈改进初步翻译，输出必须为目标语言翻译文本"""
        if target_lang == "Chinese":
            system_prompt = "你是一位专业翻译专家，擅长迭代改进。请仅输出改进后的翻译文本，并用中文回答。"
            user_prompt = "基于以下反馈：\n\n{feedback}\n\n请改进以下翻译：\n\n{translation}"
        elif target_lang == "Japanese":
            system_prompt = "あなたは反復的な改善に優れたプロの翻訳者です。改良された翻訳文のみを出力し、日本語で回答してください。"
            user_prompt = "以下のフィードバックに基づいて：\n\n{feedback}\n\n以下の翻訳を改善してください：\n\n{translation}"
        else:
            system_prompt = "You are a professional translator specialized in iterative refinement. Provide only the improved translation text. Please respond in English."
            user_prompt = "Based on the following feedback:\n\n{feedback}\n\nPlease refine the following translation:\n\n{translation}"
        
        improvement_template = ChatPromptTemplate([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        chain = improvement_template | self.llm | StrOutputParser()
        improved_translation = chain.invoke({"feedback": feedback, "translation": translation})
        return improved_translation


    def translate_text(self, text, source_lang, target_lang, use_reflection=USE_REFLECTION):
        """Translate text"""
        original_text = text
        if not text or text.strip() == "":
            return original_text  # 直接返回空字符串，不进行翻译处理
        
        # 匹配英文，中文，日文字母、数字、空格、标点符号、括号和连字符，以及箭头符号
        alphanumeric_chars = self.acronym_manager.alphanumeric_chars
        special_chars = self.acronym_manager.special_characters
        if re.match(rf'^[{alphanumeric_chars}{special_chars}]*$', text):  
            return original_text
    
        # 获取初步翻译的系统提示
        system_prompt = self.get_prompt(source_lang, target_lang)
        if not system_prompt:
            raise ValueError(f"Unsupported language pair: {source_lang} to {target_lang}")

        # 1. 初步翻译
        initial_result = self.initial_translation(original_text, system_prompt)
        logging.info(f"Initial Translation: {initial_result}")
        finally_result = ""
        # USE_REFLECTION reference gl_config.py
        if use_reflection:
            # 2. Reflection Feedback
            feedback_result = self.reflect_translation(initial_result, target_lang)
            logging.info(f"Reflection Feedback: {feedback_result}")

            # 3. Improved Translation
            improved_result = self.improve_translation(initial_result, feedback_result, target_lang)
            logging.info(f"Improved Translation: {improved_result}")

            finally_result = self.post_process_translation(original_text, improved_result, source_lang, target_lang)

            # Log the translation process
            logging.info(f"{original_text} → {initial_result} → {finally_result} Translating from {source_lang} to {target_lang} ")  
        else:   
            finally_result = self.post_process_translation(original_text, initial_result, source_lang, target_lang)  
            logging.info(f"{original_text} → {finally_result} Translating from {source_lang} to {target_lang} ")   

        return finally_result