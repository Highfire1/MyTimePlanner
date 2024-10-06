import serial
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import time

import firebase

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
    

NUMBER_TO_FUNCTION: dict = {
    # REMOTE BUTTON, MODE, MODE (VERB), CATEGORY
    69: ("POWER", "IDLE", "", "NONE", "🔌"),              # Power
    70: ("VOL+", "STUDY", "STUDYING", "ACTIVITY", "📚"),  # Volume Up
    71: ("FUNC/STOP", "WORK", "WORKING", "ACTIVITY", "💻"),  # Function/Stop
    68: ("FF_back", "", "", "", "⏪"),                  # Fast Forward Back
    64: ("play/pause", "READ", "READING", "ACTIVITY", "📖"),  # Play/Pause
    67: ("FF_forward", "EXERCISE", "EXERCISING", "ACTIVITY", "🏃‍♂️"),  # Fast Forward Forward
    7: ("DOWN", "", "", "", "⬇️"),                      # Down
    21: ("VOL-", "MEDITATION", "MEDITATING", "ACTIVITY", "🧘‍♂️"),  # Volume Down
    9: ("UP", "RESEARCH", "RESEARCHING", "ACTIVITY", "⬆️"),  # Up
    22: ("ZERO", "GREAT", "", "MOOD", "😊"),               # Zero
    25: ("EQ", "GAME", "GAMING", "ACTIVITY", "🎮"),      # Equalizer
    13: ("ST/REPT", "CODE", "CODING", "ACTIVITY", "💻"),  # Stop/Repeat
    12: ("ONE", "GOOD", "", "MOOD", "👍"),                # One
    24: ("TWO", "CLEAN", "CLEANING", "ACTIVITY", "🧹"),   # Two
    94: ("THREE", "SLEEP", "SLEEPING", "ACTIVITY", "😴"),  # Three
    8: ("FOUR", "NEUTRAL", "", "MOOD", "😐"),             # Four
    28: ("FIVE", "1HOUR", "", "TIMER", "⏳"),             # Five
    90: ("SIX", "30MIN", "", "TIMER", "⏱️"),              # Six
    66: ("SEVEN", "BAD", "", "MOOD", "😞"),                # Seven
    82: ("EIGHT", "5MIN", "", "TIMER", "⏲️"),             # Eight
    74: ("NINE", "1MIN", "", "TIMER", "⏲️"),              # Nine
}



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
            
            if int(event_code) in NUMBER_TO_FUNCTION:
                event_code = NUMBER_TO_FUNCTION[int(event_code)]
            
            # if event code is empty ignore it
            if not event_code:  
                continue
            
            if event_code == last_sent_event and last_sent_time+DELAY_IDENTICAL_EVENT > round(time.time() * 1000):
                print(f"Cancelled double event: {event_code}")
            
            elif event_code[3] == "TIMER" or  event_code[3] == "NONE":
                print(f"Ignored {event_code}")
                # timers handled at arduino level
                # ignore none buttons
                pass
            
            elif event_code[0] == "POWER":
                # hardcoded power off button
                print("Ending current event.")
                firebase.end_current_event()
                last_sent_event = event_code
                last_sent_time = round(time.time() * 1000)
            
            else:
                print(f"Received: {event_code}")
                firebase.end_current_event()
                firebase.set_new_current_event(event_code)
                
                last_sent_event = event_code
                last_sent_time = round(time.time() * 1000)
                