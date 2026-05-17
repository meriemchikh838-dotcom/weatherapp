import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime
from collections import deque
import time

st.set_page_config(page_title="Weather Monitor - Track B", page_icon="🌤️", layout="wide")

# ============================================
# CONFIGURATION
# ============================================

CITIES = {
    "London, UK": (51.5074, -0.1278),
    "New York, USA": (40.7128, -74.0060),
    "Tokyo, Japan": (35.6762, 139.6503),
    "Paris, France": (48.8566, 2.3522),
    "Sydney, Australia": (-33.8688, 151.2093),
    "Mumbai, India": (19.0760, 72.8777),
    "Dubai, UAE": (25.2048, 55.2708),
    "Singapore": (1.3521, 103.8198),
    "Berlin, Germany": (52.5200, 13.4050),
    "Rome, Italy": (41.9028, 12.4964)
}

WINDOW_SIZE = 20
TEMP_ALERT_HIGH = 30
TEMP_ALERT_LOW = 0
WIND_ALERT = 50

# ============================================
# INITIALIZE SESSION STATE
# ============================================

if 'temps' not in st.session_state:
    st.session_state.temps = deque(maxlen=WINDOW_SIZE)
    st.session_state.humidities = deque(maxlen=WINDOW_SIZE)
    st.session_state.winds = deque(maxlen=WINDOW_SIZE)
    st.session_state.times = deque(maxlen=WINDOW_SIZE)
    st.session_state.last_update = None
    st.session_state.city = "London, UK"
    st.session_state.auto_refresh = False
    st.session_state.alert_history = []

# ============================================
# API FUNCTIONS
# ============================================

def get_weather(lat, lon):
    """Get real weather data from Open-Meteo API"""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            weather = data['current_weather']
            
            # Get humidity
            hourly_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=relativehumidity_2m"
            hourly_response = requests.get(hourly_url, timeout=10)
            humidity = 65
            if hourly_response.status_code == 200:
                hourly_data = hourly_response.json()
                if 'hourly' in hourly_data and 'relativehumidity_2m' in hourly_data['hourly']:
                    humidity = hourly_data['hourly']['relativehumidity_2m'][0]
            
            return {
                'temp': weather['temperature'],
                'wind': weather['windspeed'],
                'humidity': humidity,
                'success': True
            }
        return {'success': False}
    except Exception as e:
        return {'success': False}

def update_data():
    """Fetch data and update sliding window"""
    lat, lon = CITIES[st.session_state.city]
    weather = get_weather(lat, lon)
    
    if weather['success']:
        now = datetime.now()
        st.session_state.temps.append(weather['temp'])
        st.session_state.humidities.append(weather['humidity'])
        st.session_state.winds.append(weather['wind'])
        st.session_state.times.append(now)
        st.session_state.last_update = now
        
        # Check for alerts
        temp = weather['temp']
        if temp > TEMP_ALERT_HIGH:
            st.session_state.alert_history.insert(0, f"HEAT: {temp:.1f}C at {now.strftime('%H:%M:%S')}")
        elif temp < TEMP_ALERT_LOW:
            st.session_state.alert_history.insert(0, f"FREEZE: {temp:.1f}C at {now.strftime('%H:%M:%S')}")
        
        if weather['wind'] > WIND_ALERT:
            st.session_state.alert_history.insert(0, f"WIND: {weather['wind']:.1f} km/h at {now.strftime('%H:%M:%S')}")
        
        st.session_state.alert_history = st.session_state.alert_history[:10]
        return True
    return False

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.title("Controls")
    st.markdown("---")
    
    st.session_state.city = st.selectbox("Select City", list(CITIES.keys()))
    
    st.markdown("---")
    
    if st.button("Manual Refresh", use_container_width=True):
        with st.spinner("Fetching..."):
            if update_data():
                st.success("Updated!")
                st.rerun()
            else:
                st.error("Failed to fetch")
    
    auto_refresh = st.toggle("Auto-Refresh (every 10 sec)", value=st.session_state.auto_refresh)
    if auto_refresh != st.session_state.auto_refresh:
        st.session_state.auto_refresh = auto_refresh
        st.rerun()
    
    if st.button("Reset All Data", use_container_width=True):
        st.session_state.temps.clear()
        st.session_state.humidities.clear()
        st.session_state.winds.clear()
        st.session_state.times.clear()
        st.session_state.alert_history.clear()
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.last_update:
        st.success(f"Last update: {st.session_state.last_update.strftime('%H:%M:%S')}")
    else:
        st.info("Click refresh to start")
    
    st.caption(f"Data points: {len(st.session_state.temps)}/{WINDOW_SIZE}")
    st.caption(f"Total updates: {len(st.session_state.temps)}")

