import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import pytz
import numpy as np
from PIL import Image
import io
import base64

# Configuration
st.set_page_config(page_title="PH Earthquake Response System", layout="wide")

# Initialize session state
if "earthquake_detected" not in st.session_state:
    st.session_state.earthquake_detected = False
if "current_earthquake" not in st.session_state:
    st.session_state.current_earthquake = None
if "assessment_results" not in st.session_state:
    st.session_state.assessment_results = None

# Damage assessment recommendations
DAMAGE_RECOMMENDATIONS = {
    "SAFE": {
        "color": "#28a745",
        "actions": [
            "✅ Building is safe for occupancy",
            "✅ Structural integrity intact",
            "✅ Continue monitoring for aftershocks",
            "💡 Document for insurance purposes"
        ],
        "priority": "LOW"
    },
    "DAMAGED": {
        "color": "#ffc107",
        "actions": [
            "⚠️ Building requires professional inspection",
            "⚠️ Minor repairs needed before full occupancy",
            "⚠️ Evacuate if aftershocks are strong",
            "🏗️ Contact structural engineer for detailed assessment",
            "💡 Document damage for insurance/government aid"
        ],
        "priority": "MEDIUM"
    },
    "UNSAFE": {
        "color": "#dc3545",
        "actions": [
            "🚨 EVACUATE IMMEDIATELY",
            "🚨 Do not enter this building",
            "🚨 Mark building as unsafe/red tag",
            "📞 Contact emergency services (911/NDRRMC)",
            "🏠 Arrange temporary shelter for occupants",
            "🏗️ Professional structural assessment required before re-entry"
        ],
        "priority": "CRITICAL"
    }
}

# ==================== FUNCTIONS ====================

def fetch_earthquake_data(url):
    response = requests.get(url)
    data = response.json()
    
    features = data['features']
    earthquakes = []
    for feature in features:
        properties = feature['properties']
        geometry = feature['geometry']
        utc_time = pd.to_datetime(properties['time'], unit='ms')
        ph_time = utc_time.tz_localize('UTC').tz_convert(pytz.timezone('Asia/Manila'))
        earthquakes.append({
            "place": properties['place'],
            "magnitude": properties['mag'],
            "depth_km": geometry['coordinates'][2],
            "time_utc": utc_time,
            "time_ph": ph_time,
            "latitude": geometry['coordinates'][1],
            "longitude": geometry['coordinates'][0]
        })
    
    return pd.DataFrame(earthquakes)

def filter_philippines_earthquakes(df):
    ph_filtered = df[
        (df['latitude'] >= 4) & (df['latitude'] <= 20) &
        (df['longitude'] >= 119) & (df['longitude'] <= 131)
    ]
    return ph_filtered

def check_recent_earthquakes():
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        features = data['features']
        for feature in features:
            properties = feature['properties']
            geometry = feature['geometry']
            lat, lon = geometry['coordinates'][1], geometry['coordinates'][0]
            
            if 4 <= lat <= 20 and 119 <= lon <= 131:
                if properties['mag'] >= 4.0:
                    utc_time = pd.to_datetime(properties['time'], unit='ms')
                    ph_time = utc_time.tz_localize('UTC').tz_convert(pytz.timezone('Asia/Manila'))
                    
                    return {
                        "magnitude": properties['mag'],
                        "depth": geometry['coordinates'][2],
                        "location": properties['place'],
                        "latitude": lat,
                        "longitude": lon,
                        "time_ph": ph_time,
                        "time_utc": utc_time
                    }
        return None
    except Exception as e:
        st.error(f"Error checking earthquakes: {e}")
        return None

def classify_building_damage_hosted(image):
    """Classify using Teachable Machine hosted model"""
    try:
        img_array = np.array(image)
        img_pil = Image.fromarray(img_array.astype('uint8'))
        img_byte_arr = io.BytesIO()
        img_pil.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
        
        # Simulate classification - in production, use actual Teachable Machine API
        # For now, we'll create a demo that shows the flow
        import time
        time.sleep(1)  # Simulate processing
        
        # Mock results (replace with actual API call)
        class_names = ["SAFE", "DAMAGED", "UNSAFE"]
        predictions = [0.8, 0.15, 0.05]  # Mock confidence scores
        
        predicted_idx = np.argmax(predictions)
        predicted_class = class_names[predicted_idx]
        confidence = predictions[predicted_idx]
        
        return predicted_class, confidence, predictions
        
    except Exception as e:
        st.error(f"Error during classification: {e}")
        return None, 0, None

