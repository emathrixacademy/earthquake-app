# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import requests
# from datetime import datetime
# import pytz

# # Function to fetch earthquake data
# def fetch_earthquake_data(url):
#     response = requests.get(url)
#     data = response.json()
    
#     # Parse the data
#     features = data['features']
#     earthquakes = []
#     for feature in features:
#         properties = feature['properties']
#         geometry = feature['geometry']
#         utc_time = pd.to_datetime(properties['time'], unit='ms')
#         local_time = utc_time.tz_localize('UTC').tz_convert(pytz.timezone('America/Los_Angeles'))  # Convert to local timezone
#         earthquakes.append({
#             "place": properties['place'],
#             "magnitude": properties['mag'],
#             "time_utc": utc_time,
#             "time_local": local_time,
#             "latitude": geometry['coordinates'][1],
#             "longitude": geometry['coordinates'][0]
#         })
    
#     return pd.DataFrame(earthquakes)

# # Fetch real-time earthquake data
# realtime_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
# realtime_earthquake_data = fetch_earthquake_data(realtime_url)

# # Fetch historical earthquake data
# historical_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"
# historical_earthquake_data = fetch_earthquake_data(historical_url)

# # Streamlit app layout
# st.title("Real-Time Earthquake Monitoring Webapp")
# st.markdown("This app visualizes real-time and historical earthquake data from the US Geological Survey (USGS).")

# # Filter by magnitude
# min_magnitude = st.slider("Minimum Magnitude", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
# filtered_realtime_data = realtime_earthquake_data[realtime_earthquake_data["magnitude"] >= min_magnitude]
# filtered_historical_data = historical_earthquake_data[historical_earthquake_data["magnitude"] >= min_magnitude]

# # Create a Plotly map for real-time earthquakes
# fig_realtime = px.scatter_mapbox(
#     filtered_realtime_data,
#     lat="latitude",
#     lon="longitude",
#     size="magnitude",
#     color="magnitude",
#     hover_name="place",
#     hover_data={"time_utc": True, "time_local": True, "magnitude": True},
#     zoom=1,
#     height=600,
#     title="Recent Earthquakes (Last Hour)"
# )

# # Create a Plotly map for historical earthquakes
# fig_historical = px.scatter_mapbox(
#     filtered_historical_data,
#     lat="latitude",
#     lon="longitude",
#     size="magnitude",
#     color="magnitude",
#     hover_name="place",
#     hover_data={"time_utc": True, "time_local": True, "magnitude": True},
#     zoom=1,
#     height=600,
#     title="Historical Earthquakes (Last Month)"
# )

# fig_realtime.update_layout(mapbox_style="open-street-map")
# fig_historical.update_layout(mapbox_style="open-street-map")

# # Display the maps
# st.plotly_chart(fig_realtime)
# st.plotly_chart(fig_historical)

# # Display the filtered raw data
# st.subheader("Filtered Real-Time Earthquake Data")
# st.write(filtered_realtime_data)

# st.subheader("Filtered Historical Earthquake Data")
# st.write(filtered_historical_data)

# # Additional Information
# st.sidebar.subheader("About This App")
# st.sidebar.info(
#     """
#     This application fetches real-time and historical earthquake data from the USGS API and visualizes it on interactive maps.
#     Use the slider to filter earthquakes by magnitude. The times are displayed in both UTC and local time.
#     """
# )


import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import pytz

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

# Filter earthquakes to Philippines region
def filter_philippines_earthquakes(df):
    # Philippines bounding box: lat 5-20°N, lon 120-130°E
    ph_filtered = df[
        (df['latitude'] >= 4) & (df['latitude'] <= 20) &
        (df['longitude'] >= 119) & (df['longitude'] <= 131)
    ]
    return ph_filtered

# Fetch data
realtime_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
historical_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"

realtime_data = fetch_earthquake_data(realtime_url)
historical_data = fetch_earthquake_data(historical_url)

# Filter to Philippines only
ph_realtime = filter_philippines_earthquakes(realtime_data)
ph_historical = filter_philippines_earthquakes(historical_data)

