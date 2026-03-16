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
    background-color: #F8F9FB;
}

[data-testid="stHeader"] {
    background-color: rgba(255, 255, 255, 0);
}

h1, h2, h3 {
    color: #1D3143;
    font-weight: 700 !important;
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
my_place = fetch_my_place()
place_name = my_place.get("name", "AroundU") if my_place else "AroundU"

with st.sidebar:
    st.title(f"🏙️ {place_name}")
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
        
        metrics = ['visits', 'saves', 'calls']
        curr_vals = [data[m] for m in metrics]
        prev_vals = [prev_data[m] for m in metrics]
        
        growth_data = pd.DataFrame({
            'Metric': [m.capitalize() for m in metrics] * 2,
            'Value': curr_vals + prev_vals,
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
nd_title_text='Query Type', margin=dict(t=20, b=20, l=20, r=20), height=400)# =========================
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
    st.title("⚙️ Manage Your Place")
    st.info("Update your business details visible to customers.")
    
    place = fetch_my_place()
    categories = fetch_categories()
    
    if place and categories:
        # Map category name to ID for the selectbox
        cat_options = {c['name']: c['id'] for c in categories}
        current_cat_name = next((name for name, id in cat_options.items() if id == place.get('category_id')), "Cafe")

        with st.form("edit_place_form"):
            name = st.text_input("Business Name", value=place.get("name", ""))
            description = st.text_area("Description", value=place.get("description", ""), height=150)
            
            # --- CATEGORY DROPDOWN ---
            selected_cat_name = st.selectbox("Category", options=list(cat_options.keys()), index=list(cat_options.keys()).index(current_cat_name) if current_cat_name in cat_options else 0)
            
            address = st.text_input("Address", value=place.get("address", ""))
            phone = st.text_input("Phone", value=place.get("phone", ""))
            website = st.text_input("Website", value=place.get("website", ""))
            
            st.markdown("### 📍 Location")
            st.info("Paste a Google Maps link to automatically update coordinates.")
            loc_link = st.text_input("Google Maps Link", placeholder="https://www.google.com/maps/...")
            
            with st.expander("Raw Coordinates (Optional)"):
                c1, c2 = st.columns(2)
                with c1:
                    lat = st.number_input("Latitude", value=place.get("latitude", 0.0), format="%.6f")
                with c2:
                    lon = st.number_input("Longitude", value=place.get("longitude", 0.0), format="%.6f")
            
            # --- SOCIAL MEDIA LINKS ---
            st.markdown("### 📱 Social Media")
            with st.expander("Social Media & Contact Links"):
                facebook = st.text_input("Facebook URL", value=place.get("facebook_url", ""))
                instagram = st.text_input("Instagram URL", value=place.get("instagram_url", ""))
                tiktok = st.text_input("TikTok URL", value=place.get("tiktok_url", ""))
                whatsapp = st.text_input("WhatsApp Number", value=place.get("whatsapp_number", ""), help="e.g. +201234567890")
            
            submit = st.form_submit_button("Save Changes", use_container_width=True)
            if submit:
                update_data = {
                    "name": name,
                    "description": description,
                    "category_id": cat_options[selected_cat_name],
                    "address": address,
                    "phone": phone,
                    "website": website,
                    "latitude": lat,
                    "longitude": lon,
                    "facebook_url": facebook,
                    "instagram_url": instagram,
                    "whatsapp_number": whatsapp,
                    "tiktok_url": tiktok
                }
                if loc_link:
                    update_data["location_link"] = loc_link
                
                update_place_details(place.get("id"), update_data)
        
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
                    if img_url.startswith("/"):
                        base = BACKEND_BASE_URL.replace('/api', '').rstrip('/')
                        if img_url.startswith("/uploads/"):
                            img_url = f"{base}{img_url}"
                        else:
                            img_url = f"{base}/uploads{img_url}"
                    
                    st.image(img_url, use_container_width=True)
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
                    if img_url.startswith("/"):
                        base = BACKEND_BASE_URL.replace('/api', '').rstrip('/')
                        if img_url.startswith("/uploads/"):
                            img_url = f"{base}{img_url}"
                        else:
                            img_url = f"{base}/uploads{img_url}"
                        
                    st.image(img_url, use_container_width=True)
                    if img.get("caption"):
                        st.caption(img["caption"])
                    if st.button("Remove", key=f"del_menu_{img['id']}", type="secondary", icon="🗑️"):
                        delete_place_image(img['id'])
        else:
            st.info("No menu photos uploaded yet.")
    else:
        st.error("Could not load data. Please refresh.")

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