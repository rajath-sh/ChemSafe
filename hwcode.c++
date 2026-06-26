#include <Keypad.h>
#include <DHT.h>
#include <time.h>
#include <sys/time.h>

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

#define DHT_TYPE DHT11      // change to DHT11 if you have a DHT11
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
bool alarmBlinking = false;
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

void handleKeypad() {
  char key = keypad.getKey();
  if (!key) return;
  Serial.print("Key: ");
  Serial.println(key);

  if (key == '#') {
    if (enteredPIN == CORRECT_PIN) {
      Serial.println(">> CORRECT PIN - access granted");
      wrongAttempts = 0;
      alarmBlinking = false;
      setAlarm(false);
    } else {
      wrongAttempts++;
      Serial.print(">> WRONG PIN - attempt ");
      Serial.print(wrongAttempts);
      Serial.println(" of 3");
      if (wrongAttempts >= 3) {
        Serial.println("* THREE WRONG ATTEMPTS - ALARM ON! *");
        alarmBlinking = true;
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
    Serial.println("NO DATA (check sensor type DHT11/DHT22, DATA=D4, VCC, GND, try VIN)");
  } else {
    Serial.print("OK  Temp="); Serial.print(t0);
    Serial.print("  Hum="); Serial.println(h0);
  }

  struct tm t;
  t.tm_year = 2025 - 1900; t.tm_mon = 0; t.tm_mday = 1;
  t.tm_hour = startHour; t.tm_min = startMinute; t.tm_sec = startSecond;
  t.tm_isdst = 0;
  time_t epoch = mktime(&t);
  struct timeval now = { .tv_sec = epoch, .tv_usec = 0 };
  settimeofday(&now, NULL);

  Serial.printf("Clock set to %02d:%02d:%02d\n", startHour, startMinute, startSecond);
}

unsigned long lastSensorPrint = 0;

void loop() {
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
    setAlarm(false);
  }

  if (alarmBlinking) {
    if (millis() - lastBlink > 300) {
      lastBlink = millis();
      blinkState = !blinkState;
      setAlarm(blinkState);
    }
  } else if (!night) {
    setAlarm(false);
  }

  if (millis() - lastSensorPrint > 2000) {
    lastSensorPrint = millis();

    float temp  = dht.readTemperature();
    float hum   = dht.readHumidity();
    int   light = readLight();
    int   gas   = readGas();

    // Dedicated DHT line so it's always visible
    Serial.print(">> DHT  Temperature: ");
    if (isnan(temp)) Serial.print("NO READING"); else { Serial.print(temp); Serial.print(" C"); }
    Serial.print("   Humidity: ");
    if (isnan(hum)) Serial.println("NO READING"); else { Serial.print(hum); Serial.println(" %"); }

    // Other sensors
    Serial.print("   Light: "); Serial.print(light);
    Serial.print(" | Gas: ");   Serial.println(gas);
  }
}