import os
import pandas as pd
import json

def cache_data(filename, func, *args, refresh=False, **kwargs):
    """
    Data caching function: reads from a local cache file if it exists; otherwise,
    calls the provided function to generate data and saves it to the cache.

    Parameters:
        filename (str): Path to the cache file.
        func (callable): Function used to generate the data.
        *args: Additional positional arguments passed to the function.
        refresh (bool): Whether to force refresh the cache.
        **kwargs: Additional keyword arguments passed to the function.

    Returns:
        data: The loaded or generated data (can be a DataFrame, list, dict, or set).
    """
    if os.path.exists(filename) and not refresh:
        try:
            print(f"Loading from cache: {filename}")
            return pd.read_json(filename, orient='records')
        except Exception as e:
            print(f"Failed to load cache ({e}), fetching fresh data...")

    print(f"Fetching data and saving to cache: {filename}")
    data = func(*args, **kwargs)

    if isinstance(data, pd.DataFrame):
        try:
            data.to_json(filename, orient='records', indent=2)
        except Exception as e:
            print(f"Failed to save DataFrame to cache: {e}")
    elif isinstance(data, (list, dict, set)):
        try:
            with open(filename, 'w') as f:
                json.dump(list(data) if isinstance(data, set) else data, f, indent=2)
        except Exception as e:
            print(f"Failed to save JSON to cache: {e}")
    else:
        raise TypeError(f"Unsupported data type for caching: {type(data)}")

    return data
