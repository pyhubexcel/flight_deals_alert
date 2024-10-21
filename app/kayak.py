from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from twocaptcha import TwoCaptcha
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from app.db import saving_flight_data
import time, os


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
        time.sleep(10)
        accept_button.click()
        print("Closed privacy policy popup.")
       
    except Exception as e:
        print(f"An error occurred while closing the privacy policy popup: {e}")



# Main scraping logic
def scrape_flights(driver, departure_date, origin_city, departure_city):
    time.sleep(5)

    def click_show_more():
        n=1
        while n<=10:
           
            try:
                time.sleep(10)
                button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "ULvh-button"))
                )
                button.click()
                
                print("Show more button clicked")
                time.sleep(2)
            except Exception as e:
                print("No more results to show.")
                break

            n+=1
        
    time.sleep(20)
    click_show_more()
    flights = driver.find_elements(By.CLASS_NAME, 'hJSA-item')
    flight_data_list = []
    
    
    for flight in flights:
        try:
            airline = flight.find_element(By.CLASS_NAME, 'c5iUd-leg-carrier').find_element(By.TAG_NAME, 'img').get_attribute('alt')
        except NoSuchElementException:
            continue

        try:
            departure_time = flight.find_element(By.XPATH, './/div[contains(@class, "vmXl")][1]/span[1]').text
        except NoSuchElementException:
            continue

        try:
            arrival_time = flight.find_element(By.XPATH, './/div[contains(@class, "vmXl")][1]/span[3]').text
        except NoSuchElementException:
            continue

        try:
            start_destination = flight.find_element(By.XPATH, './/div[contains(@class, "c_cgF")][1]/span[1]').text
        except NoSuchElementException:
            continue

        try:
            end_destination = flight.find_element(By.XPATH, './/div[contains(@class, "c_cgF")][2]/span[1]').text
        except NoSuchElementException:
            continue

        try:
            duration = flight.find_element(By.XPATH, './/div[contains(@class, "xdW8-mod-full-airport")]/div[contains(@class, "vmXl")]').text
        except NoSuchElementException:
            continue

        time.sleep(10)

        try:
            stops = flight.find_element(By.CLASS_NAME, 'JWEO-stops-text').text
        except NoSuchElementException:
            continue

        try:
            price = driver.find_element(By.CLASS_NAME, 'f8F1-price-text').text
        except NoSuchElementException:
            continue

        try:
                # Extracting the economy class
            flight_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, './/a[contains(@class, "Iqt3") and @role="link"]'))
            ).get_attribute('href')
        except (NoSuchElementException, TimeoutException):
            continue

        try:
            economy_class = driver.find_element(By.CLASS_NAME, 'DOum-name').get_attribute('title')
        except NoSuchElementException:
            continue

        
        source_website = "https://www.kayak.co.in/flights/"

        flight_link = source_website + flight_link

        flight_id = f"{start_destination}_{end_destination}_{departure_time}_{arrival_time}_{airline}_{price}_{departure_date}"

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
            "Flight Unique Id": flight_id,
            'From City':  origin_city,
            'To City': departure_city,
            'Departure Date': departure_date,
            'Source Website': "https://www.kayak.co.in/flights/" 
        }
        print(data)
        saving_flight_data(data)
        flight_data_list.append(data)
        print("Saved flight data to DB:", data)
        
     

def kayakmain(origin , destination, departure_date, origin_city, departure_city):
    driver = init_driver()
    url =f"https://www.kayak.co.in/flights/{origin}-{destination}/{departure_date}?sort=bestflight_b"
    driver.get(url)
    print("Navigated to Kayak flights page.")
    try:
        api_key = os.getenv("CAPTCHA-KEY")
        callback_function, sitekey = get_captcha_params(script, driver)
        token = solver_captcha(api_key, sitekey, driver.current_url)
        if token:
            send_token_callback(driver, callback_function, token)
        else:
            print("Failed to solve captcha.")
            return

        close_privacy_popup(driver)
        time.sleep(10)
       
        scrape_flights(driver, departure_date, origin_city, departure_city)

    except Exception as e:
        print(f"An error occurred during execution: {e}")
    finally:
        driver.quit()


