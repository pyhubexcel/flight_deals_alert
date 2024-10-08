import os
from uuid import UUID
import asyncio
import datetime
from datetime import date
from .models import User, FlightBookingInfo, FlightInfo, SessionLocal
# from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from .utils import (validate_email, format_location_kiwi,
                     format_location_kayak)
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
from .kiwi import kiwimain
from .kayak import kayakmain
from celery import Celery
# from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

app1 = FastAPI()

# Add CORS middleware
app1.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


conf = ConnectionConfig(
   MAIL_USERNAME="atul.etech2011@gmail.com",
   MAIL_PASSWORD="aqvyqthjlhrurdrh",
   MAIL_PORT=587,
   MAIL_SERVER="smtp.gmail.com",
   MAIL_FROM="atul.etech2011@gmail.com",  # Add this field
   USE_CREDENTIALS=True,
   MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
   VALIDATE_CERTS=True
)

CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

celery_app = Celery(
    "app",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    broker_connection_retry_on_startup=True,
    enable_utc=True,
    task_default_queue='app_queue'
)

def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@celery_app.task(name="app.scrape_kiwi_task")
def scrape_kiwi_task(formatted_origin_kiwi, formatted_destination_kiwi, start_date, origin_city, destination_city):
    db = SessionLocal()
    try:
        kiwimain(formatted_origin_kiwi, formatted_destination_kiwi, start_date, origin_city, destination_city)
    finally:
        db.close()


@celery_app.task(name="app.scrape_kayak_process_task")
def scrape_kayak_process_task(formatted_origin_kayak, formatted_destination_kayak, start_date):
    db = SessionLocal()
    try:
        kayakmain(formatted_origin_kayak, formatted_destination_kayak, start_date)
    finally:
        db.close()

class Userinfo(BaseModel):
    email_id: str

class FlightBookingDetails(BaseModel):
    origin_city : str
    destination_city: str
    start_date: date
    country_name_origin: str
    country_name_destination: str
    end_date: Optional[date]=None
    first_name: str
    last_name: str
    user_id: int

class Alert(BaseModel):
    origin_city : str
    destination_city: str
    start_date: date


@app1.post("/v1/email-verification") 
def registration(user_details: Userinfo, db: Session = Depends(get_db)):
    email_id = user_details.email_id
    if not email_id:
        return JSONResponse(status_code=400, content={"message": "Please provide a valid email address"})
    
    email_isvalid = validate_email(email_id)
    if email_isvalid:
        existing_user = db.query(User).filter(User.email_id == email_id).first()
        if existing_user:
            return JSONResponse(status_code=400, content={"message": "Email already exists"})
        
        user_email = User(email_id=email_id)
        db.add(user_email)
        db.commit()
        return JSONResponse(status_code=201, content={"message": "Your email is registered"})
    return JSONResponse(status_code=400, content={"message": "Please provide a valid email format"})


@app1.post("/v1/user-flight-details") 
def registration(flight_booking: FlightBookingDetails, db: Session = Depends(get_db)):
    origin_city = flight_booking.origin_city
    destination_city = flight_booking.destination_city
    country_name_origin = flight_booking.country_name_origin
    country_name_destination = flight_booking.country_name_origin
    start_date = flight_booking.start_date
    end_date = flight_booking.end_date
    user_id = flight_booking.user_id
    first_name = flight_booking.first_name
    last_name = flight_booking.last_name
    formatted_origin_kiwi = format_location_kiwi(origin_city, country_name_origin)
    formatted_destination_kiwi = format_location_kiwi(destination_city, country_name_destination)
    scrape_kiwi_task.delay(formatted_origin_kiwi, formatted_destination_kiwi, start_date, origin_city, destination_city)
    formatted_origin_kayak = format_location_kayak(origin_city)
    formatted_destination_kayak = format_location_kayak(destination_city)
    scrape_kayak_process_task.delay(formatted_origin_kayak, formatted_destination_kayak, start_date)
    flight_info = FlightBookingInfo(start_destination=origin_city, end_destination=destination_city, 
          start_destination_country=country_name_origin, end_destination_country=country_name_destination,
            start_date=start_date, end_date=end_date ,user_id=user_id, first_name=first_name, last_name=last_name)
    db.add(flight_info)
    db.commit()
    return JSONResponse(status_code=201, content={"message": "Flight details are saved"})

@app1.get("/v1/alert/{flight_booking_id}")
def alert(flight_booking_id: int, db: Session = Depends(get_db)):
    flight_booking = db.query(FlightBookingInfo).filter(FlightBookingInfo.id == flight_booking_id).first()

    if not flight_booking:
        raise HTTPException(status_code=404, detail="Flight booking not found")

    booking_start_destination = flight_booking.start_destination
    booking_end_destination = flight_booking.end_destination
    booking_start_date = flight_booking.start_date

    matching_flights = db.query(FlightInfo).filter(
        FlightInfo.user_input_origin == booking_start_destination,
        FlightInfo.user_input_destination == booking_end_destination,
        FlightInfo.start_date == booking_start_date
    ).all()

    flight_details = [
        {
            "start_destination": flight.start_destination,
            "end_destination": flight.end_destination,
            "departure_time": flight.departure_time,
            "arrival_time": flight.arrival_time,
            "duration": flight.duration,
            "stops": flight.stops,
            "airline": flight.airline,
            "economy_class": flight.economy_class,
            "price": flight.price,
            "flight_link": flight.flight_link,
            "source_website": flight.source_website
        }
        for flight in matching_flights
    ]

    if not matching_flights:
        raise HTTPException(status_code=404, detail="No matching flights found")

    send_email_sync(flight_details)

    # message = MessageSchema(
    #    subject="Fastapi-Mail module",
    #    recipients=["aayush.excel2011@gmail.com"],
    #    body=str(flight_details),
    #    subtype="plain" 
    #    )

    # fm = FastMail(conf)
    # fm.send_message(message)  # No need for await, it's a synchronous call



    return JSONResponse(
    status_code=200, 
    content={
        "message": "Email sent successfully with matching flight details", 
        "data": flight_details
        }
    )

def send_email_sync(flight_details):
    message = MessageSchema(
       subject="Fastapi-Mail module",
       recipients=["aayush.excel2011@gmail.com"],
       body=str(flight_details),
       subtype="plain" 
       )
    
    fm = FastMail(conf)
    # Running the async function synchronously
    asyncio.run(fm.send_message(message))






