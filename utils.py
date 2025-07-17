import re

BOT_PATTERN = r'\bbot\b|\[bot\]|-bot'

def filter_bots(df, login_col='login'):
    if login_col in df.columns:
        return df[~df["login"].str.contains(r"\[bot\]", na=False)]
    return df


def classify_file(file_path):
    file_name = file_path.split('/')[-1].lower()
    if file_path.endswith('.py'):
        return 'Python'
    elif file_path.endswith('.html'):
        return 'HTML'
    elif file_path.endswith('.scss'):
        return 'SCSS'
    elif file_name == 'glossary.yml':
        return 'Glossary YAML'
    elif file_path.endswith(('.yml', '.yaml')):
        return 'YAML'
    elif file_path.endswith('.md'):
        return 'Markdown'
    else:
        return 'Other'
