import os
import sys
import json
import time
import ssl
import random
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Load env variables from backend/.env
load_dotenv()

BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT", 8883))
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")
USE_TLS = os.getenv("MQTT_USE_TLS", "true").lower() == "true"

TEST_TOPIC = "lab/LAB-1/sensorData"
COMMAND_TOPIC = "lab/LAB-1/command"

# Real-life ESP32 nodes usually publish fast, often every 2 seconds
PUBLISH_INTERVAL = 2  

if not BROKER:
    print("Error: MQTT_BROKER not found in .env file. Please check backend/.env")
    sys.exit(1)

print("=" * 60)
print("ChemSafe Continuous MQTT Simulator (Two-Way)")
print("=" * 60)
print(f"Broker:        {BROKER}")
print(f"Publish Topic: {TEST_TOPIC}")
print(f"Command Topic: {COMMAND_TOPIC}")
print(f"Interval:      Every {PUBLISH_INTERVAL} seconds")
print("-" * 60)

# State Flags
transmit_data = True
disable_vibration = False

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[SUCCESS] Connected to HiveMQ Cloud!")
        print(f"[INFO] Subscribing to command topic: {COMMAND_TOPIC}")
        client.subscribe(COMMAND_TOPIC)
    else:
        print(f"[ERROR] Connection failed with return code {rc}")

def on_message(client, userdata, msg):
    global transmit_data, disable_vibration
    print(f"\n[COMMAND RECEIVED] Topic: {msg.topic}")
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Command Payload: {json.dumps(payload)}")
        
        # Check for the action format from test_send_command.py
        action = payload.get("action")
        if action == "stop_transmission":
            print(">> ACTION: Turning OFF all sensor transmissions!")
            transmit_data = False
        elif action == "resume_transmission":
            print(">> ACTION: Resuming sensor transmissions!")
            transmit_data = True
            
        # Check for the target/command format from the Web Dashboard (NodesManagement.jsx)
        target = payload.get("target")
        command = payload.get("command")
        
        if target and command:
            if target == "vibration" and command == "offline":
                print(">> ACTION (from Web): Disabling vibration sensor!")
                disable_vibration = True
            elif target == "vibration" and command == "online":
                print(">> ACTION (from Web): Enabling vibration sensor!")
                disable_vibration = False
            elif command == "offline":
                print(f">> ACTION (from Web): Turning OFF {target} sensor!")
                # If we get offline commands for sensors, let's just turn everything off for simulation
                transmit_data = False
            elif command == "online":
                print(f">> ACTION (from Web): Turning ON {target} sensor!")
                transmit_data = True
                
    except Exception as e:
        print(f"[WARNING] Could not parse command payload: {e}")

# Initialize MQTT Client
client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="chemsafe_continuous_simulator_node",
    protocol=mqtt.MQTTv5
)

client.username_pw_set(USERNAME, PASSWORD)

if USE_TLS:
    client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)

client.on_connect = on_connect
client.on_message = on_message

print("Connecting to MQTT Broker...")
try:
    client.connect(BROKER, PORT, keepalive=60)
except Exception as e:
    print(f"[ERROR] Failed to connect: {e}")
    sys.exit(1)

client.loop_start()
time.sleep(2)

print("Starting continuous simulation loop (Press Ctrl+C to stop)...")

start_time = time.time()
last_spike_cycle = 0

try:
    while True:
        elapsed = time.time() - start_time
        
        # Only publish if we haven't received a command to stop
        if transmit_data:
            temp = 24.0 + random.uniform(-1.0, 1.0)
            hum = 50.0 + random.uniform(-5.0, 5.0)
            gas = 700.0 + random.uniform(-50.0, 50.0) # Raw ADC (approx 400 PPM)
            light = 2000.0 + random.uniform(-100.0, 100.0) # Raw ADC
            vib = 0.01 + random.uniform(0.0, 0.02)
            
            # Force a critical alert periodically (every 30 seconds)
            current_cycle = int(elapsed // 30)
            if current_cycle > 0 and current_cycle != last_spike_cycle:
                print(f"\n[ALERT] {current_cycle * 30} seconds reached! Forcing a critical gas and temperature spike!")
                temp = 55.0  # Critical
                gas = 1500.0   # Critical (High ADC)
                last_spike_cycle = current_cycle
                
            payload = {
                "temperature": round(temp, 2),
                "humidity": round(hum, 2),
                "gas": round(gas, 2),
                "light": round(light, 2)
            }
            
            # If vibration isn't disabled by user command, include it
            if not disable_vibration:
                payload["vibration"] = round(vib, 2)
            else:
                payload["vibration"] = 0.0

            print(f"[{time.strftime('%H:%M:%S')}] Publishing (elapsed: {int(elapsed)}s)...")
            client.publish(TEST_TOPIC, json.dumps(payload), qos=1)
        else:
            # We are muted by a command
            pass
            
        time.sleep(PUBLISH_INTERVAL)

except KeyboardInterrupt:
    print("\nStopping simulator...")

client.loop_stop()
client.disconnect()
print("Disconnected from MQTT Broker.")
