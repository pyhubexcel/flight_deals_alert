import re, asyncio
import json
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

conf = ConnectionConfig(
   MAIL_USERNAME="atul.etech2011@gmail.com",
   MAIL_PASSWORD="aqvyqthjlhrurdrh",
   MAIL_PORT=587,
   MAIL_SERVER="smtp.gmail.com",
   MAIL_FROM="atul.etech2011@gmail.com",
   USE_CREDENTIALS=True,
   MAIL_STARTTLS=True,
   MAIL_SSL_TLS=False,
   VALIDATE_CERTS=True
)


def validate_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'   
    if re.match(email_regex, email):
        return True
    else:
        return False


def format_location_kiwi(city_name, country_name):
    city_name_formatted = city_name.lower().replace(" ", "-")
    country_name_formatted = country_name.lower().replace(" ", "-")
    return f"{city_name_formatted}-{country_name_formatted}"


def format_location_kayak(city_name):
    with open('app/cities_data.json', 'r') as file:
        data = json.load(file)
    city_name = data['cities'][city_name]['airport_codes']
    city_name = city_name[0]
    return city_name


def send_verification_email(email: str, magic_link: str):
    message = MessageSchema(
        subject="Verify your account",
        recipients=[email],  # List of recipients
        body=f"Please click on the following link to verify your account: {magic_link}",
        subtype="html"
    )
    fm = FastMail(conf)
    asyncio.run(fm.send_message(message))


def generate_magic_link(token: str):
    # Replace with your domain
    return f"http://116.202.210.102:8000/verify/{token}"


def flight_details_email(content):
    message = MessageSchema(
       subject="Fastapi-Mail module",
       recipients=["aayush.excel2011@gmail.com"],
       body=str(content),
       subtype="plain" 
       )
    fm = FastMail(conf)
    # Running the async function synchronously
    asyncio.run(fm.send_message(message))
