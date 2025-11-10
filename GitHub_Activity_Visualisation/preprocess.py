import pandas as pd

def preprocess_datetime_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Convert specified columns to datetime format and remove timezone information.

    Parameters:
        df (pd.DataFrame): The input DataFrame.
        columns (list[str]): List of column names to be converted.

    Returns:
        pd.DataFrame: The processed DataFrame with timezone-naive datetime columns.
    """
    if not df.empty:
        for col in columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col]).dt.tz_localize(None)
    return df


def preprocess_commit_data(commit_df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess commit datetime column.
    """
    return preprocess_datetime_columns(commit_df, ["date"])


def preprocess_pr_data(pr_df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess pull request datetime columns.
    """
    return preprocess_datetime_columns(pr_df, ["created_at", "merged_at"])


def preprocess_issue_data(issue_df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess issue datetime columns.
    """
    return preprocess_datetime_columns(issue_df, ["created_at", "closed_at"])


def preprocess_comments_data(comments_df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess comment datetime column.
    """
    return preprocess_datetime_columns(comments_df, ["created_at"])
