import requests
from dotenv import load_dotenv
import os
from app.db import saving_flight_data

# Load environment variables from .env file
load_dotenv()

# Function to fetch flight data from SerpAPI
def get_flight_data(api_key, origin, destination, outbound_date, return_date, currency="USD", language="en", show_hidden=True):
    url = "https://serpapi.com/search.json"
    
    # Parameters for the API call
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": currency,
        "hl": language,
        "api_key": api_key
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        flight_data = response.json()
        print(flight_data)
        return flight_data
        
    else:
        print(f"Error: {response.status_code}")
        return None

# Function to extract flight details from both best_flights and other_flights

def extract_flight_details(flight_data):
    if not flight_data:
        print("No flight data found.")
        return []

    flights_list = []  # List to store extracted flight dictionaries

    # Extract details from "best_flights"
    if "best_flights" in flight_data:
        flights = flight_data['best_flights']
        flights_list.extend(display_flight_details(flights))

    # Extract details from "other_flights"
    if "other_flights" in flight_data:
        other_flights = flight_data['other_flights']
        flights_list.extend(display_flight_details(other_flights))

    return flights_list 

# Helper function to display flight details and create a dictionary
def display_flight_details(flights):
    flight_dicts = []  # List to hold dictionaries for each flight

    for flight in flights:
        try:
            # Extract required fields
            origin = flight['flights'][0]['departure_airport']['name']
            destination = flight['flights'][-1]['arrival_airport']['name']
            departure_time = flight['flights'][0]['departure_airport']['time']
            arrival_time = flight['flights'][-1]['arrival_airport']['time']
            total_duration = flight.get('total_duration', 'N/A')
            airline = flight['flights'][0].get('airline', 'N/A')
            seat_class = flight['flights'][0].get('travel_class', 'Economy')

           
            price = flight.get('price', 'N/A')
            if price != 'N/A':
                price = f"${price} USD" 

            # Extract layovers and stop details
            layovers = flight.get('layovers', [])
            stops = len(layovers)
            layover_details = [f"{layover['name']} ({layover['duration']} mins)" for layover in layovers]
            layover_str = ', '.join(layover_details) if layover_details else "Direct flight"

            # Convert total duration from minutes to hours and minutes
            if isinstance(total_duration, int):
                hours = total_duration // 60
                minutes = total_duration % 60
                total_duration = f"{hours}h {minutes}m"

            # Generate flight link
           
            booking_token = flight.get('booking_token')
            if booking_token:
                flight_link = f"https://serpapi.com/search.json?engine=google_flights&departure_id={origin}&arrival_id={destination}&outbound_date={departure_time.split(' ')[0]}&return_date={arrival_time.split(' ')[0]}&currency=USD&hl=en&booking_token={booking_token}"
            else:
                flight_link = f"https://www.google.com/travel/flights/booking?hl=en#flt={flight.get('departure_token', '')}"
            source_website = "https://www.google.com/travel/flights/" 

            # Create a dictionary for the flight details
            flight_info = {
                "Start Destination": origin,
                "End Destination": destination,
                "Departure Time": departure_time,
                "Arrival Time": arrival_time,
                "Duration": total_duration,
                "Stops":  layover_str,
                "Airline": airline,
                "Economy Class": seat_class,
                "Price": price,
                "Flight Link": flight_link,
                "Source Website": source_website
                
            }
            saving_flight_data(flight_info)
            flight_dicts.append(flight_info)  

            

        except KeyError as e:
            print(f"Key not found: {e}")

    return flight_dicts  

# Main part of the script
if __name__ == "__main__":
    API_KEY = '6038f85478078f50c1243e55bd4e6e4c6fc09eb5f68b82161cfd7ef351d49c32'
    
    origin = "DEL"  # Delhi IATA code
    destination = "BOM"  # Mumbai IATA code
    outbound_date = "2024-10-03"
    return_date = "2024-10-10"
    
    # Fetch the flight data
    flight_data = get_flight_data(API_KEY, origin, destination, outbound_date, return_date)
    
    # Extract and display the details
    flight_details_list = extract_flight_details(flight_data)

    # Print the flight details dictionary for demonstration
    for flight in flight_details_list:
        print(flight)
        



# import requests
# from dotenv import load_dotenv
# import os
# from db import saving_flight_data

# # Load environment variables from .env file
# load_dotenv()

# # Function to fetch flight data from SerpAPI
# def get_flight_data(api_key, origin, destination, outbound_date, return_date, currency="USD", language="en"):
#     url = "https://serpapi.com/search.json"
    
