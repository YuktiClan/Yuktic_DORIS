# -----------------------------------------------------------
# SELENIUM IMPORTS
# -----------------------------------------------------------
# Tools used to locate elements, interact with dropdowns,
# and wait for elements to load on the webpage.
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -----------------------------------------------------------
# STANDARD PYTHON LIBRARIES
# -----------------------------------------------------------
# Used for time delays, file operations, regex cleaning,
# threading tasks, and date conversions.
import time
import random
import os
import re
import threading
from datetime import datetime

# -----------------------------------------------------------
# HTTP REQUESTS
# -----------------------------------------------------------
# Used to download captcha image directly from the website URL.
import requests

# -----------------------------------------------------------
# MYSQL DATABASE CONNECTOR
# -----------------------------------------------------------
# Used to connect and store scraped property records.
import mysql.connector

# -----------------------------------------------------------
# OCR AND IMAGE PROCESSING
# -----------------------------------------------------------
# EasyOCR reads captcha text.
# OpenCV and NumPy are used for preprocessing the captcha image
# to improve OCR accuracy.
import easyocr
import numpy as np
import cv2

# -----------------------------------------------------------
# ENVIRONMENT VARIABLE LOADER
# -----------------------------------------------------------
# Loads database credentials and other configs from .env file.
from dotenv import load_dotenv

# -----------------------------------------------------------
# IMPORT MAIN MODULE
# -----------------------------------------------------------
# Used for accessing scraper control flags and
# sending live status updates to frontend.


# -----------------------------------------------------------
# ASYNC SUPPORT
# -----------------------------------------------------------
# Used for asynchronous status broadcasting to frontend.
import asyncio




load_dotenv()

# -----------------------------------------------------------
# SELENIUM EXCEPTION HANDLING
# -----------------------------------------------------------
# Handles cases where expected browser alerts are not present.
from selenium.common.exceptions import NoAlertPresentException


# OCR READER INITIALIZATION
# -----------------------------------------------------------
# Initialize EasyOCR reader once globally for performance.
reader = easyocr.Reader(["en"], gpu=False)



def send_status(msg, broadcast_status):
    try:
        asyncio.run(broadcast_status(msg))
    except RuntimeError:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.create_task(broadcast_status(msg))
        
        
