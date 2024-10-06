import serial
import sqlite3
import uuid
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Set up FastAPI app
app = FastAPI(redoc_url="/")

# Set up the serial connection to the Arduino
# Adjust 'COM3' and baudrate as per your setup
ser = serial.Serial('COM8', 115200, timeout=0.1)

# Set up SQLite database
conn = sqlite3.connect('events.db')
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        event_code TEXT,
        timestamp TEXT
    )
''')
conn.commit()

# Function to read serial input and save event
def save_event(event_code):
    event_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO events (id, event_code, timestamp)
        VALUES (?, ?, ?)
    ''', (event_id, event_code, timestamp))
    conn.commit()



# FastAPI model for returning event data
class Event(BaseModel):
    id: str
    event_code: str
    timestamp: str
    
# Function to create a new SQLite connection
def get_db_connection():
    conn = sqlite3.connect('events.db')
    return conn

@app.get("/events", response_model=list[Event])
def get_events():
    
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM events')
    rows = cursor.fetchall()
    
    conn.close()
    return [{"id": row[0], "event_code": row[1], "timestamp": row[2]} for row in rows]

NUMBER_TO_FUNCTION:dict = {
    69: "power",
    70: "VOL+",
    71: "FUNC/STOP",
    
}


# Main function to continuously read from serial and save to database
def main():
    while True:
        if ser.in_waiting > 0:
            value = ser.readline()
            event_code = value.decode("utf-8").strip()
            if event_code:  # Ensure event code is not empty
                print(f"Received: {event_code}")
                save_event(event_code)

if __name__ == "__main__":
    import threading
    # Use Uvicorn to run the FastAPI app
    api_thread = threading.Thread(target=lambda: uvicorn.run(app, host='0.0.0.0', port=8000))
    api_thread.daemon = True
    api_thread.start()

    # Run the main serial reading loop
    main()
