import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import numpy as np
from PIL import Image
import tensorflow as tf
import io

# Mobile-first configuration
st.set_page_config(
    page_title="PH Earthquake Response",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile optimization
st.markdown("""
    <style>
    body { margin: 0; padding: 0; }
    .main { padding: 1rem; }
    button { width: 100%; padding: 0.75rem; font-size: 1rem; }
    </style>
    """, unsafe_allow_html=True)

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

# Function to check for recent earthquakes
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
            
            # Check if in Philippines
            if 4 <= lat <= 20 and 119 <= lon <= 131:
                if properties['mag'] >= 4.0:  # Only significant earthquakes
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

# Load Teachable Machine model
@st.cache_resource
def load_model(model_path):
    """
    Load TensorFlow Lite model from Teachable Machine
    Export your Teachable Machine model as TensorFlow Lite
    model_path: local path to .tflite file or URL
    """
    try:
        interpreter = tf.lite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        return interpreter
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

# Run inference on image
def classify_building_damage(image, interpreter, input_shape=(224, 224)):
    """Classify building damage from image"""
    try:
        # Prepare image
        img_array = np.array(image).astype(np.float32)
        img_resized = Image.fromarray(image).resize(input_shape)
        img_array = np.array(img_resized) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        # Get input and output tensors
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        # Run inference
        interpreter.set_tensor(input_details[0]['index'], img_array)
        interpreter.invoke()
        
        # Get predictions
        output_data = interpreter.get_tensor(output_details[0]['index'])
        predictions = output_data[0]
        
        class_names = ["SAFE", "DAMAGED", "UNSAFE"]
        confidence = np.max(predictions)
        class_idx = np.argmax(predictions)
        predicted_class = class_names[class_idx]
        
        return predicted_class, float(confidence), predictions
    
    except Exception as e:
        st.error(f"Error during classification: {e}")
        return None, 0, None

# ==================== MAIN APP ====================

# Header
st.title("🚨 PH Earthquake Response")
st.markdown("Real-time Detection + AI Building Assessment")

# Check for earthquakes
st.session_state.current_earthquake = check_recent_earthquakes()

if st.session_state.current_earthquake:
    st.session_state.earthquake_detected = True
    
    eq = st.session_state.current_earthquake
    
    # Alert banner
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
    st.subheader("Step 1: Assess Building Damage")
    
    # NOTE: Replace with your actual Teachable Machine model path
    MODEL_PATH = "model.tflite"  # Download from Teachable Machine as TensorFlow Lite
    
    st.info("""
    **How to get your model:**
    1. Train on Teachable Machine with 3 categories: SAFE, DAMAGED, UNSAFE
    2. Click Export → TensorFlow Lite → Download .tflite file
    3. Upload to your repository or use a shareable link
    """)
    
    # Image input
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📸 Camera**")
        camera_photo = st.camera_input("Take photo")
    
    with col2:
        st.write("**📁 Upload**")
        uploaded_file = st.file_uploader("Choose image", type=["jpg", "jpeg", "png"])
    
    # Process image
    image_to_process = None
    if camera_photo:
        image_to_process = Image.open(camera_photo)
    elif uploaded_file:
        image_to_process = Image.open(uploaded_file)
    
    if image_to_process:
        st.divider()
        st.subheader("Step 2: AI Analysis")
        
        # Display image
        st.image(image_to_process, caption="Building Assessment Photo", use_container_width=True)
        
        if st.button("🔍 Analyze Building Damage", type="primary", use_container_width=True):
            with st.spinner("Analyzing damage..."):
                # Load model and classify
                interpreter = load_model(MODEL_PATH)
                
                if interpreter:
                    predicted_class, confidence, all_predictions = classify_building_damage(
                        image_to_process, 
                        interpreter
                    )
                    
                    st.session_state.assessment_results = {
                        "class": predicted_class,
                        "confidence": confidence,
                        "predictions": all_predictions
                    }
                    st.rerun()
    
    # Display assessment results
    if st.session_state.assessment_results:
        st.divider()
        st.subheader("Step 3: Assessment Report")
        
        result = st.session_state.assessment_results
        damage_class = result['class']
        confidence = result['confidence']
        rec = DAMAGE_RECOMMENDATIONS[damage_class]
        
        # Result card
        st.markdown(f"""
            <div style="background-color: {rec['color']}; color: white; padding: 1.5rem; border-radius: 0.5rem; margin: 1rem 0;">
                <h2>{damage_class}</h2>
                <p><strong>Confidence:</strong> {confidence*100:.1f}%</p>
                <p><strong>Priority:</strong> {rec['priority']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Recommendations
        st.subheader("Recommended Actions")
        for action in rec['actions']:
            st.write(action)
        
        # Additional info
        st.divider()
        
        if damage_class == "UNSAFE":
            st.error("**CRITICAL: Contact emergency services immediately**")
            st.write("- NDRRMC Hotline: 1-800-1-READY (1-800-1-73239)")
            st.write("- Local Emergency Management Office")
            st.write("- Bureau of Fire Protection (BFP)")
        
        elif damage_class == "DAMAGED":
            st.warning("**Building requires professional inspection**")
            st.write("- Contact a licensed structural engineer")
            st.write("- File insurance claim with photographic evidence")
            st.write("- Contact local government for assistance programs")
        
        else:
            st.success("**Building is safe for occupancy**")
            st.write("- Monitor for aftershocks")
            st.write("- Conduct routine maintenance check")
            st.write("- Document for records")
        
        # Clear assessment
        st.divider()
        if st.button("Clear Assessment & Start Over"):
            st.session_state.assessment_results = None
            st.rerun()

else:
    st.info("No significant earthquakes detected in the Philippines in the last hour.")
    st.write("This app will automatically alert when an earthquake (magnitude 4.0+) is detected.")
    
    # Manual test option
    st.divider()
    st.subheader("🧪 Test Mode")
    if st.checkbox("Enable test mode (simulate earthquake)"):
        st.session_state.earthquake_detected = True
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
st.caption("PH Earthquake Response System v1.0 | Data: USGS | AI: TensorFlow Lite + Teachable Machine")
