from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
import re

class TranslationCore:
    def __init__(self, model_name="qwen2.5:14b", endpoint_url="http://192.168.146.137:11434/v1", temperature=0.0):
        # 初始化模型
        self.llm = ChatOpenAI(model=model_name, base_url=endpoint_url, api_key="my-api-key", temperature=temperature)
        
        # 语言特定的提示词
        self.language_prompts = {
            "Chinese": {
                "English": """You are a professional translator. Follow these rules:
                    1. Translation Rules:
                    - Keep acronyms and proper nouns unchanged (e.g., IEM, BMW, etc.)
                    - Maintain formal and professional tone
                    - Keep technical terms consistent
                    2. Format Requirements:
                    - Preserve original punctuation and formatting
                    - Do not add any explanatory notes or comments
                    3. Output: Return only the translated text
                    4. Special Cases:
                    - Company names and locations should follow official English names if available
                    - If unsure about an acronym, keep it as is""",
                "Japanese": """You are a professional translator. Follow these rules:
                    1. Translation Rules:
                    - Keep acronyms and proper nouns unchanged (e.g., IEM, BMW, etc.)
                    - Use appropriate keigo (敬語) for formal documents
                    - Maintain natural Japanese flow
                    2. Format Requirements:
                    - Use appropriate Japanese punctuation
                    - Do not add any explanatory notes
                    3. Output: Return only the translated text
                    4. Special Cases:
                    - Company names and locations should follow official Japanese names if available
                    - If unsure about an acronym, keep it as is"""
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

    def preprocess_text(self, text):
        """预处理文本，保护特殊标记"""
        # 使用正则表达式找出并保护缩写词
        protected_terms = {"IEM","TSAP"}
        
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
        
        return final_text