def start_scraper(driver, sro_name, locality_name, broadcast_status, is_stopped):
    # Import timeout exception locally to avoid namespace conflicts
    from selenium.common.exceptions import TimeoutException


    # -----------------------------------------------------------
    # GLOBAL VARIABLES
    # -----------------------------------------------------------
    # wait : Selenium wait object
    # selected_sro_name / selected_locality_name :
    # store current search parameters.
    global wait
    global selected_sro_name
    global selected_locality_name
    wait = WebDriverWait(driver, 30)

    print("\nContinuing with existing browser session\n")

    send_status("Auto captcha detection start",broadcast_status )

    # -----------------------------------------------------------
    # CAPTCHA FILE PATH SETUP
    # -----------------------------------------------------------
    # Ensures captcha image is saved inside backend directory.

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CAPTCHA_PATH = os.path.join(BASE_DIR, "captcha.png")

    # -----------------------------------------------------------
    # CAPTCHA OCR PROCESSING FUNCTION
    # -----------------------------------------------------------
    # Steps:
    # 1. Load captcha image
    # 2. Convert to grayscale
    # 3. Apply threshold
    # 4. Remove noise
    # 5. Detect character contours
    # 6. Use EasyOCR to read each character

    def read_captcha_ocr(image_path):

        img = cv2.imread(image_path)

        if img is None:
            return ""

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply threshold to separate characters
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        # Invert colors for better OCR recognition
        thresh = 255 - thresh

        # Remove small noise from image
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # Enlarge image for better OCR accuracy
        thresh = cv2.resize(thresh, None, fx=3, fy=3)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        letters = []


        # Extract each detected character region
        for cnt in contours:

            x, y, w, h = cv2.boundingRect(cnt)

            if w > 10 and h > 20:
                letter = thresh[y : y + h, x : x + w]
                letters.append((x, letter))
        
        # Sort letters by horizontal position
        letters = sorted(letters, key=lambda x: x[0])

        captcha = ""

        for _, letter in letters:

            result = reader.readtext(
                letter, detail=0, allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            )

            if result:
                captcha += result[0]
                
        # Remove unwanted characters
        captcha = re.sub("[^A-Z0-9]", "", captcha)

        if len(captcha) != 6:
            return ""

        return captcha

    # -----------------------------------------------------------
    # CAPTCHA AUTO DELETE
    # -----------------------------------------------------------
    # Deletes captcha image after 120 seconds to prevent
    # unnecessary file accumulation.


    def delete_captcha():

        time.sleep(120)

        if os.path.exists(CAPTCHA_PATH):
            os.remove(CAPTCHA_PATH)
            print("Captcha image deleted automatically.")

    # -----------------------------------------------------------
    # CAPTCHA DOWNLOAD FUNCTION
    # -----------------------------------------------------------
    # Fetches captcha image URL from webpage and saves it locally.

    def download_captcha():

        if os.path.exists(CAPTCHA_PATH):
            os.remove(CAPTCHA_PATH)

        captcha_img = driver.find_elements(
            By.XPATH, "//img[contains(@src,'CaptchaImage')]"
        )

        if not captcha_img:
            print("Captcha not present → refreshing only")

            refresh_captcha()

            for _ in range(3):
                captcha_img = driver.find_elements(
                    By.XPATH, "//img[contains(@src,'CaptchaImage')]"
                )

                if captcha_img:
                    break

                print("Retrying captcha load...")
                time.sleep(2)

            if not captcha_img:
                print("Captcha still missing after retries ❌")
                return False   # 🔥 important

        # ✅ ALWAYS define captcha_src
        captcha_src = captcha_img[0].get_attribute("src")

        try:
            captcha_data = requests.get(captcha_src, timeout=10).content

            with open(CAPTCHA_PATH, "wb") as f:
                f.write(captcha_data)

            print("Captcha downloaded ✅")
            return True   # 🔥 important

        except Exception as e:
            print("Captcha download failed:", e)
            return False

    # -----------------------------------------------------------
    # CAPTCHA REFRESH HANDLER
    # -----------------------------------------------------------
    # Refreshes captcha in the following cases:
    # - OCR failed
    # - Incorrect captcha alert
    # - ASP.NET server error page

    def refresh_captcha():

        print("Refreshing captcha...")

        try:
            alert = driver.switch_to.alert
            print("Alert detected:", alert.text)
            alert.accept()
            time.sleep(1)
        except:
            pass

        # detect ASP.NET server error page
        if "Server Error in '/' Application" in driver.page_source:
            print("Website crashed. Reloading search page...")

            driver.get(
                "https://esearch.delhigovt.nic.in/Complete_search_without_regyear.aspx"
            )
            time.sleep(6)

            # reselect SRO
            sro_element = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//select[contains(@id,'ddl_sro')]")
                )
            )

            Select(sro_element).select_by_visible_text(selected_sro_name)

            time.sleep(3)

            # reselect locality
            locality_element = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//select[contains(@id,'ddl_loc')]")
                )
            )

            Select(locality_element).select_by_visible_text(selected_locality_name)

            time.sleep(3)

            if not download_captcha():
                print("Retrying captcha download...")

                for _ in range(2):
                    time.sleep(2)
                    if download_captcha():
                        break
            time.sleep(random.uniform(1, 3))
            return

        try:
            refresh_btn = driver.find_element(
                By.XPATH, "//input[contains(@id,'ibtnRefresh')]"
            )

            # store old captcha element
            old_captcha = driver.find_element(
                By.XPATH, "//img[contains(@src,'CaptchaImage')]"
            )

            driver.execute_script("arguments[0].click();", refresh_btn)

            # wait until captcha changes
            wait.until(EC.staleness_of(old_captcha))

            time.sleep(1)

        except:
            print("Refresh button not found → FULL RESET")

            driver.delete_all_cookies()
            driver.get("https://esearch.delhigovt.nic.in/Complete_search_without_regyear.aspx")

            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//select[contains(@id,'ddl_sro')]")
                )
            )

            ensure_selection()

        if not download_captcha():
            print("Retrying captcha download...")

            for _ in range(2):
                time.sleep(2)
                if download_captcha():
                    break
        time.sleep(random.uniform(1, 3))


    # -----------------------------------------------------------
    # ENSURE DROPDOWN SELECTION
    # -----------------------------------------------------------
    # Sometimes ASP.NET refresh resets dropdown selections.
    # This function verifies and restores them.
    def ensure_selection():

        # check SRO
        sro_dropdown = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//select[contains(@id,'ddl_sro')]")
            )
        )

        current_sro = Select(sro_dropdown).first_selected_option.text.strip()

        if current_sro != selected_sro_name:

            print("SRO reset detected. Re-selecting SRO...")

            Select(sro_dropdown).select_by_visible_text(selected_sro_name)

            time.sleep(random.uniform(2, 4))

        # check locality
        locality_dropdown = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//select[contains(@id,'ddl_loc')]")
            )
        )

        current_loc = Select(locality_dropdown).first_selected_option.text.strip()

        if current_loc != selected_locality_name:

            print("Locality reset detected. Re-selecting locality...")

            Select(locality_dropdown).select_by_visible_text(selected_locality_name)

            time.sleep(random.uniform(2, 4))

    # -----------------------------------------------------------
    # DATABASE CONNECTION
    # -----------------------------------------------------------
    # Connect to MySQL database using credentials stored in .env.
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

    cursor = db.cursor(dictionary=True)
    
    # -----------------------------------------------------------
    # STORE CURRENT SEARCH PARAMETERS
    # -----------------------------------------------------------
    selected_sro_name = sro_name
    selected_locality_name = locality_name

    # -----------------------------------------------------------
    # MARK SCRAPING STATUS AS IN_PROGRESS
    # -----------------------------------------------------------
    cursor.execute("""
    UPDATE property_records
    SET scrape_status='IN_PROGRESS'
    WHERE sro_name=%s AND locality_name=%s
    """,(selected_sro_name, selected_locality_name))

    db.commit()

    # -----------------------------------------------------------
    # SELECT SRO AND LOCALITY
    # -----------------------------------------------------------
    # Selects the required Sub-Registrar Office and Locality
    # from dropdowns on the search page.
    print("Selecting SRO:", selected_sro_name)

    sro_dropdown = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//select[contains(@id,'ddl_sro')]")
        )
    )

    Select(sro_dropdown).select_by_visible_text(selected_sro_name)
    
    time.sleep(random.uniform(2, 4))

    # wait until locality dropdown refreshes
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//select[contains(@id,'ddl_loc')]")
        )
    )

    print("Selecting Locality:", selected_locality_name)

    locality_dropdown = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//select[contains(@id,'ddl_loc')]")
        )
    )

    Select(locality_dropdown).select_by_visible_text(selected_locality_name)
    time.sleep(random.uniform(2, 4))

    # wait until locality is actually selected
    wait.until(
        EC.text_to_be_present_in_element(
            (By.XPATH, "//select[contains(@id,'ddl_loc')]"),
            selected_locality_name
        )
    )

    print("Locality selected:", selected_locality_name)

    # -----------------------------------------------------------
    # DOWNLOAD INITIAL CAPTCHA
    # -----------------------------------------------------------
    
    
    # ✅ ADD THIS BLOCK HERE
    if not driver.find_elements(By.XPATH, "//input[contains(@id,'txtcaptcha')]"):
        print("Captcha input not found → resetting page")

        driver.delete_all_cookies()

        driver.get("https://esearch.delhigovt.nic.in/Complete_search_without_regyear.aspx")

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//select[contains(@id,'ddl_sro')]")
            )
        )

        ensure_selection()

    # ✅ EXISTING CODE

    if not download_captcha():
        print("Retrying captcha download...")

        for _ in range(2):
            time.sleep(2)
            if download_captcha():
                break
    time.sleep(random.uniform(1, 3))

    attempt = 0
    max_attempts = 3

    while True:
        time.sleep(random.uniform(3, 6))

        if is_stopped():
            print("Scraper stopped by user")

            send_status("Scraper stopped by user", broadcast_status)

            driver.delete_all_cookies()
            driver.get("https://esearch.delhigovt.nic.in/Complete_search_without_regyear.aspx")

            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//select[contains(@id,'ddl_sro')]")
                )
            )

            print("Returned to clean search page after stop")

            return

        if attempt < max_attempts:

            # ✅ NORMAL OCR FLOW
            if not os.path.exists(CAPTCHA_PATH):
                if not download_captcha():
                    print("Retrying captcha download...")

                    for _ in range(2):
                        time.sleep(2)
                        if download_captcha():
                            break
                time.sleep(random.uniform(1, 3))

            ocr_text = read_captcha_ocr(CAPTCHA_PATH)

            print("OCR detected captcha:", ocr_text)

            if len(ocr_text) < 6:
                print("OCR result less than 6 characters, refreshing captcha...")
                refresh_captcha()
                time.sleep(random.uniform(2, 4))
                continue

            captcha = ocr_text
            print("Using OCR captcha:", captcha)


        elif attempt == max_attempts:

            print("OCR failed → forcing fresh captcha page")

            driver.delete_all_cookies()
            driver.get("https://esearch.delhigovt.nic.in/Complete_search_without_regyear.aspx")

            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//select[contains(@id,'ddl_sro')]")
                )
            )

            ensure_selection()
            time.sleep(3)

            # ✅ FORCE CAPTCHA TO LOAD
            for _ in range(3):
                if not download_captcha():
                    print("Retrying captcha download...")

                    for _ in range(2):
                        time.sleep(2)
                        if download_captcha():
                            break

                if os.path.exists(CAPTCHA_PATH):
                    print("Captcha ready for frontend ✅")
                    break

                print("Retrying captcha download...")
                time.sleep(2)

            attempt += 1
            continue


        else:

            # 🔥 MANUAL CAPTCHA MODE
            

            send_status("Auto captcha failed. Enter captcha manually", broadcast_status)
            


            print("\nWaiting for captcha from frontend...")

            if not os.path.exists(CAPTCHA_PATH):
                if not download_captcha():
                    print("Retrying captcha download...")

                    for _ in range(2):
                        time.sleep(2)
                        if download_captcha():
                            break
                time.sleep(2)

            captcha_file = os.path.join(BASE_DIR, "captcha_input.txt")

            start_time = time.time()

            while True:
                if os.path.exists(captcha_file):
                    with open(captcha_file, "r") as f:
                        captcha = f.read().strip()

                    os.remove(captcha_file)
                    print("Received captcha:", captcha)
                    break

                if time.time() - start_time > 60:
                    print("Timeout → refreshing captcha for user")

                    refresh_captcha()

                    for _ in range(3):
                        if not download_captcha():
                            print("Retrying captcha download...")

                            for _ in range(2):
                                time.sleep(2)
                                if download_captcha():
                                    break
                        if os.path.exists(CAPTCHA_PATH):
                            break
                        time.sleep(2)

                    send_status("Captcha expired. New captcha loaded.",broadcast_status)

                    start_time = time.time()
                    

                    for _ in range(3):
                        if not download_captcha():
                            print("Retrying captcha download...")

                            for _ in range(2):
                                time.sleep(2)
                                if download_captcha():
                                    break
                        if os.path.exists(CAPTCHA_PATH):
                            break
                        time.sleep(2)

                    
                    

                    start_time = time.time()

        time.sleep(3)

        captcha_box = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[contains(@id,'txtcaptcha')]")
            )
        )

        captcha_box.clear()
        captcha_box.send_keys(captcha)
        
        # -------- WEBSITE CRASH CHECK --------
        if "Server Error in '/' Application" in driver.page_source:
            print("Website crashed before captcha submit. Reloading...")

            driver.delete_all_cookies()

            driver.get("https://esearch.delhigovt.nic.in/Complete_search_without_regyear.aspx")

            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//select[contains(@id,'ddl_sro')]")
                )
            )

            ensure_selection()
            refresh_captcha()
            time.sleep(random.uniform(2, 4))
            continue
        # -------------------------------------
        

        # always re-locate search button to avoid stale element
        search_btn = driver.find_element(By.XPATH, "//input[@value='Search']")

        driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)

        time.sleep(random.uniform(3, 6))

        driver.execute_script("arguments[0].click();", search_btn)

        time.sleep(1)

        # FIRST handle captcha alert
        try:
            alert = driver.switch_to.alert
            print("Captcha incorrect:", alert.text)

            alert.accept()

            print("Waiting for page to stabilize after captcha error...")

            time.sleep(3)

            # re-locate captcha box (ASP.NET refreshes controls)
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[contains(@id,'txtcaptcha')]")
                )
            )

            if not download_captcha():
                print("Retrying captcha download...")

                for _ in range(2):
                    time.sleep(2)
                    if download_captcha():
                        break
            time.sleep(random.uniform(1, 3))

            attempt += 1
            continue

        except NoAlertPresentException:
            pass


        # THEN wait for results table
        try:

            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//table[contains(@id,'gv_search')]")
                )
            )

        

        except TimeoutException:

            print("Checking if results or message appeared...")

            time.sleep(3)

            # check results table
            table_check = driver.find_elements(
                By.XPATH, "//table[contains(@id,'gv_search')]"
            )

            if len(table_check) > 0:
                print("Results loaded after delay")
                break

            # check message (no data / remote server)
            msg = driver.find_elements(
                By.XPATH, "//span[contains(@id,'lblmsg')]"
            )

            if msg:
                message_text = msg[0].text.strip()
                print("Website message:", message_text)

                status_message = (
                    f"No data available for this SRO/Locality ({message_text}). "
                    "Returned to search page. Please re-enter SRO and Locality."
                )

                send_status(status_message, broadcast_status)

                print("No records found for this SRO and Locality")

                cursor.execute(
                """
                INSERT INTO property_records
                (reg_no, reg_date, first_party, second_party,
                property_address, area, deed_type, property_type,
                sro_name, locality_name, scrape_status)
                VALUES (NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,%s,%s,'COMPLETED')
                """,
                (selected_sro_name, selected_locality_name)
                )

                db.commit()

                # return to search page
                driver.get(
                    "https://esearch.delhigovt.nic.in/Complete_search_without_regyear.aspx"
                )

                wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//select[contains(@id,'ddl_sro')]")
                    )
                )
                

                return

            print("Manual captcha incorrect → refreshing captcha")

            # reset attempt so it stays in manual mode
            attempt = max_attempts + 1  

            # refresh captcha properly
            refresh_captcha()

            # ensure captcha is downloaded
            for _ in range(3):
                if not download_captcha():
                    print("Retrying captcha download...")

                    for _ in range(2):
                        time.sleep(2)
                        if download_captcha():
                            break
                if os.path.exists(CAPTCHA_PATH):
                    print("New captcha ready for frontend ✅")
                    break
                time.sleep(2)

            # notify frontend again
            send_status("Captcha incorrect. Please try again.", broadcast_status)
            continue

        

        # check if result table exists
        table = driver.find_elements(By.XPATH, "//table[contains(@id,'gv_search')]")

        if len(table) == 0:

            print("Captcha incorrect (no results table)")

            if attempt > max_attempts:
                attempt = max_attempts + 1   # stay in manual mode
            else:
                attempt += 1
            

            time.sleep(2)

            if not download_captcha():
                print("Retrying captcha download...")

                for _ in range(2):
                    time.sleep(2)
                    if download_captcha():
                        break
            time.sleep(random.uniform(1, 3))

            continue

        else:

            print("Captcha correct. Results loaded.")
            send_status("Captcha correct. Start fetching data", broadcast_status)

            time.sleep(8)

            # ensure results table fully renders
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            
            try:

                page_size = driver.find_elements(By.XPATH, "//select[contains(@name,'ddlPageSize')]")

                if page_size:

                    try:
                        Select(page_size[0]).select_by_value("20")
                        print("Rows per page changed to 20")

                        time.sleep(2)

                    except:
                        print("Page size change failed")

                else:
                    print("Pagination not present. Skipping page size change.")

                

                # wait for table to refresh
                time.sleep(4)

            except Exception as e:
                print("Could not change page size:", e)

            break
        
    

    # -----------------------------------------------------------
    # CAPTCHA SOLVING LOOP
    # -----------------------------------------------------------
    
    
    
    from selenium.webdriver.common.keys import Keys
    from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

    def go_to_page_one():

        try:

            print("Jumping directly to Page 1...")

            # wait for pagination input
            page_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[contains(@class,'gotopage')]")
                )
            )

            current_page = page_box.get_attribute("value")

            if current_page == "1":
                print("Already on Page 1")
                return

            # locate again to avoid stale element
            page_box = driver.find_element(
                By.XPATH, "//input[contains(@class,'gotopage')]"
            )

            page_box.clear()
            page_box.send_keys("1")
            page_box.send_keys(Keys.ENTER)

            # wait for table reload
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//table[contains(@id,'gv_search')]")
                )
            )

            print("Now on Page 1")

        except StaleElementReferenceException:

            print("Page refreshed, retrying page jump...")

            go_to_page_one()

        except TimeoutException:

            print("Pagination not available.")

    # -----------------------------------------------------------
    # SCRAPING PROPERTY RECORDS
    # -----------------------------------------------------------
    # Extracts property registration records from the results table
    # and inserts them into the MySQL database.

    data = []

    while True:
        time.sleep(random.uniform(3, 7))

        if is_stopped():
            print("Scraper stopped by user")

            send_status("Scraper stopped by user", broadcast_status)

            # go back to search page
            driver.delete_all_cookies()

            driver.get("https://esearch.delhigovt.nic.in/Complete_search_without_regyear.aspx")

            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//select[contains(@id,'ddl_sro')]")
                )
            )

            print("Returned to search page after stop")

            return

        send_status("Fetching property records", broadcast_status)
        
        print("\nScraping page...")

        rows = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//table[contains(@id,'gv_search')]//tr")
            )
        )

        page_data = []

        for r in rows:

            cols = r.find_elements(By.TAG_NAME, "td")

            row = [c.text.strip() for c in cols]

            if (
                len(row) >= 11
                and row[0].isdigit()
                and row[1]
                and row[2]
                and row[4]
                and row[6]
            ):

                page_data.append(row)
                data.append(row)

        for r in page_data:
            print(" | ".join(r))

        print("Rows scraped:", len(page_data))

       
        insert_data = []

        for row in page_data:

            try:
                reg_date = datetime.strptime(row[1], "%d-%m-%Y").date()
            except:
                reg_date = datetime.strptime(row[1], "%d %b %Y").date()

            insert_data.append((
                row[0],
                reg_date,
                row[2],
                row[4],
                row[6],
                row[8],
                row[9],
                row[10],
                selected_sro_name,
                selected_locality_name
            ))

        clean_data = [d for d in insert_data if d[8] and d[9]]

        cursor.executemany(
        """
        INSERT IGNORE INTO property_records
        (reg_no, reg_date, first_party, second_party,
        property_address, area, deed_type, property_type,
        sro_name, locality_name, scrape_status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'IN_PROGRESS')
        """,
        clean_data
        )

        db.commit()

        # -------- NEXT PAGE --------
        next_btn = driver.find_elements(By.XPATH, "//input[@title='Next Page']")

        if len(next_btn) > 0:

            print("Moving to next page...")

            driver.execute_script("arguments[0].click();", next_btn[0])

            time.sleep(random.uniform(4, 8))

            continue

        # -------- PREVIOUS YEAR --------

        prev_year = driver.find_elements(By.XPATH, "//input[@value='Previous Year']")

        if len(prev_year) > 0:

            print("\nMoving to previous year...\n")

            driver.execute_script("arguments[0].click();", prev_year[0])
            
            time.sleep(random.uniform(5, 10))

            # wait until results table reloads
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//table[contains(@id,'gv_search')]")
                )
            )

            time.sleep(2)

            go_to_page_one()

            continue

        print("\nNo more years available. Returning to search page...")

        # go back to search page
        driver.delete_all_cookies()

        driver.get("https://esearch.delhigovt.nic.in/Complete_search_without_regyear.aspx")

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//select[contains(@id,'ddl_sro')]")
            )
        )

        print("\nReturned to starting page. Ready for next SRO search.\n")

        send_status("Returned to search page. Please re-enter SRO and Locality", broadcast_status)

        break

    print("\nScraping complete")
    send_status("Scraping completed", broadcast_status)
    print("Total rows:", len(data))


    selected_sro_name = sro_name
    selected_locality_name = locality_name

    # mark scraping completed
    cursor.execute("""
    UPDATE property_records
    SET scrape_status='COMPLETED'
    WHERE sro_name=%s AND locality_name=%s
    """,(selected_sro_name, selected_locality_name))
    
    db.commit()

    db.close()
