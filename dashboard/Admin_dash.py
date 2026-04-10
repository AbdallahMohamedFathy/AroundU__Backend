import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from streamlit_option_menu import option_menu
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
from datetime import datetime, timedelta
import requests
import os

# ── CONFIGURATION ────────────────────────────────────────────────
BACKEND_BASE_URL = "https://aroundubackend-production.up.railway.app/api"

# ── API URLs ──────────────────────────────────────────────────────
CLUSTERING_API = "https://mazenmaher26-admin-location.hf.space"
ANOMALY_API    = "https://mazenmaher26-admin-anomaly.hf.space"

# ═══════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════
st.set_page_config(page_title="AroundU | Admin Dashboard", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #F8F9FB;
}

[data-testid="stHeader"] {
    background-color: rgba(255, 255, 255, 0);
}

/* Sidebar Style Sync with Owner Dash */
section[data-testid="stSidebar"] {
    background-color: #055e9b !important;
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
    font-size: 26px !important;
    color: #FFFFFF !important;
    padding-top: 10px !important;
    font-weight: 800 !important;
    margin-bottom: 0px !important;
    letter-spacing: -0.5px;
}

section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] p {
    font-size: 14px !important;
    color: rgba(255, 255, 255, 0.7) !important;
    margin-bottom: 25px !important;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

/* Sidebar selected background logic */
.nav-link-selected {
    background-color: rgba(255, 255, 255, 0.15) !important;
}

.nav-link, .nav-link-selected, .nav-link:hover {
    background-color: transparent !important;
}

div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:has(div.nav-link) {
    background-color: transparent !important;
}

/* Premium Metric Cards */
div[data-testid="stMetric"] {
    background-color: white;
    border-left: 5px solid #055e9b;
    padding: 24px;
    border-radius: 16px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
    transition: all 0.2s ease-in-out;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.06);
}

/* Plot Containers */
.plot-container {
    background-color: white;
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04);
}

h1, h2, h3 { 
    color: #1E293B; 
    font-family: 'Inter', sans-serif; 
    font-weight: 700; 
}

/* Custom Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 32px;
}

.stTabs [data-baseweb="tab"] {
    height: 52px;
    background-color: transparent;
    padding: 10px 16px;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    color: #055e9b !important;
    border-bottom: 3px solid #055e9b !important;
}

/* Table styling fixes */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
}

/* Sidebar Widget Styling (Ghost Style) */
section[data-testid="stSidebar"] .stButton > button {
    background-color: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(255,255,255,0.2) !important;
    border-color: white !important;
}

section[data-testid="stSidebar"] [data-baseweb="base-input"],
section[data-testid="stSidebar"] [data-baseweb="input"],
section[data-testid="stSidebar"] [data-baseweb="input"] > div {
    background-color: rgba(255, 255, 255, 0.12) !important;
    border: none !important;
    outline: none !important;
    border-radius: 10px !important;
    box-shadow: none !important;
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
    margin-bottom: 10px;
}

.kpi-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(29, 49, 67, 0.12);
    border-top-color: #055e9b;
}

.kpi-title { 
    font-size: 13px; 
    color: #65797E; 
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
}
.kpi-value { 
    font-size: 34px; 
    font-weight: 800; 
    color: #1D3143; 
    margin: 8px 0;
}
.kpi-delta { 
    font-size: 12px; 
    color: #055e9b; 
    font-weight: 600;
}
section[data-testid="stSidebar"] [data-baseweb="input"] > div {
    background-color: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 10px !important;
    color: white !important;
}

section[data-testid="stSidebar"] [data-baseweb="input"] input {
    color: white !important;
}

section[data-testid="stSidebar"] label p {
    color: white !important;
    font-weight: 600 !important;
}

</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# AUTHENTICATION LOGIC
# ═══════════════════════════════════════════════════════════
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
            return None, f"Error ({response.status_code}): {error_detail}"
    except Exception as e:
        return None, f"Connection error: {e}"

def logout():
    st.session_state.token = None
    st.rerun()

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.get('token')}"}

if 'token' not in st.session_state:
    st.session_state.token = None

if st.session_state.token is None:
    # --- LOGIN SCREEN ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏙️ AroundU Admin")
        st.subheader("Beni Suef Intelligence Portal")
        
        with st.form("login_form"):
            email = st.text_input("Admin Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Access Dashboard", use_container_width=True)
            
            if submitted:
                token, error_msg = login_user(email, password)
                if token:
                    st.session_state.token = token
                    st.success("Access granted!")
                    st.rerun()
                else:
                    st.error(error_msg or "Invalid email or password.")
    st.stop()

# ═══════════════════════════════════════════════════════════
# DATA FETCHING ENGINE (Real APIs)
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def fetch_admin_stats(start_date, end_date):
    try:
        params = {"start_date": str(start_date), "end_date": str(end_date)}
        res = requests.get(f"{BACKEND_BASE_URL}/dashboard/admin/stats/overview", params=params, headers=get_headers())
        if res.status_code == 200: return res.json()
    except: pass
    return {} # Always return empty dict to prevent AttributeError .get()

@st.cache_data(ttl=60)
def fetch_trending_data(start_date, end_date):
    cols = ["Date", "Visits", "New_Users", "New_Owners", "Saves", "Reviews", "Chats", "Directions"]
    try:
        params = {"start_date": str(start_date), "end_date": str(end_date)}
        res = requests.get(f"{BACKEND_BASE_URL}/dashboard/admin/stats/trending", params=params, headers=get_headers(), timeout=15)
        if res.status_code == 200:
            data = res.json()
            df = pd.DataFrame(data)
            if not df.empty:
                df['Date'] = pd.to_datetime(df['date'])
                df.rename(columns={
                    "visits": "Visits", "new_users": "New_Users", "new_owners": "New_Owners",
                    "saves": "Saves", "reviews": "Reviews", "chats": "Chats", "directions": "Directions"
                }, inplace=True)
                for c in cols:
                    if c not in df.columns: df[c] = 0
                return df[cols].sort_values("Date")
    except Exception as e:
        st.sidebar.warning(f"Trending Data API delay: {e}")
    return pd.DataFrame(columns=cols)

@st.cache_data(ttl=300)
def fetch_all_places():
    cols = ["Place_ID", "Name", "Category", "District", "Visits", "Saves", "Rating", "Reviews", "Status", "Added"]
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/dashboard/admin/stats/places", headers=get_headers(), timeout=15)
        if res.status_code == 200: 
            df = pd.DataFrame(res.json())
            if not df.empty:
                # Ensure snake_case from API is mapped to Title Case if needed
                mapping = {
                    "place_id": "Place_ID", "name": "Name", "category": "Category",
                    "district": "District", "visits": "Visits", "saves": "Saves",
                    "rating": "Rating", "reviews": "Reviews", "status": "Status", "added": "Added"
                }
                df.rename(columns={k: v for k, v in mapping.items() if k in df.columns}, inplace=True)
                # Ensure all expected columns exist
                for c in cols:
                    if c not in df.columns: df[c] = None
                
                # Numeric conversions for safety
                numeric_cols = ["Visits", "Saves", "Rating", "Reviews"]
                for nc in numeric_cols:
                    df[nc] = pd.to_numeric(df[nc], errors='coerce').fillna(0)
                
                # Date conversion
                df["Added"] = pd.to_datetime(df["Added"], errors='coerce')
                    
                return df[cols]
    except Exception as e:
        st.sidebar.error(f"Places API Error: {e}")
    
    # Robust empty fallback with correct types
    df_empty = pd.DataFrame(columns=cols)
    for nc in ["Visits", "Saves", "Rating", "Reviews"]:
        df_empty[nc] = pd.to_numeric(df_empty[nc])
    return df_empty

@st.cache_data(ttl=300)
def fetch_all_users():
    cols = ["User_ID", "Name", "District", "Reviews", "Saves", "Status", "Joined", "Last_Login"]
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/dashboard/admin/stats/users", headers=get_headers(), timeout=15)
        if res.status_code == 200: 
            df = pd.DataFrame(res.json())
            if not df.empty:
                mapping = {
                    "user_id": "User_ID", "name": "Name", "district": "District",
                    "reviews": "Reviews", "saves": "Saves", "status": "Status",
                    "joined": "Joined", "last_login": "Last_Login"
                }
                df.rename(columns={k: v for k, v in mapping.items() if k in df.columns}, inplace=True)
                for c in cols:
                    if c not in df.columns: df[c] = None
                
                # Numeric conversions
                for nc in ["Reviews", "Saves"]:
                    df[nc] = pd.to_numeric(df[nc], errors='coerce').fillna(0)
                return df[cols]
    except Exception as e:
        st.sidebar.error(f"Users API Error: {e}")
    
    df_empty = pd.DataFrame(columns=cols)
    for nc in ["Reviews", "Saves"]:
        df_empty[nc] = pd.to_numeric(df_empty[nc])
    return df_empty

