# ChemSafe IoT

ChemSafe is a comprehensive Chemical Laboratory Safety Management Platform featuring real-time IoT sensor integration, incident management, chemical inventory tracking, and an AI-powered assistant.

## Features
- **Real-Time IoT Sensor Monitoring:** Monitors Temperature, Humidity, Gas, Light, and Vibration via ESP32 nodes communicating over MQTT (HiveMQ Cloud).
- **Incident & Alert Management:** Automatically triggers alerts when sensor thresholds are breached. Allows staff assignment and resolution tracking.
- **Inventory Management:** Track chemicals, stock levels, and hazard classes.
- **AI Assistant:** Integrated Gemini 2.5 Flash AI to help analyze sensor readings, generate reports, and assist with lab safety protocols.
- **Dashboard & Analytics:** Comprehensive overview of all active nodes, alerts, and personnel.

## Tech Stack
- **Frontend:** React (Vite), React Router, Lucide Icons, Vanilla CSS
- **Backend:** FastAPI (Python), SQLite (or Firebase), Paho-MQTT, Google Generative AI
- **Hardware Integration:** Compatible with ESP32 or simulated via Python scripts

## Quick Start

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd ChemSafe
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt

# Create a .env file based on .env.example
cp .env.example .env
# Edit .env with your MQTT and Gemini API keys

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```

### 4. Running the Hardware Simulator
If you don't have physical ESP32 nodes, you can simulate hardware data:
```bash
cd backend
# Make sure your virtual environment is activated
python test_hivemq.py
```

## Environment Variables
The backend requires a `.env` file to run correctly. Refer to `backend/.env.example` for the required fields, including your `GEMINI_API_KEY` and HiveMQ credentials.
