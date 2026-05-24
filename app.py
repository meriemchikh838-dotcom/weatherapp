"""
Weather Monitoring Dashboard - Track B
=======================================
A real-time weather monitoring dashboard with sliding window data visualization,
threshold alerts, and auto-refresh capabilities.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime
from collections import deque
import time

# ============================================
# STEP 1: PAGE CONFIGURATION
# ============================================
# Set the Streamlit page title, icon, and layout mode
st.set_page_config(page_title="Weather Monitor - Track B", page_icon="🌤️", layout="wide")

# ============================================
# STEP 2: CONFIGURATION CONSTANTS
# ============================================
# Dictionary of cities with their geographical coordinates (latitude, longitude)
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

# Sliding window size - stores only the last N readings
WINDOW_SIZE = 20

# Alert thresholds for weather parameters
TEMP_ALERT_HIGH = 30      # Temperature above 30°C triggers heat alert
TEMP_ALERT_LOW = 0        # Temperature below 0°C triggers freeze warning
WIND_ALERT = 50           # Wind speed above 50 km/h triggers wind alert

# ============================================
# STEP 3: SESSION STATE INITIALIZATION
# ============================================
# Streamlit session state persists data across reruns
# Using deques with maxlen creates automatic sliding windows

if 'temps' not in st.session_state:
    # Deque for temperature readings (automatically drops oldest when full)
    st.session_state.temps = deque(maxlen=WINDOW_SIZE)
    # Deque for humidity readings
    st.session_state.humidities = deque(maxlen=WINDOW_SIZE)
    # Deque for wind speed readings
    st.session_state.winds = deque(maxlen=WINDOW_SIZE)
    # Deque for timestamps of each reading
    st.session_state.times = deque(maxlen=WINDOW_SIZE)
    # Timestamp of the last successful data fetch
    st.session_state.last_update = None
    # Currently selected city
    st.session_state.city = "London, UK"
    # Auto-refresh toggle state
    st.session_state.auto_refresh = False
    # List to store alert messages (max 10 most recent)
    st.session_state.alert_history = []

# ============================================
# STEP 4: API FUNCTIONS
# ============================================

def get_weather(lat, lon):
    """
    Fetch real-time weather data from Open-Meteo API
    
    Parameters:
    -----------
    lat : float
        Latitude of the location
    lon : float
        Longitude of the location
    
    Returns:
    --------
    dict : Weather data containing temperature, wind speed, humidity,
           and success status
    """
    try:
        # Fetch current weather data (temperature and wind speed)
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            weather = data['current_weather']
            
            # Fetch humidity data separately (hourly forecast)
            hourly_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=relative_humidity_2m"
            hourly_response = requests.get(hourly_url, timeout=10)
            humidity = 65  # Default fallback value
            
            if hourly_response.status_code == 200:
                hourly_data = hourly_response.json()
                if 'hourly' in hourly_data and 'relativehumidity_2m' in hourly_data['hourly']:
                    humidity = hourly_data['hourly']['relative_humidity_2m'][0]
            
            return {
                'temp': weather['temperature'],
                'wind': weather['windspeed'],
                'humidity': humidity,
                'success': True
            }
        return {'success': False}
    except Exception as e:
        # Return failure status on any exception (network error, timeout, etc.)
        return {'success': False}

def update_data():
    """
    Fetch current weather data and update the sliding window deques
    Also checks for threshold violations and adds alerts to history
    
    Returns:
    --------
    bool : True if data was successfully fetched and updated, False otherwise
    """
    # Get coordinates for selected city
    lat, lon = CITIES[st.session_state.city]
    weather = get_weather(lat, lon)
    
    if weather['success']:
        now = datetime.now()
        
        # Append new data to sliding windows
        st.session_state.temps.append(weather['temp'])
        st.session_state.humidities.append(weather['humidity'])
        st.session_state.winds.append(weather['wind'])
        st.session_state.times.append(now)
        st.session_state.last_update = now
        
        # Check for temperature alerts
        temp = weather['temp']
        if temp > TEMP_ALERT_HIGH:
            st.session_state.alert_history.insert(0, f"HEAT: {temp:.1f}C at {now.strftime('%H:%M:%S')}")
        elif temp < TEMP_ALERT_LOW:
            st.session_state.alert_history.insert(0, f"FREEZE: {temp:.1f}C at {now.strftime('%H:%M:%S')}")
        
        # Check for wind alerts
        if weather['wind'] > WIND_ALERT:
            st.session_state.alert_history.insert(0, f"WIND: {weather['wind']:.1f} km/h at {now.strftime('%H:%M:%S')}")
        
        # Keep only the last 10 alerts
        st.session_state.alert_history = st.session_state.alert_history[:10]
        return True
    return False

# ============================================
# STEP 5: SIDEBAR CONTROLS
# ============================================

with st.sidebar:
    st.title("Controls")
    st.markdown("---")
    
    # City selection dropdown
    st.session_state.city = st.selectbox("Select City", list(CITIES.keys()))
    
    st.markdown("---")
    
    # Manual refresh button
    if st.button("Manual Refresh", use_container_width=True):
        with st.spinner("Fetching..."):
            if update_data():
                st.success("Updated!")
                st.rerun()
            else:
                st.error("Failed to fetch")
    
    # Auto-refresh toggle switch
    auto_refresh = st.toggle("Auto-Refresh (every 10 sec)", value=st.session_state.auto_refresh)
    if auto_refresh != st.session_state.auto_refresh:
        st.session_state.auto_refresh = auto_refresh
        st.rerun()
    
    # Reset button to clear all stored data
    if st.button("Reset All Data", use_container_width=True):
        st.session_state.temps.clear()
        st.session_state.humidities.clear()
        st.session_state.winds.clear()
        st.session_state.times.clear()
        st.session_state.alert_history.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Status indicators
    if st.session_state.last_update:
        st.success(f"Last update: {st.session_state.last_update.strftime('%H:%M:%S')}")
    else:
        st.info("Click refresh to start")
    
    # Display current data collection status
    st.caption(f"Data points: {len(st.session_state.temps)}/{WINDOW_SIZE}")
    st.caption(f"Total updates: {len(st.session_state.temps)}")

# ============================================
# STEP 6: MAIN CONTENT HEADER
# ============================================

st.title("Real-Time Weather Intelligence Dashboard")
st.caption("Track B: Live Streaming | Sliding Window | Multi-Chart Visualization | Threshold Alerts")

# ============================================
# STEP 7: ALERT BANNER
# ============================================
# Display prominent alert messages when thresholds are exceeded

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
# STEP 8: CURRENT METRICS DISPLAY
# ============================================
# Display key metrics with delta indicators (change from previous reading)

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
# STEP 9: MULTI-CHART VISUALIZATION
# ============================================
# Create three vertically stacked charts showing trends over time

st.subheader("Sliding Window Visualizations (Last 20 Readings)")

if len(st.session_state.temps) >= 2:
    # Create subplot with 3 rows, 1 column
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Temperature Trend (C)", "Humidity Trend (%)", "Wind Speed Trend (km/h)"),
        vertical_spacing=0.12,
        shared_xaxes=True
    )
    
    # CHART 1: Temperature (Line chart with fill)
    # Color points differently when alert thresholds are crossed
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
            fill='tozeroy',  # Fill area under the line
            fillcolor='rgba(255,107,53,0.15)'
        ),
        row=1, col=1
    )
    
    # Add horizontal lines for alert thresholds
    fig.add_hline(y=TEMP_ALERT_HIGH, line_dash="dash", line_color="red",
                  annotation_text=f"Heat Alert ({TEMP_ALERT_HIGH}C)", 
                  row=1, col=1)
    fig.add_hline(y=TEMP_ALERT_LOW, line_dash="dash", line_color="blue",
                  annotation_text=f"Freeze ({TEMP_ALERT_LOW}C)", 
                  row=1, col=1)
    
    # CHART 2: Humidity (Line chart)
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
    
    # CHART 3: Wind Speed (Bar chart)
    # Color bars red when exceeding wind alert threshold
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
    
    # Add wind alert threshold line
    fig.add_hline(y=WIND_ALERT, line_dash="dash", line_color="red",
                  annotation_text=f"Wind Alert ({WIND_ALERT} km/h)", 
                  row=3, col=1)
    
    # Update layout and axes properties
    fig.update_layout(
        height=800,
        showlegend=False,
        hovermode='x unified',  # Show all values at the same x coordinate
        template='plotly_white'
    )
    
    # Set y-axis ranges for consistent scaling
    fig.update_yaxes(title_text="Temperature (C)", range=[-10, 45], row=1, col=1)
    fig.update_yaxes(title_text="Humidity (%)", range=[0, 100], row=2, col=1)
    fig.update_yaxes(title_text="Wind Speed (km/h)", range=[0, 80], row=3, col=1)
    fig.update_xaxes(title_text="Time", row=3, col=1)
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # STEP 10: STATISTICS SECTION
    # ============================================
    # Calculate and display summary statistics for the current window
    
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
            # Calculate overall trend from first to last reading
            trend = temp_array[-1] - temp_array[0]
            st.metric("Temperature Trend", f"{trend:+.1f}C")
else:
    st.info("Collecting data... Perform a manual refresh to see the charts (need 2+ data points)")

# ============================================
# STEP 11: ALERT HISTORY
# ============================================
# Display the most recent alerts in a scrollable list

if st.session_state.alert_history:
    st.subheader("Alert History")
    for alert in st.session_state.alert_history[:5]:  # Show only last 5 alerts
        if "HEAT" in alert:
            st.error(alert)
        elif "FREEZE" in alert:
            st.warning(alert)
        elif "WIND" in alert:
            st.info(alert)

# ============================================
# STEP 12: RAW DATA TABLE (Expandable)
# ============================================
# Provide option to view the underlying data in tabular format

with st.expander("View Raw Data"):
    if len(st.session_state.temps) > 0:
        # Create pandas DataFrame from deques
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
# STEP 13: AUTO-REFRESH LOGIC
# ============================================
# If auto-refresh is enabled, wait 10 seconds and fetch new data
# Limited to 50 updates to prevent infinite loops

if st.session_state.auto_refresh and len(st.session_state.temps) < 50:
    time.sleep(10)      # Wait 10 seconds between refreshes
    update_data()       # Fetch new data
    st.rerun()          # Rerun the app to update the UI
