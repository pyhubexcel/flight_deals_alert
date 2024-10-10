import os
import uuid
import datetime
from datetime import date, timedelta
from typing import List, Optional

# from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from celery import Celery
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from .utils import (validate_email, format_location_kiwi,
                     format_location_kayak, flight_details_email,
                     send_verification_email, generate_magic_link)
from .kiwi import kiwimain
from .kayak import kayakmain
from .models import (User, FlightBookingInfo, FlightInfo,
                     VerificationToken, SessionLocal)

app1 = FastAPI()

# Add CORS middleware
app1.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
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


@app1.post("/v1/register/")
def registration(user_details: Userinfo, db: Session = Depends(get_db)):
    email_id = user_details.email_id
    if not email_id:
        return JSONResponse(status_code=400, content={"message": "Please provide a valid email address"})
    
    email_isvalid = validate_email(email_id)
    if email_isvalid:
        existing_user = db.query(User).filter(User.email_id == email_id).first()
        if existing_user:
            return JSONResponse(status_code=400, content={"message": "Email already exists"})
        created_at = date.today()
        user_email = User(email_id=email_id, created_at=created_at, islogin=1, isauthenticated=1)
        db.add(user_email)
        db.commit()
        return JSONResponse(status_code=201, content={"message": "Your email is registered",
                                                "user_email": user_email.email_id, "user_id": user_email.id})
    return JSONResponse(status_code=400, content={"message": "Please provide a valid email format"})


@app1.post("/v1/login/")
def login(user_details: Userinfo, db: Session = Depends(get_db)):
    email_id = user_details.email_id
    if not email_id:
        return JSONResponse(status_code=400, content={"message": "Please provide a valid email address"})
    
    email_isvalid = validate_email(email_id)
    if email_isvalid:
        existing_user = db.query(User).filter(User.email_id == email_id).first()
        if not existing_user:
            return JSONResponse(status_code=400, content={"message": "Email does not exists with us"})
        verification_token = db.query(VerificationToken).filter(
        VerificationToken.user_id == existing_user.id).first()
        token = str(uuid.uuid4())
        expires_at = datetime.datetime.now() + timedelta(hours=2)
        if verification_token:
            verification_token.token = token
            verification_token.expires_at = expires_at
            verification_token.is_used = False
            db.commit()
        else:
            verification_token = VerificationToken(
                user_id=existing_user.id, token=token, expires_at=expires_at
            )
            db.add(verification_token)
            db.commit()
        magic_link = generate_magic_link(token)
        send_verification_email(email_id, magic_link)
        return JSONResponse(status_code=201, content={"message": "Verification Email is send at your registered email_id and will be valid for only two hours"})
    return JSONResponse(status_code=400, content={"message": "Please provide a valid email format"})


@app1.post("/v1/user-flight-details/{user_id}") 
def registration(flight_booking: FlightBookingDetails, user_id: int, db: Session = Depends(get_db)):
    origin_city = flight_booking.origin_city
    destination_city = flight_booking.destination_city
    country_name_origin = flight_booking.country_name_origin
    country_name_destination = flight_booking.country_name_destination
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


@app1.get("/verify/{token}")
def verify_user(token: str, db: Session = Depends(get_db)):
    # Find the verification token in the database
    try:
        verification_token = db.query(VerificationToken).filter(VerificationToken.token == token).one()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content="Invalid token"
        )

    # Check if the token is already used or expired
    if verification_token.is_used:
        return JSONResponse(
            content="Token has already been used",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if datetime.datetime.now() > verification_token.expires_at:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content="Token has expired"
        )

    verification_token.is_used = True
    db.commit()

    return {"message": "Email verified successfully!"}


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

    flight_details_email(flight_details)
    return JSONResponse(
        status_code=200, 
        content={
            "message": "Email sent successfully with matching flight details", 
            "data": flight_details
        }
    )

@app1.get("/v1/get-profile")
def profile_details(user_details:Userinfo, db: Session = Depends(get_db)):
    email_id = user_details.email_id
    existing_user = db.query(User).filter(User.email_id == email_id).first()
    if existing_user.islogin==True:
        user_info = {
            "email_id": existing_user.email_id,
            "created_at": existing_user.created_at
        }
        return JSONResponse(
        status_code=200, 
        content={
            "data": user_info
        }
    )
    if existing_user.islogin==True:
        return JSONResponse(status=400, content = {"error": "You are not authenticated"})

  
@app1.post("/v1/logout/{user_id}")
def logout(user_id: int, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == user_id).first()
    existing_user.islogin = False
    existing_user.isauthenticated = False
    return JSONResponse(status=200, content={"mesage": "You ahve been logged out"})


