import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import pytz
import os

st.set_page_config(page_title="PH Earthquake Response System", layout="wide")

# Initialize session state
if "selected_city" not in st.session_state:
    st.session_state.selected_city = None
if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []
if "assessment_data" not in st.session_state:
    st.session_state.assessment_data = {}

# Function to fetch earthquake data
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

# Filter to Philippines
def filter_philippines_earthquakes(df):
    ph_filtered = df[
        (df['latitude'] >= 4) & (df['latitude'] <= 20) &
        (df['longitude'] >= 119) & (df['longitude'] <= 131)
    ]
    return ph_filtered

# Philippine municipalities and their approximate coordinates
ph_municipalities = {
    "Calabarzon Region": {
        "Quezon City": {"lat": 14.6349, "lon": 121.0388},
        "Makati": {"lat": 14.5547, "lon": 121.0244},
        "Tagaytay": {"lat": 14.1345, "lon": 121.0075},
        "Cavite City": {"lat": 14.3742, "lon": 120.8958},
        "Lucena": {"lat": 14.1950, "lon": 121.6206},
        "Pasay": {"lat": 14.5480, "lon": 121.0080},
    },
    "National Capital Region": {
        "Manila": {"lat": 14.5994, "lon": 120.9842},
        "Taguig": {"lat": 14.5794, "lon": 121.0566},
        "Valenzuela": {"lat": 14.6899, "lon": 120.9819},
        "Navotas": {"lat": 14.6588, "lon": 120.9255},
    },
    "Visayas": {
        "Cebu City": {"lat": 10.3157, "lon": 123.8854},
        "Iloilo City": {"lat": 10.6898, "lon": 122.5547},
        "Bacolod": {"lat": 10.3932, "lon": 123.0136},
    },
    "Mindanao": {
        "Davao City": {"lat": 7.0731, "lon": 125.6121},
        "Cagayan de Oro": {"lat": 8.4874, "lon": 124.6426},
    }
}

# Main title
st.title("🚨 Philippines Earthquake Response System")
st.markdown("Real-time monitoring + Damage Assessment")

# Fetch earthquake data
realtime_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
historical_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"

realtime_data = fetch_earthquake_data(realtime_url)
historical_data = fetch_earthquake_data(historical_url)

ph_realtime = filter_philippines_earthquakes(realtime_data)
ph_historical = filter_philippines_earthquakes(historical_data)

# ==================== SECTION 1: EARTHQUAKE MONITORING ====================
st.divider()
st.header("1️⃣ Real-Time Earthquake Monitoring")

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

# Filter controls
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

# Map display
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

# ==================== SECTION 2: DAMAGE ASSESSMENT ====================
st.divider()
st.header("2️⃣ Post-Earthquake Damage Assessment")

# City/Municipality Selection
st.subheader("Select Affected Area")

region = st.selectbox("Region", list(ph_municipalities.keys()))
city = st.selectbox("City/Municipality", list(ph_municipalities[region].keys()))

if city:
    st.session_state.selected_city = city
    city_coords = ph_municipalities[region][city]
    
    st.success(f"✅ Selected: **{city}**")
    st.write(f"Coordinates: {city_coords['lat']:.4f}°N, {city_coords['lon']:.4f}°E")

st.divider()

# ==================== SECTION 3: IMAGE CAPTURE & UPLOAD ====================
st.subheader("3️⃣ Capture Building/Road Integrity Data")

if st.session_state.selected_city:
    st.info(f"📍 Capturing damage assessment data for: **{st.session_state.selected_city}**")
    
    # Three tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["📸 Camera", "📁 Upload Files", "📋 Review Uploads"])
    
    with tab1:
        st.write("Take a photo directly from your device camera")
        camera_photo = st.camera_input("Take a photo of building/road damage")
        
        if camera_photo is not None:
            st.image(camera_photo, caption="Captured Image", use_container_width=True)
            
            if st.button("Add to Assessment (Camera)"):
                from datetime import datetime as dt
                timestamp = dt.now().strftime("%Y-%m-%d %H:%M:%S")
                
                image_entry = {
                    "timestamp": timestamp,
                    "city": st.session_state.selected_city,
                    "source": "camera",
                    "image_data": camera_photo.getvalue()
                }
                
                st.session_state.uploaded_images.append(image_entry)
                st.success(f"✅ Image added to {st.session_state.selected_city} assessment")
                st.rerun()
    
    with tab2:
        st.write("Upload photos from your device")
        uploaded_files = st.file_uploader(
            "Choose images of building/road damage",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="file_uploader"
        )
        
        if uploaded_files:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                for uploaded_file in uploaded_files:
                    st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
            
            with col2:
                if st.button("Add All to Assessment"):
                    from datetime import datetime as dt
                    timestamp = dt.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    for uploaded_file in uploaded_files:
                        image_entry = {
                            "timestamp": timestamp,
                            "city": st.session_state.selected_city,
                            "source": "upload",
                            "filename": uploaded_file.name,
                            "image_data": uploaded_file.getvalue()
                        }
                        st.session_state.uploaded_images.append(image_entry)
                    
                    st.success(f"✅ {len(uploaded_files)} images added to assessment")
                    st.rerun()
    
    with tab3:
        st.write("Review all captured/uploaded images")
        
        if len(st.session_state.uploaded_images) > 0:
            st.metric("Total Images Uploaded", len(st.session_state.uploaded_images))
            
            # Filter by city
            city_filter = st.selectbox(
                "Filter by city",
                ["All"] + list(set([img["city"] for img in st.session_state.uploaded_images]))
            )
            
            filtered_images = st.session_state.uploaded_images
            if city_filter != "All":
                filtered_images = [img for img in filtered_images if img["city"] == city_filter]
            
            # Display images in a grid
            for idx, img_entry in enumerate(filtered_images):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{img_entry['city']}** | {img_entry['timestamp']}")
                    st.image(img_entry["image_data"], use_container_width=True)
                
                with col2:
                    if st.button(f"Remove", key=f"remove_{idx}"):
                        st.session_state.uploaded_images.pop(idx)
                        st.rerun()
            
            # Clear all button
            st.divider()
            if st.button("Clear All Images"):
                st.session_state.uploaded_images = []
                st.rerun()
        
        else:
            st.info("No images uploaded yet. Use Camera or Upload tabs to add images.")

else:
    st.warning("Please select a city/municipality first to begin damage assessment")

# ==================== SECTION 4: NEXT STEPS ====================
st.divider()
st.subheader("4️⃣ Next Steps")

st.info("""
**Phase 2 (Coming Soon):** Machine Learning Classification
- Your uploaded building photos will be analyzed by Teachable Machine
- Damage levels: Safe | Damaged | Unsafe
- Automated damage reports for emergency response
""")
