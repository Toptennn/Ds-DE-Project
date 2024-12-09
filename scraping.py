from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import time
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import logging

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# MongoDB Configuration
MONGO_URI = "mongodb+srv://toptenwatthana:6Bc5Efc5klSSom05@paperdatabase.juww5.mongodb.net/"
DB_NAME = "paper_database"                      # ชื่อฐานข้อมูลที่คุณให้มา
COLLECTION_NAME = "research_papers"            # ชื่อ collection ที่ต้องการเก็บข้อมูล

# Initialize MongoDB Client
try:
    client = MongoClient(MONGO_URI)
    # ตรวจสอบการเชื่อมต่อ
    client.admin.command('ismaster')
    logging.info("MongoDB connection successful.")
except ConnectionFailure:
    logging.error("MongoDB connection failed.")
    exit()

db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# สร้าง index เพื่อป้องกันการบันทึกข้อมูลซ้ำ (บนฟิลด์ 'title')
collection.create_index("title", unique=True)

API_KEY = "ead2fa067c42804755e105071fcedb4b"

def solve_captcha(api_key, site_url, site_key):
    create_task_payload = {
        "clientKey": api_key,
        "task": {
            "type": "NoCaptchaTaskProxyless",
            "websiteURL": site_url,
            "websiteKey": site_key
        }
    }

    response = requests.post("https://api.capmonster.cloud/createTask", json=create_task_payload)
    response.raise_for_status()  # ตรวจสอบข้อผิดพลาด HTTP
    task_id = response.json().get("taskId")
    
    if not task_id:
        logging.error("Error creating CAPTCHA task: %s", response.json())
        return None

    while True:
        result_payload = {"clientKey": api_key, "taskId": task_id}
        result_response = requests.post("https://api.capmonster.cloud/getTaskResult", json=result_payload)
        result_response.raise_for_status()
        result = result_response.json()

        if result.get("status") == "ready":
            return result["solution"]["gRecaptchaResponse"]
        else:
            logging.info("Waiting for CAPTCHA solution...")
            time.sleep(5)

# Selenium WebDriver Setup
options = Options()
# ลบหรือคอมเมนต์บรรทัดนี้เพื่อเปิดใช้งานโหมดไม่ headless
# options.add_argument("--headless") 
options.add_argument("--disable-gpu") 
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)  # ส่ง options ให้ Chrome

URL = 'https://www.scopus.com/sources.uri'
logging.info("Navigating to URL: %s", URL)
driver.get(URL)

sub_keywords = ["Marketing", "Economics, Econometrics and Finance"]

