import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from streamlit_option_menu import option_menu
from datetime import datetime, timedelta
import requests
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="AroundU | Owner Dashboard", layout="wide")

st.markdown("""
<style>

.stApp {
    background-color: #FFFFFF;
}

h1, h2, h3 {
    color: #1D3143;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #1D3143;
}

section[data-testid="stSidebar"] * {
    color: white;
}

/* KPI Cards */
.kpi-card {
    background: #FFFFFF;
    padding: 22px;
    border-radius: 14px;
    border-left: 6px solid #2F5C85;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transition: all 0.25s ease;
    cursor: pointer;
}

.kpi-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.12);
    border-left: 6px solid #61A3BB;
}

.kpi-title { font-size: 14px; color: #65797E; }
.kpi-value { font-size: 34px; font-weight: bold; color: #1D3143; }
.kpi-delta { font-size: 14px; color: #61A3BB; }

/* DATE INPUT */
[data-baseweb="input"] input {
    color: #1D3143 !important;
    font-weight: 500 !important;
}
div[data-baseweb="input"] span {
    color: #1D3143 !important;
}

/* CALENDAR - أسماء أيام الأسبوع */
[data-baseweb="calendar"] [role="columnheader"] {
    color: #65797E !important;
    font-weight: 600 !important;
}

/* اليوم الحالي */
[data-baseweb="calendar"] [aria-current="date"] {
    border: 2px solid #2F5C85 !important;
    border-radius: 50% !important;
}

/* إزالة outline */
button:focus, button:focus-visible {
    outline: none !important;
    box-shadow: none !important;
}

</style>
""", unsafe_allow_html=True)


# --- CONFIGURATION ---
BACKEND_BASE_URL = "https://aroundubackend-production.up.railway.app/api"

# --- AUTHENTICATION LOGIC ---
def login_user(email, password):
    try:
        response = requests.post(
            f"{BACKEND_BASE_URL}/mobile/auth/login",
            data={"username": email, "password": password}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            return None
    except Exception as e:
        st.error(f"Login error: {e}")
        return None

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
    return {"visits": 0, "orders": 0, "saves": 0, "calls": 0, "directions": 0}

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
    return pd.DataFrame(columns=['Date', 'Visits', 'Orders', 'Saves', 'Directions', 'Calls', 'Review_sentiment'])

@st.cache_data(ttl=30)
def fetch_chatbot_stats(start_date, end_date):
    try:
        params = {"start_date": start_date, "end_date": end_date}
        res = requests.get(f"{BACKEND_BASE_URL}/owner/chatbot-stats", params=params, headers=get_headers())
        if res.status_code == 200: return res.json()
        handle_api_error(res)
    except: pass
    return {"queries": 0, "success_rate": 0.0}

def fetch_my_place():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/owner/my-place", headers=get_headers())
        if res.status_code == 200: return res.json()
        if res.status_code != 401:
            st.error(f"Backend returned {res.status_code}: {res.text}")
        handle_api_error(res)
    except Exception as e:
        st.error(f"Connection error: {e}")
    return None

def update_place_details(place_id, data):
    try:
        res = requests.put(f"{BACKEND_BASE_URL}/dashboard/places/{place_id}", json=data, headers=get_headers())
        if res.status_code == 200:
            st.success("✅ Place updated successfully!")
            return True
        st.error(f"❌ Failed to update: {res.text}")
    except Exception as e:
        st.error(f"Error: {e}")
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
def fetch_location_data():
    try:
        res = requests.get(f"{BACKEND_BASE_URL}/owner/location-heatmap", headers=get_headers())
        if res.status_code == 200: return pd.DataFrame(res.json())
        handle_api_error(res)
    except: pass
    return pd.DataFrame()

# --- MAIN APP LOGIC ---
if 'token' not in st.session_state:
    st.session_state.token = None

if st.session_state.token is None:
    # --- LOGIN SCREEN ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://raw.githubusercontent.com/AbdallahMohamedFathy/AroundU__Backend/main/logo.png", width=100) # Placeholder for logo
        st.title("🏙️ Welcome to AroundU")
        st.subheader("Owner Dashboard Login")
        
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                token = login_user(email, password)
                if token:
                    st.session_state.token = token
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
    st.stop()

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.title("🏙️ AroundU")
    st.caption("Beni Suef Business Intelligence")

    selected = option_menu(
        "Main Menu",
        options=["Dashboard", "Customer Insights", "Operations", "Location Logic", "Manage Place"],
        icons=['speedometer2', 'chat-square-text', 'clock-history', 'geo-alt', 'gear'],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"background-color": "#1D3143", "padding": "5px"},
            "menu-title": {"color": "#FFFFFF", "font-weight": "bold", "font-size": "15px"},
            "icon": {"color": "#61A3BB", "font-size": "18px"},
            "nav-link": {
                "color": "white", "font-size": "16px",
                "text-align": "left", "margin": "2px",
                "--hover-color": "#619FB8",
            },
            "nav-link-selected": {
                "background-color": "#2F5C85",
                "color": "white", "font-weight": "bold"
            }
        }
    )

    st.markdown("---")
    
    st.markdown("### 📅 Select Date Range")
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
        
        metrics = ['visits', 'orders', 'saves', 'calls']
        curr_vals = [data[m] for m in metrics]
        prev_vals = [prev_data[m] for m in metrics]
        
        growth_data = pd.DataFrame({
            'Metric': [m.capitalize() for m in metrics] * 2,
            'Value': curr_vals + prev_vals,
            'Period': ['Selected Period'] * 4 + ['Previous Period'] * 4
        })
        fig_growth = px.bar(growth_data, x='Metric', y='Value', color='Period',
            barmode='group', text='Value', text_auto='.2s',
            color_discrete_map={'Selected Period': '#2F5C85', 'Previous Period': '#61A3BB'},
            template="plotly_white")
        fig_growth.update_traces(textposition='outside')
        fig_growth.update_layout(yaxis_title='Total Count', xaxis_title='Metric',
            margin=dict(t=40, b=40, l=40, r=40))
        st.plotly_chart(fig_growth, use_container_width=True)

    with col_right:
        st.subheader("🤖 Chatbot Stats")
        bot_stats = fetch_chatbot_stats(start_date, end_date)
        st.metric("Bot Resolution Rate", f"{bot_stats['success_rate']:.1f}%")
        query_types = pd.DataFrame({'Type': ['Menu', 'Hours', 'Location', 'Pricing'], 'Val': [40, 30, 20, 10]})
        fig_pie = px.pie(query_types, values='Val', names='Type', hole=0.5, color='Type',
            color_discrete_map={'Menu': '#2F5C85', 'Hours': '#61A3BB', 'Location': '#65797E', 'Pricing': '#1D3143'})
        fig_pie.update_traces(textinfo='percent+label', textfont_size=14,
            pull=[0.02, 0.04, 0.02, 0.04], marker=dict(line=dict(color='#FFFFFF', width=2)))
        fig_pie.update_layout(legend_title_text='Query Type', margin=dict(t=20, b=20, l=20, r=20), height=400)# =========================
