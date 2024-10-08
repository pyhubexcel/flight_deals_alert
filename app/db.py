from .models import FlightInfo, SessionLocal
from sqlalchemy.orm import Session

def saving_flight_data(flight_info):
    session: Session = SessionLocal()
    flight_unique_id = flight_info.get("Flight Unique Id")

    existing_flight = session.query(FlightInfo).filter_by(flight_unique_field=flight_unique_id).first()

    if existing_flight:
        existing_flight.start_destination = flight_info.get("Start Destination")
        existing_flight.end_destination = flight_info.get("End Destination")
        existing_flight.departure_time = flight_info.get("Departure Time")
        existing_flight.arrival_time = flight_info.get("Arrival Time")
        existing_flight.duration = flight_info.get("Duration")
        existing_flight.stops = flight_info.get("Stops")
        existing_flight.airline = flight_info.get("Airline")
        existing_flight.economy_class = flight_info.get("Economy Class")
        existing_flight.price = flight_info.get("Price")
        existing_flight.flight_link = flight_info.get("Flight Link")
        existing_flight.source_website = flight_info.get("Source Website")
        existing_flight.user_input_origin = flight_info.get('From City')
        existing_flight.user_input_destination = flight_info.get('To City')
        existing_flight.start_date = flight_info.get('Departure Date')
    else:
        new_flight = FlightInfo(
            start_destination=flight_info.get("Start Destination"),
            end_destination=flight_info.get("End Destination"),
            departure_time=flight_info.get("Departure Time"),
            arrival_time=flight_info.get("Arrival Time"),
            duration=flight_info.get("Duration"),
            stops=flight_info.get("Stops"),
            airline=flight_info.get("Airline"),
            economy_class=flight_info.get("Economy Class"),
            price=flight_info.get("Price"),
            flight_link=flight_info.get("Flight Link"),
            source_website=flight_info.get("Source Website"),
            flight_unique_field=flight_unique_id,
            user_input_origin=flight_info.get('From City'),
            user_input_destination=flight_info.get('To City'),
            start_date=flight_info.get('Departure Date'),
        )
        session.add(new_flight)
    session.commit()