@st.cache_data(ttl=300)
def fetch_category_stats():
    cols = ["Category", "Count", "Visits", "Saves"]
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/dashboard/admin/stats/categories", headers=get_headers(), timeout=15)
        if res.status_code == 200: 
            df = pd.DataFrame(res.json())
            if not df.empty:
                mapping = {"category": "Category", "count": "Count", "visits": "Visits", "saves": "Saves"}
                df.rename(columns={k: v for k, v in mapping.items() if k in df.columns}, inplace=True)
                for c in cols:
                    if c not in df.columns: df[c] = None
                
                # Numeric conversions
                for nc in ["Count", "Visits", "Saves"]:
                    df[nc] = pd.to_numeric(df[nc], errors='coerce').fillna(0)
                return df[cols]
    except Exception as e:
        pass
    return pd.DataFrame(columns=cols)

@st.cache_data(ttl=60)
def fetch_moderation_data():
    rev_cols = ["Review_ID", "User", "Place", "Review", "Rating", "Date"]
    own_cols = ["Owner_ID", "Name", "Business", "Category", "Submitted"]
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/dashboard/admin/moderation/pending", headers=get_headers(), timeout=15)
        if res.status_code == 200: 
            data = res.json()
            df_rev = pd.DataFrame(data.get("flagged_reviews", []))
            df_own = pd.DataFrame(data.get("pending_owners", []))
            
            if not df_rev.empty:
                mapping = {"review_id": "Review_ID", "user": "User", "place": "Place", "review": "Review", "rating": "Rating", "date": "Date"}
                df_rev.rename(columns={k: v for k, v in mapping.items() if k in df_rev.columns}, inplace=True)
                for c in rev_cols:
                    if c not in df_rev.columns: df_rev[c] = None
                df_rev = df_rev[rev_cols]
            else:
                df_rev = pd.DataFrame(columns=rev_cols)

            if not df_own.empty:
                mapping = {"owner_id": "Owner_ID", "name": "Name", "business": "Business", "category": "Category", "submitted": "Submitted"}
                df_own.rename(columns={k: v for k, v in mapping.items() if k in df_own.columns}, inplace=True)
                for c in own_cols:
                    if c not in df_own.columns: df_own[c] = None
                df_own = df_own[own_cols]
            else:
                df_own = pd.DataFrame(columns=own_cols)
                
            return df_rev, df_own
    except Exception as e:
        st.sidebar.error(f"Moderation API Error: {e}")
    
    df_rev = pd.DataFrame(columns=rev_cols)
    df_rev["Rating"] = pd.to_numeric(df_rev["Rating"])
    return df_rev, pd.DataFrame(columns=own_cols)

@st.cache_data(ttl=60)
def fetch_recent_interactions(limit=1000):
    cols = ["user_id", "place_id", "user_lat", "user_lon", "visited_at", "cluster"]
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/dashboard/admin/interactions/recent", params={"limit": limit}, headers=get_headers(), timeout=15)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                # Ensure numeric types for coordinates and cluster
                for nc in ["user_lat", "user_lon", "cluster"]:
                    if nc in df.columns:
                        df[nc] = pd.to_numeric(df[nc], errors='coerce').fillna(0)
                return df
    except Exception as e:
        pass
    return pd.DataFrame(columns=cols)

@st.cache_data(ttl=300)
def fetch_all_properties():
    cols = ["Property_ID", "Title", "Price", "District", "Status", "Owner", "Owner_Email", "Added"]
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/dashboard/admin/stats/properties", headers=get_headers(), timeout=15)
        if res.status_code == 200: 
            data = res.json()
            if not data:
                return pd.DataFrame(columns=cols)
                
            df = pd.DataFrame(data)
            mapping = {
                "property_id": "Property_ID", "title": "Title", "price": "Price",
                "district": "District", "status": "Status", "owner": "Owner",
                "owner_email": "Owner_Email", "added": "Added"
            }
            # Rename lower_case keys if they exist
            df.rename(columns={k: v for k, v in mapping.items() if k in df.columns}, inplace=True)
            
            # Ensure all columns exist
            for c in cols:
                if c not in df.columns: df[c] = None
            
            # Numeric conversions
            if "Price" in df.columns:
                df["Price"] = pd.to_numeric(df["Price"], errors='coerce').fillna(0)
            
            return df[cols]
        else:
            st.error(f"❌ Properties API Error: [HTTP {res.status_code}] {res.text[:100]}")
    except Exception as e:
        st.error(f"❌ Properties Connection Error: {e}")
    
    return pd.DataFrame(columns=cols)

def fetch_chatbot_analytics():
    # Placeholder/Mock data to fix crash
    types = pd.DataFrame([
        {"Type": "Menu/Pricing", "Val": 45},
        {"Type": "Availability", "Val": 30},
        {"Type": "Location/Directions", "Val": 15},
        {"Type": "General Info", "Val": 10}
    ])
    places = pd.DataFrame([
        {"Place": "Sultan Restaurant", "Chats": 120, "Resolved": 115},
        {"Place": "City Cafe", "Chats": 85, "Resolved": 80},
        {"Place": "Pharmacy El-Ezaby", "Chats": 50, "Resolved": 48},
        {"Place": "Beni Suef University", "Chats": 40, "Resolved": 35}
    ])
    return types, places

# --- Database Management Helpers ---

def list_db_tables():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/dashboard/admin/db/tables", headers=get_headers(), timeout=15)
        if res.status_code == 200: 
            return res.json()
        else:
            st.sidebar.error(f"DB Tables API Error ({res.status_code}): {res.text[:100]}")
    except Exception as e:
        st.sidebar.error(f"Connection Error: {e}")
    return []

def fetch_table_content(table_name):
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/dashboard/admin/db/table/{table_name}", headers=get_headers(), timeout=15)
        if res.status_code == 200: return res.json()
    except Exception as e:
        st.error(f"Fetch Content Error: {e}")
    return {"columns": [], "data": []}

def update_db_record(table_name, row_id, data):
    try:
        res = requests.put(f"{BACKEND_BASE_URL}/dashboard/admin/db/table/{table_name}/{row_id}", json=data, headers=get_headers())
        return res.status_code == 200
    except: return False

def delete_db_record(table_name, row_id):
    try:
        res = requests.delete(f"{BACKEND_BASE_URL}/dashboard/admin/db/table/{table_name}/{row_id}", headers=get_headers())
        return res.status_code == 200
    except: return False

def insert_db_record(table_name, data):
    try:
        res = requests.post(f"{BACKEND_BASE_URL}/dashboard/admin/db/table/{table_name}", json=data, headers=get_headers())
        return res.status_code == 200
    except: return False

# --- CREATE PROPERTY ---------------------------------------------
def update_place_status_api(place_id, active):
    try:
        res = requests.post(
            f"{BACKEND_BASE_URL}/dashboard/admin/places/{place_id}/status",
            params={"active": str(active).lower()},
            headers=get_headers()
        )
        if res.status_code == 200:
            status_txt = "activated" if active else "suspended"
            st.toast(f"✅ Place {place_id} {status_txt} successfully!", icon="🚫")
            return True, res.json().get("message")
        return False, res.text
    except Exception as e:
        return False, str(e)

def update_user_status_api(user_id, active):
    try:
        res = requests.post(
            f"{BACKEND_BASE_URL}/dashboard/admin/users/{user_id}/status",
            params={"active": str(active).lower()},
            headers=get_headers()
        )
        if res.status_code == 200:
            status_txt = "activated" if active else "suspended"
            st.toast(f"✅ User {user_id} {status_txt} successfully!", icon="👤")
            return True, res.json().get("message")
        return False, res.text
    except Exception as e:
        return False, str(e)

# ── MODERATION ACTIONS ──────────────────────────────────────────
def delete_review(review_id_str):
    try:
        rid = int(review_id_str.replace("R-", ""))
        res = requests.delete(f"{BACKEND_BASE_URL}/dashboard/admin/reviews/{rid}", headers=get_headers())
        if res.status_code == 200:
            st.toast(f"✅ Review {review_id_str} deleted successfully", icon="🗑️")
            return True
    except Exception as e:
        st.error(f"Error deleting review: {e}")
    return False

def create_property_with_owner_api(prop_data):
    try:
        res = requests.post(f"{BACKEND_BASE_URL}/dashboard/admin/properties", json=prop_data, headers=get_headers())
        if res.status_code == 200:
            return res.json(), None
        else:
            try:
                body = res.json()
                err = body.get("detail") or str(body)
            except:
                err = res.text or "No response body"
            return None, f"[HTTP {res.status_code}] {err}"
    except Exception as e:
        return None, str(e)

