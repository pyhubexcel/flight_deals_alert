from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from twocaptcha import TwoCaptcha
import time
import csv
import os
from selenium.webdriver.common.keys import Keys
# from app.db import saving_flight_data
from selenium.common.exceptions import NoSuchElementException, TimeoutException


# Function to initialize WebDriver
def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = ChromeService(executable_path=ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# JavaScript script to find reCAPTCHA clients
script = """
    function findRecaptchaClients() {
        if (typeof (___grecaptcha_cfg) !== 'undefined') {
            return Object.entries(___grecaptcha_cfg.clients).map(([cid, client]) => {
                const data = { id: cid, version: cid >= 10000 ? 'V3' : 'V2' };
                const objects = Object.entries(client).filter(([_, value]) => value && typeof value === 'object');
                objects.forEach(([toplevelKey, toplevel]) => {
                    const found = Object.entries(toplevel).find(([_, value]) => (
                        value && typeof value === 'object' && 'sitekey' in value && 'size' in value
                    ));
                    if (typeof toplevel === 'object' && toplevel instanceof HTMLElement && toplevel['tagName'] === 'DIV'){
                        data.pageurl = toplevel.baseURI;
                    }
                    if (found) {
                        const [sublevelKey, sublevel] = found;
                        data.sitekey = sublevel.sitekey;
                        const callbackKey = data.version === 'V2' ? 'callback' : 'promise-callback';
                        const callback = sublevel[callbackKey];
                        if (!callback) {
                            data.callback = null;
                            data.function = null;
                        } else {
                            data.function = callback;
                            const keys = [cid, toplevelKey, sublevelKey, callbackKey].map((key) => `['${key}']`).join('');
                            data.callback = `___grecaptcha_cfg.clients${keys}`;
                        }
                    }
                });
                return data;
            });
        }
        return [];
    }
    return findRecaptchaClients();
"""

# Getters
def get_captcha_params(script, browser):
    retries = 0
    while retries < 5:
        try:
            result = browser.execute_script(script)
            if not result or not result[0]:
                raise IndexError("Callback name is empty or null")
            callback_function_name = result[0]['function']
            sitekey = result[0]['sitekey']
            print("Got the callback function name and sitekey")
            return callback_function_name, sitekey
        except (IndexError, KeyError, TypeError):
            retries += 1
            time.sleep(1)

def get_user_input():
    from_city = input("Enter departure city (From): ")
    to_city = input("Enter destination city (To): ")
    # departure_date = input("Enter departure date (YYYY-MM-DD): ")
    return from_city, to_city

# Solver captcha using 2Captcha
def solver_captcha(apikey, sitekey, url):
    solver = TwoCaptcha(apikey)
    try:
        result = solver.recaptcha(sitekey=sitekey, url=url)
        print("Captcha solved")
        return result['code']
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Send solved captcha token to the callback function
def send_token_callback(browser, callback_function, token):
    script = f"{callback_function}('{token}')"
    browser.execute_script(script)
    print("The token is sent to the callback function")

# Function to close the privacy policy popup
def close_privacy_popup(driver):
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button//div[text()='Accept all']"))
        )
        accept_button.click()
        print("Closed privacy policy popup.")
    except Exception as e:
        print(f"An error occurred while closing the privacy policy popup: {e}")


def uncheck_agoda_checkbox(driver):
    try:
        # Locate the checkbox element
        agoda_checkbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='AGD-CMP2FD_en_IN_FFDCMP2']"))
        )
        
        # Check if it is selected, and if so, click to unselect
        is_checked = agoda_checkbox.get_attribute("checked") or agoda_checkbox.get_attribute("aria-checked") == "true"
        if is_checked:
            agoda_checkbox.click()
            print("Unselected Agoda checkbox.")
        else:
            print("Agoda checkbox was already unselected.")
    except Exception as e:
        print(f"An error occurred while unchecking Agoda checkbox: {e}")


def change_month(month_name,driver,day):
    while True:
        # Get the current visible month label
        month_label = driver.find_element(By.CLASS_NAME, "w0lb-month-name").text
        
        if month_name in month_label:
            break
        else:
            print("dfsdfdfsdfs")
            # Find and click the 'Next month' button
            next_button = driver.find_element(By.XPATH, "//div[@role='button' and @aria-label='Next month']")
            next_button.click()
            time.sleep(1)  # Give it time to load the next month
        time.sleep(5)

    try:
        date_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@role='button' and text()='{day}']"))
        )
        date_button.click()
        time.sleep(10)
        print(month_name,"dddddddddddddddddddddddddddddddddd",day)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        

