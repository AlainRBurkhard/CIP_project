""" 
Stage03 - Variables Transformation

Input - stage02_cleaned_mediamarkt.csv.csv
Output - stage03_mediamarkt.csv
 
"""

################################################################################################################################
                    # Library importing
import pandas as pd
import time
from datetime import datetime
import numpy as np
import re
import requests

################################################################################################################################
                    # Library importing
    
df = pd.read_csv('data/stage02_cleaned_mediamarkt.csv')


def convert_to_gb(value):
    if isinstance(value, str):
        if 'TB' in value:
            # Convert TB to GB by multiplying by 1000
            return int(float(value.replace('TB', '')) * 1000)
        elif 'GB' in value:

            return int(value.replace('GB', ''))
    elif isinstance(value, (int, float)):

        return int(value)
    else:
 
        return None

# Apply the conversion function to the 'storage' column
df['memory_GB'] = df['storage'].apply(convert_to_gb)

df['rating_100'] = df['rating'] * 20

df['screen_price_ratio'] = df['price'] / df['size']

new_order = ['brand', 'model', 'memory_GB', 'camera_MP', 'size', 'color', 'rating_100', 'reviews_count', 'delivery_time', 'price',  'screen_price_ratio', 'source', 'date']
df = df[new_order]

file_name = "data/stage03_mediamarkt.csv"
# Save the DataFrame to CSV in the same directory as the script
df.to_csv(file_name, index=False)

