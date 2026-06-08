import os
import sys
import json
import ssl
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT", 8883))
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")
USE_TLS = os.getenv("MQTT_USE_TLS", "true").lower() == "true"

COMMAND_TOPIC = "lab/LAB-1/command"

# Ask the user what command they want to send
print("Choose a command to send to LAB-1:")
print("1. stop_transmission (Turns OFF all sensor data)")
print("2. resume_transmission (Turns ON all sensor data)")
print("3. disable_vibration (Zeros out the vibration sensor)")
choice = input("Enter 1, 2, or 3: ").strip()

action_map = {
    "1": "stop_transmission",
    "2": "resume_transmission",
    "3": "disable_vibration"
}

action = action_map.get(choice)
if not action:
    print("Invalid choice. Exiting.")
    sys.exit(1)

payload = {"action": action}

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connected! Publishing command to {COMMAND_TOPIC} -> {json.dumps(payload)}")
        client.publish(COMMAND_TOPIC, json.dumps(payload), qos=1)
        print("Command published successfully!")
        client.disconnect()
    else:
        print(f"Connection failed with return code {rc}")

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
client.username_pw_set(USERNAME, PASSWORD)
if USE_TLS:
    client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)

client.on_connect = on_connect

client.connect(BROKER, PORT, keepalive=60)
client.loop_forever()