# ============================================
# MAIN CONTENT
# ============================================

st.title("Real-Time Weather Intelligence Dashboard")
st.caption("Track B: Live Streaming | Sliding Window | Multi-Chart Visualization | Threshold Alerts")

# ============================================
# ALERT BANNER
# ============================================

if len(st.session_state.temps) > 0:
    current_temp = st.session_state.temps[-1]
    current_wind = st.session_state.winds[-1]
    
    col1, col2 = st.columns(2)
    with col1:
        if current_temp > TEMP_ALERT_HIGH:
            st.error(f"HEAT ALERT! {current_temp:.1f}C exceeds {TEMP_ALERT_HIGH}C!")
        elif current_temp < TEMP_ALERT_LOW:
            st.warning(f"FREEZE WARNING! {current_temp:.1f}C below freezing!")
        else:
            st.success(f"Temperature normal: {current_temp:.1f}C")
    
    with col2:
        if current_wind > WIND_ALERT:
            st.warning(f"HIGH WIND ALERT! {current_wind:.1f} km/h exceeds {WIND_ALERT} km/h!")
        else:
            st.info(f"Wind speed: {current_wind:.1f} km/h")

# ============================================
# CURRENT METRICS
# ============================================

if len(st.session_state.temps) > 0:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        temp_change = None
        if len(st.session_state.temps) > 1:
            temp_change = st.session_state.temps[-1] - st.session_state.temps[-2]
        st.metric("Temperature", f"{st.session_state.temps[-1]:.1f}C", 
                  delta=f"{temp_change:+.1f}C" if temp_change else None)
    
    with col2:
        humidity_change = None
        if len(st.session_state.humidities) > 1:
            humidity_change = st.session_state.humidities[-1] - st.session_state.humidities[-2]
        st.metric("Humidity", f"{st.session_state.humidities[-1]:.0f}%",
                  delta=f"{humidity_change:+.0f}%" if humidity_change else None)
    
    with col3:
        wind_change = None
        if len(st.session_state.winds) > 1:
            wind_change = st.session_state.winds[-1] - st.session_state.winds[-2]
        st.metric("Wind Speed", f"{st.session_state.winds[-1]:.1f} km/h",
                  delta=f"{wind_change:+.1f}" if wind_change else None)
    
    with col4:
        st.metric("Window Size", f"{len(st.session_state.temps)}/{WINDOW_SIZE}")
else:
    st.info("Click 'Manual Refresh' or enable 'Auto-Refresh' to start")

st.markdown("---")

# ============================================
# MULTIPLE CHARTS
# ============================================

st.subheader("Sliding Window Visualizations (Last 20 Readings)")

