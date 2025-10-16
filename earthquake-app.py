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

# Mobile-first configuration
st.set_page_config(
    page_title="PH Earthquake Response",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile-optimized CSS
st.markdown("""
    <style>
    [data-testid="stMain"] { max-width: 100%; }
    button { width: 100%; padding: 1rem; font-size: 1.1rem; font-weight: bold; border-radius: 10px; }
    .alert-banner { padding: 1.5rem; border-radius: 10px; margin: 1rem 0; text-align: center; }
    .service-ready { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 2rem; border-radius: 15px; margin: 1rem 0; }
    .action-button { background: #dc3545; color: white; font-weight: bold; padding: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if "earthquake_detected" not in st.session_state:
    st.session_state.earthquake_detected = False
if "current_earthquake" not in st.session_state:
    st.session_state.current_earthquake = None
if "assessment_results" not in st.session_state:
    st.session_state.assessment_results = None

# Damage recommendations
DAMAGE_RECOMMENDATIONS = {
    "SAFE": {
        "color": "#28a745",
        "bg_gradient": "linear-gradient(135deg, #28a745 0%, #20c997 100%)",
        "actions": [
            "Building is safe for occupancy",
            "Structural integrity intact",
            "Continue monitoring for aftershocks",
            "Document for insurance purposes"
        ],
        "priority": "LOW"
    },
    "DAMAGED": {
        "color": "#ffc107",
        "bg_gradient": "linear-gradient(135deg, #ffc107 0%, #ff9800 100%)",
        "actions": [
            "Building requires professional inspection",
            "Minor repairs needed before full occupancy",
            "Evacuate if aftershocks are strong",
            "Contact structural engineer for assessment",
            "Document damage for insurance/aid"
        ],
        "priority": "MEDIUM"
    },
    "UNSAFE": {
        "color": "#dc3545",
        "bg_gradient": "linear-gradient(135deg, #dc3545 0%, #c82333 100%)",
        "actions": [
            "EVACUATE IMMEDIATELY - Do not enter this building",
            "Mark building as unsafe (Red Tag)",
            "Contact emergency services (911/NDRRMC)",
            "Arrange temporary shelter for occupants",
            "Professional structural assessment required"
        ],
        "priority": "CRITICAL"
    }
}

# Functions
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
            "time_ph": ph_time,
            "latitude": geometry['coordinates'][1],
            "longitude": geometry['coordinates'][0]
        })
    return pd.DataFrame(earthquakes)

def filter_philippines_earthquakes(df):
    return df[
        (df['latitude'] >= 4) & (df['latitude'] <= 20) &
        (df['longitude'] >= 119) & (df['longitude'] <= 131)
    ]

def check_recent_earthquakes():
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        for feature in data['features']:
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
    except:
        return None

def classify_building_damage_hosted(image):
    """AI classification of building damage"""
    try:
        import time
        time.sleep(1)
        
        # Mock classification - replace with actual Teachable Machine API
        class_names = ["SAFE", "DAMAGED", "UNSAFE"]
        predictions = [0.8, 0.15, 0.05]
        
        predicted_idx = np.argmax(predictions)
        predicted_class = class_names[predicted_idx]
        confidence = predictions[predicted_idx]
        
        return predicted_class, confidence, predictions
    except Exception as e:
        st.error(f"Error: {e}")
        return None, 0, None

# ==================== MAIN APP ====================

# HEADER - Always visible
st.title("PH Earthquake Response")
st.markdown("Emergency Building Damage Assessment")

# Check for earthquakes
st.session_state.current_earthquake = check_recent_earthquakes()

# ==================== EARTHQUAKE STATUS ====================
col1, col2, col3 = st.columns(3)

with col1:
    if st.session_state.current_earthquake:
        st.markdown(f"""
            <div style="background: #dc3545; color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                <h3>EARTHQUAKE DETECTED</h3>
                <p style="font-size: 1.2rem; margin: 0;">Mag {st.session_state.current_earthquake['magnitude']}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="background: #28a745; color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                <h3>NO ALERT</h3>
                <p style="font-size: 0.9rem; margin: 0;">Ready to monitor</p>
            </div>
        """, unsafe_allow_html=True)

with col2:
    # Fetch latest data
    realtime_data = fetch_earthquake_data("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson")
    ph_realtime = filter_philippines_earthquakes(realtime_data)
    st.metric("Earthquakes (1hr)", len(ph_realtime))

with col3:
    historical_data = fetch_earthquake_data("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson")
    ph_historical = filter_philippines_earthquakes(historical_data)
    st.metric("Earthquakes (1mo)", len(ph_historical))

st.divider()

# ==================== SERVICE STATUS ====================
if st.session_state.current_earthquake:
    eq = st.session_state.current_earthquake
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 2rem; border-radius: 15px; margin: 1rem 0; text-align: center;">
            <h2>EARTHQUAKE DETECTED</h2>
            <p><strong>Magnitude:</strong> {eq['magnitude']}</p>
            <p><strong>Location:</strong> {eq['location']}</p>
            <p><strong>Time:</strong> {eq['time_ph'].strftime('%H:%M:%S')}</p>
            <p><strong>Depth:</strong> {eq['depth']:.1f} km</p>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 2rem; border-radius: 15px; margin: 1rem 0; text-align: center;">
            <h2>SERVICE READY</h2>
            <p>Damage assessment service is ready to use</p>
            <p>Take or upload building photos when needed</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# ==================== PRIMARY ACTION - IMAGE CAPTURE ====================
st.header("ASSESS BUILDING DAMAGE")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Camera")
    camera_photo = st.camera_input("Take a photo", key="camera")

with col2:
    st.subheader("Upload")
    uploaded_file = st.file_uploader("Select image", type=["jpg", "jpeg", "png"], key="upload")

# Get image
image_to_process = None
if camera_photo:
    image_to_process = Image.open(camera_photo)
elif uploaded_file:
    image_to_process = Image.open(uploaded_file)

# Display and analyze
if image_to_process:
    st.divider()
    st.image(image_to_process, caption="Building Assessment", use_container_width=True)
    
    if st.button("ANALYZE DAMAGE", type="primary", use_container_width=True):
        with st.spinner("AI is analyzing..."):
            predicted_class, confidence, all_predictions = classify_building_damage_hosted(image_to_process)
            
            if predicted_class:
                st.session_state.assessment_results = {
                    "class": predicted_class,
                    "confidence": confidence,
                    "predictions": all_predictions
                }
                st.rerun()

# ==================== RESULTS ====================
if st.session_state.assessment_results:
    st.divider()
    
    result = st.session_state.assessment_results
    damage_class = result['class']
    confidence = result['confidence']
    rec = DAMAGE_RECOMMENDATIONS[damage_class]
    
    # Large result banner
    st.markdown(f"""
        <div style="background: {rec['bg_gradient']}; color: white; padding: 2rem; border-radius: 15px; margin: 1rem 0; text-align: center;">
            <h1>{damage_class}</h1>
            <p style="font-size: 1.1rem;">Confidence: {confidence*100:.0f}%</p>
            <p style="font-size: 0.9rem; margin-top: 1rem;">Priority: {rec['priority']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Actions
    st.subheader("What to Do")
    for action in rec['actions']:
        st.write(f"▸ {action}")
    
    # Emergency contacts
    if damage_class == "UNSAFE":
        st.divider()
        st.error("CRITICAL - CONTACT EMERGENCY SERVICES")
        st.write("📞 **NDRRMC Hotline:** 1-800-1-73239 (1-800-1-READY)")
        st.write("📞 **Bureau of Fire Protection (BFP):** 911")
        st.write("📍 **Local Emergency Management Office**")
    
    # Clear button
    st.divider()
    if st.button("Assess Another Building", use_container_width=True):
        st.session_state.assessment_results = None
        st.rerun()

# ==================== OPTIONAL: MONITORING DATA ====================
st.divider()

with st.expander("Show Earthquake Monitoring Data"):
    st.subheader("Real-Time Earthquake Map (Last Hour)")
    
    if len(ph_realtime) > 0:
        fig_realtime = px.scatter_mapbox(
            ph_realtime,
            lat="latitude",
            lon="longitude",
            size="magnitude",
            color="magnitude",
            hover_name="place",
            hover_data={"magnitude": ":.2f", "depth_km": ":.1f"},
            zoom=5,
            height=400
        )
        fig_realtime.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(center=dict(lat=12.5, lon=125), zoom=5)
        )
        st.plotly_chart(fig_realtime, use_container_width=True)
    else:
        st.info("No earthquakes in the last hour")
    
    st.subheader("Earthquake Statistics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Earthquakes (1 month)", len(ph_historical))
        if len(ph_historical) > 0:
            st.metric("Max Magnitude", f"{ph_historical['magnitude'].max():.1f}")
    
    with col2:
        if len(ph_historical) > 0:
            avg_depth = ph_historical['depth_km'].mean()
            st.metric("Average Depth", f"{avg_depth:.1f} km")

# Test mode
with st.expander("Test Mode"):
    if st.button("Simulate Earthquake"):
        st.session_state.current_earthquake = {
            "magnitude": 6.5,
            "depth": 25,
            "location": "Calabarzon",
            "latitude": 14.5,
            "longitude": 121.5,
            "time_ph": datetime.now(pytz.timezone('Asia/Manila')),
            "time_utc": datetime.now(pytz.timezone('UTC'))
        }
        st.rerun()

st.caption("PH Earthquake Response v3.0 | USGS + Teachable Machine")
