# This script was initially developed as a Jupyter notebook for interactive data cleaning and exploration. 
# For practical reasons and to enhance performance during batch processing, all interactive User Interface (UI) 
# elements and visualizations have been commented out. 
# This adjustment ensures that the script runs efficiently in a non-interactive, automated environment.

#P.S. Iniatial cleaning process was made during the scraping 

################################################################################################################################
                    # Library importing
    
import pandas as pd
import time
from datetime import datetime
import ydata_profiling
from pandas_profiling import ProfileReport
import numpy as np
import re
import requests

################################################################################################################################
                    # Reading CSV-File
    
df = pd.read_csv('data/scraped_mediamarkt.csv')

# Interesting ressources that creates a resume of all your dataset
profile = ProfileReport(df, title='Data Profiling Report', explorative=True)

# General information about the dataframe

"""
df.info()
df.describe()

df.duplicated().sum()  # Find number of duplicates

df.isnull().sum() 

df.nunique()
"""

################################################################################################################################
"""                           Manipulating Target Variabeles
        Target variables are the columns that are important for the end DF structure           """

#Not all columns scraped are going to be part of the end dataframe selected to upload in MariaDB
#For this reason they are not part of the cleaninc scope
#Columns that will be droped: 
        #"Page" : This column identify the page number where the phone was hosted, helping to find the phone in manual search
        #"Article_number": Unique serial number for each phone in the website, would be necessary merge data scraped in 
        #different timestamp to the same phone
        #"Condition": Necessary in the case of scrapping refurbished phone data
################################################################################################################################
                                                                                            
################################################################################################################################
                    # Brand Column
    
#Overall look on the dataname of column brand   
#df['brand'].unique()
df['brand'] = df['brand'].str.lower() #Transforming all data in column to lowercase
                                
#Number of missing data in brand column
#df['brand'].isnull().sum() 

#Creating a list with all brands for dataset and additional known brands
#The idea behind the list is to avaluate the names scraped for brand, anything
#different from the list it will be added but the adm will have a notification to verify the brand
valid_brands = ['apple', 'xiaomi', 'samsung', 'nothing', 'motorola', 'fairphone', 
                'google', 'doro', 'inoi', 'emporia', 'one', 'nokia', 'ruggear', 
                'oppo', 'crosscall', 'wiko', 'peaq', 'huawei', 'lg', 'sony', 'htc', 
                'oneplus', 'zte', 'alcatel', 'asus', 'blackberry', 'realme', 'vivo', 
                'tecno', 'lenovo', 'meizu', 'honor', 'ulefone', 'cat']

def validate_brand(brand):
    if brand not in valid_brands:
        print(f"Unrecognized brand, please verify: {brand}") #Returns message to adm to verify names
                                                             #not in the brand list

# Apply the function to the 'brand' column
df['brand'].apply(validate_brand)

################################################################################################################################
                    # Model Column

#Overall look on the dataname of column model   
#df['model'].unique()

df['model'] = df['model'].str.lower() #Transforming all data in column to lowercase

#The strategy of validation from the brand column, using a function to verify the presence of the name scrapped
#in a list, could be also used in the model column, for that would be necessary to create a list with "all" models for 
#each brand

def strip(model):         #Deleting empty space at the end of the string
    return model.rstrip()

df['model'] = df['model'].apply(strip)

#Number of missing data in model column
#df['model'].isnull().sum() 

################################################################################################################################
                    # Category Column
    
# Only smartphones are the interest of the scrapping

#Overall look on the dataname of column category   
#df['category'].unique()

#Filtering df to accept only rows with category column value == smartphone
df = df[df['category'] == 'Smartphone']

df['category'] = df['category'].str.lower() #Transforming all data in column to lowercase

#Number of missing data in category column
#df['category'].isnull().sum() 

################################################################################################################################
                    # Size Column

#Overall look on the dataname of column size
#df['size'].unique()

df_size_nan = df[np.isnan(df['size'])] #filtering rows with missing values for size
#print(len(df_size_nan))

size_verification = df_size_nan['source']     #printing to user url link for manual input
for index, url in size_verification.items():
    #print(f"{index}: {url}")

#Few phones don't follow the main structure and is necessary to manual verify values
#Columns could be left empty

    size_manually = {  #dict with index and size collected
    131: 5.00,
    142: 3.25,
    189: 3.00,
    254: 5.00
    }

# Update the 'size' column in the DataFrame with the manual colected data
for index, size in size_manually.items():
    df.at[index, 'size'] = size

#Confirming that there is no more missing values
#df['size'].isnull().sum() 

################################################################################################################################
                    # Storage Column
    
#Overall look on the dataname of column Storage    
#df['storage'].unique()

df_space_nan = df[pd.isnull(df['storage'])]    #filtering df to rows where storage column has missing values
storage_verification = df_space_nan['source']  #Serie from df_space_nan with all source column results 
for index, url in storage_verification.items():
    #print(f"{index}: {url}")                  #Printing all urls for manual input
    
    storage_manually = {  #dict of index storage value
    131: '32 GB',
    142: '8 GB'
    }

