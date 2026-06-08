import requests
import time
import random
from datetime import datetime

# URL for the backend simulation endpoint
API_URL = "http://127.0.0.1:8000/api/mqtt/simulate"

# You need an Admin token to hit this endpoint
# For testing with Auth disabled, you might just need a fake Authorization header or none depending on your auth setup.
# If auth is disabled, this should work directly.
HEADERS = {
    "Content-Type": "application/json"
}

def simulate_readings(lab_id: str):
    """Generates random sensor readings. Some are normal, some will trigger alerts."""
    
    # 20% chance to generate a CRITICAL high reading, otherwise normal
    is_anomaly = random.random() < 0.2
    
    payload = {
        "lab_id": lab_id,
        "temperature": random.uniform(80.0, 100.0) if is_anomaly else random.uniform(20.0, 25.0),
        "humidity": random.uniform(80.0, 95.0) if is_anomaly else random.uniform(40.0, 50.0),
        "gas": random.uniform(10.0, 50.0) if is_anomaly else random.uniform(0.0, 1.0),
        "vibration": random.uniform(5.0, 15.0) if is_anomaly else random.uniform(0.1, 0.5),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Sending to {lab_id}: {payload}")
    
    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        if response.status_code == 200:
            print("  -> Success: Processed by Threshold Engine")
        else:
            print(f"  -> Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"  -> Connection Error: {e}")

if __name__ == "__main__":
    print("🧪 Starting ChemSafe Sensor Simulation...")
    print("Press Ctrl+C to stop.\n")
    
    target_labs = ["LAB-1", "LAB-2", "LAB-3"]
    
    try:
        while True:
            # Pick a random lab
            lab = random.choice(target_labs)
            simulate_readings(lab)
            
            # Wait 5 seconds before sending the next reading
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
