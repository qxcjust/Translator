from ollama_client import OllamaClient

class TranslationCore:
    def __init__(self, ollama_api_key):
        self.ollama_client = OllamaClient(api_key=ollama_api_key)

    def translate_text(self, text, source_lang, target_lang):
        return self.ollama_client.translate_text(text, source_lang, target_lang)