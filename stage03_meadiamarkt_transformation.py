import pandas as pd
import time
from datetime import datetime
import ydata_profiling
from pandas_profiling import ProfileReport
import numpy as np
import re
import requests

df = pd.read_csv('data/cleaned_mediamarkt.csv')

df_space_nan = df[pd.isnull(df['storage'])]
storage_verification = df_space_nan['source']
for index, url in storage_verification.items():
    print(f"{index}: {url}")
    
storage_manually = {
    128: '32 GB',
    137: '8 GB'
}

# Update the 'size' column in the DataFrame
for index, storage in storage_manually.items():
    df.at[index, 'storage'] = storage

def convert_to_gb(value):
    if isinstance(value, str):
        if 'TB' in value:
            # Convert TB to GB by multiplying by 1000
            return int(float(value.replace('TB', '')) * 1000)
        elif 'GB' in value:
            # Simply remove 'GB' from the string and convert to int
            return int(value.replace('GB', ''))
    elif isinstance(value, (int, float)):
        # If it's a numerical type, we assume it's already in GB
        return int(value)
    else:
        # If the value is neither string nor numeric, we may want to handle this differently
        # For example, you could return None or raise an error
        return None

# Apply the conversion function to the 'storage' column
df['memory_GB'] = df['storage'].apply(convert_to_gb)

df['rating_100'] = df['rating'] * 20

df['screen_price_ratio'] = df['price'] / df['size']

file_name = "data/stage03_mediamarkt.csv"
# Save the DataFrame to CSV in the same directory as the script
df.to_csv(file_name, index=False)

