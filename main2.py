# main2.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
VAS_USERNAME = os.getenv("VAS_USERNAME")
VAS_PASSWORD = os.getenv("VAS_PASSWORD")

# Setup Chrome WebDriver
def setup_driver():
    options = Options()
    # Uncomment the next line to run headless
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

# Login to VAS
def login_vas():
    driver = setup_driver()
    try:
        print("Navigating to VAS login...")
        driver.get("https://va-vasbo.ipps.co.th/vas-web/auth/login")
        time.sleep(2)

        # Fill in credentials
        driver.find_element(By.ID, "usernameforshow").send_keys(VAS_USERNAME)
        driver.find_element(By.ID, "passwordforshow").send_keys(VAS_PASSWORD)

        # Submit the form
        driver.find_element(By.ID, "passwordforshow").submit()

        time.sleep(3)
        print("✅ Logged into VAS. Ready for next steps (CSV download).")

    except Exception as e:
        print("❌ Error during VAS login:", e)
    finally:
        driver.quit()

# Run it
if __name__ == "__main__":
    login_vas()
