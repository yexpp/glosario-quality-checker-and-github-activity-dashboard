import re
import os
import pandas as pd
import hashlib

# Pattern to detect bot users based on login names
BOT_PATTERN = r'\bbot\b|\[bot\]|-bot'

# Mapping from file extensions to language or file types
EXTENSION_MAP = {
    '.py': 'Python',
    '.html': 'HTML',
    '.scss': 'SCSS',
    '.yml': 'YAML',
    '.yaml': 'YAML',
    '.md': 'Markdown'
}

def filter_bots(df, login_col='login'):
    """
    Remove rows where the login column matches common bot patterns.

    Parameters:
        df (pd.DataFrame): Input DataFrame containing a login column.
        login_col (str): Name of the login column.

    Returns:
        pd.DataFrame: Filtered DataFrame without bot users.
    """
    if login_col in df.columns:
        return df[~df[login_col].str.contains(BOT_PATTERN, flags=re.IGNORECASE, na=False, regex=True)]
    return df


def classify_file(file_path):
    """
    Classify the type of a file based on its extension or filename.

    Parameters:
        file_path (str): Path to the file.

    Returns:
        str: Detected file type or 'Misc' if unknown.
    """
    file_name = os.path.basename(file_path).lower()

    # Special case: glossary file
    if file_name == 'glossary.yml':
        return 'Glossary YAML'

    ext = os.path.splitext(file_name)[1]
    return EXTENSION_MAP.get(ext, 'Misc')


def anonymize_login(df, login_col='login', salt='default_salt'):
    """
    Anonymize user login names by hashing them with a salt.

    Parameters:
        df (pd.DataFrame): Input DataFrame with login column.
        login_col (str): Name of the login column.
        salt (str): Salt string used for consistent hashing.

    Returns:
        pd.DataFrame: DataFrame with anonymized login values.
    """
    if login_col not in df.columns:
        return df

    def make_anon(u):
        if pd.isna(u):
            return u
        h = hashlib.sha256((str(u) + salt).encode('utf-8')).hexdigest()
        return f'user_{h[:8]}'

    df[login_col] = df[login_col].apply(make_anon)
    return df
