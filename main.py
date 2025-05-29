from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()
USERNAME = os.getenv("V2_USERNAME")
PASSWORD = os.getenv("V2_PASSWORD")

# Setup Chrome WebDriver
def setup_driver():
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

# Login to V2 system
def login_and_test_v2():
    driver = setup_driver()
    try:
        print("Opening browser and navigating to login page...")
        driver.get("https://v2.ipps.co.th/agents/login")
        time.sleep(2)

        print("Filling in login credentials...")
        driver.find_element(By.ID, "email").send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)

        print("Clicking login button...")
        driver.find_element(By.XPATH, "//button[@type='submit' and contains(., 'Login')]").click()
        time.sleep(3)

        # Get E-Money balance using precise structure
        balance_element = driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'd-flex') and .//div[text()='E-Money']]//div[contains(text(), 'Balance:')]"
        )

        text = balance_element.text.strip()  # e.g. "Balance: 241.67 THB"
        balance_str = text.replace("Balance:", "").replace("THB", "").strip()
        balance_value = float(balance_str)

        print(f"✅ Extracted E-Money Balance: {balance_value} THB")

    except Exception as e:
        print("❌ Error during login or scraping:", e)
    finally:
        driver.quit()

# Run the test
if __name__ == "__main__":
    login_and_test_v2()
