""" 
Stage02 - cleaning process

Input - stage01_scraped_mediamarkt.csv
Output - stage02_cleaned_mediamarkt.csv

This script was initially developed as a Jupyter notebook for interactive data cleaning and exploration. 
For practical reasons and to enhance performance during batch processing, all interactive User Interface (UI) 
elements and visualizations have been commented out. 
This adjustment ensures that the script runs efficiently in a non-interactive, automated environment. 
"""

#P.S. Iniatial cleaning process was made during the scraping

################################################################################################################################
                    # Library importing
    
import time
from datetime import datetime
import ydata_profiling
from pandas_profiling import ProfileReport
import numpy as np
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.options import Options

options = Options()
options.add_argument("--headless")

################################################################################################################################
                    # Reading CSV-File
    
df = pd.read_csv('data/stage_01_scraped_mediamarkt.csv')

# Interesting ressources that creates a resume of all your dataset
profile = ProfileReport(df, title='Data Profiling Report', explorative=True)
# html profile
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

driver = webdriver.Firefox(options=options)
wait = WebDriverWait(driver, 5) 

display_sizes = {} # Assuming size_verification is a series with URLs to check
size_verification = df_size_nan['webpage']

for index, url in size_verification.items():
    try:
        driver.get(url)  # Navigate to each URL
        wait.until(EC.presence_of_element_located((By.ID, 'features')))  # Wait for the features section to load

        display_size_in_inches = driver.execute_script("""
            var features = document.querySelector('#features');
            var sections = features.querySelectorAll('section');
            for (var i = 0; i < sections.length; i++) {
                var h2 = sections[i].querySelector('h2');
                if (h2 && h2.textContent.trim().toLowerCase() === 'display') {
                    var dts = sections[i].querySelectorAll('dt');
                    for (var j = 0; j < dts.length; j++) {
                        if (dts[j].textContent.trim() === 'Bildschirmdiagonale (Zoll):') {
                            var dd = dts[j].nextElementSibling;
                            if (dd) {
                                return dd.textContent.replace('"', '').trim();
                            }
                            return null;
                        }
                    }
                }
            }
            return 'Display section or data not found';
            """)

        display_sizes[url] = display_size_in_inches
        
       

    except TimeoutException:
        pass
    except Exception as e:
        pass

# Close the WebDriver after the loop
driver.quit()

for url, size in display_sizes.items():
    df.loc[df['webpage'] == url, 'size'] = size

#Confirming that there is no more missing values
#df['size'].isnull().sum() 

################################################################################################################################
                    # Storage Column
    
#Overall look on the dataname of column Storage    
#df['storage'].unique()

df_space_nan = df[pd.isnull(df['storage'])]    #filtering df to rows where storage column has missing values

driver = webdriver.Firefox(options=options)
wait = WebDriverWait(driver, 5) 

storages = {}
storage_verification = df_space_nan['webpage'] # Assuming size_verification is a series with URLs to check

for index, url in storage_verification.items():
    try:
        driver.get(url)  # Navigate to each URL 
        wait.until(EC.presence_of_element_located((By.ID, 'features')))  # Wait for the features section to load

        storagevalues = driver.execute_script("""
            var features = document.getElementById('features');
            if (!features) {
                return 'Features section not found';
            }
            var sections = features.querySelectorAll('section');
            for (var i = 0; i < sections.length; i++) {
                var h2 = sections[i].querySelector('h2');
                if (h2 && h2.textContent.trim().toLowerCase() === 'technische merkmale') {
                    var dts = sections[i].querySelectorAll('dt');
                    for (var j = 0; j < dts.length; j++) {
                        if (dts[j].textContent.trim() === 'Speicherkapazität:') {
                            var dd = dts[j].nextElementSibling;
                            return dd ? dd.textContent.trim() : null;
                        }
                    }
                }
            }
            return 'Display section or data not found';
        """)

        storages[url] = storagevalues
        
    except TimeoutException:
        pass
    except Exception as e:
        pass

driver.quit()  # Close the WebDriver after the loop

for url, storage in storages.items():
    df.loc[df['webpage'] == url, 'storage'] = storage
    
################################################################################################################################
                    # Color Column

#Overall look on the dataname of column Color      
#df['color'].unique()

df['color'] = df['color'].str.lower()

colors = ['black', 'blue', 'green', 'red', 'yellow', 'white', 'gray', 'purple', 'pink', 'orange', 
          'brown', 'silver', 'gold', 'titanium', 'platinum', 'schwarz', 'weiss']