# Streamlit layout
st.set_page_config(page_title="PH Earthquake Monitor", layout="wide")
st.title("🇵🇭 Philippines Earthquake Monitoring System")
st.markdown("Real-time earthquake data focused on the Philippine region (Updated from USGS)")

# Key metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Earthquakes (Last Hour)", len(ph_realtime))
with col2:
    st.metric("Earthquakes (Last Month)", len(ph_historical))
with col3:
    max_mag_realtime = ph_realtime['magnitude'].max() if len(ph_realtime) > 0 else 0
    st.metric("Max Magnitude (1hr)", f"{max_mag_realtime:.1f}")
with col4:
    max_mag_monthly = ph_historical['magnitude'].max() if len(ph_historical) > 0 else 0
    st.metric("Max Magnitude (1mo)", f"{max_mag_monthly:.1f}")

# Filter controls
st.sidebar.header("Filter Options")
min_magnitude = st.sidebar.slider("Minimum Magnitude", 0.0, 10.0, 2.0, 0.1)
depth_range = st.sidebar.slider("Depth Range (km)", 0, 700, (0, 700))

# Apply filters
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

# Create maps
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
        hover_data={
            "magnitude": ":.2f",
            "depth_km": ":.1f",
            "time_ph": True,
            "latitude": False,
            "longitude": False
        },
        zoom=5,
        height=500,
        title="Recent Earthquakes"
    )
    fig_realtime.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(
            center=dict(lat=12.5, lon=125),
            zoom=5
        )
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
        hover_data={
            "magnitude": ":.2f",
            "depth_km": ":.1f",
            "time_ph": True,
            "latitude": False,
            "longitude": False
        },
        zoom=5,
        height=500,
        title="Monthly Earthquakes"
    )
    fig_historical.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(
            center=dict(lat=12.5, lon=125),
            zoom=5
        )
    )
    st.plotly_chart(fig_historical, use_container_width=True)

# Statistics and analysis
st.divider()
st.subheader("📊 Data Analysis")

col1, col2 = st.columns(2)

with col1:
    st.write("**Hourly Earthquakes by Magnitude**")
    if len(ph_realtime_filtered) > 0:
        mag_dist = ph_realtime_filtered.groupby(pd.cut(ph_realtime_filtered['magnitude'], bins=5)).size()
        st.bar_chart(mag_dist)
    else:
        st.info("No earthquakes detected in the last hour")

with col2:
    st.write("**Monthly Earthquakes by Depth**")
    if len(ph_historical_filtered) > 0:
        depth_fig = px.histogram(
            ph_historical_filtered,
            x="depth_km",
            nbins=20,
            labels={"depth_km": "Depth (km)"}
        )
        st.plotly_chart(depth_fig, use_container_width=True)
    else:
        st.info("No earthquakes in selected range")

# Data tables
st.divider()
st.subheader("📋 Detailed Data")

tab1, tab2 = st.tabs(["Last Hour", "Last Month"])

with tab1:
    if len(ph_realtime_filtered) > 0:
        display_realtime = ph_realtime_filtered[['place', 'magnitude', 'depth_km', 'time_ph']].copy()
        display_realtime = display_realtime.sort_values('time_ph', ascending=False)
        st.dataframe(display_realtime, use_container_width=True)
    else:
        st.info("No earthquakes in the last hour")

with tab2:
    if len(ph_historical_filtered) > 0:
        display_historical = ph_historical_filtered[['place', 'magnitude', 'depth_km', 'time_ph']].copy()
        display_historical = display_historical.sort_values('time_ph', ascending=False)
        st.dataframe(display_historical, use_container_width=True)
    else:
        st.info("No earthquakes in selected range")

# Footer
st.sidebar.divider()
st.sidebar.info(
    """
    **About This App**
    
    Monitors earthquakes in the Philippines using USGS data.
    - Times shown in Philippine Time (PHT)
    - Data updates every 5 minutes
    - Bounding box: 4-20°N, 119-131°E
    
    **Data Source:** USGS Earthquake Hazards Program
    """
)
