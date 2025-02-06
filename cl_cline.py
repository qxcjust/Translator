import argparse
import logging
from file_translator import FileTranslator

# 配置日志记录
logging.basicConfig(level=logging.DEBUG)

def main():
    parser = argparse.ArgumentParser(description="Translate files using the FileTranslator class.")
    parser.add_argument("file_path", type=str, help="Path to the input file")
    parser.add_argument("output_path", type=str, help="Path to the output file")
    parser.add_argument("source_lang", type=str, help="Source language code (e.g., English)")
    parser.add_argument("target_lang", type=str, help="Target language code (e.g., Chinese)")
    args = parser.parse_args()

    translator = FileTranslator()
    try:
        translator.translate_file(args.file_path, args.output_path, args.source_lang, args.target_lang, None)
        logging.info(f"Translation completed successfully. Output file: {args.output_path}")
    except Exception as e:
        logging.error(f"Translation failed: {e}")
        raise

if __name__ == "__main__":
    main()