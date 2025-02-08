from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
import re
import logging


# 配置日志记录
logging.basicConfig(level=logging.INFO)

class TranslationCore:
    def __init__(self, model_name="qwen2.5:14b", endpoint_url="http://192.168.146.137:11434/v1", temperature=0.0):
        # 初始化模型
        self.llm = ChatOpenAI(model=model_name, base_url=endpoint_url, api_key="my-api-key", temperature=temperature)
        
        # 使用目标语言编写提示词
        self.language_prompts = {
            "Chinese": {
                "English": """You are a professional automotive industry translator. Rules:
                    1. Translation Rules:
                    - Keep acronyms and proper nouns unchanged (e.g., IEM, BMW)
                    - Maintain professional tone
                    - Keep technical terms consistent
                    2. Format Requirements:
                    - Preserve original formatting
                    - No explanatory notes
                    3. Output: Translated text only
                    4. Special Cases:
                    - Use official English names for companies and locations
                    - Keep unknown acronyms unchanged""",
                    
                "Japanese": """自動車産業の専門翻訳者として、以下のルールに従ってください：
                    1. 翻訳ルール：
                    - 略語と固有名詞は変更しない（例：IEM、BMW）
                    - 自然な日本語の表現を維持
                    - 専門用語の一貫性を保つ
                    - 外来語は適切なカタカナ表記に変換（例：demo→デモ）
                    2. 形式要件：
                    - 原文の形式を維持
                    - 説明的な注釈を付けない
                    3. 出力：翻訳テキストのみ
                    4. 特殊なケース：
                    - 会社名や地名は公式の日本語名称を使用
                    - 不明な略語はそのまま維持
                    5. カタカナ変換規則：
                    - demo → デモ
                    - test → テスト
                    - space → スペース
                    - system → システム
                    注意：英単語が含まれている場合は、適切な日本語カタカナ表記に変換してください。"""
            },
            "English": {
                "Chinese": """作为汽车行业专业翻译，请遵循以下规则：
                    1. 翻译规则：
                    - 保持缩写词和专有名词不变（如 IEM、BMW）
                    - 使用专业的中文表达
                    - 保持术语一致性
                    2. 格式要求：
                    - 保持原有格式
                    - 不添加解释说明
                    3. 输出：仅输出翻译文本
                    4. 特殊情况：
                    - 使用公司和地点的官方中文名称
                    - 未知缩写保持原样""",
                    
                "Japanese": """自動車産業の専門翻訳者として、以下のルールに従ってください：
                    1. 翻訳ルール：
                    - 略語と固有名詞は変更しない（例：IEM、BMW）
                    - 自然な日本語の表現を維持
                    - 専門用語の一貫性を保つ
                    - 外来語は適切なカタカナ表記に変換（例：demo→デモ）
                    2. 形式要件：
                    - 原文の形式を維持
                    - 説明的な注釈を付けない
                    3. 出力：翻訳テキストのみ
                    4. 特殊なケース：
                    - 会社名や地名は公式の日本語名称を使用
                    - 不明な略語はそのまま維持
                    5. カタカナ変換規則：
                    - demo → デモ
                    - test → テスト
                    - space → スペース
                    - system → システム
                    注意：英単語が含まれている場合は、適切な日本語カタカナ表記に変換してください。"""
            },
            "Japanese": {
                "Chinese": """作为汽车行业专业翻译，请遵循以下规则：
                    1. 翻译规则：
                    - 保持缩写词和专有名词不变（如 IEM、BMW）
                    - 使用专业的中文表达
                    - 保持术语一致性
                    2. 格式要求：
                    - 保持原有格式
                    - 不添加解释说明
                    3. 输出：仅输出翻译文本
                    4. 特殊情况：
                    - 使用公司和地点的官方中文名称
                    - 未知缩写保持原样""",
                    
                "English": """You are a professional automotive industry translator. Rules:
                    1. Translation Rules:
                    - Keep acronyms and proper nouns unchanged (e.g., IEM, BMW)
                    - Maintain professional tone
                    - Keep technical terms consistent
                    2. Format Requirements:
                    - Preserve original formatting
                    - No explanatory notes
                    3. Output: Translated text only
                    4. Special Cases:
                    - Use official English names for companies and locations
                    - Keep unknown acronyms unchanged"""
            }
        }

    def get_prompt(self, source_lang, target_lang):
        """获取特定语言对的提示词"""
        if source_lang in self.language_prompts and target_lang in self.language_prompts[source_lang]:
            return self.language_prompts[source_lang][target_lang]
        return None

    def preprocess_text(self, text):
        """预处理文本，保护特殊标记"""
        # 使用正则表达式找出并保护缩写词
        protected_terms = {}
        protected_terms['IEM'] = "IEM"
        protected_terms['TSAP'] = "TSAP"
        
        # 保护大写字母组成的缩写词
        acronyms = re.finditer(r'\b[A-Z]{2,}\b', text)
        for i, match in enumerate(acronyms):
            key = f"__ACRONYM_{i}__"
            protected_terms[key] = match.group()
            text = text.replace(match.group(), key)
        
        return text, protected_terms

    def postprocess_text(self, text, protected_terms):
        """后处理文本，恢复特殊标记"""
        for key, value in protected_terms.items():
            text = text.replace(key, value)
        return text

    def translate_text(self, text, source_lang, target_lang):
        """翻译文本"""
        if re.match(r'^\s*$', text):
            return ""
        elif re.match(r'^[a-zA-Z0-9]+$', text):
            return text
            
        # 预处理文本
        processed_text, protected_terms = self.preprocess_text(text)
        
        # 获取特定语言对的提示词
        system_prompt = self.get_prompt(source_lang, target_lang)
        if not system_prompt:
            raise ValueError(f"Unsupported language pair: {source_lang} to {target_lang}")

        # 创建特定语言对的提示模板
        prompt = ChatPromptTemplate([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        # 构建翻译链
        chain = prompt | self.llm | StrOutputParser()
        
        # 执行翻译
        response = chain.invoke({"input": processed_text})
        
        # 后处理文本
        final_text = self.postprocess_text(response, protected_terms)
        # 翻译前后结果，log输出
        logging.info(f"{text} → {processed_text} → {response} → {final_text} Translating from {source_lang} to {target_lang} ")        

        return final_text
