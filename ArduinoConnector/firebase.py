import random
import time
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import pytz
# Constants for mapping remote buttons to functions
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


# Initialize Firebase
cred = credentials.Certificate('firebase_credentials.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def get_current_datetime() -> datetime:
    """Get the current date and time in the Vancouver timezone."""
    return datetime.now(pytz.timezone("America/Vancouver"))

def get_negative_hours(hours) -> timedelta:
    """Return a timedelta representing a negative hour offset."""
    return timedelta(hours=-hours)

def send_completed_event(event_type: tuple, event_start: datetime, event_end: datetime): # type: ignore
    if event_start == None:
        event_start = get_current_datetime()
    
    if event_end == None:
        event_end = get_current_datetime()
    """Send a completed event to Firebase with detailed information."""
    # Calculate event details
    duration_in_seconds = int((event_end - event_start).total_seconds())
    
    # Document reference
    doc_ref = db.collection("events").document(str(event_start))
    
    # Save event details to Firestore
    doc_ref.set({
        "event_type": event_type,
    
        "event_start": event_start,
        "event_end": event_end,
        "duration": duration_in_seconds,
    })

def end_current_event():
    """End the current event and save it to Firebase."""
    
    # get current event and store it
    doc_ref = db.collection("metadata").document("current_event")
    current_event_data = doc_ref.get().to_dict()

    if current_event_data and current_event_data.get("current_event") is not None:
        
        array = current_event_data["current_event"]
        
        if array:
            send_completed_event(
                array,
                current_event_data["event_start"],
                get_current_datetime()
            )
    
    # Clear current event metadata but keep information
    doc_ref.set({
        "current_event": None,
       
        "event_start": current_event_data.get("event_start", None),
    })

def set_new_current_event(current_event: tuple, event_start: datetime = None):
    """Set a new current event in Firebase."""
    if event_start is None:
        event_start = get_current_datetime()
        
    if current_event[3] == "ACTIVITY":
    
        event_type = current_event
        if event_type:
            doc_ref = db.collection("metadata").document("current_event")
            doc_ref.set({
                "current_event": current_event,
                "event_start": event_start,
            })
            
            # send_completed_event(current_event, event_start, None)
            
            
    elif current_event[3] == "MOOD":
        doc_ref = db.collection("metadata").document("mood")
        doc_ref.set({
                "mood": current_event,
            })
        # send_completed_event(current_event, event_start, None)

def send_test_firebase_data():
    """Send test event data to Firebase."""
    for i in range(0, 7 * 24, 24):
        d = i
        send_completed_event(("VOL-", "EAT", "CHOWING DOWN", "ACTIVITY"),
                             get_current_datetime() - timedelta(hours=18 + d),
                             get_current_datetime() - timedelta(hours=16 + d))
        send_completed_event(("VOL+", "STUDY", "STUDYING", "ACTIVITY"),
                             get_current_datetime() - timedelta(hours=6 + d),
                             get_current_datetime() - timedelta(hours=4 + d))
        send_completed_event(("FF_forward", "EXERCISE", "EXERCISING", "ACTIVITY"),
                             get_current_datetime() - timedelta(hours=3 + d),
                             get_current_datetime() - timedelta(hours=d))

# Uncomment to test sending data
send_test_firebase_data()
