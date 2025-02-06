from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
import re

class TranslationCore:
    def __init__(self, model_name="qwen2.5:14b", endpoint_url="http://192.168.146.137:11434/v1", temperature=0.1):
        # 初始化模型
        self.llm = ChatOpenAI(model=model_name, base_url=endpoint_url, api_key="my-api-key", temperature=temperature)
        
        # 语言特定的提示词
        self.language_prompts = {
            "Chinese": {
                "English": """You are a professional Chinese to English translator specializing in automotive and technical documentation. Follow these rules:
                    1. Translation Style:
                    - Maintain formal and professional tone
                    - Use standard American English terminology
                    - Keep technical terms consistent with industry standards
                    2. Technical Terms:
                    - Preserve automotive industry terminology accuracy
                    - Maintain consistency in technical translations
                    3. Format Requirements:
                    - Preserve all original formatting and punctuation
                    - Do not add any explanatory notes or comments
                    4. Output: Provide only the translated text""",
                "Japanese": """You are a professional Chinese to Japanese translator specializing in automotive and technical documentation. Follow these rules:
                    1. Translation Style:
                    - Use appropriate keigo (敬語) for formal documents
                    - Maintain natural Japanese flow
                    - Ensure proper use of particles and sentence structure
                    2. Technical Terms:
                    - Use standard Japanese automotive terminology
                    - Maintain consistency in technical translations
                    3. Format Requirements:
                    - Preserve all original formatting
                    - Use appropriate Japanese punctuation
                    4. Output: Provide only the translated text"""
            },
            "English": {
                "Chinese": """You are a professional English to Chinese translator specializing in automotive and technical documentation. Follow these rules:
                    1. Translation Style:
                    - Use standard Simplified Chinese
                    - Maintain formal and professional tone
                    - Ensure natural Chinese expression
                    2. Technical Terms:
                    - Use standard Chinese automotive terminology
                    - Maintain consistency in technical translations
                    3. Format Requirements:
                    - Preserve all original formatting
                    - Use appropriate Chinese punctuation
                    4. Output: Provide only the translated text""",
                "Japanese": """You are a professional English to Japanese translator specializing in automotive and technical documentation. Follow these rules:
                    1. Translation Style:
                    - Use appropriate keigo (敬語) for formal documents
                    - Maintain natural Japanese flow
                    - Follow Japanese grammar structure
                    2. Technical Terms:
                    - Use standard Japanese automotive terminology
                    - Maintain consistency in technical translations
                    3. Format Requirements:
                    - Preserve all original formatting
                    - Use appropriate Japanese punctuation
                    4. Output: Provide only the translated text"""
            },
            "Japanese": {
                "Chinese": """You are a professional Japanese to Chinese translator specializing in automotive and technical documentation. Follow these rules:
                    1. Translation Style:
                    - Use standard Simplified Chinese
                    - Maintain formal and professional tone
                    - Ensure natural Chinese expression
                    2. Technical Terms:
                    - Use standard Chinese automotive terminology
                    - Maintain consistency in technical translations
                    3. Format Requirements:
                    - Preserve all original formatting
                    - Use appropriate Chinese punctuation
                    4. Output: Provide only the translated text""",
                "English": """You are a professional Japanese to English translator specializing in automotive and technical documentation. Follow these rules:
                    1. Translation Style:
                    - Maintain formal and professional tone
                    - Use standard American English terminology
                    - Ensure natural English expression
                    2. Technical Terms:
                    - Use standard English automotive terminology
                    - Maintain consistency in technical translations
                    3. Format Requirements:
                    - Preserve all original formatting
                    - Use appropriate English punctuation
                    4. Output: Provide only the translated text"""
            }
        }

    def get_prompt(self, source_lang, target_lang):
        """获取特定语言对的提示词"""
        if source_lang in self.language_prompts and target_lang in self.language_prompts[source_lang]:
            return self.language_prompts[source_lang][target_lang]
        return None

    def translate_text(self, text, source_lang, target_lang):
        """翻译文本"""
        if re.match(r'^\s*$', text):
            return ""
        elif re.match(r'^[a-zA-Z0-9]+$', text):
            return text
            
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
        response = chain.invoke({"input": text})
        return response