if len(st.session_state.temps) >= 2:
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Temperature Trend (C)", "Humidity Trend (%)", "Wind Speed Trend (km/h)"),
        vertical_spacing=0.12,
        shared_xaxes=True
    )
    
    # Chart 1: Temperature
    temp_colors = ['red' if t > TEMP_ALERT_HIGH or t < TEMP_ALERT_LOW else '#FF6B35' 
                   for t in list(st.session_state.temps)]
    
    fig.add_trace(
        go.Scatter(
            x=list(st.session_state.times),
            y=list(st.session_state.temps),
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#FF6B35', width=3),
            marker=dict(size=8, color=temp_colors),
            fill='tozeroy',
            fillcolor='rgba(255,107,53,0.15)'
        ),
        row=1, col=1
    )
    
    fig.add_hline(y=TEMP_ALERT_HIGH, line_dash="dash", line_color="red",
                  annotation_text=f"Heat Alert ({TEMP_ALERT_HIGH}C)", 
                  row=1, col=1)
    fig.add_hline(y=TEMP_ALERT_LOW, line_dash="dash", line_color="blue",
                  annotation_text=f"Freeze ({TEMP_ALERT_LOW}C)", 
                  row=1, col=1)
    
    # Chart 2: Humidity
    fig.add_trace(
        go.Scatter(
            x=list(st.session_state.times),
            y=list(st.session_state.humidities),
            mode='lines+markers',
            name='Humidity',
            line=dict(color='#00BFFF', width=3),
            marker=dict(size=8, color='#00BFFF'),
            fill='tozeroy',
            fillcolor='rgba(0,191,255,0.15)'
        ),
        row=2, col=1
    )
    
    # Chart 3: Wind Speed
    wind_colors = ['red' if w > WIND_ALERT else '#32CD32' for w in list(st.session_state.winds)]
    
    fig.add_trace(
        go.Bar(
            x=list(st.session_state.times),
            y=list(st.session_state.winds),
            name='Wind Speed',
            marker_color=wind_colors,
            opacity=0.7
        ),
        row=3, col=1
    )
    
    fig.add_hline(y=WIND_ALERT, line_dash="dash", line_color="red",
                  annotation_text=f"Wind Alert ({WIND_ALERT} km/h)", 
                  row=3, col=1)
    
    fig.update_layout(
        height=800,
        showlegend=False,
        hovermode='x unified',
        template='plotly_white'
    )
    
    fig.update_yaxes(title_text="Temperature (C)", range=[-10, 45], row=1, col=1)
    fig.update_yaxes(title_text="Humidity (%)", range=[0, 100], row=2, col=1)
    fig.update_yaxes(title_text="Wind Speed (km/h)", range=[0, 80], row=3, col=1)
    fig.update_xaxes(title_text="Time", row=3, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Statistics
    st.subheader("Window Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    temp_array = list(st.session_state.temps)
    humidity_array = list(st.session_state.humidities)
    wind_array = list(st.session_state.winds)
    
    with col1:
        st.metric("Avg Temperature", f"{np.mean(temp_array):.1f}C")
    with col2:
        st.metric("Avg Humidity", f"{np.mean(humidity_array):.0f}%")
    with col3:
        st.metric("Avg Wind Speed", f"{np.mean(wind_array):.1f} km/h")
    with col4:
        if len(temp_array) > 1:
            trend = temp_array[-1] - temp_array[0]
            st.metric("Temperature Trend", f"{trend:+.1f}C")
else:
    st.info("Collecting data... Perform a manual refresh to see the charts (need 2+ data points)")

# ============================================
# ALERT HISTORY
# ============================================

if st.session_state.alert_history:
    st.subheader("Alert History")
    for alert in st.session_state.alert_history[:5]:
        if "HEAT" in alert:
            st.error(alert)
        elif "FREEZE" in alert:
            st.warning(alert)
        elif "WIND" in alert:
            st.info(alert)

# ============================================
# DATA TABLE
# ============================================

with st.expander("View Raw Data"):
    if len(st.session_state.temps) > 0:
        data_df = pd.DataFrame({
            'Timestamp': list(st.session_state.times),
            'Temperature (C)': list(st.session_state.temps),
            'Humidity (%)': list(st.session_state.humidities),
            'Wind Speed (km/h)': list(st.session_state.winds)
        })
        st.dataframe(data_df, use_container_width=True)
    else:
        st.info("No data available")

# ============================================
# AUTO-REFRESH LOGIC
# ============================================

if st.session_state.auto_refresh and len(st.session_state.temps) < 50:
    time.sleep(10)
    update_data()
    st.rerun()
