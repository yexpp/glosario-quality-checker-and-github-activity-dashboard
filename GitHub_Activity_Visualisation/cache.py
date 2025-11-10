import os
import pandas as pd
import json

def cache_data(filename, func, *args, refresh=False, **kwargs):
    if os.path.exists(filename) and not refresh:
        try:
            print(f"Loading from cache: {filename}")
            return pd.read_json(filename, orient='records')
        except Exception as e:
            print(f"Failed to load cache ({e}), fetching fresh data...")

    print(f"Fetching data and saving to cache: {filename}")
    data = func(*args, **kwargs)

    if isinstance(data, pd.DataFrame):
        data.to_json(filename, orient='records', indent=2)
    elif isinstance(data, (list, dict, set)):

        with open(filename, 'w') as f:
            json.dump(list(data) if isinstance(data, set) else data, f, indent=2)
    else:
        raise TypeError(f"Unsupported data type for caching: {type(data)}")

    return data
