import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime
from collections import deque
import time

st.set_page_config(page_title="Weather Monitor", page_icon="🌤️", layout="wide")

# Cities data
CITIES = {
    "London, UK": (51.5074, -0.1278),
    "New York, USA": (40.7128, -74.0060),
    "Tokyo, Japan": (35.6762, 139.6503),
    "Paris, France": (48.8566, 2.3522),
    "Sydney, Australia": (-33.8688, 151.2093),
    "Mumbai, India": (19.0760, 72.8777)
}

WINDOW_SIZE = 20
TEMP_ALERT = 30

# Initialize data
if 'temps' not in st.session_state:
    st.session_state.temps = deque(maxlen=WINDOW_SIZE)
    st.session_state.times = deque(maxlen=WINDOW_SIZE)
    st.session_state.winds = deque(maxlen=WINDOW_SIZE)
    st.session_state.last_update = None
    st.session_state.city = "London, UK"

def get_weather(lat, lon):
    """Get real weather data"""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            weather = data['current_weather']
            return {
                'temp': weather['temperature'],
                'wind': weather['windspeed'],
                'success': True
            }
        return {'success': False}
    except:
        return {'success': False}

# Sidebar
with st.sidebar:
    st.title("Controls")
    st.session_state.city = st.selectbox("Select City", list(CITIES.keys()))
    
    if st.button("Get Weather Data", use_container_width=True):
        lat, lon = CITIES[st.session_state.city]
        weather = get_weather(lat, lon)
        
        if weather['success']:
            now = datetime.now()
            st.session_state.temps.append(weather['temp'])
            st.session_state.times.append(now)
            st.session_state.winds.append(weather['wind'])
            st.session_state.last_update = now
            st.success(f"Updated: {weather['temp']}°C")
        else:
            st.error("Error fetching data")
    
    if st.button("Clear Data", use_container_width=True):
        st.session_state.temps.clear()
        st.session_state.times.clear()
        st.session_state.winds.clear()
        st.rerun()
    
    if st.session_state.last_update:
        st.info(f"Last update: {st.session_state.last_update.strftime('%H:%M:%S')}")
    st.caption(f"Data points: {len(st.session_state.temps)}/{WINDOW_SIZE}")

# Main content
st.title("🌤️ Real-Time Weather Monitor")
st.caption("Track B: Live Data with Sliding Window Visualization")

# Show alert if temperature is high
if len(st.session_state.temps) > 0:
    current_temp = st.session_state.temps[-1]
    if current_temp > TEMP_ALERT:
        st.error(f"⚠️ HEAT ALERT! Temperature {current_temp}°C exceeds {TEMP_ALERT}°C!")
    else:
        st.success(f"✅ Temperature: {current_temp}°C")

# Metrics
if len(st.session_state.temps) > 0:
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Temperature", f"{st.session_state.temps[-1]:.1f}°C")
    with col2:
        st.metric("Wind Speed", f"{st.session_state.winds[-1]:.1f} km/h")
else:
    st.info("Click 'Get Weather Data' to start")

# Sliding window chart
st.subheader("Temperature Trend (Last 20 Readings)")

if len(st.session_state.temps) >= 2:
    df = pd.DataFrame({
        'Time': list(st.session_state.times),
        'Temperature': list(st.session_state.temps)
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Time'],
        y=df['Temperature'],
        mode='lines+markers',
        name='Temperature',
        line=dict(color='#FF6B35', width=3),
        marker=dict(size=8, color='red' if df['Temperature'].iloc[-1] > TEMP_ALERT else '#FF6B35')
    ))
    
    fig.add_hline(y=TEMP_ALERT, line_dash="dash", line_color="red", 
                  annotation_text=f"Alert ({TEMP_ALERT}°C)")
    
    fig.update_layout(
        height=400,
        yaxis=dict(range=[-10, 45]),  # Fixed range
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Stats
    avg_temp = np.mean(list(st.session_state.temps))
    st.metric("Average Temperature", f"{avg_temp:.1f}°C")
else:
    st.info("Get weather data 2+ times to see the chart")