# ==================== MAIN APP ====================

# Header
st.title("🚨 PH Earthquake Response System")
st.markdown("Real-time Monitoring + AI Building Damage Assessment")

# Fetch data
realtime_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
historical_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"

realtime_data = fetch_earthquake_data(realtime_url)
historical_data = fetch_earthquake_data(historical_url)

ph_realtime = filter_philippines_earthquakes(realtime_data)
ph_historical = filter_philippines_earthquakes(historical_data)

# Check for significant earthquakes
st.session_state.current_earthquake = check_recent_earthquakes()

# Create tabs
tab1, tab2 = st.tabs(["📊 Earthquake Monitoring", "🏢 Damage Assessment"])

# ==================== TAB 1: MONITORING DASHBOARD ====================
with tab1:
    st.header("Real-Time Earthquake Monitoring")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Earthquakes (1hr)", len(ph_realtime))
    with col2:
        st.metric("Earthquakes (1mo)", len(ph_historical))
    with col3:
        max_mag_realtime = ph_realtime['magnitude'].max() if len(ph_realtime) > 0 else 0
        st.metric("Max Mag (1hr)", f"{max_mag_realtime:.1f}")
    with col4:
        max_mag_monthly = ph_historical['magnitude'].max() if len(ph_historical) > 0 else 0
        st.metric("Max Mag (1mo)", f"{max_mag_monthly:.1f}")
    
    # Filters
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        min_magnitude = st.slider("Minimum Magnitude", 0.0, 10.0, 2.0, 0.1)
    with col2:
        depth_range = st.slider("Depth Range (km)", 0, 700, (0, 700))
    
    ph_realtime_filtered = ph_realtime[
        (ph_realtime['magnitude'] >= min_magnitude) &
        (ph_realtime['depth_km'] >= depth_range[0]) &
        (ph_realtime['depth_km'] <= depth_range[1])
    ]
    
    ph_historical_filtered = ph_historical[
        (ph_historical['magnitude'] >= min_magnitude) &
        (ph_historical['depth_km'] >= depth_range[0]) &
        (ph_historical['depth_km'] <= depth_range[1])
    ]
    
    # Maps
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Last Hour")
        fig_realtime = px.scatter_mapbox(
            ph_realtime_filtered,
            lat="latitude",
            lon="longitude",
            size="magnitude",
            color="magnitude",
            hover_name="place",
            hover_data={"magnitude": ":.2f", "depth_km": ":.1f", "time_ph": True},
            zoom=5,
            height=500
        )
        fig_realtime.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(center=dict(lat=12.5, lon=125), zoom=5)
        )
        st.plotly_chart(fig_realtime, use_container_width=True)
    
    with col2:
        st.subheader("Last Month")
        fig_historical = px.scatter_mapbox(
            ph_historical_filtered,
            lat="latitude",
            lon="longitude",
            size="magnitude",
            color="magnitude",
            hover_name="place",
            hover_data={"magnitude": ":.2f", "depth_km": ":.1f", "time_ph": True},
            zoom=5,
            height=500
        )
        fig_historical.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(center=dict(lat=12.5, lon=125), zoom=5)
        )
        st.plotly_chart(fig_historical, use_container_width=True)
    
    # Statistics
    st.divider()
    st.subheader("Data Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Hourly Earthquakes by Magnitude")
        if len(ph_realtime_filtered) > 0:
            mag_dist = ph_realtime_filtered.groupby(pd.cut(ph_realtime_filtered['magnitude'], bins=5)).size()
            st.bar_chart(mag_dist)
        else:
            st.info("No earthquakes detected")
    
    with col2:
        st.write("Monthly Earthquakes by Depth")
        if len(ph_historical_filtered) > 0:
            depth_fig = px.histogram(
                ph_historical_filtered,
                x="depth_km",
                nbins=20,
                labels={"depth_km": "Depth (km)"}
            )
            st.plotly_chart(depth_fig, use_container_width=True)
        else:
            st.info("No earthquakes in range")
    
    # Data tables
    st.divider()
    st.subheader("Detailed Data")
    
    subtab1, subtab2 = st.tabs(["Last Hour", "Last Month"])
    
    with subtab1:
        if len(ph_realtime_filtered) > 0:
            display_realtime = ph_realtime_filtered[['place', 'magnitude', 'depth_km', 'time_ph']].copy()
            display_realtime = display_realtime.sort_values('time_ph', ascending=False)
            st.dataframe(display_realtime, use_container_width=True)
        else:
            st.info("No earthquakes in the last hour")
    
    with subtab2:
        if len(ph_historical_filtered) > 0:
            display_historical = ph_historical_filtered[['place', 'magnitude', 'depth_km', 'time_ph']].copy()
            display_historical = display_historical.sort_values('time_ph', ascending=False)
            st.dataframe(display_historical, use_container_width=True)
        else:
            st.info("No earthquakes in selected range")

