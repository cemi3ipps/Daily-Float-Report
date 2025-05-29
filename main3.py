import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load environment variables
load_dotenv()
CIMB_COMPANY_ID = os.getenv("CIMB_COMPANY_ID")
CIMB_USERNAME = os.getenv("CIMB_USERNAME")
CIMB_PASSWORD = os.getenv("CIMB_PASSWORD")

# Setup Chrome WebDriver (reuse logic from main2.py)
def setup_driver(download_dir=None):
    options = Options()
    options.add_argument("--headless")  # Enable headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
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
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    return webdriver.Chrome(options=options)

# CIMB login and balance extraction (stub - update selectors as needed)
def login_and_get_cimb_balance():
    driver = setup_driver()
    try:
        print("Navigating to CIMB login page...")
        driver.get("https://www.bizchannel.cimbthai.com/corp/common2/login.do?action=loginRequest")
        time.sleep(2)
        print("Page title after loading login page:", driver.title)
        print("Current URL:", driver.current_url)

        print("\n[INFO] You may now manually press LOGOUT in the browser. Wait at least 10 seconds after the dashboard appears before logging out to ensure all debug info is printed.")

        # Fill in CIMB login form with explicit error handling
        try:
            company_field = driver.find_element(By.ID, "corpId")
            print("Found company ID field.")
        except Exception as e:
            print("❌ Could not find company ID field (corpId):", e)
            return
        try:
            user_field = driver.find_element(By.ID, "userName")
            print("Found username field.")
        except Exception as e:
            print("❌ Could not find username field (userName):", e)
            return
        try:
            password_field = driver.find_element(By.ID, "passwordEncryption")
            print("Found password field.")
        except Exception as e:
            print("❌ Could not find password field (passwordEncryption):", e)
            return
        try:
            login_button = driver.find_element(By.NAME, "submit1")
            print("Found login button.")
        except Exception as e:
            print("❌ Could not find login button (submit1):", e)
            return
        # Now fill and submit
        company_field.send_keys(CIMB_COMPANY_ID)
        user_field.send_keys(CIMB_USERNAME)
        password_field.send_keys(CIMB_PASSWORD)
        login_button.click()
        print("Login submitted, waiting for dashboard...")
        print("Login submitted, waiting for dashboard to load...")
        from selenium.common.exceptions import NoSuchElementException, TimeoutException
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        try:
            # Wait for URL to change to 'returnMain'
            WebDriverWait(driver, 20).until(
                EC.url_contains("returnMain")
            )
            print("✅ URL changed to dashboard. Now waiting for frameset...")
            # Wait for menuFrame to appear
            WebDriverWait(driver, 20).until(
                lambda d: len(d.find_elements(By.NAME, "menuFrame")) > 0
            )
            print("✅ Frameset loaded, proceeding to frame navigation.")
            print("[WAIT] Dashboard loaded. Waiting 5 seconds...")
            time.sleep(5)
        except Exception:
            print("❌ Dashboard did not load after login. Stopping.")
            return None

        # --- Frame switching logic ---
        cimb_balance = None
        try:
            # 1. Switch to menuFrame to click menu items
            driver.switch_to.default_content()
            driver.switch_to.frame("menuFrame")
            print("[WAIT] Switched to menuFrame. Waiting 5 seconds...")
            time.sleep(5)
            # Click 'Account Service & Information Management'
            menu_div = driver.find_element(By.XPATH, "//div[contains(text(), 'Account Service')]")
            menu_div.click()
            print("✅ Clicked 'Account Service & Information Management' menu.")
            print("[WAIT] Clicked Account Service & Information Management. Waiting 5 seconds...")
            time.sleep(5)
            # Print all <a> links in menuFrame after expanding menu
            links = driver.find_elements(By.TAG_NAME, "a")
            print("[DEBUG] Links in menuFrame after expanding menu:")
            for idx, link in enumerate(links):
                print(f"  Link {idx}: '{link.text.strip()}' | href={link.get_attribute('href')}")
            # Click 'Account Summary' using its id
            account_summary_link = driver.find_element(By.ID, "subs8")
            account_summary_link.click()
            print("✅ Clicked 'Account Summary' link.")
            print("[WAIT] Clicked Account Summary. Waiting 10 seconds...")
            time.sleep(10)
        except Exception:
            print("❌ Could not find or click the menu or Account Summary in menuFrame.")
            return None
        try:
            # 2. Switch to mainFrame to extract account and balance
            driver.switch_to.default_content()
            driver.switch_to.frame("mainFrame")
            print("[WAIT] Switched to mainFrame. Waiting 5 seconds...")
            time.sleep(5)
            # Find the available balance for the account
            balance_link = driver.find_element(By.XPATH, "//a[contains(@onclick, \"onViewLastTransaction('7013252356\")]")
            balance_text = balance_link.text.strip().replace(',', '')
            cimb_balance = float(balance_text)
            print(f"✅ Extracted CIMB Available Balance: {cimb_balance} THB")
            print("[WAIT] Extracted balance. Waiting 5 seconds...")
            time.sleep(5)
            # Attempt to logout via topFrame
            try:
                driver.switch_to.default_content()
                driver.switch_to.frame("topFrame")
                logout_link = driver.find_element(By.XPATH, "//a[contains(@href, 'action=logout') or @onclick='logout()']")
                logout_link.click()
                print("✅ Clicked logout link. Session closed.")
            except Exception:
                print("❌ Could not find or click the logout link. Please check manually.")
        except Exception:
            print("❌ Could not find or extract the account or balance in mainFrame.")
        try:
            # 3. Switch to topFrame or mainFrame to click logout (try both)
            driver.switch_to.default_content()
            try:
                driver.switch_to.frame("topFrame")
            except Exception:
                try:
                    driver.switch_to.frame("mainFrame")
                except Exception:
                    pass
            logout_link = driver.find_element(By.XPATH, "//a[contains(@href, 'action=logout') or @onclick='logout()']")
            logout_link.click()
            print("✅ Clicked logout link. Session closed.")
        except Exception:
            print("❌ Could not find or click the logout link. Please check manually.")
        return cimb_balance

    except Exception as e:
        print("❌ Error during CIMB login or scraping:", e)
    finally:
        # Do NOT close the browser automatically so user can inspect manually
        pass

if __name__ == "__main__":
    balance = login_and_get_cimb_balance()
    if balance is not None:
        print(f"\nCIMB Available Balance: {balance:,.2f} THB")
    else:
        print("\nNo CIMB balance found.")
