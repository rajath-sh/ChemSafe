import requests
import time
import random
from datetime import datetime

import argparse

def get_args():
    parser = argparse.ArgumentParser(description="Simulate ChemSafe sensor readings")
    parser.add_argument("--url", type=str, default="http://34.14.202.89:8000", help="Base URL of the ChemSafe backend")
    return parser.parse_args()

args = get_args()
API_BASE_URL = args.url
SIMULATE_URL = f"{API_BASE_URL}/api/mqtt/simulate"
LABS_URL = f"{API_BASE_URL}/api/sensors/labs"

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
        response = requests.post(SIMULATE_URL, json=payload, headers=HEADERS)
        if response.status_code == 200:
            print("  -> Success: Processed by Threshold Engine")
        else:
            print(f"  -> Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"  -> Connection Error: {e}")

if __name__ == "__main__":
    print(f"🧪 Starting ChemSafe Sensor Simulation against {API_BASE_URL}...")
    print("Press Ctrl+C to stop.\n")
    
    # Fetch active labs from the database
    target_labs = []
    try:
        print("Fetching registered labs...")
        response = requests.get(LABS_URL)
        if response.status_code == 200:
            labs = response.json()
            target_labs = [lab['lab_id'] for lab in labs]
            print(f"Found {len(target_labs)} labs: {', '.join(target_labs)}")
            if len(target_labs) > 1:
                print("\nMultiple labs detected.")
                for idx, l in enumerate(target_labs):
                    print(f"[{idx + 1}] {l}")
                choice = input("Enter the number of the lab to simulate (or press Enter for all): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(target_labs):
                    target_labs = [target_labs[int(choice) - 1]]
                    print(f"Selected: {target_labs[0]}")
                else:
                    print("Simulating on all labs.")
        else:
            print(f"Failed to fetch labs: {response.status_code}")
    except Exception as e:
        print(f"Could not connect to {LABS_URL}: {e}")
        
    if not target_labs:
        print("No labs found in the database. Defaulting to MOCK-LAB-01.")
        target_labs = ["MOCK-LAB-01"]
    
    try:
        while True:
            # Pick a random lab from the dynamically fetched list
            lab = random.choice(target_labs)
            simulate_readings(lab)
            
            # Wait 5 seconds before sending the next reading
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
