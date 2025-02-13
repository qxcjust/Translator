from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
import re
import logging
from acronym_manager import AcronymManager

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
                "English": """You are a professional translator for the automotive industry. Follow these rules:
                    1. Translation Rules:
                    - Keep acronyms and proper nouns unchanged (e.g., IEM, BMW).
                    - Maintain a professional and technical tone.
                    - Ensure consistency in technical terms.
                    2. Format Requirements:
                    - Preserve original formatting.
                    - Do not add explanations, comments, or footnotes.
                    3. Output Requirements:
                    - Only provide the translated text without any additional information.
                    4. Special Cases:
                    - Use official English names for companies and locations.
                    - Keep unknown acronyms unchanged.""",

                "Japanese": """自動車産業の専門翻訳者として、以下のルールに従ってください：
                    1. 翻訳ルール：
                    - 略語や固有名詞（例：IEM、BMW、woP、iAuto、ZCU_FR等）はそのまま維持。
                    - 正確かつ専門的な日本語表現を使用。
                    - 技術用語の一貫性を保持。
                    - 自然な日本語表現を使用し、**簡体字を日本語で使われる漢字に変換**してください。
                    - **簡体字（例：「体」、「国」、「区」）は日本語の漢字（例：「體」、「國」、「區」）に置き換えてください**。
                    - 外来語は適切なカタカナ表記に変換（例：demo → デモ，base → ベース）。
                    - **文頭の数字や記号（例：「1.」「2.」「3.」）は絶対に変更しないでください**。
                    - **数字や時間表記（例：「3.29」）は変更せず、そのまま保持**してください。
                    - **原文のラベル構造（例：「形式：」「内容：」）は日本語に翻訳すること**
                    - **コロン（：）前のラベル語句は必ず翻訳し、記号は日本語フォーマットに変換**                    
                    2. 形式要件：
                    - **注釈や説明文を一切追加しないこと**。
                    - **翻訳結果のみを出力し、理由や説明を含めないこと**。
                    - 元のフォーマット（数字、句読点など）を維持する。
                    3. 出力要件：
                    - **翻訳されたテキストのみを提供**してください。それ以外の情報は含めないこと。
                    4. 特殊なケース：
                    - 会社名や地名は公式の日本語表記を使用。
                    - 不明な略語はそのまま維持。
                    5. **漢字変換の例**：
                    - 簡体字「詳細」→ 日本語「詳細」
                    - 簡体字「議題」→ 日本語「議題」
                    **注意**：すべての中国簡体字は、日本語で一般的に使用される漢字に変換してください。
                    - 特定の翻訳例：
                    - 「Why demonstration by LLM？」 → 「なぜLLMによるデモ？」
                    - **原文が中文である場合は、日本語に翻訳してください。**""",
            },

            "English": {
                "Chinese": """作为汽车行业的专业翻译，请严格遵循以下规则：
                    1. 翻译规则：
                    - 略語や固有名詞（例：IEM、BMW、woP、iAuto等）はそのまま維持。
                    - 采用专业且正式的中文表达。
                    - 确保技术术语的一致性。
                    2. 格式要求：
                    - 维持原始格式。
                    - 不添加解释、注释或额外内容。
                    3. 输出要求：
                    - 仅提供翻译文本，不包含其他信息。
                    4. 特殊情况：
                    - 公司和地名使用官方的中文名称。
                    - 未知缩写保持原样。""",

                "Japanese": """自動車産業の専門翻訳者として、以下のルールに従ってください：
                    1. 翻訳ルール：
                    - 略語や固有名詞（例：IEM、BMW、woP、iAuto、ZCU_FR等）はそのまま維持。
                    - 正確かつ専門的な日本語表現を使用。
                    - 技術用語の一貫性を保持。
                    - 自然な日本語表現を使用し、**簡体字を日本語で使われる漢字に変換**してください。
                    - **簡体字（例：「体」、「国」、「区」）は日本語の漢字（例：「體」、「國」、「區」）に置き換えてください**。
                    - 外来語は適切なカタカナ表記に変換（例：demo → デモ，base → ベース）。
                    - **文頭の数字や記号（例：「1.」「2.」「3.」）は絶対に変更しないでください**。
                    - **数字や時間表記（例：「3.29」）は変更せず、そのまま保持**してください。
                    - **原文のラベル構造（例：「形式：」「内容：」）は日本語に翻訳すること**
                    - **コロン（：）前のラベル語句は必ず翻訳し、記号は日本語フォーマットに変換**                    
                    2. 形式要件：
                    - **注釈や説明文を一切追加しないこと**。
                    - **翻訳結果のみを出力し、理由や説明を含めないこと**。
                    - 元のフォーマット（数字、句読点など）を維持する。
                    3. 出力要件：
                    - **翻訳されたテキストのみを提供**してください。それ以外の情報は含めないこと。
                    4. 特殊なケース：
                    - 会社名や地名は公式の日本語表記を使用。
                    - 不明な略語はそのまま維持。
                    5. **漢字変換の例**：
                    - 簡体字「详细」→ 日本語「詳細」
                    - 簡体字「议题」→ 日本語「議題」
                    **注意**：すべての中国簡体字は、日本語で一般的に使用される漢字に変換してください。"""
            },

            "Japanese": {
                "Chinese": """作为汽车行业的专业翻译，请严格遵循以下规则：
                    1. 翻译规则：
                    - 保持缩写词和专有名词不变（如 IEM、BMW）。
                    - 采用专业且正式的中文表达。
                    - 确保技术术语的一致性。
                    2. 格式要求：
                    - 维持原始格式。
                    - 不添加解释、注释或额外内容。
                    3. 输出要求：
                    - 仅提供翻译文本，不包含其他信息。
                    4. 特殊情况：
                    - 公司和地名使用官方的中文名称。
                    - 未知缩写保持原样。""",

                "English": """You are a professional translator for the automotive industry. Follow these rules:
                    1. Translation Rules:
                    - Keep acronyms and proper nouns unchanged (e.g., IEM, BMW).
                    - Maintain a professional and technical tone.
                    - Ensure consistency in technical terms.
                    2. Format Requirements:
                    - Preserve original formatting.
                    - Do not add explanations, comments, or footnotes.
                    3. Output Requirements:
                    - Only provide the translated text without any additional information.
                    4. Special Cases:
                    - Use official English names for companies and locations.
                    - Keep unknown acronyms unchanged."""
            }
        }

    def get_prompt(self, source_lang, target_lang):
        """Get the prompt for a specific language pair"""
        if source_lang in self.language_prompts and target_lang in self.language_prompts[source_lang]:
            return self.language_prompts[source_lang][target_lang]
        return None

    def preprocess_text(self, text):
        """Preprocess text to protect special markers"""
        protected_terms = self.acronym_manager.protected_terms
        # Protect acronyms composed of uppercase letters
        acronyms = re.finditer(r'\b[a-zA-Z0-9]+\b', text)
        for i, match in enumerate(acronyms):
            key = f"__ACRONYM_{i}__"
            protected_terms[key] = match.group()
            text = text.replace(match.group(), key)
        
        # 保护箭头符号
        arrows = re.finditer(r'[↑↓←→↗↙]', text)
        for i, match in enumerate(arrows):
            key = f"__ARROW_{i}__"
            protected_terms[key] = match.group()
            text = text.replace(match.group(), key)
            
        return text, protected_terms

    def postprocess_text(self, text, protected_terms):
        """Postprocess text to restore special markers"""
        # Ensure the order of restoration is correct
        for key, value in reversed(list(protected_terms.items())):
            text = text.replace(key, value)
        return text

    def translate_text(self, text, source_lang, target_lang):
        """Translate text"""
        if not text or text.strip() == "":
            return ""  # 直接返回空字符串，不进行翻译处理
        
        # 匹配英文，中文，日文字母、数字、空格、标点符号、括号和连字符，以及箭头符号
        alphanumeric_chars = self.acronym_manager.alphanumeric_chars
        special_chars = self.acronym_manager.special_characters
        if re.match(rf'^[{alphanumeric_chars}{special_chars}]*$', text):  
            return text
    
        # Preprocess text
        processed_text, protected_terms = self.preprocess_text(text)
        
        # Get the prompt for the specific language pair
        system_prompt = self.get_prompt(source_lang, target_lang)
        if not system_prompt:
            raise ValueError(f"Unsupported language pair: {source_lang} to {target_lang}")

        # Create a prompt template for the specific language pair
        prompt = ChatPromptTemplate([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        # Build the translation chain
        chain = prompt | self.llm | StrOutputParser()
        
        # Execute translation
        response = chain.invoke({"input": processed_text})
        
        # Postprocess text
        final_text = self.postprocess_text(response, protected_terms)
        # Log the translation process
        logging.info(f"{text} → {processed_text} → {response} → {final_text} Translating from {source_lang} to {target_lang} ")        

        return final_text