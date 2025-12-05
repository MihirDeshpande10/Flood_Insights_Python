# app.py  — Streamlit dashboard for Flood & Weather Insights
import streamlit as st  # type: ignore
import requests
import pandas as pd
from datetime import datetime
import os  # <--- IMPORTANT

# Default backend URL:
# - On Streamlit Cloud → takes BACKEND_URL from environment
# - On your laptop      → falls back to localhost:8000
DEFAULT_BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


st.set_page_config(page_title="Flood Risk Insights Dashboard", layout="wide")

st.title("🌧️ Flood & Weather Insights (NGO Dashboard)")
st.markdown("Simple dashboard for NGOs & analysts — fetches weather + risk from the FastAPI backend.")

# Sidebar controls
st.sidebar.header("Controls")
backend_url = st.sidebar.text_input("Backend URL", DEFAULT_BACKEND)
city = st.sidebar.text_input("City / Town", "Pune")
lang = st.sidebar.selectbox("Language", ["English", "Hindi", "Marathi"])
fetch_button = st.sidebar.button("Get Forecast")

# Helper: call backend
def get_forecast(backend: str, city_name: str, timeout: int = 20):
    try:
        resp = requests.get(f"{backend}/city_forecast", params={"city": city_name}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Could not fetch forecast: {e}")

# When user asks for data
if fetch_button:
    with st.spinner("Fetching forecast from backend..."):
        try:
            data = get_forecast(backend_url, city)
        except Exception as e:
            st.error(str(e))
            st.stop()

    # Top row: location + KPIs
    st.subheader(data.get("location", city))
    col1, col2, col3 = st.columns(3)
    col1.metric("24h Rain (mm)", data.get("rolling_24", "N/A"))
    col2.metric("72h Rain (mm)", data.get("rolling_72", "N/A"))
    risk = data.get("risk", {})
    risk_display = f"Flood: {risk.get('flood','N/A')}  |  Heat: {risk.get('heat','N/A')}  |  Storm: {risk.get('storm','N/A')}"
    col3.metric("Risk Summary", risk_display)

    # Advisory banner (bilingual)
    advisory = data.get("advisory_en", "")
    if lang == "Hindi":
        advisory = data.get("advisory_hi", advisory)
    elif lang == "Marathi":
        advisory = data.get("advisory_mr", advisory)

    st.warning(advisory)

    # Build DataFrame from hourly arrays
    df = pd.DataFrame({
        "time": data.get("times", []),
        "temp_C": data.get("temperature", []),
        "precip_mm": data.get("precip", []),
        "humidity_%": data.get("humidity", []),
        "wind_m_s": data.get("wind", []),
    })

    if not df.empty:
        # convert time column to datetime (best-effort)
        try:
            df["time"] = pd.to_datetime(df["time"])
        except Exception:
            pass

        # Show interactive line chart (precip & temp)
        st.subheader("Recent Hourly Data")
        st.line_chart(df.set_index("time")[["precip_mm", "temp_C"]])

        # Show raw table
        with st.expander("Show hourly table"):
            st.dataframe(df)

        # CSV download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, file_name=f"{city.replace(' ','_')}_weather.csv")

    # Map: show location point if lat/lon present
    if data.get("lat") and data.get("lon"):
        try:
            loc_df = pd.DataFrame([{"lat": float(data["lat"]), "lon": float(data["lon"])}])
            st.subheader("Location on map")
            st.map(loc_df)
        except Exception:
            pass

    # Farmer Reports (placeholder)
    st.subheader("Community / Farmer Reports")
    st.info(" ")

    st.success("Forecast loaded — you can download CSV or change city/backend and fetch again.")
else:
    st.info("Enter a city and click **Get Forecast** in the sidebar to retrieve data from your backend.")
    st.caption("Make sure your FastAPI backend is running (uvicorn on port 8000) and the Backend URL is correct.")

