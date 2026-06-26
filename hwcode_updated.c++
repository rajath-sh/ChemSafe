#include <Keypad.h>
#include <DHT.h>
#include <time.h>
#include <sys/time.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

// --- WiFi & MQTT Configuration ---
const char* ssid = "YOUR_WIFI_SSID";          // <-- CHANGE THIS
const char* password = "YOUR_WIFI_PASSWORD";  // <-- CHANGE THIS

const char* mqtt_server = "ae06d63a615b43ea9f6de716dba74b1d.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "RVS_IOT_ChemSafe";
const char* mqtt_password = "123_263_Rvs";

const char* command_topic = "lab/LAB-5d8c623ef0404050/command";
const char* publish_topic = "lab/LAB-5d8c623ef0404050/sensorData";

WiFiClientSecure espClient;
PubSubClient client(espClient);

// --- Set the current time here at upload (24-hour format) ---
int startHour   = 23;
int startMinute = 0;
int startSecond = 0;

// --- Night-time window (24-hour format) ---
const int NIGHT_START_HOUR = 22;
const int NIGHT_END_HOUR   = 6;

// --- Pin Definitions ---
#define LED_PIN     18
#define BUZZER_PIN  21
#define DHT_PIN     4
#define LDR_AOUT    36
#define LDR_DOUT    23
#define MQ135_AOUT  35
#define MQ135_DOUT  34

#define DHT_TYPE DHT11
DHT dht(DHT_PIN, DHT_TYPE);

// --- Keypad setup (4x4) ---
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'D','C','B','A'},
  {'#','9','6','3'},
  {'0','8','5','2'},
  {'*','7','4','1'}
};
byte rowPins[ROWS] = {13, 12, 14, 27};
byte colPins[COLS] = {26, 25, 32, 15};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// --- PIN config ---
const String CORRECT_PIN = "4567";
String enteredPIN = "";

// --- State ---
int  wrongAttempts = 0;
bool alarmBlinking = false;       // Driven by keypad
bool remoteAlarmBlinking = false; // Driven by website toggle
bool promptedTonight = false;

unsigned long lastBlink = 0;
bool blinkState = false;

// --- Sensor Read Helpers ---
int   readLight()    { return analogRead(LDR_AOUT); }
bool  isDark()       { return digitalRead(LDR_DOUT) == HIGH; }
int   readGas()      { return analogRead(MQ135_AOUT); }
bool  gasAlert()     { return digitalRead(MQ135_DOUT) == HIGH; }

void setAlarm(bool on) {
  digitalWrite(LED_PIN,    on ? HIGH : LOW);
  digitalWrite(BUZZER_PIN, on ? HIGH : LOW);
}

bool isNightTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) return false;
  int hour = timeinfo.tm_hour;
  if (NIGHT_START_HOUR < NIGHT_END_HOUR) {
    return (hour >= NIGHT_START_HOUR && hour < NIGHT_END_HOUR);
  } else {
    return (hour >= NIGHT_START_HOUR || hour < NIGHT_END_HOUR);
  }
}

