import re

def validate_email(email):
    # Define the regular expression for a valid email ID
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    
    # Use the match function to check if the email fits the pattern
    if re.match(email_regex, email):
        return True
    else:
        return False


def format_location_kiwi(city_name, country_name):
    city_name_formatted = city_name.lower().replace(" ", "-")
    country_name_formatted = country_name.lower().replace(" ", "-")
    return f"{city_name_formatted}-{country_name_formatted}"

def format_location_kayak(city_name):
    # Convert to lowercase and remove spaces
    return city_name.lower().replace(" ", "")