color_translation = {
    'schwarz': 'black', 'weiss': 'white', 'grau': 'gray',
    'hellgrün': 'light green', 'hellblau': 'light blue', 'violett': 'violet',
    'dunkelblau': 'dark blue', 'blau': 'blue', 'graphit': 'graphite',
    'rot': 'red', 'grün': 'green', 'gelb': 'yellow',
    'orange': 'orange', 'rosa': 'pink', 'lila': 'purple',
    'braun': 'brown', 'beige': 'beige', 'türkis': 'turquoise',
    'gold': 'gold', 'silber': 'silver', 'kupfer': 'copper',
    'marine': 'navy', 'oliv': 'olive', 'khaki': 'khaki',
    'karmesin': 'crimson', 'fuchsia': 'fuchsia', 'aquamarin': 'aquamarine',
    'koralle': 'coral', 'indigo': 'indigo', 'elfenbein': 'ivory',
    'lavendel': 'lavender', 'limette': 'lime', 'magenta': 'magenta',
    'maroon': 'maroon', 'ocker': 'ochre', 'pfirsich': 'peach',
    'pflaume': 'plum', 'saphir': 'sapphire', 'smaragd': 'emerald',
    'sonne': 'sun', 'taupe': 'taupe', 'teal': 'teal',
    'zimt': 'cinnamon', 'zitrone': 'lemon'
}


def extract_color(value):
    # Check if the string contains numbers, 'GB', or specific special characters
    if re.search(r'\d|GB|[()/]', value):
        value_lower = value.lower()   # Convert the value to lowercase to make the search case-insensitive

        for color in colors:        # Search for each color in the string
            if re.search(r'\b' + color + r'\b', value_lower):
                return color  # Return the color with the first letter capitalized

        return 'unknown'   # Return 'Unknown' or any other placeholder if no known color is found

    
    return value    # If the string doesn't contain the specified patterns, return it as is

df['color'] = df['color'].apply(extract_color)
df['color'] = df['color'].replace(color_translation)

################################################################################################################################
                    # Price Column
    
#Overall look on the dataname of column Price      
#df['price'].unique()

def clean_price(value):
    try:
        value = str(value)    # Convert the value to string in case it's not
        matches = re.findall(r'\d+\.?\d*', value)  # Find all numeric sequences
        if matches:
            # Return the last match as a float
            return float(matches[-1])
    except Exception as e:
        print(f"Error cleaning price for value {value}: {e}")  # Log the error and return the value as is or return NaN

df['price'] = df['price'].apply(clean_price)
df['price'] = df['price'].astype(float)

################################################################################################################################
                    # Date Column
    
df['date'] = pd.to_datetime(df['date']) #Transforming date column to datetime

################################################################################################################################
                    # Reviews count
    
#Overall look on the dataname of column reviews_count       
#df['reviews_count'].unique()
    
df['reviews_count'] = df['reviews_count'].str.replace('(', '', regex=False).str.replace(')', '', regex=False)
df['reviews_count'] = df['reviews_count'].fillna('0').astype(int)

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
    text = str(text)    # Convert text to string to handle cases where text is not a string

    if pd.isnull(text) or "nicht mehr verfügbar" in text or "nicht lieferbar" in text or "ausverkauft" in text or "kein Liefertermin" in text:
        return None
    else:
        numbers = [int(num) for num in re.findall(r'\d+', text)]  # Find all numbers in the string

        if numbers:
            return max(numbers)  # Return the highest number, assuming it's the upper limit of days
        else:
            return None  # Return None if no numbers are found

df['delivery_time'] = df['delivery_time'].apply(extract_days) # Assuming you have a DataFrame 'df' with a column 'delivery_time'

df['delivery_time'].astype(float) # Apply the function to the delivery_time column

################################################################################################################################
                    # Camera_MP
    
def extract_memory_mp(value):
    if not isinstance(value, str):
        return None  # Return None if the value is not a string
    
    # Find all numeric sequences in the string
    matches = re.findall(r'\d+', value)
    if matches:
        return int(matches[0])         # Convert the first match to an integer
    return None

df['camera_MP'] = df['camera_MP'].apply(extract_memory_mp)

################################################################################################################################
                    # Dropping columns 
    
df = df.drop(columns=['category', 'article_number', 'condition' ])

################################################################################################################################
                    # Reorganizing columns order

new_order = ['brand', 'model', 'size', 'storage', 'color', 'rating', 'reviews_count', 'delivery_time', 'price', 'webpage', 'source', 'camera_MP', 'date']
df = df[new_order]

################################################################################################################################
                    # Saving Df to CSV
    
file_name = "data/stage02_cleaned_mediamarkt.csv"
df.to_csv(file_name, index=False) # Save the DataFrame to CSV in the same directory as the script

################################################################################################################################
""" Author: Alain Ramon Burkhard """