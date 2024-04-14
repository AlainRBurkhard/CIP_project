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

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

time_now = datetime.now().isoformat()[:-7].replace(":", "-")
file_handler = logging.FileHandler(f'logs/scrapping-{time_now}.log', encoding='utf-8', mode='w')
file_handler.setLevel(logging.INFO)

file_handler.setFormatter(formatter)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)

# Add both handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

driver = webdriver.Firefox()
# TODO: driverless mode

# #My Source
wait = WebDriverWait(driver, 4)
# mediamarkt_home = driver.get("https://www.mediamarkt.ch/de/category/_smartphone-680815.html?searchParams=&sort=&view=PRODUCTGRID&page=1")

def collect_phones_info_from_page(driver) -> list[dict]:
    smartphones = driver.find_elements(By.CSS_SELECTOR, 'ul.products-grid > li')

    phone_list_page = []
    for phone in smartphones:   
        #Info: brand, model, size, space
        info = phone.find_element(By.CSS_SELECTOR, "a.product-link").text
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
        
        condition = 'new'
        
        source = 'mediamarkt'
        
        link_element = phone.find_element(By.CSS_SELECTOR, 'a.photo')
        phone_url = link_element.get_attribute('href')
        
        
        phone_features = {
            "page" : i,
            "brand": brand,
            "model": model,
            "category": category,
            "size": size,
            "storage": storage,
            "color": color,
            "price": price,
            "source": source,
            "webpage": phone_url,
            "condition": condition,
            "date": pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))
        }
        
        phone_list_page.append(phone_features)

    return phone_list_page

def get_additional_phone_info(driver):
    phone = {}
    try:
        # Wait until article number element is present on the webpage
        css_selector = 'dl.group > dd > span[itemprop]'
        article_number = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        article_number = article_number.get_attribute('content').split(':')[1]
        logger.info(f"\t{article_number=}")
        phone['article_number'] = article_number

    except (NoSuchElementException, TimeoutException) as e:
        logger.warning(f" {phone['webpage'] =}")
        logger.warning(f" {css_selector =}")
        logger.warning(e)  

    try:
        # Wait until number of reviews element is present on the webpage
        css_selector = '.bv_numReviews_text'
        reviews_count = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector ))).text
        logger.info(f" \t{reviews_count=}")
        phone['reviews_count'] = reviews_count

    except (NoSuchElementException, TimeoutException) as e:
        logger.warning(f" {phone['webpage'] =}")
        logger.warning(f" {css_selector =}")
        logger.warning(e) 
    
    try:
        # Camera 
        css_selector = '.bv_numReviews_text' #features > section:nth-child(3) > dl:nth-child(2) > dd:nth-child(4)
        n_of_reviews = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector ))).text
        logger.info(f" \t{n_of_reviews=}")
        phone['n_of_reviews'] = n_of_reviews

    except (NoSuchElementException, TimeoutException) as e:
        logger.warning(f" {phone['webpage'] =}")
        logger.warning(f" {css_selector =}")
        logger.warning(e) 


    try:
        # Wait until rating element is present on the webpage
        css_selector = 'div[itemprop="ratingValue"]'
        rating = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        logger.info(f" \t{rating=}")
        phone['rating'] = rating.text

    except (NoSuchElementException, TimeoutException) as e:
        logger.warning(f" {phone['webpage'] =}")
        logger.warning(f" {css_selector =}")
        logger.warning(e) 


    try:
        css_selector = 'div.box.infobox.availability > ul > li > p > span'
        delivery_time = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))).text
        logger.info(f" \t{delivery_time=}")
        phone['delivery_time'] = delivery_time

    except (NoSuchElementException, TimeoutException) as e:
        logger.warning(f" {phone['webpage'] =}")
        logger.warning(f" {css_selector =}")
        logger.warning(e) 
    
    return phone


phone_list = [] 
i = 1
max_pages = None
while (max_pages is None) or (i <= max_pages):
    url = f"https://www.mediamarkt.ch/de/category/_smartphone-680815.html" + \
          f"?searchParams=&sort=&view=PRODUCTGRID&page={i}"
    
    try:
        driver.get(url)
    except WebDriverException as e:
        logger.warning(f"Error: {e}")
        break
        
    if max_pages is None:
        css_selector = ".pagination > li:last-child"
        max_pages = int(wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))).get_attribute('data-value'))
    
    
    phone_list_page = collect_phones_info_from_page(driver)
    for phone in phone_list_page:
        phone['time_of_scrapping'] = datetime.now()
        phone['datails_getted'] = False
        phone['status'] = 'Initial scrapping'
    
    phone_list.extend(phone_list_page)    
            
    time.sleep(2)
    
    i += 1   
    
    
    ### going inside each phone page
for phone in phone_list:
    if phone['datails_getted']:
        continue

    driver.get(phone['webpage'])
    logger.info(phone['webpage'])

    ## catching broken pages
    try:
        body = driver.find_element(By.CSS_SELECTOR, "body > *")
    except NoSuchElementException:
        logger.warning(phone['webpage'])
        logger.warning("page broken")
        phone['status'] = 'detailed page broken'
        continue

    new_details = get_additional_phone_info(driver)
    phone.update(new_details)
    phone['datails_getted'] = True
    phone['status'] = 'successfully scraped'

    time.sleep(2)
    
    
logger.info(len(phones))
logger.info(f"{max_pages=}")

driver.quit()

df = pd.DataFrame(phone_list)

file_name = "data/stage_01_scraped_mediamarkt.csv"
# Save the DataFrame to CSV in the same directory as the script
df.to_csv(file_name, index=False)