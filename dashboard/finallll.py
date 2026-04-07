import streamlit as st
import re
import pandas as pd
import plotly.express as px
import numpy as np
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
from streamlit_option_menu import option_menu
from datetime import datetime, timedelta
import requests
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="AroundU | Owner Dashboard", layout="wide")

st.markdown("""
<style>

.stApp {
    background-color: #F8F9FB;
}

[data-testid="stHeader"] {
    background-color: rgba(255, 255, 255, 0);
}

/* Sidebar Style Refactor (Blue Header/Strip Style) */
section[data-testid="stSidebar"] {
    background-color: #F8F9FB !important; /* Make parent clean */
}

section[data-testid="stSidebar"] > div:first-child {
    background-color: #055e9b !important;
    border-radius: 0px 40px 40px 0px !important;
    margin-right: 0px !important;
    height: 96vh !important;
    margin-top: 2vh !important;
    box-shadow: 10px 0 30px rgba(0,0,0,0.1) !important;
}

section[data-testid="stSidebar"] .stMarkdown h1 {
    font-size: 24px !important;
    color: #FFFFFF !important;
    padding-top: 35px !important;
    font-weight: 800 !important;
    margin-bottom: 0px !important;
}

section[data-testid="stSidebar"] .stMarkdown p {
    font-size: 14px !important;
    color: rgba(255, 255, 255, 0.7) !important;
    margin-bottom: 30px !important;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

/* Sidebar Logout Button (Ghost Style) */
div[data-testid="stSidebar"] button {
    background-color: transparent !important;
    border: 1px solid rgba(255, 255, 255, 0.4) !important;
    color: #FFFFFF !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
    margin-top: 30px !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stSidebar"] button:hover {
    background-color: rgba(255, 255, 255, 0.1) !important;
    color: #FFFFFF !important;
    border-color: #FFFFFF !important;
}

/* Sidebar date input and widget styling - no border, seamless */
section[data-testid="stSidebar"] [data-baseweb="base-input"],
section[data-testid="stSidebar"] [data-baseweb="input"],
section[data-testid="stSidebar"] [data-baseweb="input"] > div {
    background-color: rgba(255, 255, 255, 0.12) !important;
    border: none !important;
    outline: none !important;
    border-radius: 10px !important;
    box-shadow: none !important;
}

section[data-testid="stSidebar"] [data-baseweb="input"] input {
    color: #FFFFFF !important;
    background-color: transparent !important;
    border: none !important;
    outline: none !important;
}

section[data-testid="stSidebar"] [data-baseweb="base-input"] svg {
    fill: #FFFFFF !important;
}

/* Sidebar button - make it fully transparent/ghost */
section[data-testid="stSidebar"] .stButton > button {
    background-color: rgba(255,255,255,0.15) !important;
    border: 1.5px solid rgba(255,255,255,0.45) !important;
    color: #FFFFFF !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(255,255,255,0.28) !important;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    color: rgba(255, 255, 255, 0.9) !important;
}

/* KPI Cards */
.kpi-card {
    background: #FFFFFF;
    padding: 24px;
    border-radius: 16px;
    border-top: 4px solid #61A3BB;
    box-shadow: 0 4px 20px rgba(29, 49, 67, 0.08);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: default;
}

.kpi-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(29, 49, 67, 0.12);
    border-top-color: #2F5C85;
}

.kpi-title { 
    font-size: 14px; 
    color: #65797E; 
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
}
.kpi-value { 
    font-size: 36px; 
    font-weight: 800; 
    color: #1D3143; 
    margin: 8px 0;
}
.kpi-delta { 
    font-size: 14px; 
    font-weight: 600;
    color: #61A3BB; 
}

/* Review Cards */
.review-card {
    background: #FFFFFF;
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 20px;
    border: 1px solid #E9ECEF;
    box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    transition: all 0.3s ease;
}

.review-card:hover {
    border-color: #61A3BB;
    box-shadow: 0 8px 24px rgba(97, 163, 187, 0.1);
}

.review-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.user-name {
    font-weight: 700;
    color: #1D3143;
    font-size: 17px;
}

.review-date {
    color: #adb5bd;
    font-size: 13px;
}

.sentiment-badge {
    padding: 6px 14px;
    border-radius: 30px;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
}

.sentiment-positive {
    background-color: #E7F3F7;
    color: #61A3BB;
}

.sentiment-negative {
    background-color: #FEECEB;
    color: #E63946;
}

.review-comment {
    color: #4A5568;
    font-size: 15px;
    line-height: 1.6;
}

</style>
""", unsafe_allow_html=True)


# --- UTILITIES ---
def extract_coordinates(url):
    """
    Client-side coordinate extraction for Google Maps links (including short links).
    """
    if not url: return None, None
    
    try:
        # 1. Resolve short URL if necessary
        resolved_url = url
        if any(domain in url for domain in ["goo.gl", ".page.link", "maps.app.goo.gl"]):
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            # Aggressive redirect following
            session = requests.Session()
            res = session.get(url, allow_redirects=True, headers=headers, timeout=10.0)
            resolved_url = res.url
            
        decoded_url = requests.utils.unquote(resolved_url)
        
        # Super-comprehensive patterns including CID and FTID variations
        patterns = [
            r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)',
            r'@(-?\d+\.\d+),(-?\d+\.\d+)',
            r'[?&]q=([-+]?\d*\.\d+|\d+),([-+]?\d*\.\d+|\d+)',
            r'/([-+]?\d+\.\d+),([-+]?\d+\.\d+)',
            r'll=([-+]?\d+\.\d+),([-+]?\d+\.\d+)',
            r'place/([-+]?\d+\.\d+),([-+]?\d+\.\d+)',
            r'place/.*@([-+]?\d+\.\d+),([-+]?\d+\.\d+)',
            r'(-?\d+\.\d+)\+(-?\d+\.\d+)',
            r'latitude=([-+]?\d+\.\d+)&longitude=([-+]?\d+\.\d+)', # Common in some embedded links
            r'center=([-+]?\d+\.\d+)%2C([-+]?\d+\.\d+)' # Static maps / embedded
        ]

        for text in [resolved_url, decoded_url]:
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return float(match.group(1)), float(match.group(2))
    except Exception as e:
        pass
    return None, None


# --- CONFIGURATION ---
BACKEND_BASE_URL = "https://aroundubackend-production.up.railway.app/api"

# --- AUTHENTICATION LOGIC ---
def login_user(email, password):
    try:
        response = requests.post(
            f"{BACKEND_BASE_URL}/mobile/auth/login",
            data={"username": email.lower().strip(), "password": password}
        )
        if response.status_code == 200:
            return response.json().get("access_token"), None
        else:
            try:
                error_detail = response.json().get("detail", "Invalid credentials")
            except:
                error_detail = response.text or "Unknown error"
            return None, f"Backend Error ({response.status_code}): {error_detail}"
    except Exception as e:
        return None, f"Connection error: {e}"

