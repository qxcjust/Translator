import click
from task_manager import translate_file

@click.command()
@click.argument('file_path')
@click.argument('output_path')
@click.argument('source_lang')
@click.argument('target_lang')
def cli_translate(file_path, output_path, source_lang, target_lang):
    translate_file.delay(file_path, output_path, source_lang, target_lang)

if __name__ == "__main__":
    cli_translate()