# Update the 'size' column in the DataFrame wth storage_manually
for index, storage in storage_manually.items():
    df.at[index, 'storage'] = storage
    
################################################################################################################################
                    # Color Column

#Overall look on the dataname of column Color      
#df['color'].unique()


colors = ['black', 'blue', 'green', 'red', 'yellow', 'white', 'gray', 'purple', 'pink', 'orange', 
          'brown', 'silver', 'gold', 'titanium', 'platinum', 'schwarz', 'weiss']

def extract_color(value):
    # Check if the string contains numbers, 'GB', or specific special characters
    if re.search(r'\d|GB|[()/]', value):
        # Convert the value to lowercase to make the search case-insensitive
        value_lower = value.lower()

        # Search for each color in the string
        for color in colors:
            if re.search(r'\b' + color + r'\b', value_lower):
                return color.capitalize()  # Return the color with the first letter capitalized

        # Return 'Unknown' or any other placeholder if no known color is found
        return 'Unknown'
    
    # If the string doesn't contain the specified patterns, return it as is
    return value

df['color'] = df['color'].apply(extract_color)
#df['color'].unique()

df_color_nan = df[pd.isnull(df['color'])]

################################################################################################################################
                    # Price Column
    
#Overall look on the dataname of column Price      
#df['price'].unique()

def clean_price(value):
    # Find all numeric sequences
    matches = re.findall(r'\d+\.?\d*', value)
    if matches:
        # Return the last match
        return matches[-1]
    return value 

df['price'] = df['price'].apply(clean_price)
df['price'] = df['price'].astype(float)

################################################################################################################################
                    # Source Column
    
df_source_nan = df[pd.isnull(df['source'])]

"""
def check_url_status(url):
    try:
        response = requests.head(url, timeout=2)  # Using HEAD instead of GET to speed up the process
        if response.status_code == 200:
            return 'Working'
        else:
            return f'Broken ({response.status_code})'
    except requests.RequestException as e:
        return f'Error ({e})'

# Apply the function to check each URL
df['status'] = df['source'].apply(check_url_status)
"""

################################################################################################################################
                    # Date Column
    
df['date'] = pd.to_datetime(df['date']) #Transforming date column to datetime

################################################################################################################################
                    # N_of_reviews Column
    
#Overall look on the dataname of column N_of_reviews          
#df['n_of_reviews'].unique()

df_n_of_reviews_nan = df[pd.isnull(df['n_of_reviews'])] #Filtering df to rows where n_of_reviews has a missing value
#len(df_n_of_reviews_nan)

n_of_reviews_nan_verification = df_n_of_reviews_nan['source']  #Serie from df_n_of_reviews_nan with all source column results
                                                               #for manual verification
for index, url in n_of_reviews_nan_verification.items():
    #print(f"{index}: {url}")
    reviews_manually = {54: '(5)'}
    
for index, reviews in reviews_manually.items():
    df.at[index, 'n_of_reviews'] = reviews
    
df['n_of_reviews'] = df['n_of_reviews'].str.replace('(', '', regex=False).str.replace(')', '', regex=False)
df['n_of_reviews'] = df['n_of_reviews'].fillna('0').astype(int)

################################################################################################################################
                    # Rating Column
    
#df['rating'].unique()

df_rating_nan = df[pd.isnull(df['rating'])]

rating_nan_verification = df_rating_nan['source']
for index, url in rating_nan_verification.items():
    #print(f"{index}: {url}")
    break

df['rating'] = df['rating'].fillna('0').astype(float)

################################################################################################################################
                    # Delivery Column
    
#df['delivery_time'].unique()

def extract_days(text):
    # Convert text to string to handle cases where text is not a string
    text = str(text)
    
    if pd.isnull(text) or "nicht mehr verfügbar" in text or "nicht lieferbar" in text or "ausverkauft" in text or "kein Liefertermin" in text:
        return None
    else:
        # Find all numbers in the string
        numbers = [int(num) for num in re.findall(r'\d+', text)]
        if numbers:
            return max(numbers)  # Return the highest number, assuming it's the upper limit of days
        else:
            return None  # Return None if no numbers are found

# Assuming you have a DataFrame 'df' with a column 'delivery_time'
df['delivery_time'] = df['delivery_time'].apply(extract_days)

# Apply the function to the delivery_time column
df['delivery_time'].astype(float)

################################################################################################################################
                    # Dropping columns 
    
df = df.drop(columns=['page', 'article_number', 'condition' ])

################################################################################################################################
                    # Reorganizing columns order

new_order = ['brand', 'model', 'category', 'size', 'storage', 'color', 'rating', 'n_of_reviews', 'delivery_time', 'price', 'source', 'date']
df = df[new_order]

################################################################################################################################
                    # Saving Df to CSV
    
file_name = "data/cleaned_mediamarkt.csv"
# Save the DataFrame to CSV in the same directory as the script
df.to_csv(file_name, index=False)

print("File sucessfully ran, cleaned_mediamarkt.csv is on the folder data")