def logout():
    st.session_state.token = None
    st.rerun()

# --- API HELPERS ---
def get_headers():
    return {"Authorization": f"Bearer {st.session_state.get('token')}"}

def handle_api_error(response):
    if response.status_code == 401:
        st.warning("Session expired. Please login again.")
        logout()
    return None


# --- DATA FETCHING ---
@st.cache_data(ttl=30)
def fetch_dashboard_data(start_date, end_date):
    try:
        params = {"start_date": start_date, "end_date": end_date}
        res = requests.get(f"{BACKEND_BASE_URL}/owner/dashboard", params=params, headers=get_headers())
        if res.status_code == 200: return res.json()
        handle_api_error(res)
    except: pass
    return {"visits": 0, "saves": 0, "calls": 0, "directions": 0}

@st.cache_data(ttl=30)
def fetch_analytics_data(start_date, end_date):
    try:
        params = {"start_date": start_date, "end_date": end_date}
        res = requests.get(f"{BACKEND_BASE_URL}/owner/analytics", params=params, headers=get_headers())
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df.columns = [col.capitalize() for col in df.columns]
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
            return df
        handle_api_error(res)
    except: pass
    return pd.DataFrame(columns=['Date', 'Visits', 'Saves', 'Directions', 'Calls', 'Review_sentiment'])

@st.cache_data(ttl=30)
def fetch_chatbot_stats(start_date, end_date):
    try:
        params = {"start_date": start_date, "end_date": end_date}
        res = requests.get(f"{BACKEND_BASE_URL}/owner/chatbot-stats", params=params, headers=get_headers())
        if res.status_code == 200: return res.json()
        handle_api_error(res)
    except: pass
    return {"queries": 0, "success_rate": 0.0}

@st.cache_data(ttl=60)
def fetch_anomalies():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/owner/anomalies", headers=get_headers())
        if res.status_code == 200: return res.json()
        handle_api_error(res)
    except: pass
    return []

@st.cache_data(ttl=60)
def fetch_anomalies_summary():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/owner/anomalies/summary", headers=get_headers())
        if res.status_code == 200: return res.json()
        handle_api_error(res)
    except: pass
    return {}

@st.cache_data(ttl=60)
def fetch_opportunities():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/owner/opportunities", headers=get_headers())
        if res.status_code == 200: return res.json()
        handle_api_error(res)
    except: pass
    return []

def fetch_my_place():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/owner/my-place", headers=get_headers())
        if res.status_code == 200: 
            return res.json()
        handle_api_error(res)
    except Exception as e:
        st.error(f"Connection error: {e}")
    return None

def fetch_my_places():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/owner/my-places", headers=get_headers())
        if res.status_code == 200: return res.json()
        handle_api_error(res)
    except: pass
    return []

def add_branch_request(data):
    try:
        res = requests.post(f"{BACKEND_BASE_URL}/owner/add-branch", json=data, headers=get_headers())
        if res.status_code == 200:
            st.success("✅ Branch added successfully!")
            st.rerun()
            return True
        st.error(f"❌ Failed to add branch: {res.text}")
    except Exception as e:
        st.error(f"Error: {e}")
    return False

@st.cache_data(ttl=300)
def fetch_categories():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/mobile/categories")
        if res.status_code == 200: return res.json()
    except: pass
    return []

def update_place_details(place_id, data):
    try:
        res = requests.put(f"{BACKEND_BASE_URL}/dashboard/places/{place_id}", json=data, headers=get_headers())
        if res.status_code == 200:
            st.success("✅ Place updated successfully!")
            st.cache_data.clear()
            st.rerun()
            return True
        st.error(f"❌ Failed to update: {res.text}")
    except Exception as e:
        st.error(f"Error: {e}")
def delete_place_image(image_id):
    try:
        res = requests.delete(f"{BACKEND_BASE_URL}/dashboard/upload/image/{image_id}", headers=get_headers())
        if res.status_code == 204:
            st.success("🗑️ Image deleted!")
            st.cache_data.clear()
            st.rerun()
            return True
        st.error(f"❌ Failed to delete: {res.text}")
    except Exception as e:
        st.error(f"Error: {e}")
    return False

def upload_image(place_id, image_type, file, caption=None):
    try:
        data = {"place_id": place_id, "image_type": image_type}
        if caption: data["caption"] = caption
        
        files = {"file": (file.name, file.getvalue(), file.type)}
        res = requests.post(f"{BACKEND_BASE_URL}/dashboard/upload/place-image", data=data, files=files, headers=get_headers())
        
        if res.status_code == 201:
            st.success(f"✅ {image_type.capitalize()} photo uploaded!")
            st.cache_data.clear()
            st.rerun()
            return True
        st.error(f"❌ Upload failed: {res.text}")
    except Exception as e:
        st.error(f"Upload error: {e}")
    return False

@st.cache_data(ttl=30)
def fetch_review_data(start_date, end_date):
    try:
        params = {"start_date": start_date, "end_date": end_date}
        res = requests.get(f"{BACKEND_BASE_URL}/owner/reviews", params=params, headers=get_headers())
        if res.status_code == 200: return res.json()
        handle_api_error(res)
    except: pass
    return {"positive": 0, "negative": 0}

@st.cache_data(ttl=30)
def fetch_review_list(start_date, end_date):
    try:
        params = {"start_date": start_date, "end_date": end_date}
        res = requests.get(f"{BACKEND_BASE_URL}/owner/reviews/list", params=params, headers=get_headers())
        if res.status_code == 200: return res.json()
        handle_api_error(res)
        st.error(f"Failed to fetch reviews: Backend returned {res.status_code}")
    except Exception as e:
        st.error(f"Error fetching reviews: {e}")
    return []

@st.cache_data(ttl=30)
def fetch_location_data():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/owner/location-heatmap", headers=get_headers())
        if res.status_code == 200: return pd.DataFrame(res.json())
        handle_api_error(res)
    except: pass
    return pd.DataFrame()

@st.cache_data(ttl=30)
def fetch_interactions_locations():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/owner/interactions-locations", headers=get_headers())
        if res.status_code == 200: return pd.DataFrame(res.json())
        handle_api_error(res)
    except: pass
    return pd.DataFrame()

@st.cache_data(ttl=30)
def fetch_active_visitors():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/owner/active-visitors", headers=get_headers())
        if res.status_code == 200: return res.json()
        handle_api_error(res)
    except: pass
    return []