# 2️⃣ CUSTOMER INSIGHTS
# =========================
elif selected == "Customer Insights":
    st.title("🤖 Customer & Review Analysis")
    reviews = fetch_review_data(start_date, end_date)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Customer Sentiment Overview")
        if reviews['positive'] > 0 or reviews['negative'] > 0:
            sentiment_df = pd.DataFrame({
                'Sentiment': ['Positive', 'Negative'],
                'Count': [reviews['positive'], reviews['negative']]
            })
            fig_reviews = px.bar(sentiment_df, x='Sentiment', y='Count', 
                color='Sentiment',
                color_discrete_map={'Positive': '#61A3BB', 'Negative': '#65797E'},
                template="plotly_white")
            st.plotly_chart(fig_reviews, use_container_width=True)
        else:
            st.info("No review data available for this period.")
        
    with c2:
        st.subheader("Review Ratings Overview")
        st.markdown(f"""
        <div style="background:#F8F9FA; padding:20px; border-radius:10px; border-left:5px solid #2F5C85;">
            <p style="color:#65797E; margin-bottom:5px;">Total Reviews in period</p>
            <h2 style="color:#1D3143; margin:0;">{reviews['positive'] + reviews['negative']}</h2>
        </div>
        """, unsafe_allow_html=True)

# =========================
# 5️⃣ MANAGE PLACE
# =========================
elif selected == "Manage Place":
    st.title("⚙️ Manage Your Place")
    st.info("Update your business details visible to customers.")
    
    place = fetch_my_place()
    if place:
        with st.form("edit_place_form"):
            name = st.text_input("Business Name", value=place.get("name", ""))
            description = st.text_area("Description", value=place.get("description", ""), height=150)
            address = st.text_input("Address", value=place.get("address", ""))
            phone = st.text_input("Phone", value=place.get("phone", ""))
            website = st.text_input("Website", value=place.get("website", ""))
            
            c1, c2 = st.columns(2)
            with c1:
                lat = st.number_input("Latitude", value=place.get("latitude", 0.0), format="%.6f")
            with c2:
                lon = st.number_input("Longitude", value=place.get("longitude", 0.0), format="%.6f")
            
            submit = st.form_submit_button("Save Changes")
            if submit:
                update_data = {
                    "name": name,
                    "description": description,
                    "address": address,
                    "phone": phone,
                    "website": website,
                    "latitude": lat,
                    "longitude": lon
                }
                update_place_details(place.get("id"), update_data)
    else:
        st.error("Could not fetch place details. Please try again.")

elif selected == "Operations":
    st.title("⏰ Operational Efficiency")
    st.info("Operational analytics based on historical interaction patterns.")
    
    df = fetch_analytics_data(start_date, end_date)
    if not df.empty and 'Date' in df.columns:
        df['Hour'] = df['Date'].dt.hour
        df['Day'] = df['Date'].dt.day_name()
        
        st.subheader("Hourly Interaction Volume")
        fig_line = px.line(df, x='Date', y=['Visits', 'Calls'], 
            color_discrete_sequence=['#2F5C85', '#61A3BB'],
            title="Interaction Trends Over Time")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("Insufficient data to display operational trends.")

# =========================
# 4️⃣ LOCATION LOGIC
# =========================
elif selected == "Location Logic":
    st.title("📍 Location Analysis: Beni Suef")
    map_data = fetch_location_data()
    
    BS_LAT, BS_LON = 29.0661, 31.0994
    if not map_data.empty:
        fig_map = px.density_mapbox(map_data, lat='lat', lon='lon', z='intensity',
            radius=15, center=dict(lat=BS_LAT, lon=BS_LON), zoom=15,
            mapbox_style="open-street-map", height=700)
        fig_map.update_layout(
            coloraxis_colorbar=dict(title="Intensity",
                title_font=dict(color="#1D3143"), tickfont=dict(color="#1D3143")),
            margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No location interaction data available for this selection.")
else:
        st.warning("No location data available for the current selection.")