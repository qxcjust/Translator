from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
import re
import logging
from acronym_manager import AcronymManager
import os
import datetime
import csv

# 配置日志记录
logging.basicConfig(level=logging.INFO)

class TranslationCore:
    def __init__(self, model_name="qwen2.5:14b", endpoint_url="http://192.168.146.137:11434/v1", temperature=0.2):
        # Initialize model
        self.llm = ChatOpenAI(model=model_name, base_url=endpoint_url, api_key="my-api-key", temperature=temperature)
        # 创建 AcronymManager 实例
        self.acronym_manager = AcronymManager()
        
        # Write prompts in target language
        self.language_prompts = {
            "Chinese": {
                "English": """You are a professional automotive translator. STRICT RULES:
                    1. TRANSLATION RULES:
                    - PRESERVE acronyms/proper nouns (e.g., ZCU) 
                    - MAINTAIN technical tone
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
                "Japanese": """自動車専門翻訳者として厳格に遵守:
                    1. 翻訳規則:
                    - 略語/固有名詞保持（例：ZCU）
                    - 専門的表現厳守
                    - 技術用語一貫性保持
                    - 簡体字→日本語漢字変換必須
                    2. 形式規則:
                    - 原文フォーマット厳守
                    - 説明/注釈厳禁
                    - 箇条書き形式保持
                    3. 出力制御:
                    - 翻訳文のみ出力
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
                "Chinese": """作为汽车行业专业翻译，请严格遵循：
                    1. 翻译规则：
                    - 保留英文缩写/专有名词（例：ZCU）
                    - 保持技术文档的专业语气
                    - 确保技术术语一致性
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

                "Japanese": """自動車技術翻訳者として厳守事項：
                    1. 翻訳規則：
                    - 英語略語/固有名詞保持（例：ZCU）
                    - 技術文書の専門的表現維持
                    - 技術用語の一貫性確保
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
                "Chinese": """作为汽车行业专业译员，请遵守：
                    1. 翻译规则：
                    - 保留日语汉字/片假名术语（例：ECU、ハイブリッド）
                    - 专业术语统一转换（例：ブレーキ → 制动器）
                    - 技術参数精确转换
                    2. 格式要求：
                    - 完全保留原文编号结构
                    - 中日标点符号转换（「」→“”）
                    - 保留所有数字格式
                    3. 特殊処理：
                    - 日本企业使用官方中文名（例：トヨタ → 丰田）
                    - 计量单位转换（例：km → 公里）
                    - 日本標準日期格式変換（令和→公历）
                    4. 質量制御：
                    - 禁止添加译者注
                    - 人名/地名音译需准确
                    - 防止过度本地化""",

                "English": """As automotive translation expert, follow STRICT rules:
                    1. Translation Rules:
                    - Preserve Japanese technical terms (e.g., ECU, ハイブリッド)
                    - Convert measurements to imperial/metric units when appropriate
                    - Maintain formal technical tone
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
        """执行严格的内容校验"""
        # 结构完整性校验
        if self.check_structure_integrity(original, translation):
            logging.warning("Structure inconsistency detected")
            return False
        
        # 幻覚パターンチェック
        if any(pattern.search(translation) for pattern in self.acronym_manager.hallucination_patterns):
            logging.error("Hallucination pattern detected")
            return False
        
        # 数字保存チェック
        if not self.check_numeric_consistency(original, translation):
            logging.warning("Numeric inconsistency found")
            return False
        
        return True

    def check_structure_integrity(self, original, translated):
        """检查结构一致性"""
        # 比較段落数
        orig_para = len(original.split('\n'))
        trans_para = len(translated.split('\n'))
        if orig_para != trans_para:
            return True
        
        # 检查列表项一致性
        orig_bullets = re.findall(r'^\d+\.', original, re.M)
        trans_bullets = re.findall(r'^\d+\.', translated, re.M)
        return len(orig_bullets) != len(trans_bullets)

    def check_numeric_consistency(self, original, translated):
        """数字一致性校验"""
        orig_numbers = re.findall(r'\b\d+\.?\d*\b', original)
        trans_numbers = re.findall(r'\b\d+\.?\d*\b', translated)
        return orig_numbers == trans_numbers
    


    def initial_translation(self, processed_text, system_prompt):
        """增强的初步翻译流程"""
        max_retry = 3
        for attempt in range(max_retry):
            prompt_template = ChatPromptTemplate([
                ("system", system_prompt),
                ("user", "{input}")
            ])
            chain = prompt_template | self.llm | StrOutputParser()
            translation = chain.invoke({"input": processed_text})
            
            # 执行严格校验
            if self.validate_translation(processed_text, translation):
                return translation
            logging.warning(f"Validation failed, retrying ({attempt+1}/{max_retry})")
        
        self.log_hallucination(processed_text, translation)
        return processed_text

    def reflect_translation(self, translation, target_lang):
        """反思与反馈阶段：请模型检查初步翻译，指出问题并提出改进建议，输出必须为目标语言反馈"""
        if target_lang == "Chinese":
            system_prompt = "你是一位汽车行业的翻译专家，请只提供简明、建设性的反馈，并请用中文回答。"
            user_prompt = "请审查以下翻译，指出可能存在的问题（例如不准确、格式、技术术语等），并提出改进建议：\n\n{translation}"
        elif target_lang == "Japanese":
            system_prompt = "あなたは自動車産業の翻訳の専門家です。簡潔で建設的なフィードバックのみを提供し、日本語で回答してください。"
            user_prompt = "以下の翻訳を確認し、問題点（不正確さ、フォーマット、技術用語の不整合など）を指摘し、改善案を提示してください：\n\n{translation}"
        else:
            system_prompt = "You are a translation expert for the automotive industry. Provide only concise, constructive feedback. Please respond in English."
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
            system_prompt = "你是一位汽车行业的专业翻译专家，擅长迭代改进。请仅输出改进后的翻译文本，并用中文回答。"
            user_prompt = "基于以下反馈：\n\n{feedback}\n\n请改进以下翻译：\n\n{translation}"
        elif target_lang == "Japanese":
            system_prompt = "あなたは自動車産業の反復的な改善に優れたプロの翻訳者です。改良された翻訳文のみを出力し、日本語で回答してください。"
            user_prompt = "以下のフィードバックに基づいて：\n\n{feedback}\n\n以下の翻訳を改善してください：\n\n{translation}"
        else:
            system_prompt = "You are a professional translator specialized in iterative refinement for the automotive industry. Provide only the improved translation text. Please respond in English."
            user_prompt = "Based on the following feedback:\n\n{feedback}\n\nPlease refine the following translation:\n\n{translation}"
        
        improvement_template = ChatPromptTemplate([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        chain = improvement_template | self.llm | StrOutputParser()
        improved_translation = chain.invoke({"feedback": feedback, "translation": translation})
        return improved_translation


    def translate_text(self, text, source_lang, target_lang):
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

        # 2. 反思与反馈
        feedback_result = self.reflect_translation(initial_result, target_lang)
        logging.info(f"Reflection Feedback: {feedback_result}")

        # 3. 迭代改进
        improved_result = self.improve_translation(initial_result, feedback_result, target_lang)
        logging.info(f"Improved Translation: {improved_result}")

        # Log the translation process
        logging.info(f"{original_text} → {initial_result} → {improved_result} Translating from {source_lang} to {target_lang} ")   

        return improved_result