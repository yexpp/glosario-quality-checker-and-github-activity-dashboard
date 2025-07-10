import os
import pandas as pd

def cache_data(filename, func, *args, refresh=False, **kwargs):
    if os.path.exists(filename) and not refresh:
        try:
            print(f"Loading from cache: {filename}")
            return pd.read_pickle(filename)
        except Exception as e:
            print(f"Failed to load cache ({e}), fetching fresh data...")
    print(f"Fetching data and saving to cache: {filename}")
    data = func(*args, **kwargs)
    data.to_pickle(filename)
    return data