// --- MQTT Callback ---
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(">> MQTT Command Received: " + message);

  if (String(topic) == command_topic) {
    if (message.indexOf("\"command\": \"alarm\"") != -1 || message.indexOf("\"command\":\"alarm\"") != -1) {
      if (message.indexOf("\"state\": \"on\"") != -1 || message.indexOf("\"state\":\"on\"") != -1) {
        Serial.println(">> Website commanded Alarm ON");
        remoteAlarmBlinking = true;
      } else if (message.indexOf("\"state\": \"off\"") != -1 || message.indexOf("\"state\":\"off\"") != -1) {
        Serial.println(">> Website commanded Alarm OFF");
        // Keypad Superiority: Ignore remote 'off' if keypad triggered the alarm!
        if (alarmBlinking) {
          Serial.println(">> Ignored: Keypad alarm is currently active!");
        } else {
          remoteAlarmBlinking = false;
          setAlarm(false);
        }
      }
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32Client-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("connected");
      client.subscribe(command_topic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void handleKeypad() {
  char key = keypad.getKey();
  if (!key) return;
  Serial.print("Key: ");
  Serial.println(key);

  if (key == '#') {
    if (enteredPIN == CORRECT_PIN) {
      Serial.println(">> CORRECT PIN - access granted");
      wrongAttempts = 0;
      
      // KEYPAD SUPERIORITY: Correct PIN shuts off BOTH the keypad alarm and the remote alarm instantly.
      alarmBlinking = false;
      remoteAlarmBlinking = false;
      setAlarm(false);
      
    } else {
      wrongAttempts++;
      Serial.print(">> WRONG PIN - attempt ");
      Serial.print(wrongAttempts);
      Serial.println(" of 3");
      if (wrongAttempts >= 3) {
        Serial.println("* THREE WRONG ATTEMPTS - ALARM ON! *");
        alarmBlinking = true;
        
        // MQTT INTRUSION ALERT
        if (client.connected()) {
          String alertPayload = "{\"keypad_alert\": true, \"message\": \"Unauthorized Keypad Access: 3 wrong passwords entered!\"}";
          client.publish(publish_topic, alertPayload.c_str());
          Serial.println(">> Intrusion Alert Sent to Website!");
        }
      }
    }
    enteredPIN = "";
  }
  else if (key == '*') {
    enteredPIN = "";
    Serial.println(">> cleared");
  }
  else {
    enteredPIN += key;
    Serial.print("Entered so far: ");
    Serial.println(enteredPIN);
  }
}

void setup() {
  Serial.begin(115200);
  delay(200);

  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LDR_DOUT, INPUT);
  pinMode(MQ135_DOUT, INPUT);
  setAlarm(false);

  dht.begin();
  keypad.setDebounceTime(10);

  // Quick DHT startup check
  delay(2000);
  float t0 = dht.readTemperature();
  float h0 = dht.readHumidity();
  Serial.print("DHT startup check -> ");
  if (isnan(t0) || isnan(h0)) {
    Serial.println("NO DATA");
  } else {
    Serial.print("OK  Temp="); Serial.print(t0);
    Serial.print("  Hum="); Serial.println(h0);
  }

  // Set Clock
  struct tm t;
  t.tm_year = 2025 - 1900; t.tm_mon = 0; t.tm_mday = 1;
  t.tm_hour = startHour; t.tm_min = startMinute; t.tm_sec = startSecond;
  t.tm_isdst = 0;
  time_t epoch = mktime(&t);
  struct timeval now = { .tv_sec = epoch, .tv_usec = 0 };
  settimeofday(&now, NULL);

  // WiFi & MQTT Setup
  Serial.println();
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
  
  espClient.setInsecure(); // Trust HiveMQ certificate
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
}

unsigned long lastSensorPrint = 0;

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  bool night = isNightTime();

  if (night) {
    if (!promptedTonight) {
      promptedTonight = true;
      Serial.println("\n>> NIGHT TIME - ENTER PASSWORD, then press #");
    }
    handleKeypad();
  } else {
    promptedTonight = false;
    wrongAttempts = 0;
    alarmBlinking = false;
    // We do NOT reset remoteAlarmBlinking here, so the website can still turn it on during the day if needed!
  }

  // ALARM LOGIC (Handles both independently)
  bool isBlinkingNow = alarmBlinking || remoteAlarmBlinking;

  if (isBlinkingNow) {
    if (millis() - lastBlink > 300) {
      lastBlink = millis();
      blinkState = !blinkState;
      setAlarm(blinkState);
    }
  } else if (!night) {
    setAlarm(false);
  }

  // PERIODIC SENSOR PUBLISH
  if (millis() - lastSensorPrint > 2000) {
    lastSensorPrint = millis();

    float temp  = dht.readTemperature();
    float hum   = dht.readHumidity();
    int   light = readLight();
    int   gas   = readGas();

    // Print to Serial
    Serial.print(">> DHT  Temperature: ");
    if (isnan(temp)) Serial.print("NO READING"); else { Serial.print(temp); Serial.print(" C"); }
    Serial.print("   Humidity: ");
    if (isnan(hum)) Serial.println("NO READING"); else { Serial.print(hum); Serial.println(" %"); }
    Serial.print("   Light: "); Serial.print(light);
    Serial.print(" | Gas: ");   Serial.println(gas);

    // Send to Website
    if (client.connected()) {
      String tempStr = isnan(temp) ? "null" : String(temp);
      String humStr  = isnan(hum)  ? "null" : String(hum);
      String payload = "{\"temperature\": " + tempStr + 
                       ", \"humidity\": " + humStr + 
                       ", \"gas\": " + String(gas) + 
                       ", \"light\": " + String(light) + "}";
      client.publish(publish_topic, payload.c_str());
    }
  }
}
