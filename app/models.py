from sqlalchemy import (Column, Integer, String, Float,
                    DateTime, Text, ForeignKey, create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()


class FlightInfo(Base):
    __tablename__ = 'flight_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_destination = Column(String(100), nullable=False)
    end_destination = Column(String(100), nullable=False)
    departure_time = Column(String(25), nullable=False)
    arrival_time = Column(String(25), nullable=False)
    duration = Column(String(50), nullable=False)
    stops = Column(String(200), nullable=True)
    airline = Column(String(100), nullable=False)
    economy_class = Column(String(50), nullable=False)
    price = Column(String, nullable=False)
    flight_link = Column(Text, nullable=True)
    user_input_origin = Column(String(50),nullable=False)
    user_input_destination = Column(String(50),nullable=False)
    start_date = Column(String(50),nullable=False)
    end_date = Column(String(50),nullable=True)
    flight_unique_field = Column(String(250),nullable=False)
    source_website = Column(String(100), nullable=False)

class User(Base):
    __tablename__ = 'user_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(String(50), unique=True, nullable=False)

class FlightBookingInfo(Base):
    __tablename__ = 'flight_booking_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    start_destination = Column(String(100), nullable=False)
    end_destination = Column(String(100), nullable=False)
    start_destination_country = Column(String(100), nullable=False)
    end_destination_country = Column(String(100), nullable=False)
    start_date = Column(String(100), nullable=False)
    end_date = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('user_info.id'), nullable=False)


DATABASE_URL = "postgresql://superuser:Java_123@localhost:5432/blaise"
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)
