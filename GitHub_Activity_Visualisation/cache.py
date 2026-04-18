import os
import pandas as pd
import json
import sys

from tqdm import tqdm

def cache_data(filename, func, *args, refresh=False, **kwargs):
    """
    Cache data to a JSON file.

    If the file exists and refresh=False, load it as a DataFrame.
    Otherwise, call `func` to generate data and save it.

    Returns:
        DataFrame if loaded from cache; otherwise the original data.
    """
    def log(msg):
        tqdm.write(msg)

    if os.path.exists(filename) and not refresh:
        try:
            log(f"Loading {filename} ")
            return pd.read_json(filename, orient='records')
        except Exception as e:
            log(f"[cache] load failed → {e}, refetching...")

    log(f"Fetching  {filename} ")

    data = func(*args, **kwargs)

    if isinstance(data, pd.DataFrame):
        data.to_json(filename, orient='records', indent=2)
    elif isinstance(data, (list, dict, set)):
        with open(filename, "w") as f:
            json.dump(list(data) if isinstance(data, set) else data, f, indent=2)
    else:
        raise TypeError(f"Unsupported type: {type(data)}")


    return data