# Main scraping logic
def scrape_flights(driver, from_city, to_city):
    source_website = "https://www.kayak.co.in"
    # Wait for the input field to load
    time.sleep(5)
     # Click show more button if available
    def click_show_more():
        while True:
            try:
                time.sleep(10)
                button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "ULvh-button"))
                )
                button.click()
                
                print("Show more button clicked")
                time.sleep(2)
            except Exception as e:
                print("No more results to show.",str(e))
                break
        

        
    # Clear and set origin
    try:
        driver.maximize_window()
        origin_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@aria-label="Flight origin input"]'))
        )
        origin_input.clear()  # Clear the default value
        origin_input.click()
        time.sleep(1)
        origin_input.send_keys(from_city)  # Use user input for origin
        time.sleep(2)
        origin_input.send_keys(Keys.RETURN)
        print(f"Successfully selected {from_city} as the new origin!")
        
        # Clear and set destination
        destination_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='To?']"))
        )
        destination_input.clear()  # Clear the default value
        destination_input.click()
        time.sleep(1)
        destination_input.send_keys(to_city)  # Use user input for destination
        time.sleep(2)
        destination_input.send_keys(Keys.RETURN)
        print(f"Successfully selected {to_city} as the destination!")
        
        uncheck_agoda_checkbox(driver)
        
        driver.save_screenshot("dddddddddddddd.png")
        
        time.sleep(10)

        start_date_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Start date']")))
        start_date_button.click()
    
        time.sleep(10)
        month_name ="December 2024"
        day=23
        change_month(month_name,driver,day)
        
        end_date_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='End date']")))
        end_date_button.click()
    
        time.sleep(10)
        end_date =14
        end_month_name ="January 2025"
        

        change_month(end_month_name, driver, end_date)
     
        driver.save_screenshot("abcdfd.png")
  
        time.sleep(10)
        
        driver.save_screenshot("abcdfd.png")
        # Click the search button
        search_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='RxNS-button-container']"))
        )
        search_button.click()

        time.sleep(20)
        driver.save_screenshot("finaledfsd.png")
        
        click_show_more()
       

        # Gather flight data
        flights = driver.find_elements(By.CLASS_NAME, 'hJSA-item')
        flight_data_list = []
        
        
        for flight in flights:
            try:
                airline = flight.find_element(By.CLASS_NAME, 'c5iUd-leg-carrier').find_element(By.TAG_NAME, 'img').get_attribute('alt')
            except NoSuchElementException:
                airline = 'Unknown Airline'

            try:
                departure_time = flight.find_element(By.XPATH, './/div[contains(@class, "vmXl")][1]/span[1]').text
            except NoSuchElementException:
                departure_time = 'Unknown Departure Time'

            try:
                arrival_time = flight.find_element(By.XPATH, './/div[contains(@class, "vmXl")][1]/span[3]').text
            except NoSuchElementException:
                arrival_time = 'Unknown Arrival Time'

            try:
                start_destination = flight.find_element(By.XPATH, './/div[contains(@class, "c_cgF")][1]/span[1]').text
            except NoSuchElementException:
                start_destination = 'Unknown Start Destination'

            try:
                end_destination = flight.find_element(By.XPATH, './/div[contains(@class, "c_cgF")][2]/span[1]').text
            except NoSuchElementException:
                end_destination = 'Unknown End Destination'

            try:
                duration = flight.find_element(By.XPATH, './/div[contains(@class, "xdW8-mod-full-airport")]/div[contains(@class, "vmXl")]').text
            except NoSuchElementException:
                duration = 'Unknown Duration'

            time.sleep(10)

            try:
                stops = flight.find_element(By.CLASS_NAME, 'JWEO-stops-text').text
            except NoSuchElementException:
                stops = 'Unknown Stops'

            try:
                price = driver.find_element(By.CLASS_NAME, 'f8F1-price-text').text
            except NoSuchElementException:
                price = 'Unknown Price'

            try:
                 # Extracting the economy class
                flight_link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, './/a[contains(@class, "Iqt3") and @role="link"]'))
                ).get_attribute('href')
            except (NoSuchElementException, TimeoutException):
                flight_link = 'Unknown Flight Link'

            try:
                economy_class = driver.find_element(By.CLASS_NAME, 'DOum-name').get_attribute('title')
            except NoSuchElementException:
                economy_class = 'Unknown Economy Class'

            data = {
                "Airline": airline,
                "Departure Time": departure_time,
                "Arrival Time": arrival_time,
                "Start Destination": start_destination,
                "End Destination": end_destination,
                "Duration": duration,
                "Stops": stops, 
                "Price": price,
                "Flight Link": flight_link,
                "Economy Class": economy_class,
                'Source Website': source_website 
            }
            print(data)
            # saving_flight_data(data)
            flight_data_list.append(data)
            print("Saved flight data to DB:", data)
            
        # Save flight data to CSV
        # driver.save_screenshot("data.png")
        # csv_file_path = 'flight_data.csv'
        # with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        #     writer = csv.DictWriter(file, fieldnames=data.keys())
        #     writer.writeheader()
        # for flight_data in flight_data_list:
        #         writer.writerow(flight_data)

        # print(f"Flight data saved to {csv_file_path}")
       
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
        
# Main execution
def main():
    driver = init_driver()
    driver.get("https://www.kayak.co.in/flights/")
    print("Navigated to Kayak flights page.")

    try:
        api_key="80b506acd2a1a59f99486b198df8082c"
        # Solve captcha and close privacy policy
        callback_function, sitekey = get_captcha_params(script, driver)
        token = solver_captcha(api_key, sitekey, driver.current_url)
        if token:
            send_token_callback(driver, callback_function, token)
        else:
            print("Failed to solve captcha.")
            return

        close_privacy_popup(driver)
        time.sleep(10)
        # driver.save_screenshot("before_flight.png")
        
        # Get user input
        from_city, to_city = get_user_input()
        scrape_flights(driver, from_city, to_city)

    except Exception as e:
        print(f"An error occurred during execution: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