try:
    logging.info("Waiting for search-term element to load...")
    try:
        search_term = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "search-term"))
        )
        logging.info("Found search-term element. Sending keys: %s", sub_keywords[0])
        search_term.send_keys(sub_keywords[0])
    except Exception as e:
        logging.error("Failed to find search-term element: %s", e)
        driver.save_screenshot("error_search_term.png")
        raise

    try:
        logging.info("Waiting for first auto-suggest option to be clickable...")
        first = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "body_autoSugg0"))
        )
        first.find_element(By.CLASS_NAME, "checkbox-label").click()
        logging.info("Clicked first checkbox.")
    except Exception as e:
        logging.error("Failed to click first checkbox: %s", e)
        driver.save_screenshot("error_first_checkbox.png")
        raise

    try:
        apply_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "Apply"))
        )
        logging.info("Submitting first search.")
        apply_button.submit()
    except Exception as e:
        logging.error("Failed to submit first search: %s", e)
        driver.save_screenshot("error_submit_first_search.png")
        raise

    time.sleep(1)

    logging.info("Sending second keyword: %s", sub_keywords[1])
    try:
        search_term = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search-term"))
        )
        search_term.send_keys(sub_keywords[1])
    except Exception as e:
        logging.error("Failed to send second keyword: %s", e)
        driver.save_screenshot("error_second_keyword.png")
        raise

    try:
        logging.info("Waiting for second auto-suggest option to be clickable...")
        second = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "ui-autocomplete-source"))
        )
        second.find_element(By.CLASS_NAME, "checkbox-label").click()
        logging.info("Clicked second checkbox.")
    except Exception as e:
        logging.error("Failed to click second checkbox: %s", e)
        driver.save_screenshot("error_second_checkbox.png")
        raise

    try:
        apply_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "Apply"))
        )
        logging.info("Submitting second search.")
        apply_button.submit()
    except Exception as e:
        logging.error("Failed to submit second search: %s", e)
        driver.save_screenshot("error_submit_second_search.png")
        raise

    time.sleep(1)

    logging.info("Setting results per page...")
    try:
        results_per_page_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "sourceResults-resultsPerPage-button"))
        )
        results_per_page_button.click()
        logging.info("Clicked results per page button.")
    except Exception as e:
        logging.error("Failed to click results per page button: %s", e)
        driver.save_screenshot("error_results_per_page.png")
        raise

    time.sleep(1)

    try:
        logging.info("Selecting 200 results per page...")
        results_200 = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "ui-id-4"))
        )
        results_200.click()
        logging.info("Selected 200 results per page.")
    except Exception as e:
        logging.error("Failed to select 200 results per page: %s", e)
        driver.save_screenshot("error_select_200.png")
        raise

    time.sleep(1)

    logging.info("Navigating to specific page...")
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        page = 400
        onclick_str = f"ResultsTables['sourceResults'].setRange ({page}, 200); ResultsTables['sourceResults'].onCriteriaChanged (); return false;"
        is_next = soup.find('a', {'onclick': onclick_str})
        element = driver.find_elements(By.CSS_SELECTOR, "a.btn.btn-link")
        for n in element:
            if f"({page}, 200)" in str(n.get_attribute("onclick")):
                logging.info("Found and clicking the desired page link.")
                n.click()
                break
        else:
            logging.warning("Desired page link not found.")
    except Exception as e:
        logging.error("Failed to navigate to specific page: %s", e)
        driver.save_screenshot("error_navigate_page.png")
        raise

    try:
        logging.info("Waiting for page to load completely...")
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
    except Exception as e:
        logging.error("Page did not load completely: %s", e)
        driver.save_screenshot("error_page_load_complete.png")
        raise

    # ดึงลิงก์ของแหล่งข้อมูล
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.find_all('a', href=lambda href: href and href.startswith('/sourceid/') and 'tab' not in href)
        hrefs = [link['href'] for link in links]
        logging.info("Found %d links to process.", len(hrefs))
    except Exception as e:
        logging.error("Failed to extract links: %s", e)
        driver.save_screenshot("error_extract_links.png")
        raise

    for href in hrefs:
        logging.info("Processing link: %s", href)
        try:
            driver.get(f"https://www.scopus.com{href}")
            time.sleep(2)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "h2"))
            )
        except Exception as e:
            logging.error("Error loading page %s: %s", href, e)
            driver.save_screenshot(f"error_loading_page_{href.replace('/', '_')}.png")
            continue

        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # ตรวจสอบ CAPTCHA
        if "CAPTCHA" in driver.page_source or "g-recaptcha" in driver.page_source:
            logging.warning("CAPTCHA Detected!")
            try:
                site_key = soup.find("div", {"class": "g-recaptcha"}).get("data-sitekey")
                logging.info("Found site key: %s", site_key)
            except AttributeError:
                logging.error("CAPTCHA site key not found.")
                driver.save_screenshot(f"error_captcha_sitekey_{href.replace('/', '_')}.png")
                continue

            captcha_solution = solve_captcha(API_KEY, URL, site_key)
            if captcha_solution:
                logging.info("CAPTCHA Solved: %s", captcha_solution[:10] + "...")
                try:
                    captcha_input = driver.find_element(By.ID, "g-recaptcha-response")
                    driver.execute_script("arguments[0].style.display = 'block';", captcha_input)
                    captcha_input.send_keys(captcha_solution)
                    submit_button = driver.find_element(By.ID, "submit-button")
                    submit_button.click()
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.ID, "submit-button"))
                    )
                    logging.info("Submitted CAPTCHA solution.")
                except Exception as e:
                    logging.error("Error submitting CAPTCHA solution: %s", e)
                    driver.save_screenshot(f"error_submit_captcha_{href.replace('/', '_')}.png")
                    continue
            else:
                logging.error("Failed to solve CAPTCHA.")
                driver.save_screenshot(f"error_failed_captcha_{href.replace('/', '_')}.png")
                continue  # ข้ามไปยังแหล่งข้อมูลถัดไป
        
        time.sleep(2)
        title_tag = soup.find('h2', {'class': 'jnlTitle'})
        if not title_tag:
            logging.error("Title not found for %s.", href)
            driver.save_screenshot(f"error_title_not_found_{href.replace('/', '_')}.png")
            continue
        title = title_tag.text.strip()
        logging.info("Extracted title: %s", title)
        
        # ดึงปีที่เผยแพร่
        year_tag = soup.find("span", class_="right")
        if not year_tag:
            logging.error("Published year not found for %s.", title)
            driver.save_screenshot(f"error_published_year_{href.replace('/', '_')}.png")
            continue
        year_text = year_tag.text.strip()
        year = year_text.split(' ')[0].rstrip(',')
        if not year.isdigit():
            year = year_text.split(' ')[1] if len(year_text.split(' ')) > 1 else "Unknown"
        logging.info("Published year: %s", year)
        
        # ดึงข้อมูลการอ้างอิง
        citations = []
        citation_tag = soup.find('a', {'title': 'Display all citing documents for this source in this year'})
        if not citation_tag:
            logging.warning("No citation information found for paper: %s", title)
            continue
        
        try:
            citation_count = int(citation_tag.text.strip().split(' ')[0].replace(',', ''))
            citations.append({f'{2020} - {2023}': citation_count})  # ตัวอย่างช่วงเวลา
            logging.info("Citations (2020-2023): %d", citation_count)
        except (ValueError, IndexError) as e:
            logging.error("Error parsing citation count for paper %s: %s", title, e)
            continue
        
        # จัดการกับการอ้างอิงตามช่วงปีต่างๆ
        find_selectmenu = soup.find('span', {'id': 'year-button'})
        if not find_selectmenu:
            logging.warning("Year select menu not found for paper: %s", title)
            continue
        
        try:
            logging.info("Clicking on year select menu.")
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ui-selectmenu-icon"))
            ).click()
            
            all_years = soup.find('ul', {'class': 'ui-menu ui-corner-bottom ui-widget ui-widget-content'})
            years_interval = all_years.find_all('li', {'class': 'ui-menu-item'})
            logging.info("Found %d year intervals.", len(years_interval))
            for i in range(2, len(years_interval) + 1):
                try:
                    year_id = f"ui-id-{i}"
                    logging.info("Selecting year interval ID: %s", year_id)
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, year_id))
                    ).click()
                    time.sleep(1)
                    
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a[title="Display all citing documents for this source in this year"]'))
                    )
                    
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    citation_text = soup.find('a', {'title': 'Display all citing documents for this source in this year'}).text.strip().split(' ')
                    citation_number = int(citation_text[0].replace(',', ''))
                    interval_start = 2024 - 3 - i
                    interval_end = 2024 - i
                    citations.append({f'{interval_start} - {interval_end}': citation_number})
                    logging.info("Citations (%d-%d): %d", interval_start, interval_end, citation_number)
                    
                    # เปิดเมนูเลือกใหม่
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "ui-selectmenu-icon"))
                    ).click()
                    
                    # เลื่อนไปยังองค์ประกอบที่กำหนด
                    element = driver.find_element(By.ID, year_id)
                    driver.execute_script("arguments[0].scrollIntoView();", element)
                except Exception as e:
                    logging.error("Error processing year interval %d for paper %s: %s", i, title, e)
                    driver.save_screenshot(f"error_year_interval_{i}_{href.replace('/', '_')}.png")
                    continue
        except Exception as e:
            logging.error("Error handling year-wise citations for paper %s: %s", title, e)
            driver.save_screenshot(f"error_handling_year_{href.replace('/', '_')}.png")
            continue
        
        # เตรียมเอกสารที่จะบันทึก
        paper_document = {
            'title': title,
            'citation_per_year': citations,
            'published_year': year
        }
        
        # บันทึกข้อมูลลง MongoDB
        try:
            collection.insert_one(paper_document)
            logging.info("Inserted paper into MongoDB: %s", title)
        except DuplicateKeyError:
            logging.warning("Duplicate entry found for paper: %s", title)
        except Exception as e:
            logging.error("Error inserting paper into MongoDB: %s", e)
    
finally:
    driver.quit()
    client.close()

logging.info("Scraping and data insertion completed.")
