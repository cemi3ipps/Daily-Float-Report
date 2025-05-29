from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv
import pandas as pd  # For parsing Excel
import glob  # For finding downloaded files

# Load environment variables
load_dotenv()
VAS_USERNAME = os.getenv("VAS_USERNAME")
VAS_PASSWORD = os.getenv("VAS_PASSWORD")

# Setup Chrome WebDriver with custom download directory
def setup_driver(download_dir=None):
    options = Options()
    options.add_argument("--headless")  # Enable headless mode
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Set up Chrome preferences
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False
    }
    if download_dir:
        prefs["download.default_directory"] = os.path.abspath(download_dir)
        prefs["download.prompt_for_download"] = False
        prefs["directory_upgrade"] = True
        prefs["safebrowsing.enabled"] = True
    options.add_experimental_option("prefs", prefs)

    # Optional: disable the popup warning UI entirely
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")

    return webdriver.Chrome(options=options)

# Login to VAS and select previous day's report and download/parse report
def login_vas():
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    driver = setup_driver(download_dir=download_dir)
    try:
        print("Navigating to VAS login...")
        driver.get("https://va-vasbo.ipps.co.th/vas-web/auth/login")
        time.sleep(2)

        driver.find_element(By.ID, "usernameforshow").send_keys(VAS_USERNAME)
        driver.find_element(By.ID, "passwordforshow").send_keys(VAS_PASSWORD)
        driver.find_element(By.ID, "buttonforshow").click()
        time.sleep(3)

        print("Redirecting to report page...")
        driver.get("https://va-vasbo.ipps.co.th/vas-web/report/amc_all_report/")
        time.sleep(2)

        # Select previous day's date
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        print(f"Selecting report date: {yesterday}")

        date_input = driver.find_element(By.ID, "businessDate")
        driver.execute_script(f"arguments[0].value = '{yesterday}'", date_input)

        # Click Search
        search_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]")
        search_button.click()
        print("✅ Search triggered for previous day.")

        # Wait for the result to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), '.csv') or contains(text(), 'Report')]") )
        )
        print("✅ Report result appeared (next step: download).")

        # Step 1: Build expected filename
        file_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        expected_filename = f"UserAcccountStatReport_{file_date}.xlsx"

        # Step 2: Find all rows in the report table
        rows = driver.find_elements(By.XPATH, "//table//tr")

        # DEBUG: Print all table row texts
        print("DEBUG: Table rows found:")
        for idx, row in enumerate(rows):
            print(f"Row {idx}: {row.text}")
        # Save screenshot for visual debug
        driver.save_screenshot('vas_report_table.png')

        downloaded = False
        # Relaxed matching: look for report prefix and date
        file_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        for row in rows:
            try:
                if ("UserAcccountStatReport" in row.text and file_date in row.text):
                    print(f"✅ Found row with report (partial match): {row.text}")
                    # Find the download icon and click it, wait until clickable
                    download_icon = row.find_element(By.XPATH, ".//i[contains(@class, 'fa-file-o')]")
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//i[contains(@class, 'fa-file-o')]") ))
                    download_icon.click()
                    downloaded = True
                    print("⏳ Downloading report...")
                    break
            except Exception as e:
                continue
        # Only print and return error if NO row was found
        if not downloaded:
            print(f"❌ Could not find report row for {expected_filename}")
            driver.quit()
            return None

        # Step 3: Wait for the file to finish downloading
        downloaded_file_path = os.path.join(download_dir, expected_filename)
        timeout = 30  # seconds
        waited = 0
        while waited < timeout:
            # Check if file exists and is not a .crdownload
            if os.path.exists(downloaded_file_path) and not any(glob.glob(downloaded_file_path + ".crdownload")):
                print(f"✅ Download complete: {downloaded_file_path}")
                break
            time.sleep(1)
            waited += 1
        else:
            print(f"❌ Download timed out for {expected_filename}")
            driver.quit()
            return None

        # Step 4: Parse Excel file to extract value from cell B15
        try:
            df = pd.read_excel(downloaded_file_path, header=None)  # Read without headers for fixed cell
            value = df.iloc[14, 1]  # Row 15 (index 14), Column B (index 1)
            print(f"✅ Extracted VAS Balance: {value} THB")
            return value
        except Exception as e:
            print(f"❌ Error parsing Excel file: {e}")
            return None

    finally:
        driver.quit()

# Run
if __name__ == "__main__":
    login_vas()
