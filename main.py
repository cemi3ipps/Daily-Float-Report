from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
from dotenv import load_dotenv
import schedule

# Load credentials from .env
load_dotenv()
USERNAME = os.getenv("V2_USERNAME")
PASSWORD = os.getenv("V2_PASSWORD")

# Configure Selenium
def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

# Login and scrape number from V2
def login_and_scrape_v2():
    driver = setup_driver()
    try:
        driver.get("https://v2.ipps.co.th/agents/login")
        time.sleep(2)

        # Adjust selectors here based on the actual page's input field IDs/classes
        driver.find_element(By.ID, "email").send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]").click()

        time.sleep(3)  # Wait for dashboard to load

        # Adjust the following selector to match the element showing the float number
        number_text = driver.find_element(By.CSS_SELECTOR, ".dashboard-number").text
        value = float(number_text.replace(",", ""))
        print(f"Extracted value: {value}")

    except Exception as e:
        print("Error during scraping:", e)
    finally:
        driver.quit()

# Schedule to run daily at 16:00
schedule.every().day.at("16:00").do(login_and_scrape_v2)

# Keep script running
print("Scheduled script started. Waiting for 16:00 daily run...")
while True:
    schedule.run_pending()
    time.sleep(60)
