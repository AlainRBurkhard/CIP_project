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

# Setup logging configuration
def setup_logger():
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    time_now = datetime.now().isoformat()[:-7].replace(":", "-")
    file_handler = logging.FileHandler(f'logs/scrapping-{time_now}.log', encoding='utf-8', mode='w')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger

# Initialize WebDriver and WebDriverWait
def init_driver():
    driver = webdriver.Firefox()
    wait = WebDriverWait(driver, 10)
    return driver, wait

# Extract phone details from a webpage
def extract_phone_details(phone, driver, wait, logger):
    info = phone.find_element(By.CSS_SELECTOR, "a.product-link").text
    brand_model = info.split("-", 1)[0]
    brand, model = brand_model.split(" ", maxsplit=1)
    category = re.search(r' - (\w+)', info).group(1) if re.search(r' - (\w+)', info) else "unknown"
    size = re.search(r'\((\d+\.\d+)\s*"', info).group(1) if re.search(r'\((\d+\.\d+)\s*"', info) else "unknown"
    storage = re.search(r'(\d+)\s+(GB|TB)', info).group(0) if re.search(r'(\d+)\s+(GB|TB)', info) else "unknown"
    color = re.split(r',\s*(?=\w)', info)[-1].rstrip(')')

    price_elements = phone.find_elements(By.CSS_SELECTOR, 'div.price > span')
    price = "".join([elem.text for elem in price_elements]).strip("-")
    webpage = phone.find_element(By.CSS_SELECTOR, 'a.photo').get_attribute('href')
    details = get_additional_details(webpage, driver, wait, logger)

    return {
        "brand": brand,
        "model": model,
        "category": category,
        "size": size,
        "storage": storage,
        "color": color,
        "price": price,
        "webpage": webpage,
        "source": 'mediamarkt',
        "condition": 'new',
        "date": pd.to_datetime(datetime.now().strftime('%Y-%m-%d')),
        **details
    }

# Get additional details for each phone
def get_additional_details(webpage, driver, wait, logger):
    details = {}
    try:
        driver.get(webpage)
        wait.until(EC.presence_of_element_located((By.ID, 'features')))
        details = {
            "reviews_count": get_reviews_count(driver, wait, logger),
            "rating": get_rating(driver, wait, logger),
            "camera_MP": get_camera_specs(driver, logger),
            "delivery_time": get_delivery_time(driver, wait, logger)
        }
    except TimeoutException:
        logger.warning(f"Timeout while trying to access {webpage}")
    except Exception as e:
        logger.warning(f"Error processing {webpage}: {e}")
    return details

def get_reviews_count(driver, wait, logger):
    try:
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.bv_numReviews_text')))
        return element.text
    except Exception as e:
        logger.warning(f"Could not get reviews count: {e}")
        return '0'

def get_rating(driver, wait, logger):
    try:
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[itemprop="ratingValue"]')))
        return element.text
    except Exception as e:
        logger.warning(f"Could not get rating: {e}")
        return '0'

def get_camera_specs(driver, logger):
    try:
        camera_specs = driver.execute_script("""
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
            return null;
        """)
        return camera_specs
    except Exception as e:
        logger.warning(f"Could not get camera specifications: {e}")
        return 'Not available'

def get_delivery_time(driver, wait, logger):
    try:
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.box.infobox.availability > ul > li > p > span')))
        return element.text
    except Exception as e:
        logger.warning(f"Could not get delivery time: {e}")
        return 'Not available'

# Main script execution
def main():
    logger = setup_logger()
    driver, wait = init_driver()
    phone_list = []

    for page_number in range(1, 100):  # Assuming there are up to 100 pages
        url = f"https://www.mediamarkt.ch/de/category/_smartphone-680815.html?page={page_number}"
        driver.get(url)
        phones = driver.find_elements(By.CSS_SELECTOR, 'ul.products-grid > li')
        if not phones:
            break

        for phone in phones:
            phone_details = extract_phone_details(phone, driver, wait, logger)
            phone_list.append(phone_details)

    driver.quit()
    df = pd.DataFrame(phone_list)
    df.to_csv("data/stage_01_scraped_mediamarkt.csv", index=False)

if __name__ == "__main__":
    main()