@st.cache_data(ttl=30)
def fetch_peak_hour():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/owner/peak-hour", headers=get_headers())
        if res.status_code == 200: return res.json()
        handle_api_error(res)
    except: pass
    return {}

@st.cache_data(ttl=60)
def fetch_location_summary():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/owner/location-summary", headers=get_headers())
        if res.status_code == 200: return res.json()
        handle_api_error(res)
    except: pass
    return {}

def build_location_map(all_locations, active_visitors, show_pins, show_heatmap, places_list, center_lat, center_lon):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="CartoDB positron")
    
    for p in places_list:
        lat = p.get("latitude")
        lon = p.get("longitude")
        name = p.get("name") or "Branch"
        address = p.get("address") or ""
        if lat and lon:
            tooltip_html = f"📍 <b>{name}</b><br>{address}" if address else f"📍 <b>{name}</b>"
            folium.Marker(
                [float(lat), float(lon)], 
                tooltip=tooltip_html, 
                icon=folium.Icon(color="red", icon="home", prefix="fa")
            ).add_to(m)

    if show_heatmap and not all_locations.empty:
        heat_data = [[row['lat'], row['lon']] for index, row in all_locations.iterrows() if pd.notna(row['lat']) and pd.notna(row['lon'])]
        if heat_data:
            HeatMap(
                heat_data, 
                radius=22, 
                blur=18,
                min_opacity=0.35,
                gradient={"0.3": "#055e9b", "0.6": "#61A3BB", "1.0": "#E63946"}
            ).add_to(m)

    if show_pins and active_visitors:
        for visitor in active_visitors:
            if visitor.get("lat") and visitor.get("lon"):
                cluster_str = visitor.get('cluster', 'N/A')
                folium.CircleMarker(
                    location=[visitor["lat"], visitor["lon"]],
                    radius=8,
                    color="#055e9b",
                    fill=True,
                    fill_color="#61A3BB",
                    fill_opacity=0.9,
                    tooltip=f"👤 Active Visitor (Cluster: {cluster_str})"
                ).add_to(m)

    return m

# --- MAIN APP LOGIC ---
if 'token' not in st.session_state:
    st.session_state.token = None

if st.session_state.token is None:
    # --- LOGIN SCREEN ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(os.path.join(os.path.dirname(__file__), "logo.jpeg"), width=100) # Placeholder for logo
        st.title("🏙️ Welcome to AroundU")
        st.subheader("Owner Dashboard Login")
        
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                token, error_msg = login_user(email, password)
                if token:
                    st.session_state.token = token
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(error_msg or "Invalid email or password.")
    st.stop()

# =========================
# SIDEBAR
# =========================
my_place = fetch_my_place()
place_name = my_place.get("name", "AroundU") if my_place else "AroundU"

with st.sidebar:
    st.title(f"🏙️ {place_name}")
    st.caption("Beni Suef Business Intelligence")

    selected = option_menu(
        None,
        options=["Dashboard", "Customer Insights", "Operations", "Location Logic", "Manage Place"],
        icons=['house-door-fill', 'chat-square-text-fill', 'lightning-fill', 'geo-fill', 'gear-fill'],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"background-color": "#055e9b !important", "padding": "0px !important"},
            "icon": {"color": "#FFFFFF", "font-size": "18px"},
            "nav-link": {
                "color": "#FFFFFF", "font-size": "15px",
                "text-align": "left", "margin": "8px 0px",
                "padding": "12px 18px",
                "border-radius": "14px",
                "font-weight": "500",
                "--hover-color": "rgba(255, 255, 255, 0.1)",
            },
            "nav-link-selected": {
                "background-color": "#FFFFFF !important",
                "color": "#055e9b !important", 
                "font-weight": "700",
                "box-shadow": "0px 4px 10px rgba(0,0,0,0.1) !important"
            }
        }
    )

    st.markdown("---")
    
    st.markdown("### 📅 Select Date Range")

    # Force-style the date input and button to match blue sidebar (no visible borders)
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] .stDateInput div[data-baseweb="input"],
    section[data-testid="stSidebar"] .stDateInput div[data-baseweb="base-input"] {
        background-color: rgba(255,255,255,0.12) !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        border-radius: 10px !important;
    }
    section[data-testid="stSidebar"] .stDateInput input {
        color: #FFFFFF !important;
        background-color: transparent !important;
        border: none !important;
        outline: none !important;
    }
    section[data-testid="stSidebar"] .stDateInput span,
    section[data-testid="stSidebar"] .stDateInput svg {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background-color: rgba(255,255,255,0.15) !important;
        border: none !important;
        outline: none !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255,255,255,0.25) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Using fixed range as fallback, actual data is fetched per period
    max_date = datetime.now()
    date_range = st.date_input(
        "Choose period:",
        value=(max_date - timedelta(days=30), max_date),
        max_value=max_date
    )

    if st.button("🚪 Logout", use_container_width=True):
        logout()

# =========================
# FILTER LOGIC
# =========================
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date = date_range[0].strftime("%Y-%m-%d")
    end_date = date_range[1].strftime("%Y-%m-%d")
    
    # Calculate previous period for deltas
    period_days = (date_range[1] - date_range[0]).days + 1
    prev_end_date_dt = date_range[0] - timedelta(days=1)
    prev_start_date_dt = prev_end_date_dt - timedelta(days=period_days - 1)
    
    prev_start_date = prev_start_date_dt.strftime("%Y-%m-%d")
    prev_end_date = prev_end_date_dt.strftime("%Y-%m-%d")
else:
    st.warning("Please select a valid date range in the sidebar.")
    st.stop()

