import serial
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import time

# Set up FastAPI app
app = FastAPI(redoc_url="/")

# Set up the serial connection to the Arduino
# Adjust 'COM3' and baudrate as per your setup
ser = serial.Serial('COM8', 115200, timeout=0.1)


# FastAPI model for returning event data
class Event(BaseModel):
    id: str
    event_code: str
    timestamp: str
    
USERNAME = "username"
PASSWORD = "password"


NUMBER_TO_FUNCTION:dict = {
    69: "power",
    70: "VOL+",
    71: "FUNC/STOP",
    
}

    
def send_event_to_database(event_code:str) -> bool:
    url = "http://127.0.0.1:5000/add_event"
    payload = {
        "event_code": event_code
    }
    
    # Make the POST request
    response = requests.post(
        url,
        json=payload,             # Automatically sets Content-Type to application/json
        auth=(USERNAME, PASSWORD) # Basic Authentication
    )

    # Check the response
    if response.status_code == 200:
        print("Event saved to DB:", response.json())
        return True
    else:
        print("Failed to save event:", response.status_code, response.text)
        return False


last_sent_event = None
last_sent_time = round(time.time() * 1000) # current millisecond
DELAY_IDENTICAL_EVENT = 500 # 0.5 seconds

if __name__ == "__main__":
    print("ArduinoConnector Launched.")

    # Run the main serial reading loop
    while True:
        if ser.in_waiting > 0:
            value = ser.readline()
            event_code = value.decode("utf-8").strip()
            if event_code:  # Ensure event code is not empty
                
                if event_code == last_sent_event and last_sent_time+DELAY_IDENTICAL_EVENT > round(time.time() * 1000):
                    print(f"Event sent too soon after the last: {event_code}")
                
                else:
                    print(f"Received: {event_code}")
                    send_event_to_database(event_code)
                    last_sent_event = event_code
                    last_sent_time = round(time.time() * 1000)
                    