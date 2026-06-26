#!/bin/bash

echo "=================================================="
echo "   ChemSafe One-Click Google Cloud Deployment     "
echo "=================================================="

# Check for stop command
if [ "$1" == "stop" ]; then
    echo "Stopping all ChemSafe processes..."
    pkill -f "uvicorn main:app"
    pkill -f "serve -s dist"
    pkill -f "test_hivemq.py"
    echo "All processes stopped."
    exit 0
fi

# Check for simulate flag
SIMULATE=0
if [ "$1" == "--simulate" ] || [ "$2" == "--simulate" ]; then
    SIMULATE=1
fi

# 1. Kill any previously running processes so we can run this script safely multiple times
echo "[1/6] Stopping any old instances..."
pkill -f "uvicorn main:app"
pkill -f "serve -s dist"
pkill -f "test_hivemq.py"
sleep 2

# 2. Automatically fetch the VM's External IP Address (Google Cloud specific command)
echo "[2/6] Fetching Google Cloud External IP..."
EXTERNAL_IP=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)

if [ -z "$EXTERNAL_IP" ]; then
    echo "Warning: Could not fetch External IP automatically. Falling back to localhost."
    EXTERNAL_IP="127.0.0.1"
fi
echo "-> Detected IP: $EXTERNAL_IP"

# 3. Setup and start the Backend
echo "[3/6] Setting up Backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

# Start backend in the background
echo "-> Starting Backend on port 8000..."
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# 4. Start the Simulator Script (ONLY IF FLAG IS PASSED)
if [ "$SIMULATE" -eq 1 ]; then
    echo "[4/6] Starting MQTT Simulator..."
    nohup python test_hivemq.py > simulator.log 2>&1 &
else
    echo "[4/6] Skipping MQTT Simulator (run with --simulate to enable)..."
fi
cd ..

# 5. Setup and start the Frontend
echo "[5/6] Setting up Frontend..."
cd frontend

# Create a production .env file so the frontend knows where the backend is
echo "VITE_API_URL=http://$EXTERNAL_IP:8000" > .env.production

# Install dependencies and build
npm install > /dev/null 2>&1
echo "-> Building React app (this takes a minute)..."
npm run build > /dev/null 2>&1

# Install 'serve' globally if not already installed, then serve the build folder
if ! command -v serve &> /dev/null
then
    sudo npm install -g serve > /dev/null 2>&1
fi

echo "-> Starting Frontend on port 5173..."
nohup serve -s dist -l 5173 > frontend.log 2>&1 &
cd ..

echo "=================================================="
echo "Deployment Complete! 🚀"
echo ""
echo "Your ChemSafe Dashboard is live at:"
echo "http://$EXTERNAL_IP:5173"
echo ""
echo "To stop everything, run: bash deploy.sh stop"
echo "=================================================="
