📘 Flood & Weather Insights (NGO Dashboard)

A real-time flood-risk and weather-monitoring system built for NGOs and disaster-response teams.

📌 Project Overview

Flood & Weather Insights is a real-time analytics dashboard designed to assist NGOs, rescue teams, and government bodies in making faster and more informed decisions during extreme weather events.

The system combines live meteorological data, probabilistic flood-risk modeling, and interactive dashboards to help teams assess risk zones, predict flood likelihood, and monitor weather patterns instantly.

The project includes:

A FastAPI backend for live API communication

A Streamlit web dashboard for visualization

A deployed web application on Streamlit Cloud

🔗 Live App: https://floodinsightspython-fwpnpoks3phw9zux3crkhj.streamlit.app/

🚀 Key Features
✅ Real-Time Weather Monitoring

Fetches live temperature, rainfall, wind, and humidity data using Open-Meteo API.

✅ Flood-Risk Estimation Model

Applies statistical rules to identify potential flooding based on:

Rainfall intensity

Sudden temperature drops

Continuous rainfall duration

✅ FastAPI Backend

Processes live data requests

Outputs structured JSON for the frontend

✅ Streamlit Dashboard

User inputs: Location, date, forecast range

Displays weather metrics, charts, and flood alerts

✅ Deployed End-to-End System

Backend connected with frontend

Live SaaS-style interface accessible publicly

🛠 Tech Stack
Backend

Python

FastAPI

Uvicorn

Requests Library

Frontend / Dashboard

Streamlit

Pandas

Plotly / Charts

External Services

Open-Meteo API (Weather & Forecast Data)

Streamlit Cloud (Deployment)

GitHub (Source Code Hosting)

 
🔄 System Architecture
User Input (Streamlit Dashboard)
            ↓
Frontend sends request to Backend API
            ↓
Backend fetches live weather data from Open-Meteo
            ↓
Backend processes data & calculates flood probability
            ↓
Frontend displays charts, analytics, and flood alerts

⚙️ Local Setup Instructions

1. Open project folder in a terminal
Navigate to the folder that contains main.py and streamlit_app.py.

2. (Optional) Create & activate a venv

python -m venv venv
# Windows
venv\Scripts\activate
# mac / linux
source venv/bin/activate


3. Install required packages

pip install -r requirements.txt


If you don’t have requirements.txt, install the essentials:

pip install fastapi uvicorn streamlit pandas requests httpx python-multipart


4. Run the FastAPI backend (keep this terminal open)

uvicorn main:app --reload


Backend URL: http://127.0.0.1:8000

Test docs: http://127.0.0.1:8000/docs

5. Run the Streamlit frontend (open a second terminal)

streamlit run streamlit_app.py


or, if your file is named app.py:

streamlit run app.py


Frontend URL: http://localhost:8501

6. Use the app

Open the Streamlit URL, enter a city, click Get Forecast.

Streamlit sends requests to the local FastAPI backend and displays results.

 
🌍 Deployment Details

The dashboard is deployed on Streamlit Cloud, using:

GitHub repository as source

Streamlit automatically installs requirements and runs app.py

Live Deployment:

👉 https://floodinsightspython-fwpnpoks3phw9zux3crkhj.streamlit.app/