# =========================
# 1️⃣ DASHBOARD
# =========================
if selected == "Dashboard":
    st.title("📊 Business Performance Overview")

    data = fetch_dashboard_data(start_date, end_date)
    prev_data = fetch_dashboard_data(prev_start_date, prev_end_date)

    m1, m2, m3, m4 = st.columns(4)

    def get_delta_display(curr, prev):
        if prev == 0: return "0%"
        diff = ((curr - prev) / prev) * 100
        return f"{int(diff):+}%"

    m1.markdown(f"""<div class="kpi-card"><div class="kpi-title">Total Visits</div>
    <div class="kpi-value">{data['visits']}</div>
    <div class="kpi-delta">{get_delta_display(data['visits'], prev_data['visits'])}</div></div>""", unsafe_allow_html=True)

    m2.markdown(f"""<div class="kpi-card"><div class="kpi-title">Place Saved</div>
    <div class="kpi-value">{data['saves']}</div>
    <div class="kpi-delta">{get_delta_display(data['saves'], prev_data['saves'])}</div></div>""", unsafe_allow_html=True)

    m3.markdown(f"""<div class="kpi-card"><div class="kpi-title">Direction Clicks</div>
    <div class="kpi-value">{data['directions']}</div>
    <div class="kpi-delta">{get_delta_display(data['directions'], prev_data['directions'])}</div></div>""", unsafe_allow_html=True)

    m4.markdown(f"""<div class="kpi-card"><div class="kpi-title">Call Clicks</div>
    <div class="kpi-value">{data['calls']}</div>
    <div class="kpi-delta">{get_delta_display(data['calls'], prev_data['calls'])}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🚀 Growth Analysis (Current vs Previous Period)")
        df_curr = fetch_analytics_data(start_date, end_date)
        df_prev = fetch_analytics_data(prev_start_date, prev_end_date)
        
        metrics = ['visits', 'saves', 'calls']
        curr_vals = [data[m] for m in metrics]
        prev_vals = [prev_data[m] for m in metrics]
        
        growth_data = pd.DataFrame({
            'Metric': [m.capitalize() for m in metrics] * 2,
            'Value': curr_vals + prev_vals,
            'Period': ['Selected Period'] * 3 + ['Previous Period'] * 3
        })
        fig_growth = px.bar(growth_data, x='Metric', y='Value', color='Period',
            barmode='group', text='Value', text_auto='.2s',
            color_discrete_map={'Selected Period': '#1D3143', 'Previous Period': '#61A3BB'},
            template="plotly_white")
        fig_growth.update_traces(textposition='outside', marker_line_width=0)
        fig_growth.update_layout(yaxis_title='Total Count', xaxis_title='',
            margin=dict(t=40, b=40, l=40, r=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_growth, use_container_width=True)

    with col_right:
        st.subheader("🤖 Chatbot Stats")
        bot_stats = fetch_chatbot_stats(start_date, end_date)
        st.metric("Bot Resolution Rate", f"{bot_stats['success_rate']:.1f}%")
        query_types = pd.DataFrame({'Type': ['Menu', 'Hours', 'Order Status', 'General'], 'Val': [40, 30, 20, 10]})
        fig_pie = px.pie(query_types, values='Val', names='Type', hole=0.6, color='Type',
            color_discrete_map={'Menu': '#1D3143', 'Hours': '#2F5C85', 'Order Status': '#61A3BB', 'General': '#F8F9FA'})
        fig_pie.update_traces(textinfo='percent', textfont_size=14,
            marker=dict(line=dict(color='#FFFFFF', width=2)))
        fig_pie.update_layout(legend_title_text='', margin=dict(t=20, b=20, l=20, r=20), height=400)
# =========================
# 2️⃣ CUSTOMER INSIGHTS
# =========================
elif selected == "Customer Insights":

    st.title("🤖 Customer & Review Analysis")

    # Fetch data
    reviews = fetch_review_data(start_date, end_date)
    review_list = fetch_review_list(start_date, end_date)

    c1, c2 = st.columns(2)

    # -----------------------
    # Sentiment Chart
    # -----------------------
    with c1:
        st.subheader("Customer Sentiment Overview")

        positive = reviews.get("positive", 0)
        negative = reviews.get("negative", 0)

        if reviews:
            # Map API keys to human readable labels
            sentiment_map = {
                'positive': 'Positive',
                'negative': 'Negative',
                'neutral': 'Neutral',
                'unknown': 'Unknown'
            }
            
            data_list = []
            for k, v in reviews.items():
                if v > 0:
                    data_list.append({'Sentiment': sentiment_map.get(k, k.capitalize()), 'Count': v})
            
            if data_list:
                sentiment_df = pd.DataFrame(data_list)
                fig_reviews = px.bar(
                    sentiment_df,
                    x="Sentiment",
                    y="Count",
                    color="Sentiment",
                    color_discrete_map={
                        "Positive": "#61A3BB",
                        "Negative": "#E63946",
                        "Neutral": "#2F5C85",
                        "Unknown": "#F8F9FA"
                    },
                    template="plotly_white"
                )
                fig_reviews.update_traces(marker_line_width=0)
                st.plotly_chart(fig_reviews, use_container_width=True)
            else:
                st.info("No reviews with sentiment data available.")
        else:
            st.info("No review data available for this period.")

    # -----------------------
    # AI Anomaly Detection (Premium Table UI)
    # -----------------------
    st.markdown("---")
    st.markdown("""
    <style>
    .anomaly-section-title {
        font-size: 22px;
        font-weight: 800;
        color: #1D3143;
        margin-bottom: 4px;
    }
    .anomaly-table-header {
        display: grid;
        grid-template-columns: 2fr 3fr 1fr 1.2fr;
        background: #1D3143;
        color: white;
        padding: 10px 16px;
        border-radius: 10px 10px 0 0;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .anomaly-row {
        display: grid;
        grid-template-columns: 2fr 3fr 1fr 1.2fr;
        padding: 12px 16px;
        border-bottom: 1px solid #f0f0f0;
        align-items: center;
        transition: background 0.2s;
        background: white;
    }
    .anomaly-row:hover { background: #f8fafc; }
    .anomaly-row:last-child { border-radius: 0 0 10px 10px; border-bottom: none; }
    .anomaly-name { font-weight: 700; color: #1D3143; font-size: 14px; }
    .anomaly-detail { color: #4a5568; font-size: 13px; line-height: 1.4; }
    .severity-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        text-align: center;
    }
    .sev-high   { background: #ffe5e5; color: #c0392b; border: 1.5px solid #e74c3c; }
    .sev-medium { background: #fff3e0; color: #d35400; border: 1.5px solid #e67e22; }
    .sev-low    { background: #e8f5e9; color: #27ae60; border: 1.5px solid #2ecc71; }
    .category-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        background: #eef2ff;
        color: #3949ab;
    }
    .cat-user     { background: #fce4ec; color: #c2185b; }
    .cat-place    { background: #e3f2fd; color: #1565c0; }
    .cat-district { background: #f3e5f5; color: #6a1b9a; }
    .priority-block {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 14px 18px;
        border-radius: 12px;
        background: white;
        border: 1px solid #e9ecef;
        margin-bottom: 10px;
    }
    .priority-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        margin-top: 3px;
        flex-shrink: 0;
    }
    .dot-high   { background: #e74c3c; }
    .dot-medium { background: #e67e22; }
    .dot-low    { background: #2ecc71; }
    .priority-label { font-weight: 700; font-size: 14px; color: #1D3143; }
    .priority-types { font-size: 13px; color: #4a5568; margin-top: 2px; }
    .priority-impact { font-size: 12px; color: #7f8c8d; margin-top: 4px; font-style: italic; }
    .anomaly-table-wrapper {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(29, 49, 67, 0.08);
        border: 1px solid #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="anomaly-section-title">🚨 AroundU Anomaly Detection</div>', unsafe_allow_html=True)
    st.caption("AI-powered detection of abnormal activity across places, users, and districts.")

    anomalies    = fetch_anomalies()
    summary      = fetch_anomalies_summary()
    opportunities = fetch_opportunities()

    # ── Normalize anomaly list ──────────────────────────────────────────
    def _extract_anomalies(raw):
        if not raw:
            return []
        if isinstance(raw, dict):
            return raw.get("anomalies", raw.get("details", raw.get("visits", [])))
        if isinstance(raw, list):
            return raw
        return []

    # Prefer summary.details (richer) over raw anomalies list
    detail_items = _extract_anomalies(summary) if summary else _extract_anomalies(anomalies)
    # Also check summary["details"]
    if isinstance(summary, dict) and summary.get("details"):
        detail_items = summary["details"]

    # ── Severity → CSS class mapping ───────────────────────────────────
    SEV_CLASS  = {"high": "sev-high", "medium": "sev-medium", "low": "sev-low"}
    CAT_CLASS  = {"user": "cat-user", "place": "cat-place", "district": "cat-district"}
    SEV_LABEL  = {"high": "High", "medium": "Medium", "low": "Low"}

    # ── Fallback display names for known anomaly types ──────────────────
    KNOWN_DISPLAY = {
        "traffic_spike":      ("Traffic Spike",      "place",    "high"),
        "sudden_drop":        ("Sudden Drop",         "place",    "high"),
        "unusual_hours":      ("Unusual Hours",       "place",    "medium"),
        "geographic_anomaly": ("Geographic Anomaly",  "place",    "low"),
        "bot_behavior":       ("Bot Behavior",        "user",     "high"),
        "gps_spoofing":       ("GPS Spoofing",        "user",     "low"),
        "impossible_travel":  ("Impossible Travel",   "user",     "low"),
        "district_spike":     ("District Spike",      "district", "medium"),
        "dead_zone":          ("Dead Zone",           "district", "high"),
    }

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Anomaly table or empty state ───────────────────────────────────
    if detail_items:
        table_rows_html = ""
        for item in detail_items:
            if not isinstance(item, dict):
                continue

            raw_type  = str(item.get("anomaly_type", item.get("type", "unknown"))).lower().replace(" ", "_").replace("-", "_")
            defaults  = KNOWN_DISPLAY.get(raw_type, (raw_type.replace("_", " ").title(), "place", "medium"))

            display_name = defaults[0]
            category     = str(item.get("category", defaults[1])).lower()
            severity_raw = str(item.get("severity", defaults[2])).lower()
            details_txt  = item.get("details", item.get("description", "—"))

            sev_cls = SEV_CLASS.get(severity_raw, "sev-medium")
            cat_cls = CAT_CLASS.get(category, "cat-place")
            sev_lbl = SEV_LABEL.get(severity_raw, severity_raw.capitalize())

            table_rows_html += f"""
<div class="anomaly-row">
<div class="anomaly-name">{display_name}</div>
<div class="anomaly-detail">{details_txt}</div>
<div><span class="severity-badge {sev_cls}">{sev_lbl}</span></div>
<div><span class="category-pill {cat_cls}">{category.capitalize()}</span></div>
</div>"""

        st.markdown(f"""
<div class="anomaly-table-wrapper">
<div class="anomaly-table-header">
<div>Anomaly</div>
<div>Details</div>
<div>Level</div>
<div>Category</div>
</div>
{table_rows_html}
</div>
""", unsafe_allow_html=True)

    else:
        st.success("✅ No anomalies detected. All systems normal.")

    # ── Priority Summary ───────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📊 Priority Summary")

    if detail_items:
        high_items   = [a for a in detail_items if isinstance(a, dict) and str(a.get("severity","")).lower() == "high"]
        med_items    = [a for a in detail_items if isinstance(a, dict) and str(a.get("severity","")).lower() == "medium"]
        low_items    = [a for a in detail_items if isinstance(a, dict) and str(a.get("severity","")).lower() == "low"]

        def _names(lst):
            return ", ".join(
                str(a.get("anomaly_type", a.get("type","?"))).replace("_"," ").replace("-", " ").title()
                for a in lst[:4]
            ) or "—"

        p_col1, p_col2 = st.columns(2)

        with p_col1:
            if high_items:
                st.markdown(f"""
<div class="priority-block">
<div class="priority-dot dot-high"></div>
<div>
<div class="priority-label">🔴 High Priority ({len(high_items)})</div>
<div class="priority-types">{_names(high_items)}</div>
<div class="priority-impact">Immediate action required — affects data accuracy</div>
</div>
</div>""", unsafe_allow_html=True)

            if med_items:
                st.markdown(f"""
<div class="priority-block">
<div class="priority-dot dot-medium"></div>
<div>
<div class="priority-label">🟠 Medium Priority ({len(med_items)})</div>
<div class="priority-types">{_names(med_items)}</div>
<div class="priority-impact">Could be real event or fake visits — needs review</div>
</div>
</div>""", unsafe_allow_html=True)

        with p_col2:
            if low_items:
                st.markdown(f"""
<div class="priority-block">
<div class="priority-dot dot-low"></div>
<div>
<div class="priority-label">🟢 Low Priority ({len(low_items)})</div>
<div class="priority-types">{_names(low_items)}</div>
<div class="priority-impact">Monitor — low immediate risk</div>
</div>
</div>""", unsafe_allow_html=True)

            total   = len(detail_items)
            urgent  = len(high_items)
            if isinstance(summary, dict):
                total  = summary.get("total_anomalies", total)
                urgent = summary.get("urgent_anomalies", urgent)

            st.markdown(f"""
<div class="priority-block" style="border-left: 4px solid #2F5C85;">
<div>
<div class="priority-label">📈 Summary</div>
<div class="priority-types">
Total: <strong>{total}</strong> anomalies &nbsp;|&nbsp;
Urgent: <strong style="color:#e74c3c">{urgent}</strong>
</div>
</div>
</div>""", unsafe_allow_html=True)
    else:
        st.info("No anomaly data to summarise.")

    # ── Opportunities column ───────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🎯 AI Opportunities")
    if opportunities:
        opp_cols = st.columns(min(3, len(opportunities)))
        for idx, opp in enumerate(opportunities[:6]):
            title = opp.get("title", opp.get("opportunity_type", "New Opportunity")).replace("_", " ").title()
            desc  = opp.get("description", str(opp))
            with opp_cols[idx % len(opp_cols)]:
                st.markdown(f"""
<div class="priority-block" style="border-left:4px solid #61A3BB; flex-direction:column; gap:4px;">
<div class="priority-label">💡 {title}</div>
<div class="priority-types">{desc}</div>
</div>""", unsafe_allow_html=True)
    else:
        st.info("No new opportunities identified at the moment.")

    st.markdown("---")

    # -----------------------
    # Total Reviews Card
    # -----------------------
    with c2:

        st.subheader("Review Ratings Overview")

        total_reviews = sum(reviews.values()) if reviews else 0

        st.markdown(f"""
        <div style="background:#F8F9FA; padding:20px; border-radius:10px; border-left:5px solid #2F5C85;">
            <p style="color:#65797E; margin-bottom:5px;">Total Reviews in period</p>
            <h2 style="color:#1D3143; margin:0;">{total_reviews}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # -----------------------
    # Review List
    # -----------------------
    st.subheader("💬 Customer Reviews")

    if not review_list:

        st.info("No reviews available for this period.")

    else:

        for rev in review_list:

            sentiment_class = (
                "sentiment-positive"
                if rev["sentiment"] == "positive"
                else "sentiment-negative"
            )

            # Format date
            date_str = rev["date"]

            try:
                if isinstance(date_str, str):
                    date_obj = datetime.strptime(
                        date_str.split("T")[0],
                        "%Y-%m-%d"
                    )
                    date_str = date_obj.strftime("%b %d, %Y")
            except:
                pass

            st.markdown(f"""
            <div class="review-card">
                <div class="review-header">
                    <div>
                        <span class="user-name">{rev["user_name"]}</span>
                        <span style="margin-left:10px;color:#FFD700;">{rev["stars"]}</span>
                    </div>
                    <span class="sentiment-badge {sentiment_class}">{rev["sentiment"]}</span>
                </div>
                <div class="review-date">{date_str}</div>
                <div class="review-comment">{rev["comment"]}</div>
            </div>
            """, unsafe_allow_html=True)

# =========================
# 5️⃣ MANAGE PLACE
# =========================
elif selected == "Manage Place":
    st.title("⚙️ Manage Your Place & Branches")
    st.info("Update your business details and manage all your locations.")
    
    places = fetch_my_places()
    categories = fetch_categories()
    
    if places and categories:
        # --- BRANCH SELECTOR ---
        if len(places) > 1:
            branch_names = [f"{p['name']} - {p['address'] or 'No Address'}" for p in places]
            selected_idx = st.selectbox("📍 Select Branch to Edit", range(len(branch_names)), 
                                        format_func=lambda x: branch_names[x])
            place = places[selected_idx]
            st.divider()
        else:
            place = places[0]

        # --- ADD NEW BRANCH ---
        with st.expander("➕ Add New Branch", expanded=False):
            st.write("This will create a new location for your business using your existing images and details.")
            new_addr = st.text_input("Branch Address", placeholder="e.g. Al-Horreya St, Beni Suef")
            
            st.markdown("---")
            col_nb1, col_nb2 = st.columns([0.7, 0.3], vertical_alignment="bottom")
            with col_nb1:
                new_link = st.text_input("Google Maps Link", key="new_branch_link", placeholder="https://www.google.com/maps/...")
            
            # --- AUTO RESOLVE LOGIC FOR NEW BRANCH ---
            if new_link and new_link != st.session_state.get('last_new_branch_link'):
                with st.spinner("📍 Smart-extracting..."):
                    nlat, nlon = extract_coordinates(new_link)
                    if nlat and nlon:
                        st.session_state.new_branch_lat = nlat
                        st.session_state.new_branch_lon = nlon
                        st.toast(f"✅ Coordinates found: {nlat}, {nlon}", icon="📍")
                    else:
                        st.toast("⚠️ Could not extract. Check link or use 'Resolve' button.", icon="❓")
                    
                    st.session_state.last_new_branch_link = new_link
                    st.rerun()

            with col_nb2:
                if st.button("📍 Resolve", key="resolve_new_branch"):
                    if new_link:
                        nlat, nlon = extract_coordinates(new_link)
                        if nlat and nlon:
                            st.session_state.new_branch_lat = nlat
                            st.session_state.new_branch_lon = nlon
                            st.success("Coordinates extracted!")
                            st.rerun()
                        else:
                            st.error("Invalid link!")
                    else:
                        st.warning("Enter link!")

            # Initialize new branch coords
            if 'new_branch_lat' not in st.session_state:
                st.session_state.new_branch_lat = 0.0
                st.session_state.new_branch_lon = 0.0

            with st.expander("Raw Coordinates (Optional)"):
                c_nb1, c_nb2 = st.columns(2)
                with c_nb1:
                    nb_lat = st.number_input("Latitude", value=st.session_state.new_branch_lat, format="%.6f", key="nb_lat_input")
                with c_nb2:
                    nb_lon = st.number_input("Longitude", value=st.session_state.new_branch_lon, format="%.6f", key="nb_lon_input")
                st.session_state.new_branch_lat = nb_lat
                st.session_state.new_branch_lon = nb_lon

            if st.button("Create New Branch", type="primary", use_container_width=True):
                # Auto-resolve if needed
                curr_lat = st.session_state.new_branch_lat
                curr_lon = st.session_state.new_branch_lon
                
                if (curr_lat == 0 or curr_lon == 0) and new_link:
                    with st.spinner("Extracting coordinates from link..."):
                        extracted_lat, extracted_lon = extract_coordinates(new_link)
                        if extracted_lat and extracted_lon:
                            curr_lat, curr_lon = extracted_lat, extracted_lon
                
                if curr_lat != 0:
                    if add_branch_request({
                        "location_link": new_link, 
                        "address": new_addr,
                        "latitude": curr_lat,
                        "longitude": curr_lon
                    }):
                        # Clean up session state ONLY on success
                        if 'new_branch_lat' in st.session_state: del st.session_state.new_branch_lat
                        if 'new_branch_lon' in st.session_state: del st.session_state.new_branch_lon
                        st.rerun()
                else:
                    st.error("Please provide a valid location (Link or Coordinates). Use the 'Resolve' button if needed.")

        # Map category name to ID for the selectbox
        cat_options = {c['name']: c['id'] for c in categories}
        current_cat_name = next((name for name, id in cat_options.items() if id == place.get('category_id')), "Cafe")
        
        # Initialize session state for phone numbers if not present or if branch changed
        if 'current_place_id' not in st.session_state or st.session_state.current_place_id != place.get('id'):
            st.session_state.current_place_id = place.get('id')
            st.session_state.phone_list = place.get("phone") if isinstance(place.get("phone"), list) else ([place.get("phone")] if place.get("phone") else [""])

        # Display form fields (no st.form to allow interactive buttons)
        st.markdown("### 📝 Business Basics")
        name = st.text_input("Business Name", value=place.get("name", ""))
        description = st.text_area("Description", value=place.get("description", ""), height=150)
        
        # --- CATEGORY DROPDOWN ---
        selected_cat_name = st.selectbox("Category", options=list(cat_options.keys()), index=list(cat_options.keys()).index(current_cat_name) if current_cat_name in cat_options else 0)
        
        address = st.text_input("Address", value=place.get("address", ""))
        
        # --- DYNAMIC PHONE SECTION ---
        st.markdown("### 📞 Phone Numbers")
        st.caption("Add one or more contact numbers for your business.")
        
        new_phone_list = []
        for i, ph in enumerate(st.session_state.phone_list):
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                updated_ph = st.text_input(f"Phone {i+1}", value=ph, key=f"phone_input_{i}", label_visibility="collapsed")
                new_phone_list.append(updated_ph)
            with col2:
                if st.button("🗑️", key=f"del_phone_{i}", help="Remove this number"):
                    st.session_state.phone_list.pop(i)
                    st.rerun()
        
        st.session_state.phone_list = new_phone_list

        if st.button("➕ Add Phone", type="secondary"):
            st.session_state.phone_list.append("")
            st.rerun()

        website = st.text_input("Website", value=place.get("website", ""))
        
        st.markdown("### 📍 Location")
        st.info("Paste a Google Maps link below, then click '📍 Resolve Link' to automatically fill coordinates.")
        
        col_l1, col_l2 = st.columns([0.7, 0.3], vertical_alignment="bottom")
        with col_l1:
            loc_link = st.text_input("Google Maps Link", placeholder="https://www.google.com/maps/...", key="loc_link_input")
        
        # --- AUTO RESOLVE LOGIC FOR EDITING ---
        if loc_link and loc_link != st.session_state.get(f"last_link_{place.get('id')}"):
            with st.spinner("📍 Detecting new location..."):
                plat, plon = extract_coordinates(loc_link)
                if plat and plon:
                    st.session_state[f"lat_{place.get('id')}"] = plat
                    st.session_state[f"lon_{place.get('id')}"] = plon
                    st.toast("✅ Location updated!", icon="📍")
                
                st.session_state[f"last_link_{place.get('id')}"] = loc_link
                st.rerun()

        with col_l2:
            if st.button("📍 Resolve", use_container_width=True):
                if loc_link:
                    plat, plon = extract_coordinates(loc_link)
                    if plat and plon:
                        st.session_state[f"lat_{place.get('id')}"] = plat
                        st.session_state[f"lon_{place.get('id')}"] = plon
                        st.success("Coordinates updated!")
                        st.rerun()
                    else:
                        st.error("Invalid link!")
                else:
                    st.warning("Enter link!")

        # Initialize coordinates in session state if not there
        if f"lat_{place.get('id')}" not in st.session_state:
            st.session_state[f"lat_{place.get('id')}"] = place.get("latitude", 0.0)
            st.session_state[f"lon_{place.get('id')}"] = place.get("longitude", 0.0)

        with st.expander("Raw Coordinates (Optional)"):
            c1, c2 = st.columns(2)
            with c1:
                final_lat = st.number_input("Latitude", value=st.session_state[f"lat_{place.get('id')}"], 
                                         format="%.6f", key=f"lat_input_{place.get('id')}")
            with c2:
                final_lon = st.number_input("Longitude", value=st.session_state[f"lon_{place.get('id')}"], 
                                         format="%.6f", key=f"lon_input_{place.get('id')}")
            
            # Keep session state updated if user typed manually
            st.session_state[f"lat_{place.get('id')}"] = final_lat
            st.session_state[f"lon_{place.get('id')}"] = final_lon
        
        # --- SOCIAL MEDIA LINKS ---
        st.markdown("### 📱 Social Media")
        with st.expander("Social Media & Contact Links"):
            facebook = st.text_input("Facebook URL", value=place.get("facebook_url", ""))
            instagram = st.text_input("Instagram URL", value=place.get("instagram_url", ""))
            tiktok = st.text_input("TikTok URL", value=place.get("tiktok_url", ""))
            whatsapp = st.text_input("WhatsApp Number", value=place.get("whatsapp_number", ""), help="e.g. +201234567890")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Changes", use_container_width=True, type="primary"):
            # Clean empty phones
            valid_phones = [p.strip() for p in st.session_state.phone_list if p.strip()]
            
            update_data = {
                "name": name,
                "description": description,
                "category_id": cat_options[selected_cat_name],
                "address": address,
                "phone": valid_phones,
                "website": website,
                "latitude": st.session_state.get(f"lat_{place.get('id')}", place.get("latitude")),
                "longitude": st.session_state.get(f"lon_{place.get('id')}", place.get("longitude")),
                "facebook_url": facebook,
                "instagram_url": instagram,
                "whatsapp_number": whatsapp,
                "tiktok_url": tiktok
            }
            if loc_link:
                update_data["location_link"] = loc_link
            
            if loc_link:
                update_data["location_link"] = loc_link
            
            if update_place_details(place.get("id"), update_data):
                # Only clear session state after a confirmed success to force re-fetch
                if f"lat_{place.get('id')}" in st.session_state: del st.session_state[f"lat_{place.get('id')}"]
                if f"lon_{place.get('id')}" in st.session_state: del st.session_state[f"lon_{place.get('id')}"]
                st.rerun()
        
        st.markdown("---")
        st.subheader("📸 Media Gallery")
        
        # Split images by type
        all_images = place.get("images", [])
        place_imgs = [img for img in all_images if img.get("image_type") == "place"]
        menu_imgs = [img for img in all_images if img.get("image_type") == "menu"]
        
        # --- PLACE PHOTOS ---
        st.markdown("### 🏢 Place Photos")
        st.caption("Upload interior or exterior photos of your business.")
        
        with st.expander("Upload New Place Photo", expanded=False):
            place_file = st.file_uploader("Choose a photo", type=['png', 'jpg', 'jpeg', 'webp'], key="place_upload")
            place_caption = st.text_input("Photo Caption (Optional)", key="place_caption")
            if place_file:
                if st.button("Upload Place Photo", use_container_width=True):
                    upload_image(place.get("id"), "place", place_file, place_caption)
        
        if place_imgs:
            cols = st.columns(4)
            for idx, img in enumerate(place_imgs):
                with cols[idx % 4]:
                    # Build full URL if relative
                    img_url = img['image_url']
                    # Only prepend base if it's a local relative path
                    if img_url.startswith("/uploads/"):
                        base = BACKEND_BASE_URL.replace('/api', '').rstrip('/')
                        img_url = f"{base}{img_url}"
                    elif img_url.startswith("/") and not img_url.startswith("/uploads/"):
                        base = BACKEND_BASE_URL.replace('/api', '').rstrip('/')
                        img_url = f"{base}/uploads{img_url}"
                    
                    st.image(img_url, use_container_width=True)
                    st.caption(f"Path: {img_url}") # Debug label to see why it breaks
                    if img.get("caption"):
                        st.caption(img["caption"])
                    if st.button("Remove", key=f"del_place_{img['id']}", type="secondary", icon="🗑️"):
                        delete_place_image(img['id'])
        else:
            st.info("No place photos uploaded yet.")
            
        st.markdown("---")
        
        # --- MENU PHOTOS ---
        st.markdown("### 🍴 Menu Photos")
        st.caption("Upload photos of your menu items or the physical menu.")
        
        with st.expander("Upload New Menu Photo", expanded=False):
            menu_file = st.file_uploader("Choose a menu photo", type=['png', 'jpg', 'jpeg', 'webp'], key="menu_upload")
            menu_caption = st.text_input("Item Name/Description (Optional)", key="menu_caption")
            if menu_file:
                if st.button("Upload Menu Photo", use_container_width=True):
                    upload_image(place.get("id"), "menu", menu_file, menu_caption)
        
        if menu_imgs:
            cols = st.columns(4)
            for idx, img in enumerate(menu_imgs):
                with cols[idx % 4]:
                    img_url = img['image_url']
                    # Only prepend base if it's a local relative path
                    if img_url.startswith("/uploads/"):
                        base = BACKEND_BASE_URL.replace('/api', '').rstrip('/')
                        img_url = f"{base}{img_url}"
                    elif img_url.startswith("/") and not img_url.startswith("/uploads/"):
                        base = BACKEND_BASE_URL.replace('/api', '').rstrip('/')
                        img_url = f"{base}/uploads{img_url}"
                        
                    st.image(img_url, use_container_width=True)
                    st.caption(f"Path: {img_url}") # Debug label
                    if img.get("caption"):
                        st.caption(img["caption"])
                    if st.button("Remove", key=f"del_menu_{img['id']}", type="secondary", icon="🗑️"):
                        delete_place_image(img['id'])
        else:
            st.info("No menu photos uploaded yet.")
    else:
        st.error("Could not load data. Please refresh.")
# =========================
# 3️⃣ OPERATIONS
# =========================
elif selected == "Operations":
    st.title("⏰ Operational Efficiency")
    st.info("Operational analytics based on historical interaction patterns.")
    
    df = fetch_analytics_data(start_date, end_date)
    if not df.empty and 'Date' in df.columns:
        df['Hour'] = df['Date'].dt.hour
        df['Day'] = df['Date'].dt.day_name()
        
        st.subheader("Hourly Interaction Volume")
        fig_line = px.line(df, x='Date', y=['Visits', 'Calls'], 
            color_discrete_sequence=['#1D3143', '#61A3BB'],
            title="Interaction Trends Over Time")
        fig_line.update_layout(template="plotly_white")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("Insufficient data to display operational trends.")

# =========================
# 4️⃣ LOCATION LOGIC
# =========================
elif selected == "Location Logic":
    st.title("📍 Location Logic")
    st.markdown("See where your visitors are coming from — all time and recently active.")

    # ── Get owner's place coords ──────────────────────────────────────
    place       = my_place or {}
    place_id    = place.get("id", None)
    place_lat   = float(place.get("latitude",  29.0661))
    place_lon   = float(place.get("longitude", 31.0994))

    if not place_id:
        st.error("Could not load your place info. Please refresh.")
        st.stop()

    # ── Controls row ─────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 1, 1, 1])

    with ctrl1:
        window_label = st.selectbox(
            "Active session window",
            options=["Last 15 minutes", "Last 1 hour", "Last 3 hours",
                     "Last 6 hours", "Last 24 hours", "Custom"],
            index=1,
        )
        window_map = {
            "Last 15 minutes": 15,
            "Last 1 hour":     60,
            "Last 3 hours":    180,
            "Last 6 hours":    360,
            "Last 24 hours":   1440,
        }
        if window_label == "Custom":
            custom_h = st.number_input("Custom window (hours)", min_value=1, max_value=168, value=2)
            active_minutes = custom_h * 60
        else:
            active_minutes = window_map[window_label]

    with ctrl2:
        show_heatmap = st.toggle("🔥 All visitors heatmap", value=True)

    with ctrl3:
        show_pins = st.toggle("📌 Active visitor pins", value=True)

    with ctrl4:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.divider()

    # ── Fetch data ────────────────────────────────────────────────────
    with st.spinner("Loading AI visitor insights and locations..."):
        all_df = fetch_interactions_locations()
        active_visitors = fetch_active_visitors()
        peak_hour_data = fetch_peak_hour()
        owner_summary = fetch_location_summary()
        places_list = fetch_my_places()

    # ── KPI cards ─────────────────────────────────────────────────────
    k1, k2, k3 = st.columns(3)
    total_count  = len(all_df)
    active_count = len(active_visitors)
    
    # From peak hour data
    peak_time_str = "N/A"
    if peak_hour_data and "peak" in peak_hour_data:
        peak_time_str = str(peak_hour_data["peak"])

    k1.markdown(f"""<div class="kpi-card">
        <div class="kpi-title">👥 Total Visitors (all time)</div>
        <div class="kpi-value">{total_count}</div>
        <div class="kpi-delta">Recorded map interactions</div>
    </div>""", unsafe_allow_html=True)

    k2.markdown(f"""<div class="kpi-card">
        <div class="kpi-title">🟢 Active Visitors</div>
        <div class="kpi-value">{active_count}</div>
        <div class="kpi-delta">AI Live Detection</div>
    </div>""", unsafe_allow_html=True)

    k3.markdown(f"""<div class="kpi-card">
        <div class="kpi-title">⏳ Peak Traffic Hour</div>
        <div class="kpi-value">{peak_time_str}</div>
        <div class="kpi-delta">AI Predicted Focus Time</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── AI Summary Block ──────────────────────────────────────────────
    if owner_summary and "summary" in owner_summary:
        st.info(f"🧠 **AI Location Summary:** {owner_summary['summary']}")

    # ── Map — always rendered, data is optional ───────────────────────
    if all_df.empty:
        st.warning("No visitor location data yet — showing your place on the map.")

    loc_map = build_location_map(
        all_df, active_visitors,
        show_pins, show_heatmap,
        places_list, place_lat, place_lon
    )
    st_folium(loc_map, width="100%", height=520, returned_objects=[])

    # Legend
    st.markdown("""
    <div style='font-size:13px; color:#65797E; margin-top:8px; display:flex; gap:20px;'>
        <span>🔴 <b>Your Branches</b></span>
        <span>🔵 <b>Active visitors (pins)</b></span>
        <span>🌡️ <b>All visitors density (heatmap)</b></span>
    </div>
    """, unsafe_allow_html=True)
