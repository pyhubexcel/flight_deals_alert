from playwright.sync_api import sync_playwright
from .db import saving_flight_data
import time



def construct_url(from_city, to_city, departure_date):
    base_url = 'https://www.kiwi.com/en/search/results'
    url = f"{base_url}/{from_city}/{to_city}/{departure_date}/no-return"
    print(url)
    return url

def accept_cookies(page):
    """Accept the cookies consent pop-up if it appears."""
    try:
        page.wait_for_selector("button[data-test='CookiesPopup-Accept']", timeout=10000)
        page.click("button[data-test='CookiesPopup-Accept']")
        print("Cookies accepted.")
    except Exception as e:
        print(f"Cookies popup not found or could not be accepted: {e}")

def scrape_flight_cards(page, scraped_flights_set, origin_city, destination_city, departure_date):
    """Scrape the flight cards data from the current page."""
    flight_data = []
    time.sleep(5)
    source_website = "https://www.kiwi.com"
    
    flight_cards = page.query_selector_all("div[data-test='ResultCardWrapper']")

    if flight_cards:
        print(f"Found {len(flight_cards)} flight cards to scrape.")
        for index, card in enumerate(flight_cards, start=1):
            try:
                origin = card.query_selector("div[data-test='ResultCardStopPlace']").inner_text().strip()
                destination = card.query_selector_all("div[data-test='ResultCardStopPlace']")[1].inner_text().strip()
                departure_time = card.query_selector_all("time")[0].inner_text().strip()
                arrival_time = card.query_selector_all("time")[2].inner_text().strip()
                duration = card.query_selector("div[data-test='ResultCardSectorDuration']").inner_text().strip()
                stops = card.query_selector("div[data-test*='StopCountBadge']").inner_text().strip()
                airline = card.query_selector("div[data-test='ResultCardCarrierLogo'] img").get_attribute('alt')
                seat_class_element = card.query_selector("div[data-test='BagageBreakdown']")
                seat_class = seat_class_element.inner_text().strip() if seat_class_element else 'Economy'
                price = card.query_selector("div[data-test='ResultCardPrice']").inner_text().strip().replace('\xa0', ' ')

                # Create a unique identifier for this flight to avoid duplicates
                flight_id = f"{origin}_{destination}_{departure_time}_{arrival_time}_{airline}_{price}_{departure_date}"

                if flight_id in scraped_flights_set:
                    print(f"Duplicate flight found")
                    continue

                # Click the Select button to reveal the flight link
                select_button = card.query_selector("div[data-test='BookingButton'] button")
                select_button.click()

                # Wait for the Continue button and its link to be visible
                page.wait_for_selector("a[data-test='ContinueButton']", timeout=15000)

                # Get the booking link
                flight_link = page.query_selector("a[data-test='ContinueButton']").get_attribute('href')

                flight_link = source_website + flight_link

                flight_info = {
                    'Start Destination': origin,
                    'End Destination': destination,
                    'Departure Time': departure_time,
                    'Arrival Time': arrival_time,
                    'Duration': duration,
                    'Stops': stops,
                    'Airline': airline,
                    'Economy Class': seat_class,
                    'Price': price,
                    'Flight Link': flight_link,
                    'Source Website': source_website,
                    'From City': origin_city,
                    'To City': destination_city,
                    'Departure Date': departure_date,
                    'Flight Unique Id': flight_id
                }
                saving_flight_data(flight_info)
                flight_data.append(flight_info)

                # Add this flight's unique ID to the set to prevent future duplicates
                scraped_flights_set.add(flight_id)

                print(f"Scraped flight")

                # Close modal or flight card if applicable
                page.click("button[data-test='ModalCloseButton']")

            except Exception as e:
                print(f"Error scraping flight card {index}: {e}")
    return flight_data


def kiwimain(from_city,to_city,departure_date, origin_city, destination_city):
  
    url = construct_url(from_city, to_city, departure_date)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Set headless=True or False based on debugging needs
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
        page = context.new_page()
        page.goto(url)

        # Accept cookies if needed
        accept_cookies(page)

        time.sleep(10)  # Allow page to load

        all_flight_data = []
        scraped_flights_set = set()  # Track unique flight entries

        # Continuously scrape and check for more flights
        while True:
            print("Scraping current page for flight data...")
            time.sleep(5)
            current_data = scrape_flight_cards(page, scraped_flights_set, origin_city, destination_city, departure_date)

            # If no new data is loaded, stop scraping
            if not current_data:
                print("No new data loaded, stopping scraper.")
                break

       
            all_flight_data.extend(current_data)

            try:
                load_more_button = page.query_selector("//button[contains(., 'Load more')]")
                if load_more_button:
                    load_more_button.click()
                    print("'Load more' button clicked, loading more results...")
                    time.sleep(5)  
                else:
                    print("No more 'Load more' button found, stopping scraper.")
                    break
            except Exception as e:
                print(f"Error loading more flights: {e}")
                break

     
        browser.close()

        
        print(f"Total Flights Scraped: {len(all_flight_data)}")
        for flight in all_flight_data:
            print(flight)