#     # Parameters for the API call
#     params = {
#         "engine": "google_flights",
#         "departure_id": origin,
#         "arrival_id": destination,
#         "outbound_date": outbound_date,
#         "return_date": return_date,
#         "currency": currency,
#         "hl": language,
#         "api_key": api_key
#     }
    
#     response = requests.get(url, params=params)
    
#     if response.status_code == 200:
#         return response.json()
#     else:
#         print(f"Error: {response.status_code}")
#         return None

# # Function to extract flight details from both best_flights and other_flights
# def extract_flight_details(flight_data):
#     if not flight_data:
#         print("No flight data found.")
#         return []

#     flights_list = []

#     # Extract details from "best_flights"
#     if "best_flights" in flight_data:
#         flights_list.extend(display_flight_details(flight_data['best_flights']))

#     # Extract details from "other_flights"
#     if "other_flights" in flight_data:
#         flights_list.extend(display_flight_details(flight_data['other_flights']))

#     return flights_list

# # Helper function to display flight details and create a dictionary
# def display_flight_details(flights):
#     flight_dicts = []

#     for flight in flights:
#         try:
#             # Extract required fields
#             origin = flight['flights'][0]['departure_airport'].get('name', 'Unknown')
#             destination = flight['flights'][-1]['arrival_airport'].get('name', 'Unknown')
#             departure_time = flight['flights'][0]['departure_airport'].get('time', 'Unknown')
#             arrival_time = flight['flights'][-1]['arrival_airport'].get('time', 'Unknown')
#             total_duration = flight.get('total_duration', 'N/A')
#             airline = flight['flights'][0].get('airline', 'N/A')
#             seat_class = flight['flights'][0].get('travel_class', 'Economy')

#             price = flight.get('price', 'N/A')
#             if price != 'N/A':
#                 price = f"${price} USD"

#             layovers = flight.get('layovers', [])
#             stops = len(layovers)
#             layover_details = [f"{layover['name']} ({layover['duration']} mins)" for layover in layovers]
#             layover_str = ', '.join(layover_details) if layover_details else "Direct flight"

#             # Convert total duration from minutes to hours and minutes
#             if isinstance(total_duration, int):
#                 hours = total_duration // 60
#                 minutes = total_duration % 60
#                 total_duration = f"{hours}h {minutes}m"

#             booking_token = flight.get('booking_token', '')  # Assuming the API provides booking_token
#             if booking_token:
#                 flight_link = (
#                     f"https://www.google.com/travel/flights/booking?"
#                     f"tfs=CBwQAhpJEgoyMDI0LTEwLTAzIh8KA0{origin}BIKMjAyNC0xMC0wMxoDQk9NKgJBSTIDODA1agwIAhIIL20vMGRsdjByDAgDEggvbS8wNHZtcBpJEgoyMDI0LTEwLTA0"
#                     f"Ih8KA0{destination}SIKMjAyNC0xMC0wMxoDQ{destination}"
#                     f"&booking_token={booking_token}"
#                 )
#             else:
#                 # Fallback to a basic search link if booking_token is missing
#                 flight_link = (
#                     f"https://www.google.com/travel/flights?q=flights%20from%20{origin}%20to%20{destination}%20on%20{departure_time}%20returning%20on%20{arrival_time}"
#                 )

#             source_website = "https://www.google.com/travel/flights/"

#             # Create a dictionary for the flight details
#             flight_info = {
#                 "Start Destination": origin,
#                 "End Destination": destination,
#                 "Departure Time": departure_time,
#                 "Arrival Time": arrival_time,
#                 "Duration": total_duration,
#                 "Stops": layover_str,
#                 "Airline": airline,
#                 "Economy Class": seat_class,
#                 "Price": price,
#                 "Flight Link": flight_link,
#                 "Source Website": source_website
#             }

#             saving_flight_data(flight_info)
#             flight_dicts.append(flight_info)

#         except KeyError as e:
#             print(f"Key not found: {e}")

#     return flight_dicts

# # Main part of the script
# if __name__ == "__main__":
#     API_KEY = os.getenv('API_KEY')

#     # Pass user input or parameters dynamically
#     origin = input("Enter origin IATA code: ") or "DEL"
#     destination = input("Enter destination IATA code: ") or "BOM"
#     outbound_date = input("Enter outbound date (YYYY-MM-DD): ") or "2024-10-02"
#     return_date = input("Enter return date (YYYY-MM-DD): ") or "2024-10-10"

#     # Fetch the flight data
#     flight_data = get_flight_data(API_KEY, origin, destination, outbound_date, return_date)

#     # Extract and display the details
#     flight_details_list = extract_flight_details(flight_data)

#     # Print the flight details dictionary for demonstration
#     for flight in flight_details_list:
#         print(flight)


