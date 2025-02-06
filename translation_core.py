from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
import re

class TranslationCore:
    def __init__(self, model_name="qwen2.5:14b", endpoint_url="http://192.168.146.137:11434/v1", temperature=0.1):
        # 初始化模型
        self.llm = ChatOpenAI(model=model_name, base_url=endpoint_url, api_key="my-api-key", temperature=temperature)
        
        self.prompt = ChatPromptTemplate([
            ("system", 
                """You are a professional translation engine specializing in the automotive industry. Follow these strict rules:
                    1. Translation Accuracy:
                    - When given text in {lg_from}, translate it precisely into {lg_to}.
                    - Ensure consistent use of industry-specific terminology.
                    2. Content Restrictions:
                    - Do not add any extra content such as explanatory notes, commentary, or any tags (e.g., <think>).
                    - Do not include any formatting symbols beyond those present in the original text (e.g., **, <>, etc.).
                    - Avoid any indication of your internal thought process or reasoning.
                    3. Punctuation and Formatting:
                    - Retain all original punctuation and formatting.
                    4. Output Requirements:
                    - The final output must include only the translated text, with no reference to the original input.
                    """
                ),
            ("user", "{input}")
        ])

        # 创建输出解析器
        self.output_parser = StrOutputParser()
        
        # 构建聊天链
        self.chain = self.prompt | self.llm | self.output_parser

    def translate_text(self, text, source_lang, target_lang):
        if re.match(r'^\s*$', text):
            translated_text = ""
        elif re.match(r'^[a-zA-Z0-9]+$', text):
            translated_text = text
        else:
            response = self.chain.invoke({"input": text, "lg_from": source_lang, "lg_to": target_lang})
            translated_text = response
        return translated_text
