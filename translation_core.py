from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
import re

class TranslationCore:
    def __init__(self, model_name="deepseek-v2:16b", endpoint_url="http://192.168.146.137:11434/v1", temperature=0):
        # 初始化模型
        self.llm = ChatOpenAI(model=model_name, base_url=endpoint_url, api_key="my-api-key", temperature=temperature)
        
        self.prompt = ChatPromptTemplate([
            ("system", 
                """You are a professional translation engine for the automotive industry. Strictly follow the following rules:
                    1. When the input is {lg_from}: Accurately translate into {lg_to}, maintaining consistency of terms.
                    2. Prohibit any additional content: including but not limited to:
                        - Explanatory notes
                        - Formatting symbols (such as **, <> etc.)
                        - Prohibit any form of thinking process (including <think> etc. tags)
                        - Prohibit including any thoughts or reasoning in the output.
                    3. Punctuation handling: Retain original symbols.
                    4. The output should only contain the translated text, not the original text."""
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
