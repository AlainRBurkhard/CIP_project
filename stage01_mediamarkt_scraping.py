"""
Stage01 - scraping process
Input - selenium driver.firefox > scraping {mediamarkt.ch}
Output - stage01_scraped_mediamarkt.csv

"""
################################################################################################################################
                    # Library importing
import logging
import os
import re
import time
from datetime import datetime
import pandas as pd
import selenium
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

################################################################################################################################
                    # Creating Log handler example.log
    
os.makedirs("logs", exist_ok=True) #creating a directory to write log file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s') # structure time , tyope(warning, info) , message

time_now = datetime.now().isoformat()[:-7].replace(":", "-")
file_handler = logging.FileHandler(f'logs/scrapping-{time_now}.log', encoding='utf-8', mode='w')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

################################################################################################################################
                    # Initializing the driver

driver = webdriver.Firefox() # TODO: driverless mode stage02

# Setting a fix wait time for element scrapping
wait = WebDriverWait(driver, 5) #necessary especially in the part 2 of the scrapping

################################################################################################################################
                    # Scaping Process

phone_list = [] #creating a empty list to save all information scrapped
i = 1 #increment for page in url

while True: 
    url = f"https://www.mediamarkt.ch/de/category/_smartphone-680815.html" + \  # My main webpage source
          f"?searchParams=&sort=&view=PRODUCTGRID&page={i}"
    
    try:
        driver.get(url)
    except WebDriverException as e:
        logger.warning(f"Error: {e}")
        break
    
    smartphones = driver.find_elements(By.CSS_SELECTOR, 'ul.products-grid > li') #catchs the grid of the collection of phones
    phone_list_page = []
    
    ##########################################################
                    # PART 01

    for phone in smartphones: #phone is a single phone element
       
        #Info: brand, model, size, space
        info = phone.find_element(By.CSS_SELECTOR, 'a.product-link').text
        
        brand_model = info.split("-")[0]
        brand, model = brand_model.split(" ", maxsplit=1)
        
        category_match = re.search(r' - (\w+)', info)
        category = category_match.group(1) if category_match else None
        
        size = re.search(r'\((\d+\.\d+)\s*"', info)
        size = size.group(1) if size else None
        
        storage = re.search(r'(\d+)\s+(GB|TB)', info)
        storage = storage.group(1) + " " + storage.group(2) if storage else None
        
        color = re.split(r',\s*(?=\w)', info)[-1].rstrip(')')
        
        price = "".join([i.text for i in phone.find_elements(By.CSS_SELECTOR, 
                                                                 'div.price > span')])
        price = price.strip("-")
        
        link_element = phone.find_element(By.CSS_SELECTOR, 'a.photo')
        phone_url = link_element.get_attribute('href')
        
        
        phone_features = { #dictionary to keys values scapped 
            "brand": brand,
            "model": model,
            "category": category,
            "size": size,
            "storage": storage,
            "color": color,
            "price": price,
            "source": 'mediamarkt',
            "webpage": phone_url,
            "condition": 'new',
            "date": pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))
        }

        
        phone_list_page.append(phone_features)
    
    
    phone_list.extend(phone_list_page)    

    ##########################################################
                    # PART 02
        
    ### going inside each phone page
    for phone in phone_list_page: #for all phone in the current page
    
        driver.get(phone['webpage']) #Using all phone individual website scraped as phone_url and saved as webpage
        logger.info(phone['webpage'])
        
        ## catching broken pages
        try:
            body = driver.find_element(By.CSS_SELECTOR, "body > *")
        except NoSuchElementException:
            logger.warning(phone['webpage'])
            logger.warning("page broken")
            continue
            
        try:
            # Wait until article number element is present on the webpage
            article_number = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'dl.group > dd > span[itemprop]')))
            article_number = article_number.get_attribute('content').split(':')[1]
            logger.info(f"\t{article_number=}")
            phone['article_number'] = article_number
        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f" {phone['webpage'] =}")
            logger.warning(f" {css_selector =}")
            logger.warning(e)  
            
        try:
            # Wait until number of reviews element is present on the webpage
            n_of_reviews = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.bv_numReviews_text'))).text
            logger.info(f" \t{n_of_reviews=}")
            phone['reviews_count'] = n_of_reviews
        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f" {phone['webpage'] =}")
            logger.warning(f" {css_selector =}")
            logger.warning(e) 
            
        try:
            # Wait until rating element is present on the webpage
            rating = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[itemprop="ratingValue"]')))
            logger.info(f" \t{rating=}")
            phone['rating'] = rating.text
        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f" {phone['webpage'] =}")
            logger.warning(f" {css_selector =}")
            logger.warning(e) 
        
        try:
            wait.until(EC.presence_of_element_located((By.ID, 'features')))
            camera_MP = driver.execute_script("""
                var features = document.querySelector('#features');
                var sections = features.querySelectorAll('section');
                for (var i = 0; i < sections.length; i++) {
                    var h2 = sections[i].querySelector('h2');
                    if (h2 && h2.textContent.trim().toLowerCase() === 'kamera') {
                        var dts = sections[i].querySelectorAll('dt');
                        for (var j = 0; j < dts.length; j++) {
                            if (dts[j].textContent.trim() === 'Rückkamera Auflösung:') {
                                var dd = dts[j].nextElementSibling;
                                return dd ? dd.textContent.trim() : null;
                            }
                        }
                    }
                }
                return null;  // Return null if no matching section or dt/dd is found
            """)
            phone['camera_MP'] = camera_MP
            logger.info(f" \t{camera_MP=}")
        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f" {phone['camera_MP'] =}")
            logger.warning(f" {css_selector =}")
            logger.warning(e) 
            
        try:
            delivery_time = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 
                                                                       'div.box.infobox.availability > ul > li > p > span'))).text
            logger.info(f" \t{delivery_time=}")
            phone['delivery_time'] = delivery_time
        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f" {phone['webpage'] =}")
            logger.warning(f" {css_selector =}")
            logger.warning(e) 

    if not smartphones:
        break
    
    time.sleep(2)
    
    i += 1
    
################################################################################################################################
                    # End of Scrape Process
    
driver.quit()

################################################################################################################################
                    # Saving Df to CSV

df = pd.DataFrame(phone_list)
file_name = "data/stage_01_scraped_mediamarkt.csv"
# Save the DataFrame to CSV in the same directory as the script
df.to_csv(file_name, index=False)

################################################################################################################################
""" Author: Alain Ramon Burkhard """