def approve_owner(owner_id_str, verified):
    try:
        oid = int(owner_id_str.replace("OWN-", ""))
        res = requests.post(
            f"{BACKEND_BASE_URL}/dashboard/admin/owners/{oid}/verify", 
            params={"verified": verified}, 
            headers=get_headers()
        )
        if res.status_code == 200:
            status_txt = "approved" if verified else "rejected"
            st.toast(f"✅ Owner {owner_id_str} {status_txt}!", icon="👤")
            return True
    except Exception as e:
        st.error(f"Error verifying owner: {e}")
    return False

def create_owner_api(owner_data):
    try:
        res = requests.post(f"{BACKEND_BASE_URL}/dashboard/admin/owners", json=owner_data, headers=get_headers())
        if res.status_code == 200:
            return res.json(), None
        else:
            try:
                body = res.json()
                err = body.get("detail") or str(body)
            except:
                err = res.text or "No response body"
            return None, f"[HTTP {res.status_code}] {err}"
    except Exception as e:
        return None, str(e)

# --- Location Logic Helpers ---

def filter_active(df: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Return only rows within the given time window."""
    if df.empty or "visited_at" not in df.columns:
        return df
    cutoff = datetime.now() - timedelta(minutes=minutes)
    
    # Ensure visited_at is datetime
    df['visited_at'] = pd.to_datetime(df['visited_at'], errors="coerce")
    ts = df['visited_at'].copy()
    return df[ts >= cutoff]

def build_location_map(all_locations, show_pins, show_heatmap, places_list, center_lat, center_lon, active_df=None):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="CartoDB positron")
    
    # Render Places
    for _, p in places_list.iterrows():
        lat = p.get("Latitude")
        lon = p.get("Longitude")
        name = p.get("Name") or "Place"
        dist = p.get("District") or ""
        if lat and lon:
            tooltip_html = f"📍 <b>{name}</b><br>{dist}"
            folium.Marker(
                [float(lat), float(lon)], 
                tooltip=tooltip_html, 
                icon=folium.Icon(color="red", icon="home", prefix="fa")
            ).add_to(m)

    # Render Heatmap
    if show_heatmap and not all_locations.empty:
        heat_data = [[row['user_lat'], row['user_lon']] for _, row in all_locations.iterrows() if pd.notna(row['user_lat']) and pd.notna(row['user_lon'])]
        if heat_data:
            HeatMap(
                heat_data, 
                radius=22, 
                blur=18,
                min_opacity=0.35,
                gradient={"0.3": "#055e9b", "0.6": "#61A3BB", "1.0": "#E63946"}
            ).add_to(m)

    # Render Visitor Pins
    if show_pins:
        target_df = active_df if active_df is not None else all_locations
        if not target_df.empty:
            for _, row in target_df.iterrows():
                ts_str = row["visited_at"].strftime("%H:%M") if pd.notna(row["visited_at"]) else "N/A"
                uid = row.get("user_id", "Anon")
                cluster = row.get("cluster", "N/A")
                lat = row.get("user_lat")
                lon = row.get("user_lon")
                
                if lat and lon:
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=6,
                        color="#055e9b",
                        fill=True,
                        fill_color="#61A3BB",
                        fill_opacity=0.8,
                        tooltip=f"👤 User {uid} (Cluster: {cluster}) · {ts_str}"
                    ).add_to(m)
    return m

def promote_user(user_id_str, new_role):
    """
    Calls the backend API to promote a user to a new role (ADMIN, OWNER, etc.)
    """
    try:
        # Extract numeric ID from "U-123" format
        uid = int(user_id_str.replace("U-", ""))
        
        # Prepare the request payload
        payload = {"role": new_role}
        
        # Call the promotion endpoint
        res = requests.post(
            f"{BACKEND_BASE_URL}/dashboard/admin/promote/{uid}",
            json=payload,
            headers=get_headers()
        )
        
        if res.status_code == 200:
            st.toast(f"✅ User {user_id_str} promoted to {new_role} successfully!", icon="🎖️")
            return True
        else:
            try:
                err = res.json().get("detail", res.text)
            except:
                err = res.text
            st.error(f"❌ Failed to promote user: {err}")
    except Exception as e:
        st.error(f"Error promoting user: {e}")
    return False

# Admin action log placeholder
admin_log = pd.DataFrame({
    "Admin":     ["Admin_01", "SuperAdmin"],
    "Action":    ["Dashboard Connected", "Production Sync"],
    "Target_ID": ["—", "—"],
    "Timestamp": ["Now", "Just Now"],
})


# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    # ✅ BUG FIX: removed external image URL → replaced with emoji + text
    st.markdown("## 🏙️ AroundU")
    st.caption("Beni Suef Admin Intelligence")
    st.markdown("<br>", unsafe_allow_html=True)

    selected = option_menu(
        menu_title=None,
        options=[
            "Overview", "Places Analytics", "User Analytics",
            "Property Management", "Reviews", "Chatbot",
            "Category Analytics", "Moderation", "Anomaly Detection",
            "Location Logic", "Database Manager"
        ],
        icons=[
            "grid-1x2", "shop", "people",
            "house", "star", "robot",
            "tags", "shield-lock", "exclamation-triangle",
            "geo-alt", "database"
        ],
        default_index=0,
        styles={
            "container":         {"background-color": "#055e9b !important", "padding": "0px !important"},
            "nav-link":          {
                "font-size": "15px", "text-align": "left", "color": "rgba(255,255,255,0.8)", 
                "padding": "12px 20px", "background-color": "transparent !important",
                "--hover-color": "rgba(255,255,255,0.1)"
            },
            "nav-link-selected": {"background-color": "rgba(255,255,255,0.15)", "color": "white", "font-weight": "600"},
        },
    )

    st.divider()
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("### 📅 Date Range")
    date_range = st.date_input(
        "Choose period:",
        value=(datetime.now() - timedelta(days=30), datetime.now()),
    )

    # Fetch global data for sidebars/alerts
    df_places = fetch_all_places()
    df_users = fetch_all_users()
    df_props = fetch_all_properties()
    flagged_reviews, pending_owners = fetch_moderation_data()

    # Alert counts in sidebar
    st.divider()
    st.markdown('<p style="color:rgba(255,255,255,0.6); font-size:12px; font-weight:700; text-transform:uppercase;">⚠️ Priority Alerts</p>', unsafe_allow_html=True)
    
    def alert_item(label, count, color="red"):
        bg = "#EF4444" if color == "red" else "#F59E0B"
        return f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <span style="font-size:14px; color:rgba(255,255,255,0.85);">{label}</span>
            <span style="background:{bg}; color:white; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:700;">{count}</span>
        </div>
        """

    st.markdown(alert_item("Flagged Reviews", len(flagged_reviews) if not flagged_reviews.empty else 0), unsafe_allow_html=True)
    st.markdown(alert_item("Pending Owners", len(pending_owners) if not pending_owners.empty else 0, "yellow"), unsafe_allow_html=True)
    st.markdown(alert_item("Suspended Users", len(df_users[df_users["Status"]=="Suspended"]) if not df_users.empty else 0), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# FILTER + HELPERS
# ═══════════════════════════════════════════════════════════
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date = date_range[0].strftime("%Y-%m-%d")
    end_date   = date_range[1].strftime("%Y-%m-%d")
    
    # Fetch real stats for the period
    stats = fetch_admin_stats(start_date, end_date)
    df_ts = fetch_trending_data(start_date, end_date)
    
    # UseTrending data as df_filtered for time charts
    df_filtered = df_ts 
else:
    st.warning("Please select a valid start AND end date.")
    st.stop()

def empty_state(msg="No data available for the selected period."):
    st.info(f"ℹ️ {msg}")

TEMPLATE = "plotly_white"


# ═══════════════════════════════════════════════════════════
# 1. OVERVIEW
# ═══════════════════════════════════════════════════════════
if selected == "Overview":
    st.title("📊 Platform Performance Overview")

    if not stats:
        empty_state()
        st.stop()

    # KPI Row 1
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Visits",     f"{stats.get('visits', 0):,}",    stats.get("visits_delta"))
    k2.metric("New Users",        f"{stats.get('new_users', 0):,}",  stats.get("users_delta"))
    k3.metric("Saved Places",     f"{stats.get('saves', 0):,}",      stats.get("saves_delta"))
    k4.metric("Direction Clicks", f"{stats.get('directions', 0):,}", stats.get("directions_delta"))

    # KPI Row 2
    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Call Clicks",   f"{stats.get('calls', 0):,}",   stats.get("calls_delta"))
    k6.metric("Total Reviews", f"{stats.get('reviews', 0):,}", stats.get("reviews_delta"))
    k7.metric("Active Places", f"{stats.get('active_places', 0):,}")
    
    chats = stats.get("chats", 0)
    res   = stats.get("resolved_chats", 0)
    k8.metric("Bot Resolution", f"{(res/chats*100):.1f}%" if chats > 0 else "N/A")

    st.markdown("<br>", unsafe_allow_html=True)

    # Row A: heatmap + signup velocity
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("⏰ Platform Visiting Hours")
        hours     = [f"{i}:00" for i in range(24)]
        days      = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        heat_data = np.random.randint(10, 100, size=(7, 24))
        heat_data[:, 18:22] += 60
        fig_heat = px.imshow(heat_data, x=hours, y=days,
                             color_continuous_scale="Viridis",
                             aspect="auto", template=TEMPLATE)
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_b:
        st.subheader("🚀 Signup Velocity")
        fig_v = px.bar(df_filtered, x="Date", y=["New_Users","New_Owners"],
                       barmode="group",
                       color_discrete_sequence=["#6366f1","#f59e0b"],
                       template=TEMPLATE)
        st.plotly_chart(fig_v, use_container_width=True)

    # ✅ BUG FIX: col_c paired with col_d — no longer alone in full row
    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("🛡️ Place Status Distribution")
        fig_st = px.pie(df_places, names="Status", hole=0.6,
                        color_discrete_sequence=["#10B981","#EF4444","#F59E0B"],
                        template=TEMPLATE)
        st.plotly_chart(fig_st, use_container_width=True)

    with col_d:
        st.subheader("📈 Trending: Visits & Signups")
        if not df_filtered.empty:
            fig_trend = px.line(df_filtered, x="Date", y=["Visits", "New_Users"],
                               color_discrete_sequence=["#055e9b", "#10B981"],
                               template=TEMPLATE)
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            empty_state("No trending data available for this period.")


# ═══════════════════════════════════════════════════════════
# 2. PLACES ANALYTICS
# ═══════════════════════════════════════════════════════════
elif selected == "Places Analytics":
    st.title("🏘️ Places Analytics")

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Total Places",     len(df_places))
    p2.metric("Active",           len(df_places[df_places["Status"] == "Active"]))
    p3.metric("Pending Approval", len(df_places[df_places["Status"] == "Pending Approval"]))
    p4.metric("Suspended",        len(df_places[df_places["Status"] == "Suspended"]))

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Places per Category")
        cat_counts = df_places["Category"].value_counts().reset_index()
        cat_counts.columns = ["Category","Count"]
        fig_cc = px.bar(cat_counts, x="Category", y="Count",
                        color="Count", color_continuous_scale="Blues",
                        text_auto=True, template=TEMPLATE)
        st.plotly_chart(fig_cc, use_container_width=True)

    with c2:
        st.subheader("🏆 Most Visited Places (Top 8)")
        top_v = df_places.nlargest(8, "Visits")
        fig_tv = px.bar(top_v, x="Visits", y="Name", orientation="h",
                        color="Visits", color_continuous_scale="Blues",
                        template=TEMPLATE)
        fig_tv.update_layout(yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig_tv, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("❤️ Most Saved Places (Top 8)")
        top_s = df_places.nlargest(8, "Saves")
        fig_ts = px.bar(top_s, x="Saves", y="Name", orientation="h",
                        color="Saves", color_continuous_scale="Greens",
                        template=TEMPLATE)
        fig_ts.update_layout(yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig_ts, use_container_width=True)

    with c4:
        st.subheader("⭐ Average Rating per Category")
        avg_c = df_places.groupby("Category")["Rating"].mean().reset_index()
        avg_c["Rating"] = avg_c["Rating"].round(2)
        fig_rc = px.bar(avg_c, x="Category", y="Rating",
                        color="Rating", color_continuous_scale="RdYlGn",
                        text_auto=".2f", template=TEMPLATE)
        fig_rc.update_layout(yaxis_range=[0, 5])
        st.plotly_chart(fig_rc, use_container_width=True)

    c5, c6 = st.columns(2)
    with c5:
        st.subheader("🌟 Highest Rated Places")
        st.dataframe(
            df_places.nlargest(8, "Rating")[["Name","Category","District","Rating","Visits"]]
            .reset_index(drop=True),
            use_container_width=True,
        )
    with c6:
        st.subheader("⚠️ Lowest Rated (Needs Attention)")
        st.dataframe(
            df_places.nsmallest(8, "Rating")[["Name","Category","District","Rating","Visits"]]
            .reset_index(drop=True),
            use_container_width=True,
        )

    st.subheader("🆕 Recently Added Places")
    recent = df_places.sort_values("Added", ascending=False).head(10).copy()
    recent["Added"] = recent["Added"].astype(str).str[:10]
    st.dataframe(
        recent[["Name","Category","District","Status","Added","Rating"]].reset_index(drop=True),
        use_container_width=True,
    )

    # ✅ NEW: Search & filter
    st.subheader("🔍 Search & Filter All Places")
    cs1, cs2, cs3 = st.columns(3)
    with cs1:
        srch = st.text_input("Search by name...")
    with cs2:
        cat_f = st.selectbox("Category", ["All"] + sorted(df_places["Category"].unique().tolist()))
    with cs3:
        sta_f = st.selectbox("Status", ["All","Active","Suspended","Pending Approval"])

    fp = df_places.copy()
    if srch:
        fp = fp[fp["Name"].str.contains(srch, case=False)]
    if cat_f != "All":
        fp = fp[fp["Category"] == cat_f]
    if sta_f != "All":
        fp = fp[fp["Status"] == sta_f]

    st.dataframe(
        fp[["Place_ID","Name","Category","District","Rating","Visits","Saves","Status"]]
        .reset_index(drop=True),
        use_container_width=True,
    )

    # ══════════════════════════════════════════════════════════
    # 🚫 SUSPEND PLACE TOOL
    # ══════════════════════════════════════════════════════════
    st.divider()
    st.subheader("🚫 Suspend a Place")
    st.caption("Suspend a place directly by entering its ID")

    # ── Init session state ────────────────────────────────────
    if "suspended_places_log" not in st.session_state:
        st.session_state.suspended_places_log = []

    sp_col1, sp_col2 = st.columns([2, 1])
    with sp_col1:
        place_id_input = st.text_input(
            "Place ID", placeholder="e.g. P-1012", key="suspend_place_input",
        )
    with sp_col2:
        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
        do_suspend_place = st.button("🚫 Suspend Place", key="btn_suspend_place", use_container_width=True)

    if do_suspend_place:
        pid = place_id_input.strip().upper()
        if not pid:
            st.warning("⚠️ Please enter a Place ID.")
        elif pid not in df_places["Place_ID"].values:
            st.error(f"❌ Place ID `{pid}` not found in the system.")
        else:
            success, msg = update_place_status_api(pid, active=False)
            if success:
                st.session_state.suspended_places_log.append({
                    "id": pid,
                    "ts": datetime.now().strftime("%H:%M:%S")
                })
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ Failed to suspend place: {msg}")

    # ── Place Suspension Log ──────────────────────────────────
    if st.session_state.suspended_places_log:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Recent Suspensions")
        for item in reversed(st.session_state.suspended_places_log[-5:]):
            st.markdown(
                f"""<div style="background:rgba(239,68,68,0.07);
                                border-left:3px solid #EF4444;
                                border-radius:8px;padding:10px 14px;
                                margin:5px 0;font-size:14px;">
                    🚫 <b>{item['id']}</b> &nbsp;·&nbsp; Suspended at {item['ts']}
                </div>""",
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════
# 3. USER ANALYTICS  (expanded)
# ═══════════════════════════════════════════════════════════
elif selected == "User Analytics":
    st.title("👥 User Analytics")

    u1, u2, u3, u4 = st.columns(4)
    u1.metric("Total Users",         len(df_users))
    u2.metric("New Users (Period)",  stats.get("new_users", 0), stats.get("users_delta"))
    u3.metric("Suspended Users",     len(df_users[df_users["Status"] == "Suspended"]) if not df_users.empty else 0)
    u4.metric("New Owners (Period)", stats.get("new_owners", 0), None)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 User Growth Trend")
        fig_ug = px.area(df_filtered, x="Date", y="New_Users",
                         color_discrete_sequence=["#2563EB"], template=TEMPLATE)
        st.plotly_chart(fig_ug, use_container_width=True)

    with col2:
        # ✅ NEW: users by district
        st.subheader("📍 Users by District")
        dist_u = df_users["District"].value_counts().reset_index()
        dist_u.columns = ["District","Users"]
        fig_du = px.bar(dist_u, x="Users", y="District", orientation="h",
                        color="Users", color_continuous_scale="Blues",
                        template=TEMPLATE)
        fig_du.update_layout(yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig_du, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        # ✅ NEW: most active users
        st.subheader("🏅 Most Active Users (by Reviews)")
        top_u = df_users.nlargest(10, "Reviews")[
            ["User_ID","Name","District","Reviews","Saves","Status"]
        ]
        st.dataframe(top_u.reset_index(drop=True), use_container_width=True)

    with col4:
        # ✅ NEW: retention pie
        st.subheader("🔄 User Retention")
        ret_df = pd.DataFrame({
            "Type":  ["Returning","New"],
            "Count": [int(df_filtered["New_Users"].sum() * 0.60),
                      int(df_filtered["New_Users"].sum() * 0.40)],
        })
        fig_ret = px.pie(ret_df, values="Count", names="Type", hole=0.55,
                         color_discrete_sequence=["#2563EB","#93C5FD"],
                         template=TEMPLATE)
        st.plotly_chart(fig_ret, use_container_width=True)

    # ✅ NEW: search users
    st.subheader("🔍 Search Users")
    su1, su2 = st.columns(2)
    with su1:
        u_srch = st.text_input("Search by name or ID...")
    with su2:
        u_sta  = st.selectbox("Filter by status", ["All","Active","Suspended"])

    fu = df_users.copy()
    if u_srch:
        fu = fu[
            fu["Name"].str.contains(u_srch, case=False) |
            fu["User_ID"].str.contains(u_srch, case=False)
        ]
    if u_sta != "All":
        fu = fu[fu["Status"] == u_sta]

    st.dataframe(
        fu[["User_ID","Name","District","Reviews","Saves","Status","Joined","Last_Login"]]
        .reset_index(drop=True),
        use_container_width=True,
    )

    # ══════════════════════════════════════════════════════════
    # 👤 SUSPEND USER TOOL
    # ══════════════════════════════════════════════════════════
    st.divider()
    st.subheader("👤 Suspend a User")
    st.caption("Deactivate a user account directly by entering their ID")

    # ── Init session state ────────────────────────────────────
    if "suspended_users_log" not in st.session_state:
        st.session_state.suspended_users_log = []

    su_col1, su_col2 = st.columns([2, 1])
    with su_col1:
        user_id_input = st.text_input(
            "User ID", placeholder="e.g. U-2001", key="suspend_user_input",
        )
    with su_col2:
        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
        do_suspend_user = st.button("🚫 Suspend User", key="btn_suspend_user", use_container_width=True)

    if do_suspend_user:
        uid = user_id_input.strip().upper()
        if not uid:
            st.warning("⚠️ Please enter a User ID.")
        elif uid not in df_users["User_ID"].values:
            st.error(f"❌ User ID `{uid}` not found in the system.")
        else:
            success, msg = update_user_status_api(uid, active=False)
            if success:
                st.session_state.suspended_users_log.append({
                    "id": uid,
                    "ts": datetime.now().strftime("%H:%M:%S")
                })
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ Failed to suspend user: {msg}")

    # ── User Suspension Log ───────────────────────────────────
    if st.session_state.suspended_users_log:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Recent User Suspensions")
        for item in reversed(st.session_state.suspended_users_log[-5:]):
            st.markdown(
                f"""<div style="background:rgba(239,68,68,0.07);
                                border-left:3px solid #EF4444;
                                border-radius:8px;padding:10px 14px;
                                margin:5px 0;font-size:14px;">
                    👤 <b>{item['id']}</b> &nbsp;·&nbsp; Suspended at {item['ts']}
                </div>""",
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════
# 4. PROPERTY MANAGEMENT
# ═══════════════════════════════════════════════════════════
elif selected == "Property Management":
    st.title("🏠 Property & Housing Management")
    
    pr1, pr2, pr3, pr4 = st.columns(4)
    pr1.metric("Total Properties", len(df_props))
    pr2.metric("Available", len(df_props[df_props["Status"]=="Available"]) if not df_props.empty else 0)
    pr3.metric("Beni Suef Listings", len(df_props[df_props["District"]=="Beni Suef"]) if not df_props.empty else 0)
    pr4.metric("Average Price", f"{df_props['Price'].mean():,.0f} EGP" if not df_props.empty and "Price" in df_props.columns else "N/A")

    st.markdown("<br>", unsafe_allow_html=True)

    tab_list, tab_add = st.tabs(["📋 Property List", "➕ Add New Property"])

    with tab_list:
        st.subheader("🔍 Search & Filter Properties")
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            p_srch = st.text_input("Search by title or ID...")
        with p_col2:
            p_sta = st.selectbox("Status Filter", ["All", "Available", "Sold/Rented"])
        
        fp = df_props.copy()
        if not fp.empty:
            if p_srch:
                fp = fp[fp["Title"].str.contains(p_srch, case=False) | fp["Property_ID"].str.contains(p_srch, case=False)]
            if p_sta != "All":
                fp = fp[fp["Status"] == p_sta]
            
            st.dataframe(fp.reset_index(drop=True), use_container_width=True)
        else:
            st.info("No properties found in the system.")

    with tab_add:
        st.subheader("🏙️ Create Property & Owner Account")
        with st.form("add_property_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Property Title *")
                price = st.number_input("Price (EGP) *", min_value=0.0)
                lat   = st.number_input("Latitude", format="%.6f", value=29.0661)
            with col2:
                email = st.text_input("Owner Email *")
                pwd   = st.text_input("Owner Password *", type="password")
                lon   = st.number_input("Longitude", format="%.6f", value=31.0994)
            
            desc = st.text_area("Description")
            link = st.text_input("Location Link (Google Maps)")
            
            submitted = st.form_submit_button("Create Property", use_container_width=True)
            if submitted:
                if not title or not email or not pwd:
                    st.error("Please fill required fields (*)")
                else:
                    prop_data = {
                        "title": title,
                        "description": desc,
                        "price": price,
                        "location_link": link,
                        "latitude": lat,
                        "longitude": lon,
                        "owner_email": email,
                        "owner_password": pwd
                    }
                    with st.spinner("Creating property and owner..."):
                        res, err = create_property_with_owner_api(prop_data)
                        if res:
                            st.success(f"Success! Property {res['property_id']} created.")
                            st.rerun()
                        else:
                            st.error(f"Creation failed: {err}")

    # Section for image upload
    st.divider()
    st.subheader("🖼️ Upload Property Images")
    if not df_props.empty:
        target_prop = st.selectbox("Select Property", df_props["Property_ID"].tolist())
        uploaded_files = st.file_uploader("Choose images (Max 5)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], key="prop_images")
        if st.button("Upload Selected Images"):
            if not uploaded_files:
                st.warning("Please select files.")
            else:
                # API call for images
                prop_id_int = int(target_prop.replace("PROP-", ""))
                files = [("images", (f.name, f.getvalue(), f.type)) for f in uploaded_files]
                with st.spinner("Uploading images..."):
                    try:
                        res = requests.post(f"{BACKEND_BASE_URL}/dashboard/admin/properties/{prop_id_int}/images", files=files, headers=get_headers())
                        if res.status_code == 200:
                            st.success("Images uploaded successfully!")
                        else:
                            st.error(f"Upload failed: {res.text}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")
    else:
        st.info("No properties available to upload images for.")


# ═══════════════════════════════════════════════════════════
# 5. REVIEWS  (expanded)
# ═══════════════════════════════════════════════════════════
elif selected == "Reviews":
    st.title("⭐ Reviews & Sentiment Analysis")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total Reviews (Period)", stats.get("reviews", 0), stats.get("reviews_delta", "0%"))
    r2.metric("Positive Sentiment",     "75%")
    r3.metric("Negative Sentiment",     "25%")
    r4.metric("Flagged Reviews",        len(flagged_reviews) if not flagged_reviews.empty else 0)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("😊 Positive vs Negative Ratio")
        fig_pie = px.pie(values=[75, 25], names=["Positive","Negative"],
                         hole=0.55,
                         color_discrete_sequence=["#10B981","#EF4444"],
                         template=TEMPLATE)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # ✅ NEW: reviews over time
        st.subheader("📅 Reviews Over Time")
        if not df_filtered.empty:
            fig_rt = px.area(df_filtered, x="Date", y="Reviews",
                             color_discrete_sequence=["#F59E0B"], template=TEMPLATE)
            st.plotly_chart(fig_rt, use_container_width=True)
        else:
            empty_state("No review data for this period.")

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("⭐ Average Rating per Category")
        avg_c = df_places.groupby("Category")["Rating"].mean().reset_index()
        avg_c["Rating"] = avg_c["Rating"].round(2)
        fig_rc = px.bar(avg_c, x="Category", y="Rating",
                        color="Rating", color_continuous_scale="RdYlGn",
                        text_auto=".2f", template=TEMPLATE)
        fig_rc.update_layout(yaxis_range=[0, 5])
        st.plotly_chart(fig_rc, use_container_width=True)

    with col4:
        # ✅ NEW: most reviewed places
        st.subheader("🏆 Most Reviewed Places (Top 8)")
        top_rev = df_places.nlargest(8, "Reviews")
        fig_mr  = px.bar(top_rev, x="Reviews", y="Name", orientation="h",
                         color="Reviews", color_continuous_scale="Oranges",
                         template=TEMPLATE)
        fig_mr.update_layout(yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig_mr, use_container_width=True)

    # ✅ NEW: places with no reviews
    st.subheader("😶 Places With No Reviews Yet")
    no_rev = df_places[df_places["Reviews"] == 0][
        ["Place_ID","Name","Category","District","Status"]
    ]
    if no_rev.empty:
        st.success("All places have at least one review.")
    else:
        st.caption(f"{len(no_rev)} places have no reviews")
        st.dataframe(no_rev.reset_index(drop=True), use_container_width=True)

    # ✅ NEW: flagged reviews table
    st.subheader("🚩 Flagged Reviews")
    st.caption("Reviews reported by users — admin action required")
    st.dataframe(
        flagged_reviews[["Review_ID","User","Place","Review","Rating","Date"]]
        .reset_index(drop=True),
        use_container_width=True,
    )


# ═══════════════════════════════════════════════════════════
# 6. CHATBOT  (fixed + expanded)
# ═══════════════════════════════════════════════════════════
elif selected == "Chatbot":
    st.title("🤖 Chatbot Intelligence")

    total_chats = stats.get("chats", 0)
    resolved    = stats.get("resolved_chats", 0)
    res_pct     = (resolved / total_chats * 100) if total_chats > 0 else 0

    ch1, ch2, ch3, ch4 = st.columns(4)
    ch1.metric("Total Chat Sessions", f"{total_chats:,}")
    ch2.metric("Resolved (AI)",       f"{resolved:,}")
    ch3.metric("Avg Resolution Rate", f"{res_pct:.1f}%")
    ch4.metric("AI Confidence",       "96%")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        # ✅ NEW: chat volume over time
        st.subheader("📅 Chat Volume Over Time")
        fig_cv = px.area(df_filtered, x="Date", y="Chats",
                         color_discrete_sequence=["#055e9b"], template=TEMPLATE)
        st.plotly_chart(fig_cv, use_container_width=True)

    with col2:
        chat_types, top_chat_places = fetch_chatbot_analytics()
        st.subheader("🔍 Query Types Distribution")
        fig_qt = px.pie(chat_types, values="Val", names="Type", hole=0.55,
                        color_discrete_sequence=px.colors.qualitative.Set2,
                        template=TEMPLATE)
        st.plotly_chart(fig_qt, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        # ✅ NEW: most active chatbot places
        st.subheader("🏆 Most Active Chatbot Places")
        fig_tcp = px.bar(top_chat_places.head(8), x="Chats", y="Place",
                         orientation="h", color="Chats",
                         color_continuous_scale="Blues", template=TEMPLATE)
        fig_tcp.update_layout(yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig_tcp, use_container_width=True)

    with col4:
        # ✅ NEW: resolved vs unresolved per place
        st.subheader("✅ Resolved vs Unresolved per Place")
        tcp = top_chat_places.head(6).copy()
        tcp["Unresolved"] = tcp["Chats"] - tcp["Resolved"]
        tcp_m = tcp.melt(id_vars="Place", value_vars=["Resolved","Unresolved"],
                         var_name="Status", value_name="Count")
        fig_ru = px.bar(tcp_m, x="Place", y="Count", color="Status",
                        barmode="stack",
                        color_discrete_map={"Resolved":"#10B981","Unresolved":"#EF4444"},
                        template=TEMPLATE)
        fig_ru.update_xaxes(tickangle=30)
        st.plotly_chart(fig_ru, use_container_width=True)


# ═══════════════════════════════════════════════════════════
# 7. CATEGORY ANALYTICS
# ═══════════════════════════════════════════════════════════
elif selected == "Category Analytics":
    st.title("🏷️ Category Analytics")

    ca1, ca2, ca3, ca4 = st.columns(4)
    ca1.metric("Total Categories",      len(df_places["Category"].unique()))
    ca2.metric("Most Places In",        df_places["Category"].value_counts().idxmax())
    ca3.metric("Most Visited Category", df_places.groupby("Category")["Visits"].sum().idxmax())
    ca4.metric("Most Saved Category",   df_places.groupby("Category")["Saves"].sum().idxmax())

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Use real category stats from API
    df_cat = fetch_category_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Places per Category")
        if not df_cat.empty:
            fig_cc = px.bar(df_cat, x="Category", y="Count",
                            color="Count", color_continuous_scale="Blues",
                            text_auto=True, template=TEMPLATE)
            st.plotly_chart(fig_cc, use_container_width=True)
        else:
            empty_state("No category data available.")

    with col2:
        st.subheader("👁️ Total Visits per Category")
        if not df_places.empty:
            cv = df_places.groupby("Category")["Visits"].sum().reset_index()
            fig_cv = px.bar(cv, x="Category", y="Visits",
                            color="Visits", color_continuous_scale="Greens",
                            text_auto=".2s", template=TEMPLATE)
            st.plotly_chart(fig_cv, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("❤️ Total Saves per Category")
        if not df_places.empty:
            cs = df_places.groupby("Category")["Saves"].sum().reset_index()
            fig_cs = px.pie(cs, values="Saves", names="Category", hole=0.5,
                            color_discrete_sequence=px.colors.qualitative.Set3,
                            template=TEMPLATE)
            st.plotly_chart(fig_cs, use_container_width=True)

    with col4:
        st.subheader("⭐ Average Rating per Category")
        if not df_places.empty:
            ar = df_places.groupby("Category")["Rating"].mean().reset_index()
            ar["Rating"] = ar["Rating"].round(2)
            fig_ar = px.bar(ar, x="Category", y="Rating",
                            color="Rating", color_continuous_scale="RdYlGn",
                            text_auto=".2f", template=TEMPLATE)
            fig_ar.update_layout(yaxis_range=[0, 5])
            st.plotly_chart(fig_ar, use_container_width=True)

    st.subheader("📋 Category Summary Table")
    cat_summary = df_places.groupby("Category").agg(
        Places       =("Place_ID", "count"),
        Total_Visits =("Visits",   "sum"),
        Total_Saves  =("Saves",    "sum"),
        Avg_Rating   =("Rating",   "mean"),
        Total_Reviews=("Reviews",  "sum"),
    ).reset_index()
    cat_summary["Avg_Rating"] = cat_summary["Avg_Rating"].round(2)
    st.dataframe(cat_summary, use_container_width=True)


# ═══════════════════════════════════════════════════════════
# 8. MODERATION
# ═══════════════════════════════════════════════════════════
elif selected == "Moderation":
    st.title("🛡️ Moderation Center")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Flagged Reviews",    len(flagged_reviews))
    m2.metric("Pending Owners",     len(pending_owners))
    m3.metric("Suspended Users",    len(df_users[df_users["Status"] == "Suspended"]))
    m4.metric("Suspended Places",   len(df_places[df_places["Status"] == "Suspended"]))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Flagged reviews — hidden until "View All" pressed ────
    rev_header_col, rev_btn_col = st.columns([4, 1])
    with rev_header_col:
        st.subheader("🚩 Flagged Reviews — Pending Action")
        st.caption("Reported by users · Admin decision required")
    with rev_btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            f"👁️ View All ({len(flagged_reviews)})",
            key="view_all_reviews",
            use_container_width=True,
        ):
            st.session_state.show_all_reviews = not st.session_state.get("show_all_reviews", False)

    if not st.session_state.get("show_all_reviews", False):
        st.markdown(
            f"""
            <div style="background:#FEF3C7;border-left:4px solid #F59E0B;
                        border-radius:8px;padding:14px 18px;color:#92400E;">
                <b>⚠️ {len(flagged_reviews)} reviews</b> are flagged and waiting for your review.
                Press <b>View All</b> to inspect and take action.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info(f"Showing all {len(flagged_reviews)} flagged reviews")
        for _, row in flagged_reviews.iterrows():
            col_info, col_act = st.columns([4, 1])
            with col_info:
                st.markdown(
                    f"**{row['Review_ID']}** &nbsp;·&nbsp; 📍 {row['Place']} "
                    f"&nbsp;·&nbsp; ⭐ {row['Rating']} &nbsp;·&nbsp; 👤 {row['User']}"
                )
                st.caption(f"_{row['Review']}_")
            with col_act:
                if st.button("🗑️ Delete", key=f"del_{row['Review_ID']}"):
                    if delete_review(row['Review_ID']):
                        st.rerun()
                if st.button("✅ Keep",   key=f"keep_{row['Review_ID']}"):
                    st.toast(f"Review {row['Review_ID']} kept.")
            st.divider()

    # ── Pending owners — hidden until "View All" pressed ─────
    own_header_col, own_btn_col = st.columns([4, 1])
    with own_header_col:
        st.subheader("👤 New Owners Pending Verification")
        st.caption("Submitted accounts awaiting admin approval")
    with own_btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            f"👁️ View All ({len(pending_owners)})",
            key="view_all_owners",
            use_container_width=True,
        ):
            st.session_state.show_all_owners = not st.session_state.get("show_all_owners", False)

    if not st.session_state.get("show_all_owners", False):
        st.markdown(
            f"""
            <div style="background:#EFF6FF;border-left:4px solid #2563EB;
                        border-radius:8px;padding:14px 18px;color:#1E40AF;">
                <b>📋 {len(pending_owners)} owner requests</b> are pending verification.
                Press <b>View All</b> to review and approve or reject them.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info(f"Showing all {len(pending_owners)} pending owner requests")
        for _, row in pending_owners.iterrows():
            col_info, col_act = st.columns([4, 1])
            with col_info:
                st.markdown(
                    f"**{row['Owner_ID']}** &nbsp;·&nbsp; {row['Name']} "
                    f"&nbsp;·&nbsp; {row['Business']} &nbsp;·&nbsp; 🏷️ {row['Category']}"
                )
                st.caption(f"Submitted: {row['Submitted']}")
            with col_act:
                if st.button("✅ Approve", key=f"apr_{row['Owner_ID']}"):
                    if approve_owner(row['Owner_ID'], verified=True):
                        st.rerun()
                if st.button("❌ Reject",  key=f"rej_{row['Owner_ID']}"):
                    if approve_owner(row['Owner_ID'], verified=False):
                        st.rerun()
            st.divider()

    # ── Suspended users ──────────────────────────────────────
    st.subheader("🚫 Suspended Users")
    sus_u = df_users[df_users["Status"] == "Suspended"][
        ["User_ID","Name","District","Reviews","Joined"]
    ].head(10).reset_index(drop=True)
    st.dataframe(sus_u, use_container_width=True)

    # ── Suspended places ─────────────────────────────────────
    st.subheader("🏚️ Suspended Places")
    sus_p = df_places[df_places["Status"] == "Suspended"][
        ["Place_ID","Name","Category","District","Rating"]
    ].head(10).reset_index(drop=True)
    st.dataframe(sus_p, use_container_width=True)

    # ── Admin action history ─────────────────────────────────
    st.subheader("📋 Admin Action History")
    st.table(admin_log)

    # ── Create Bare Owner Account ──────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("➕ Create New Owner Account")
    st.caption("Onboard a new Store or Property owner by giving them credentials")
    
    with st.form("create_owner_form"):
        co_col1, co_col2 = st.columns(2)
        with co_col1:
            co_name = st.text_input("Full Name *")
            co_email = st.text_input("Email *")
        with co_col2:
            co_pwd = st.text_input("Password *", type="password")
            st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
            co_submit = st.form_submit_button("🚀 Create Owner Account", use_container_width=True)
            
        if co_submit:
            if not co_name or not co_email or not co_pwd:
                st.error("Please fill all required fields (*)")
            else:
                with st.spinner("Creating account..."):
                    res, err = create_owner_api({
                        "full_name": co_name,
                        "email": co_email,
                        "password": co_pwd
                    })
                    if res:
                        st.success(f"✅ Owner account created for {co_email} (ID: {res['id']})")
                        st.balloons()
                    else:
                        st.error(f"❌ Failed to create owner: {err}")



# ═══════════════════════════════════════════════════════════
# 9. ANOMALY DETECTION
# ═══════════════════════════════════════════════════════════
elif selected == "Anomaly Detection":
    st.title("🚨 Anomaly Detection")

    # ── Fetch anomalies from API ──────────────────────────────────
    @st.cache_data(ttl=120)
    def fetch_real_anomalies():
        """Calls /detect on the anomaly detection API using real interactions."""
        df_int = fetch_recent_interactions(limit=1000)
        if df_int.empty:
            return [], 0
            
        try:
            # Prepare data: align schema (lat/lon) and sanitize NaNs
            visits = df_int.rename(columns={"user_lat": "lat", "user_lon": "lon"}).replace({np.nan: None}).to_dict(orient="records")
            resp = requests.post(
                f"{ANOMALY_API}/detect",
                json={"visits": visits},
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("anomalies", []), data.get("total_anomalies", 0)
            else:
                st.warning(f"Anomaly API returned {resp.status_code}")
        except Exception as e:
            st.error(f"Anomaly Detection Connection error: {e}")
        return [], 0

    @st.cache_data(ttl=120)
    def fetch_anomaly_summary(anomalies):
        """Calls POST /summary on the anomaly detection API."""
        try:
            if not anomalies:
                return []
            resp = requests.post(
                f"{ANOMALY_API}/summary",
                json={"anomalies": anomalies},
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json()["summary"]
        except Exception:
            pass
        return []

    with st.spinner("Analyzing real-time interactions..."):
        anomalies, total_anomalies = fetch_real_anomalies()
    
    summary = fetch_anomaly_summary(anomalies) if anomalies else []

    # ── KPI cards ─────────────────────────────────────────────────
    high_count   = len([a for a in anomalies if a["severity"] == "High"])
    medium_count = len([a for a in anomalies if a["severity"] == "Medium"])
    top_district = summary[0]["cluster"] if summary else "N/A"

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Total Anomalies",     total_anomalies)
    a2.metric("🔴 High Severity",    high_count)
    a3.metric("🟡 Medium Severity",  medium_count)
    a4.metric("Most Affected Cluster", f"Cluster {top_district}" if summary else "N/A")

    st.markdown("<br>", unsafe_allow_html=True)

    if not anomalies:
        st.info("ℹ️ No anomalies detected or API unavailable.")
    else:
        col1, col2 = st.columns(2)

        # ── Anomaly by Type chart ─────────────────────────────────
        with col1:
            st.subheader("📊 Anomalies by Type")
            type_counts = pd.DataFrame(anomalies)["anomaly_type"].value_counts().reset_index()
            type_counts.columns = ["Type", "Count"]
            fig_at = px.bar(type_counts, x="Count", y="Type", orientation="h",
                            color="Count", color_continuous_scale="Reds",
                            text_auto=True, template=TEMPLATE)
            fig_at.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_at, use_container_width=True)

        # ── Severity Distribution ─────────────────────────────────
        with col2:
            st.subheader("🔴 Severity Distribution")
            sev_counts = pd.DataFrame(anomalies)["severity"].value_counts().reset_index()
            sev_counts.columns = ["Severity", "Count"]
            fig_sev = px.pie(sev_counts, values="Count", names="Severity", hole=0.55,
                             color_discrete_map={"High": "#EF4444", "Medium": "#F59E0B"},
                             template=TEMPLATE)
            st.plotly_chart(fig_sev, use_container_width=True)

        # ── Anomaly Heatmap per Cluster ───────────────────────────
        if summary:
            st.subheader("🗺️ Anomaly Activity per Cluster")
            sum_df = pd.DataFrame(summary)
            fig_cl = px.bar(sum_df, x="cluster", y="total_anomalies",
                            color="total_anomalies", color_continuous_scale="Reds",
                            text_auto=True, template=TEMPLATE,
                            labels={"cluster": "Cluster", "total_anomalies": "Total Anomalies"})
            fig_cl.update_xaxes(type="category")
            st.plotly_chart(fig_cl, use_container_width=True)

        # ── Live Anomaly Feed ─────────────────────────────────────
        st.subheader("📋 Live Anomaly Feed")
        st.caption(f"Showing {len(anomalies)} flagged anomalies — sorted by score")

        for a in anomalies:
            col_info, col_act = st.columns([5, 1])
            severity_badge = "🔴" if a["severity"] == "High" else "🟡"
            with col_info:
                st.markdown(
                    f"{severity_badge} **{a['anomaly_type'].replace('_', ' ').title()}** "
                    f"&nbsp;·&nbsp; Score: `{a['score']}` "
                    f"&nbsp;·&nbsp; Place: `{a['place_id']}` "
                    f"&nbsp;·&nbsp; User: `{a['user_id']}` "
                    f"&nbsp;·&nbsp; Cluster: `{a['cluster']}`"
                )
                st.caption(f"_{a['details']}_")
            with col_act:
                if a["severity"] == "High":
                    st.button("🚫 Suspend", key=f"sus_{a['place_id']}_{a['user_id']}_{a['anomaly_type']}")
                st.button("✅ Dismiss", key=f"dis_{a['place_id']}_{a['user_id']}_{a['anomaly_type']}")
            st.divider()


# ═══════════════════════════════════════════════════════════
# 10. LOCATION LOGIC
# ═══════════════════════════════════════════════════════════
elif selected == "Location Logic":
    st.title("📍 Location Logic")
    st.markdown("See where your visitors are coming from — all time and recently active.")

    BS_LAT, BS_LON = 29.0661, 31.0994

    # --- Fetch real hotspots from clustering API ---
    @st.cache_data(ttl=300)
    def fetch_heatmap_data():
        df_int = fetch_recent_interactions(limit=1000)
        if df_int.empty: return None
        try:
            visits = df_int.rename(columns={"user_lat": "lat", "user_lon": "lon"}).replace({np.nan: None}).to_dict(orient="records")
            resp = requests.post(f"{CLUSTERING_API}/heatmap", json={"visits": visits}, timeout=20)
            if resp.status_code == 200: return resp.json().get("hotspots")
        except: pass
        return None

    @st.cache_data(ttl=300)
    def fetch_opportunities():
        """Calls POST /opportunities on the clustering API using current district/category context."""
        try:
            # We fetch all places to understand existing distribution
            df_p = fetch_all_places()
            df_i = fetch_recent_interactions(limit=1000)
            
            if df_p.empty or df_i.empty:
                return None

            places = df_p[["Category", "District"]].rename(columns={"Category":"category", "District":"district"}).to_dict(orient="records")
            visits = df_i[["cluster"]].to_dict(orient="records") # The API might need more, but let's see
            
            resp = requests.post(
                f"{CLUSTERING_API}/opportunities",
                json={"visits": visits, "places": places},
                timeout=20,
            )
            if resp.status_code == 200:
                return resp.json().get("opportunities")
        except Exception as e:
            st.warning(f"Clustering API Opportunities Error: {e}")
        return None

    hotspots      = fetch_heatmap_data()
    opportunities = fetch_opportunities()

    # ── Controls row ─────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 1, 1, 1])

    with ctrl1:
        window_label = st.selectbox(
            "Active session window",
            options=["Last 15 minutes", "Last 1 hour", "Last 3 hours",
                     "Last 6 hours", "Last 24 hours"],
            index=1,
        )
        window_map = {
            "Last 15 minutes": 15,
            "Last 1 hour":     60,
            "Last 3 hours":    180,
            "Last 6 hours":    360,
            "Last 24 hours":   1440,
        }
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

    # Prepare Data
    df_i = fetch_recent_interactions(limit=1000)
    df_active = filter_active(df_i, active_minutes)
    
    # Calculate Metrics
    total_visitors = len(df_i["user_id"].unique()) if not df_i.empty else 0
    active_now = len(df_active)
    
    # Peak Hour Logic (Historical)
    peak_hour_str = "N/A"
    if not df_i.empty:
        df_i['hour'] = pd.to_datetime(df_i['visited_at']).dt.hour
        if not df_i['hour'].isna().all():
            peak_hour = df_i['hour'].mode().iloc[0]
            peak_hour_str = f"{peak_hour}:00"

    # ── KPI cards ─────────────────────────────────────────────────────
    k1, k2, k3 = st.columns(3)
    k1.markdown(f"""<div class="kpi-card">
        <div class="kpi-title">👥 Total Visitors (all time)</div>
        <div class="kpi-value">{total_visitors}</div>
        <div class="kpi-delta">Recorded map interactions</div>
    </div>""", unsafe_allow_html=True)

    k2.markdown(f"""<div class="kpi-card">
        <div class="kpi-title">🟢 Active Visitors</div>
        <div class="kpi-value">{active_now}</div>
        <div class="kpi-delta">AI Live Detection</div>
    </div>""", unsafe_allow_html=True)

    k3.markdown(f"""<div class="kpi-card">
        <div class="kpi-title">⏳ Peak Traffic Hour</div>
        <div class="kpi-value">{peak_hour_str}</div>
        <div class="kpi-delta">AI Predicted Focus Time</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Render Map
    with st.container():
        m = build_location_map(
            all_locations=df_i,
            show_pins=show_pins,
            show_heatmap=show_heatmap,
            places_list=df_places,
            center_lat=BS_LAT,
            center_lon=BS_LON,
            active_df=df_active if show_pins else None
        )
        st_folium(m, use_container_width=True, height=520)
        
    # Legend
    st.markdown("""
    <div style='font-size:13px; color:#65797E; margin-top:8px; display:flex; gap:20px;'>
        <span>🔴 <b>All Registered Places</b></span>
        <span>🔵 <b>Active visitors (pins)</b></span>
        <span>🌡️ <b>All visitors density (heatmap)</b></span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Analytics Below Map ───────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🗺️ Most Active Districts")
        dc = df_places["District"].value_counts().reset_index()
        dc.columns = ["District","Places"]
        fig_dc = px.bar(dc, x="Places", y="District", orientation="h",
                        color="Places", color_continuous_scale="Blues",
                        template=TEMPLATE)
        fig_dc.update_layout(yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig_dc, use_container_width=True)

    with col2:
        st.subheader("🏷️ Places per District per Category")
        dcat = df_places.groupby(["District","Category"]).size().reset_index(name="Count")
        fig_dcat = px.bar(dcat, x="District", y="Count", color="Category",
                          barmode="stack", template=TEMPLATE)
        st.plotly_chart(fig_dcat, use_container_width=True)

    # ── Opportunity Map ──────────────────────────────────────────
    st.subheader("💡 Opportunity Map")
    if opportunities:
        st.caption("🟢 Live data from Location Clustering API")
        for opp in opportunities[:6]:
            urgency = opp["urgency"]
            msg = opp["message"]
            if urgency == "High": st.error(f"🔴 {msg}")
            elif urgency == "Medium": st.warning(f"🟡 {msg}")
            else: st.info(f"🔵 {msg}")
    else:
        st.caption("⚠️ API unavailable — showing market heuristics")
        st.success("📍 'New Beni Suef' has high search volume for Pharmacies but 0 registered.")
        st.info   ("📍 'Nile Corniche' has the highest concentration of Direction Clicks.")
        st.warning("📍 'El Wasta' has only 1 Cafe — potential market gap.")


# ═══════════════════════════════════════════════════════════
# 11. DATABASE MANAGER
# ═══════════════════════════════════════════════════════════
elif selected == "Database Manager":
    st.title("🗄️ Database Manager")
    st.caption("Direct CRUD access to all system tables. Use with caution.")

    tables = list_db_tables()
    if not tables:
        st.error("Could not fetch tables or API is unavailable.")
        st.stop()

    t_col1, t_col2 = st.columns([1, 2])
    with t_col1:
        target_table = st.selectbox("Select Table to Manage", tables)
    
    if target_table:
        content = fetch_table_content(target_table)
        cols = content.get("columns", [])
        data = content.get("data", [])
        
        df = pd.DataFrame(data, columns=cols)
        
        tab_view, tab_add = st.tabs(["👁️ View & Edit Data", "➕ Add New Record"])
        
        with tab_view:
            st.subheader(f"Table: {target_table}")
            st.info("💡 You can edit cells directly in the table below. Use the 'Save Changes' button to apply.")
            
            # Data Editor for editing/deleting
            edited_df = st.data_editor(
                df, 
                num_rows="dynamic", 
                use_container_width=True,
                key=f"editor_{target_table}",
                disabled=["id"] if "id" in cols else []
            )
            
            if st.button("💾 Save Changes", use_container_width=True):
                # Simple logic for updates/deletes in st.data_editor is complex for generic tables.
                # For this generic tool, we focus on manual edits for now or bulk update if possible.
                # But st.data_editor 'edited_rows' is the way.
                state = st.session_state.get(f"editor_{target_table}")
                if state:
                    edited = state.get("edited_rows", {})
                    deleted = state.get("deleted_rows", [])
                    added = state.get("added_rows", [])
                    
                    success_count = 0
                    
                    # Handle Deletes
                    for idx in deleted:
                        row_id = df.iloc[idx]["id"] if "id" in df.columns else None
                        if row_id and delete_db_record(target_table, row_id):
                            success_count += 1
                    
                    # Handle Edits
                    for idx, values in edited.items():
                        row_id = df.iloc[int(idx)]["id"] if "id" in df.columns else None
                        if row_id and update_db_record(target_table, row_id, values):
                            success_count += 1
                    
                    if success_count > 0:
                        st.success(f"Successfully processed {success_count} changes!")
                        st.rerun()
                    elif not edited and not deleted:
                        st.info("No changes detected.")

        with tab_add:
            st.subheader(f"Add to {target_table}")
            with st.form(f"add_row_{target_table}"):
                new_row_data = {}
                # Create form fields dynamically
                # Sort columns into 2 columns for better layout
                f_col1, f_col2 = st.columns(2)
                for i, c in enumerate(cols):
                    if c == "id" or c == "created_at" or c == "updated_at":
                        continue
                    
                    target_col = f_col1 if i % 2 == 0 else f_col2
                    with target_col:
                        # Heuristic for input type
                        if "is_" in c or "has_" in c:
                            new_row_data[c] = st.checkbox(c)
                        elif "id" in c and c != "id": # likely foreign key
                            new_row_data[c] = st.number_input(c, step=1, value=0)
                        elif "price" in c or "lat" in c or "lon" in c:
                            new_row_data[c] = st.number_input(c, format="%.6f", value=0.0)
                        else:
                            new_row_data[c] = st.text_input(c)
                
                if st.form_submit_button("🚀 Insert Record", use_container_width=True):
                    if insert_db_record(target_table, new_row_data):
                        st.success("Record inserted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to insert record. Check data types and constraints.")