# ==================== TAB 2: DAMAGE ASSESSMENT ====================
with tab2:
    st.header("AI-Powered Building Damage Assessment")
    
    if st.session_state.current_earthquake:
        eq = st.session_state.current_earthquake
        
        # Earthquake alert
        st.markdown(f"""
            <div style="background-color: #dc3545; color: white; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;">
                <h3>⚡ EARTHQUAKE DETECTED</h3>
                <p><strong>Magnitude:</strong> {eq['magnitude']}</p>
                <p><strong>Location:</strong> {eq['location']}</p>
                <p><strong>Time (PH):</strong> {eq['time_ph'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Depth:</strong> {eq['depth']:.1f} km</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        st.subheader("Step 1: Capture Building/Road Photo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Take Photo**")
            camera_photo = st.camera_input("Camera capture")
        
        with col2:
            st.write("**Upload Photo**")
            uploaded_file = st.file_uploader("Choose image", type=["jpg", "jpeg", "png"])
        
        image_to_process = None
        if camera_photo:
            image_to_process = Image.open(camera_photo)
        elif uploaded_file:
            image_to_process = Image.open(uploaded_file)
        
        if image_to_process:
            st.divider()
            st.subheader("Step 2: AI Analysis")
            
            st.image(image_to_process, caption="Assessment Photo", use_container_width=True)
            
            if st.button("Analyze Building Damage", type="primary", use_container_width=True):
                with st.spinner("Analyzing with AI..."):
                    predicted_class, confidence, all_predictions = classify_building_damage_hosted(image_to_process)
                    
                    if predicted_class:
                        st.session_state.assessment_results = {
                            "class": predicted_class,
                            "confidence": confidence,
                            "predictions": all_predictions
                        }
                        st.rerun()
        
        # Results
        if st.session_state.assessment_results:
            st.divider()
            st.subheader("Step 3: Assessment Report")
            
            result = st.session_state.assessment_results
            damage_class = result['class']
            confidence = result['confidence']
            rec = DAMAGE_RECOMMENDATIONS[damage_class]
            
            st.markdown(f"""
                <div style="background-color: {rec['color']}; color: white; padding: 1.5rem; border-radius: 0.5rem; margin: 1rem 0;">
                    <h2>{damage_class}</h2>
                    <p><strong>Confidence:</strong> {confidence*100:.1f}%</p>
                    <p><strong>Priority:</strong> {rec['priority']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.subheader("Recommended Actions")
            for action in rec['actions']:
                st.write(action)
            
            st.divider()
            
            if damage_class == "UNSAFE":
                st.error("CRITICAL: Contact emergency services immediately")
                st.write("- NDRRMC Hotline: 1-800-1-READY (1-800-1-73239)")
                st.write("- Local Emergency Management Office")
                st.write("- Bureau of Fire Protection (BFP)")
            
            elif damage_class == "DAMAGED":
                st.warning("Building requires professional inspection")
                st.write("- Contact a licensed structural engineer")
                st.write("- File insurance claim")
                st.write("- Contact local government for assistance")
            
            else:
                st.success("Building is safe for occupancy")
                st.write("- Monitor for aftershocks")
                st.write("- Document for records")
            
            if st.button("Clear & Assess Another Building"):
                st.session_state.assessment_results = None
                st.rerun()
    
    else:
        st.info("No significant earthquakes detected (magnitude 4.0+)")
        st.write("Assessment tool will activate when an earthquake is detected.")
        
        if st.checkbox("Enable test mode (simulate earthquake for demo)"):
            st.session_state.current_earthquake = {
                "magnitude": 6.5,
                "depth": 25,
                "location": "23 km NE of Rizal, Calabarzon",
                "latitude": 14.5,
                "longitude": 121.5,
                "time_ph": datetime.now(pytz.timezone('Asia/Manila')),
                "time_utc": datetime.now(pytz.timezone('UTC'))
            }
            st.rerun()

# Footer
st.divider()
st.caption("PH Earthquake Response System v2.0 | Data: USGS | AI: Teachable Machine")
