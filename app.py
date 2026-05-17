
### 📊 Polling Justification

The **10-second refresh rate** provides:
- Near real-time experience for weather monitoring
- Smooth sliding window animation
- Respects API rate limits (Open-Meteo allows ~360/hour)
- Optimal for trend detection

### 🎯 Features Demonstrated

1. **3 Interactive Charts**: Temperature, Humidity, Wind Speed
2. **Sliding Window**: Shows last 20 data points
3. **Auto-Refresh**: Updates automatically every 10 seconds
4. **Threshold Alerts**: Visual alerts when thresholds exceeded
5. **Conditional Formatting**: Red points for alert conditions
6. **Fixed Axes**: Charts don't jump or rescale
7. **Multi-City Support**: 10 global cities
""")

# ============================================
# AUTO-REFRESH LOGIC
# ============================================

if st.session_state.auto_refresh and len(st.session_state.temps) < 50:
time.sleep(10)
update_data()
st.rerun()
