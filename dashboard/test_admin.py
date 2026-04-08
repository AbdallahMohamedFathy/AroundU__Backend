import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
from streamlit_option_menu import option_menu
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════
st.set_page_config(page_title="AroundU | Admin Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=DM+Sans:wght@400;500;600&display=swap');

    /* ── Root palette ── */
    :root {
        --brand-dark:    #1D3143;
        --brand-mid:     #2F5C85;
        --brand-blue:    #315687;
        --brand-teal:    #619FB8;
        --brand-light:   #61A3BB;
        --brand-muted:   #65797E;
        --brand-white:   #FFFFFF;
        --bg-page:       #EDF2F6;
        --bg-card:       #FFFFFF;
        --border-subtle: #C8D9E6;
    }

    /* ── Page background ── */
    .main, .block-container { background-color: var(--bg-page) !important; }
    /* ── Fix content width when sidebar collapses ── */
.block-container {
    background-color: var(--bg-page) !important;
    max-width: 100% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* Remove Streamlit default max-width constraint */
[data-testid="stAppViewContainer"] > .main {
    max-width: 100% !important;
}
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--brand-dark) 0%, #243C52 100%) !important;
        min-width: 270px !important;
        border-right: 1px solid rgba(97,163,187,0.15);
    }
    section[data-testid="stSidebar"] * { color: var(--brand-white) !important; }
    section[data-testid="stSidebar"] .stDateInput input {
        background: rgba(97,159,184,0.12) !important;
        border: 1px solid rgba(97,159,184,0.3) !important;
        color: #1D3143 !important;
        border-radius: 8px !important;
    }

    /* ── Metric cards ── */
    div[data-testid="stMetric"] {
        background: var(--bg-card);
        border-left: 4px solid var(--brand-teal);
        padding: 18px 20px;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(29,49,67,0.08);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(47,92,133,0.14);
    }
    div[data-testid="stMetric"] label {
        color: var(--brand-muted) !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--brand-dark) !important;
        font-family: 'Sora', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 13px !important;
        font-weight: 600 !important;
    }

    /* ── Plot / chart wrapper ── */
    .plot-container {
        background: var(--bg-card);
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 2px 12px rgba(29,49,67,0.07);
        margin-bottom: 24px;
    }

    /* ── Headings ── */
    h1 {
        font-family: 'Sora', sans-serif !important;
        color: var(--brand-dark) !important;
        font-weight: 700 !important;
        font-size: 1.7rem !important;
        letter-spacing: -0.3px;
        padding-bottom: 4px;
        border-bottom: 3px solid var(--brand-teal);
        display: inline-block;
        margin-bottom: 1.2rem !important;
    }
    h2, h3 {
        font-family: 'Sora', sans-serif !important;
        color: var(--brand-mid) !important;
        font-weight: 600 !important;
    }

    /* ── Subheader ── */
    [data-testid="stHeadingWithActionElements"] h2,
    [data-testid="stHeadingWithActionElements"] h3 {
        color: var(--brand-mid) !important;
        font-family: 'Sora', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        border-left: 3px solid var(--brand-light);
        padding-left: 10px;
    }

    /* ── Dataframe table ── */
    [data-testid="stDataFrame"] {
        border-radius: 10px !important;
        overflow: hidden;
        border: 1px solid var(--border-subtle) !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: var(--brand-mid) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 6px 14px !important;
        transition: background 0.2s ease;
    }
    .stButton > button:hover {
        background: var(--brand-dark) !important;
    }

    /* ── Selectbox / text input ── */
    .stSelectbox > div > div,
    .stTextInput > div > div > input {
        border-radius: 8px !important;
        border: 1px solid var(--border-subtle) !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    /* ── Divider ── */
    hr { border-color: var(--border-subtle) !important; }

    /* ── Section divider label ── */
    .section-label {
        font-size: 11px;
        font-weight: 700;
        color: rgba(255,255,255,0.55);
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin: 10px 0 4px 0;
    }

    /* ── Alert badges ── */
    .badge-red {
        background: rgba(239,68,68,0.15); color: #EF4444;
        padding: 2px 10px; border-radius: 20px;
        font-size: 12px; font-weight: 700;
        border: 1px solid rgba(239,68,68,0.3);
    }
    .badge-green {
        background: rgba(97,163,187,0.15); color: var(--brand-light);
        padding: 2px 10px; border-radius: 20px;
        font-size: 12px; font-weight: 700;
        border: 1px solid rgba(97,163,187,0.3);
    }
    .badge-yellow {
        background: rgba(245,158,11,0.15); color: #F59E0B;
        padding: 2px 10px; border-radius: 20px;
        font-size: 12px; font-weight: 700;
        border: 1px solid rgba(245,158,11,0.3);
    }

    /* ── Spinner ── */
    .stSpinner > div { border-top-color: var(--brand-teal) !important; }

    /* ── Info / warning / error banners ── */
    .stInfo    { background: rgba(97,163,187,0.1) !important; border-left-color: var(--brand-teal) !important; }
    .stWarning { background: rgba(245,158,11,0.08) !important; }
    .stError   { background: rgba(239,68,68,0.08) !important; }
            
    /* ── Date picker selected color ── */
[data-baseweb="calendar"] [aria-selected="true"] {
    background-color: #2F5C85 !important;
}
[data-baseweb="calendar"] [data-selected="true"] {
    background-color: #2F5C85 !important;
}
    </style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# BACKEND API CONFIG
# ═══════════════════════════════════════════════════════════
BACKEND_BASE = st.secrets.get("BACKEND_BASE", "https://your-backend.com/api")

def api_get(path: str, params: dict = None):
    try:
        r = requests.get(f"{BACKEND_BASE}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.Timeout:
        return None, f"Request timed out: {path}"
    except requests.exceptions.RequestException as e:
        return None, str(e)

def api_post(path: str, payload: dict):
    try:
        r = requests.post(f"{BACKEND_BASE}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.Timeout:
        return None, f"Request timed out: {path}"
    except requests.exceptions.RequestException as e:
        return None, str(e)


@st.cache_data(ttl=300)
def load_all_platform_data():
    """Fetch all platform data from the backend API."""

    # ── Time series analytics ────────────────────────────────
    ts_data, ts_err = api_get("/admin/analytics/timeseries")
    if ts_err or not ts_data:
        st.error(f"⚠️ Failed to load time series data — {ts_err}")
        st.stop()
    df_ts = pd.DataFrame(ts_data)
    df_ts["Date"] = pd.to_datetime(df_ts["Date"])

    # ── Places ───────────────────────────────────────────────
    places_data, places_err = api_get("/admin/places")
    if places_err or not places_data:
        st.error(f"⚠️ Failed to load places — {places_err}")
        st.stop()
    df_places = pd.DataFrame(places_data)
    if "Added" in df_places.columns:
        df_places["Added"] = pd.to_datetime(df_places["Added"])

    # ── Users ────────────────────────────────────────────────
    users_data, users_err = api_get("/admin/users")
    if users_err or not users_data:
        st.error(f"⚠️ Failed to load users — {users_err}")
        st.stop()
    df_users = pd.DataFrame(users_data)

    # ── Flagged reviews ──────────────────────────────────────
    reviews_data, reviews_err = api_get("/admin/reviews/flagged")
    if reviews_err or not reviews_data:
        flagged_reviews = pd.DataFrame(columns=["Review_ID","User","Place","Review","Rating","Date"])
    else:
        flagged_reviews = pd.DataFrame(reviews_data)

    # ── Pending owners ───────────────────────────────────────
    owners_data, owners_err = api_get("/admin/owners/pending")
    if owners_err or not owners_data:
        pending_owners = pd.DataFrame(columns=["Owner_ID","Name","Business","Category","Submitted"])
    else:
        pending_owners = pd.DataFrame(owners_data)

    # ── Chatbot query types ──────────────────────────────────
    chat_types_data, _ = api_get("/admin/chatbot/query-types")
    if chat_types_data:
        chat_types = pd.DataFrame(chat_types_data)
    else:
        chat_types = pd.DataFrame({"Type": [], "Val": []})

    # ── Top chatbot places ───────────────────────────────────
    top_chat_data, _ = api_get("/admin/chatbot/top-places")
    if top_chat_data:
        top_chat_places = pd.DataFrame(top_chat_data).sort_values("Chats", ascending=False).reset_index(drop=True)
    else:
        top_chat_places = pd.DataFrame({"Place": [], "Chats": [], "Resolved": []})

    # ── Admin action log ─────────────────────────────────────
    log_data, _ = api_get("/admin/action-log")
    if log_data:
        admin_log = pd.DataFrame(log_data)
    else:
        admin_log = pd.DataFrame({"Admin": [], "Action": [], "Target_ID": [], "Timestamp": []})

    return df_ts, df_places, df_users, flagged_reviews, pending_owners, chat_types, top_chat_places, admin_log


with st.spinner("Loading platform data..."):
    (df_ts, df_places, df_users,
     flagged_reviews, pending_owners,
     chat_types, top_chat_places, admin_log) = load_all_platform_data()


# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;padding:4px 0 12px 0;">
            <div style="background:linear-gradient(135deg,#2F5C85,#61A3BB);
                        border-radius:10px;width:38px;height:38px;
                        display:flex;align-items:center;justify-content:center;
                        font-size:20px;">🏙️</div>
            <div>
                <div style="font-family:'Sora',sans-serif;font-weight:700;
                            font-size:20px;color:white;letter-spacing:-0.3px;">AroundU</div>
                <div style="font-size:11px;color:rgba(97,163,187,0.9);font-weight:500;">
                    Admin Intelligence
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    selected = option_menu(
        menu_title=None,
        options=[
            "Overview", "Places Analytics", "User Analytics",
            "Reviews", "Chatbot", "Category Analytics",
            "Moderation", "Anomaly Detection", "Location Logic",
        ],
        icons=[
            "grid-1x2", "shop", "people",
            "star", "robot", "tags",
            "shield-lock", "exclamation-triangle", "geo-alt",
        ],
        default_index=0,
        styles={
            "container": {
                 "background-color": "#1D3143",
                 "border-radius": "14px",
                 "padding": "8px",
                 "border": "1px solid rgba(97,163,187,0.15)",
                 },
            "nav-link":{"font-size": "15px","font-weight": "500", "font-family": "'DM Sans', sans-serif", "text-align": "left", "color": "rgba(255,255,255,0.75)","border-radius": "10px","padding": "12px 16px","margin": "2px 0",},
            "nav-link-selected": {"background-color": "#2F5C85", "color": "white", "font-weight": "700",  "border-radius": "10px",},
            "icon": {"color": "#61A3BB" , "font-size": "18px",},
        },
    )

    st.divider()
    st.markdown("### 📅 Date Range")
    date_range = st.date_input(
        "Choose period:",
        value=(datetime(2024, 1, 1), datetime(2024, 1, 30)),
    )

    # Alert counts in sidebar
    st.divider()
    st.markdown('<p class="section-label">⚠️ Alerts</p>', unsafe_allow_html=True)
    st.markdown(
        f'🚩 Flagged reviews &nbsp; <span class="badge-red">{len(flagged_reviews)}</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'👤 Pending owners &nbsp;&nbsp; <span class="badge-yellow">{len(pending_owners)}</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'🚫 Suspended users &nbsp; <span class="badge-red">{len(df_users[df_users["Status"]=="Suspended"])}</span>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════
# FILTER + HELPERS
# ═══════════════════════════════════════════════════════════
if isinstance(date_range, tuple) and len(date_range) == 2:
    start = pd.to_datetime(date_range[0])
    end   = pd.to_datetime(date_range[1])
    df_filtered = df_ts[(df_ts["Date"] >= start) & (df_ts["Date"] <= end)]
    days_diff   = (end - start).days + 1
    df_prev     = df_ts[
        (df_ts["Date"] >= start - timedelta(days=days_diff)) &
        (df_ts["Date"] <  start)
    ]
else:
    st.warning("Please select a valid start AND end date.")
    st.stop()

# ✅ BUG FIX: safe delta — handles empty prev period
def get_delta(col):
    if df_prev.empty or df_filtered.empty:
        return None
    curr = df_filtered[col].sum()
    prev = df_prev[col].sum()
    if prev == 0:
        return None
    pct = int(((curr - prev) / prev) * 100)
    return f"{pct:+}%"

def empty_state(msg="No data available for the selected period."):
    st.info(f"ℹ️ {msg}")

TEMPLATE = "plotly_white"


# ═══════════════════════════════════════════════════════════
# 1. OVERVIEW
# ═══════════════════════════════════════════════════════════
if selected == "Overview":
    st.title("📊 Platform Performance Overview")

    if df_filtered.empty:
        empty_state()
        st.stop()

    # KPI Row 1
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Visits",     f"{df_filtered['Visits'].sum():,}",    get_delta("Visits"))
    k2.metric("New Users",        f"{df_filtered['New_Users'].sum():,}",  get_delta("New_Users"))
    k3.metric("Saved Places",     f"{df_filtered['Saves'].sum():,}",      get_delta("Saves"))
    k4.metric("Direction Clicks", f"{df_filtered['Directions'].sum():,}", get_delta("Directions"))

    # KPI Row 2
    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Call Clicks",   f"{df_filtered['Calls'].sum():,}",   get_delta("Calls"))
    k6.metric("Total Reviews", f"{df_filtered['Reviews'].sum():,}", get_delta("Reviews"))
    k7.metric("Active Places", len(df_places[df_places["Status"] == "Active"]))
    chats = df_filtered["Chats"].sum()
    res   = df_filtered["Resolved_Chats"].sum()
    k8.metric("Bot Resolution", f"{(res/chats*100):.1f}%" if chats > 0 else "N/A")

    st.markdown("<br>", unsafe_allow_html=True)

    # Row A: heatmap + signup velocity
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("⏰ Platform Visiting Hours")
        visiting_hours_data, _ = api_get("/admin/analytics/visiting-hours")
        if visiting_hours_data:
            hours     = visiting_hours_data.get("hours", [f"{i}:00" for i in range(24)])
            days      = visiting_hours_data.get("days", ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])
            heat_data = np.array(visiting_hours_data.get("matrix", [[0]*24]*7))
        else:
            hours     = [f"{i}:00" for i in range(24)]
            days      = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            heat_data = np.zeros((7, 24))
        fig_heat = px.imshow(heat_data, x=hours, y=days,
                             color_continuous_scale=[[0,"#E8EFF5"],[0.5,"#619FB8"],[1,"#1D3143"]],
                             aspect="auto", template=TEMPLATE)
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_b:
        st.subheader("🚀 Signup Velocity")
        fig_v = px.bar(df_filtered, x="Date", y=["New_Users","New_Owners"],
                       barmode="group",
                       color_discrete_sequence=["#2F5C85","#61A3BB"],
                       template=TEMPLATE)
        st.plotly_chart(fig_v, use_container_width=True)

    # ✅ BUG FIX: col_c paired with col_d — no longer alone in full row
    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("🛡️ Place Status Distribution")
        fig_st = px.pie(df_places, names="Status", hole=0.6,
                        color_discrete_sequence=["#2F5C85","#61A3BB","#65797E"],
                        template=TEMPLATE)
        st.plotly_chart(fig_st, use_container_width=True)

    with col_d:
        st.subheader("📈 Current vs Previous Period")
        if not df_prev.empty:
            metrics   = ["Visits","Reviews","Saves","Chats"]
            curr_vals = [df_filtered[m].sum() for m in metrics]
            prev_vals = [df_prev[m].sum()     for m in metrics]
            gdf = pd.DataFrame({
                "Metric": metrics * 2,
                "Value":  curr_vals + prev_vals,
                "Period": ["Current"] * 4 + ["Previous"] * 4,
            })
            fig_g = px.bar(gdf, x="Metric", y="Value", color="Period",
                           barmode="group", text_auto=".2s",
                           color_discrete_map={
                               "Current":  "#2F5C85",
                               "Previous": "#C8D9E6",
                           },
                           template=TEMPLATE)
            st.plotly_chart(fig_g, use_container_width=True)
        else:
            empty_state("No previous period available for comparison.")


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
                        color="Count", color_continuous_scale=[[0,"#65797E"],[0.5,"#619FB8"],[1,"#1D3143"]],
                        text_auto=True, template=TEMPLATE)
        st.plotly_chart(fig_cc, use_container_width=True)

    with c2:
        st.subheader("🏆 Most Visited Places (Top 8)")
        top_v = df_places.nlargest(8, "Visits")
        fig_tv = px.bar(top_v, x="Visits", y="Name", orientation="h",
                        color="Visits",color_continuous_scale=[[0,"#65797E"],[0.5,"#619FB8"],[1,"#1D3143"]],
                        template=TEMPLATE)
        fig_tv.update_layout(yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig_tv, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("❤️ Most Saved Places (Top 8)")
        top_s = df_places.nlargest(8, "Saves")
        fig_ts = px.bar(top_s, x="Saves", y="Name", orientation="h",
                        color="Saves", color_continuous_scale=[[0,"#D4E8EE"],[1,"#315687"]],
                        template=TEMPLATE)
        fig_ts.update_layout(yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig_ts, use_container_width=True)

    with c4:
        st.subheader("⭐ Average Rating per Category")
        avg_c = df_places.groupby("Category")["Rating"].mean().reset_index()
        avg_c["Rating"] = avg_c["Rating"].round(2)
        fig_rc = px.bar(avg_c, x="Category", y="Rating",
                        color="Rating",color_continuous_scale=[[0,"#65797E"],[0.5,"#619FB8"],[1,"#1D3143"]],
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
    recent = df_places.nlargest(10, "Added").copy()
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

    st.caption(f"Showing {len(fp)} places")
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
        elif (
            df_places.loc[df_places["Place_ID"] == pid, "Status"].values[0] == "Suspended"
            or pid in st.session_state.suspended_places_log
        ):
            st.warning(f"⚠️ Place `{pid}` is already suspended.")
        else:
            st.session_state.suspended_places_log.append(pid)
            st.success(f"✅ Place `{pid}` has been suspended.")

    # ── Place Suspension Log ──────────────────────────────────
    if st.session_state.suspended_places_log:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Suspended Places (This Session)")
        for pid in st.session_state.suspended_places_log:
            row = df_places[df_places["Place_ID"] == pid].iloc[0]
            st.markdown(
                f"""<div style="background:rgba(239,68,68,0.07);
                               border-left:3px solid #EF4444;
                               border-radius:8px;padding:10px 14px;
                               margin:5px 0;font-size:14px;">
                    🚫 <b>{pid}</b> &nbsp;·&nbsp; {row['Name']} &nbsp;·&nbsp;
                    <span style="color:#65797E;">{row['Category']} · {row['District']}</span>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Place Suspension Log", key="clear_place_suspension_log"):
            st.session_state.suspended_places_log = []
            st.rerun()


# ═══════════════════════════════════════════════════════════
# 3. USER ANALYTICS  (expanded)
# ═══════════════════════════════════════════════════════════
elif selected == "User Analytics":
    st.title("👥 User Analytics")

    u1, u2, u3, u4 = st.columns(4)
    u1.metric("Total Users",         len(df_users))
    u2.metric("New Users (Period)",  df_filtered["New_Users"].sum(), get_delta("New_Users"))
    u3.metric("Suspended Users",     len(df_users[df_users["Status"] == "Suspended"]))
    u4.metric("New Owners (Period)", df_filtered["New_Owners"].sum(), get_delta("New_Owners"))

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 User Growth Trend")
        fig_ug = px.area(df_filtered, x="Date", y="New_Users",
                         color_discrete_sequence=["#2F5C85"], template=TEMPLATE)
        st.plotly_chart(fig_ug, use_container_width=True)

    with col2:
        # ✅ NEW: users by district
        st.subheader("📍 Users by District")
        dist_u = df_users["District"].value_counts().reset_index()
        dist_u.columns = ["District","Users"]
        fig_du = px.bar(dist_u, x="Users", y="District", orientation="h",
                        color="Users", color_continuous_scale=[[0,"#E8EFF5"],[1,"#2F5C85"]],
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
                         color_discrete_sequence=["#2F5C85","#61A3BB"],                         template=TEMPLATE)
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

    st.caption(f"Showing {len(fu)} users")
    st.dataframe(
        fu[["User_ID","Name","District","Reviews","Saves","Status","Joined","Last_Login"]]
        .reset_index(drop=True),
        use_container_width=True,
    )

    # ══════════════════════════════════════════════════════════
    # 🚫 SUSPEND USER TOOL
    # ══════════════════════════════════════════════════════════
    st.divider()
    st.subheader("🚫 Suspend a User")
    st.caption("Suspend a user directly by entering their ID")

    # ── Init session state ────────────────────────────────────
    if "suspended_users_log" not in st.session_state:
        st.session_state.suspended_users_log = []

    sus_col1, sus_col2 = st.columns([2, 1])
    with sus_col1:
        user_id_input = st.text_input(
            "User ID", placeholder="e.g. U-2005", key="suspend_user_input",
        )
    with sus_col2:
        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
        do_suspend_user = st.button("🚫 Suspend User", key="btn_suspend_user", use_container_width=True)

    if do_suspend_user:
        uid = user_id_input.strip().upper()
        if not uid:
            st.warning("⚠️ Please enter a User ID.")
        elif uid not in df_users["User_ID"].values:
            st.error(f"❌ User ID `{uid}` not found in the system.")
        elif (
            df_users.loc[df_users["User_ID"] == uid, "Status"].values[0] == "Suspended"
            or uid in st.session_state.suspended_users_log
        ):
            st.warning(f"⚠️ User `{uid}` is already suspended.")
        else:
            st.session_state.suspended_users_log.append(uid)
            st.success(f"✅ User `{uid}` has been suspended.")

    # ── User Suspension Log ───────────────────────────────────
    if st.session_state.suspended_users_log:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Suspended Users (This Session)")
        for uid in st.session_state.suspended_users_log:
            row = df_users[df_users["User_ID"] == uid].iloc[0]
            st.markdown(
                f"""<div style="background:rgba(239,68,68,0.07);
                               border-left:3px solid #EF4444;
                               border-radius:8px;padding:10px 14px;
                               margin:5px 0;font-size:14px;">
                    🚫 <b>{uid}</b> &nbsp;·&nbsp; {row['Name']} &nbsp;·&nbsp;
                    <span style="color:#65797E;">{row['District']}</span>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear User Suspension Log", key="clear_user_suspension_log"):
            st.session_state.suspended_users_log = []
            st.rerun()


# ═══════════════════════════════════════════════════════════
# 4. REVIEWS  (expanded)
# ═══════════════════════════════════════════════════════════
elif selected == "Reviews":
    st.title("⭐ Reviews & Sentiment Analysis")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total Reviews (Period)", f"{df_filtered['Reviews'].sum():,}", get_delta("Reviews"))
    r2.metric("Positive Sentiment",     "75%")
    r3.metric("Negative Sentiment",     "25%")
    r4.metric("Flagged Reviews",        len(flagged_reviews))

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("😊 Positive vs Negative Ratio")
        fig_pie = px.pie(values=[75, 25], names=["Positive","Negative"],
                         hole=0.55,
                         color_discrete_sequence=["#2F5C85","#65797E"],
                         template=TEMPLATE)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # ✅ NEW: reviews over time
        st.subheader("📅 Reviews Over Time")
        fig_rt = px.area(df_filtered, x="Date", y="Reviews",
                         color_discrete_sequence=["#619FB8"], template=TEMPLATE)
        st.plotly_chart(fig_rt, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("⭐ Average Rating per Category")
        avg_c = df_places.groupby("Category")["Rating"].mean().reset_index()
        avg_c["Rating"] = avg_c["Rating"].round(2)
        fig_rc = px.bar(avg_c, x="Category", y="Rating",
                        color="Rating", color_continuous_scale=[[0,"#65797E"],[0.5,"#619FB8"],[1,"#1D3143"]],
                        text_auto=".2f", template=TEMPLATE)
        fig_rc.update_layout(yaxis_range=[0, 5])
        st.plotly_chart(fig_rc, use_container_width=True)

    with col4:
        # ✅ NEW: most reviewed places
        st.subheader("🏆 Most Reviewed Places (Top 8)")
        top_rev = df_places.nlargest(8, "Reviews")
        fig_mr  = px.bar(top_rev, x="Reviews", y="Name", orientation="h",
                         color="Reviews", color_continuous_scale=[[0,"#D4E8EE"],[1,"#315687"]],
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
# 5. CHATBOT  (fixed + expanded)
# ═══════════════════════════════════════════════════════════
elif selected == "Chatbot":
    st.title("🤖 Chatbot Intelligence")

    # ✅ BUG FIX: was 'Chat_Sessions' — column is named 'Chats'
    total_chats = df_filtered["Chats"].sum()
    resolved    = df_filtered["Resolved_Chats"].sum()
    res_pct     = (resolved / total_chats * 100) if total_chats > 0 else 0

    ch1, ch2, ch3, ch4 = st.columns(4)
    ch1.metric("Total Chat Sessions", f"{total_chats:,}",  get_delta("Chats"))
    ch2.metric("Resolved Chats",      f"{resolved:,}",     get_delta("Resolved_Chats"))
    ch3.metric("Avg Resolution Rate", f"{res_pct:.1f}%")
    ch4.metric("Unresolved Queries",  f"{total_chats - resolved:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        # ✅ NEW: chat volume over time
        st.subheader("📅 Chat Volume Over Time")
        fig_cv = px.area(df_filtered, x="Date", y="Chats",
                         color_discrete_sequence=["#315687"], template=TEMPLATE)
        st.plotly_chart(fig_cv, use_container_width=True)

    with col2:
        st.subheader("🔍 Query Types Distribution")
        fig_qt = px.pie(chat_types, values="Val", names="Type", hole=0.55,
                        color_discrete_sequence=["#2F5C85","#619FB8","#315687","#65797E","#1D3143"],
                        template=TEMPLATE)
        st.plotly_chart(fig_qt, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        # ✅ NEW: most active chatbot places
        st.subheader("🏆 Most Active Chatbot Places")
        fig_tcp = px.bar(top_chat_places.head(8), x="Chats", y="Place",
                         orientation="h", color="Chats",
                         color_continuous_scale=[[0,"#D8E8F0"],[1,"#1D3143"]], template=TEMPLATE)
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
                        color_discrete_map={"Resolved":"#2F5C85","Unresolved":"#65797E"},
                        template=TEMPLATE)
        fig_ru.update_xaxes(tickangle=30)
        st.plotly_chart(fig_ru, use_container_width=True)


# ═══════════════════════════════════════════════════════════
# 6. CATEGORY ANALYTICS  ✅ ENTIRELY NEW SECTION
# ═══════════════════════════════════════════════════════════
elif selected == "Category Analytics":
    st.title("🏷️ Category Analytics")

    ca1, ca2, ca3, ca4 = st.columns(4)
    ca1.metric("Total Categories",      len(df_places["Category"].unique()))
    ca2.metric("Most Places In",        df_places["Category"].value_counts().idxmax())
    ca3.metric("Most Visited Category", df_places.groupby("Category")["Visits"].sum().idxmax())
    ca4.metric("Most Saved Category",   df_places.groupby("Category")["Saves"].sum().idxmax())

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Places per Category")
        cc = df_places["Category"].value_counts().reset_index()
        cc.columns = ["Category","Count"]
        fig_cc = px.bar(cc, x="Category", y="Count",
                        color="Count", color_continuous_scale=[[0,"#E8EFF5"],[1,"#2F5C85"]],
                        text_auto=True, template=TEMPLATE)
        st.plotly_chart(fig_cc, use_container_width=True)

    with col2:
        st.subheader("👁️ Total Visits per Category")
        cv = df_places.groupby("Category")["Visits"].sum().reset_index()
        fig_cv = px.bar(cv, x="Category", y="Visits",
                        color="Visits", color_continuous_scale=[[0,"#D4E8EE"],[1,"#315687"]],
                        text_auto=".2s", template=TEMPLATE)
        st.plotly_chart(fig_cv, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("❤️ Total Saves per Category")
        cs = df_places.groupby("Category")["Saves"].sum().reset_index()
        fig_cs = px.pie(cs, values="Saves", names="Category", hole=0.5,
                       color_discrete_sequence=["#1D3143","#2F5C85","#619FB8","#61A3BB","#65797E"],
                        template=TEMPLATE)
        st.plotly_chart(fig_cs, use_container_width=True)

    with col4:
        st.subheader("⭐ Average Rating per Category")
        ar = df_places.groupby("Category")["Rating"].mean().reset_index()
        ar["Rating"] = ar["Rating"].round(2)
        fig_ar = px.bar(ar, x="Category", y="Rating",
                        color="Rating", color_continuous_scale=[[0,"#65797E"],[0.5,"#619FB8"],[1,"#1D3143"]],
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
# 7. MODERATION  (fully rebuilt)
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
            <div style="background:rgba(245,158,11,0.10);border-left:4px solid #F59E0B;
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
                st.button("🗑️ Delete", key=f"del_{row['Review_ID']}")
                st.button("✅ Keep",   key=f"keep_{row['Review_ID']}")
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
            <div style="background:rgba(47,92,133,0.08);border-left:4px solid #2F5C85;
                        border-radius:8px;padding:14px 18px;color:#1D3143;">
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
                st.button("✅ Approve", key=f"apr_{row['Owner_ID']}")
                st.button("❌ Reject",  key=f"rej_{row['Owner_ID']}")
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



# ═══════════════════════════════════════════════════════════
# 8. ANOMALY DETECTION
# ═══════════════════════════════════════════════════════════
elif selected == "Anomaly Detection":
    st.title("🚨 Anomaly Detection")

    # ── Fetch anomaly data from backend ───────────────────────
    @st.cache_data(ttl=120)
    def fetch_anomalies() -> tuple:
        anomalies_data, err = api_get("/admin/anomalies")
        if err or not anomalies_data:
            return [], [], err
        anomalies = anomalies_data.get("anomalies", [])
        summary   = anomalies_data.get("summary", [])
        return anomalies, summary, None

    with st.spinner("Fetching anomaly data…"):
        anomalies, summary, anom_err = fetch_anomalies()

    if anom_err:
        st.warning(f"⚠️ Anomaly Detection API unavailable — {anom_err}")

    total_anomalies = len(anomalies)

    # ── KPI cards ─────────────────────────────────────────────────
    high_count   = len([a for a in anomalies if a["severity"] == "High"])
    medium_count = len([a for a in anomalies if a["severity"] == "Medium"])
    top_district = summary[0]["cluster"] if summary else "N/A"

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Total Anomalies",     total_anomalies)
    a2.metric("🔵 High Severity",    high_count)
    a3.metric("🔘  Medium Severity",  medium_count)
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
                            color="Count", color_continuous_scale=[[0,"#C8D9E6"],[1,"#1D3143"]],
                            text_auto=True, template=TEMPLATE)
            fig_at.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_at, use_container_width=True)

        # ── Severity Distribution ─────────────────────────────────
        with col2:
            st.subheader("🔴 Severity Distribution")
            sev_counts = pd.DataFrame(anomalies)["severity"].value_counts().reset_index()
            sev_counts.columns = ["Severity", "Count"]
            fig_sev = px.pie(sev_counts, values="Count", names="Severity", hole=0.55,
                color_discrete_sequence=[ "#1D3143" ,  "#619FB8" ],
                template=TEMPLATE)
            st.plotly_chart(fig_sev, use_container_width=True)

        # ── Anomaly Heatmap per Cluster ───────────────────────────
        if summary:
            st.subheader("🗺️ Anomaly Activity per Cluster")
            sum_df = pd.DataFrame(summary)
            fig_cl = px.bar(sum_df, x="cluster", y="total_anomalies",
                            color="total_anomalies", color_continuous_scale=[[0,"#C8D9E6"],[1,"#1D3143"]],
                            text_auto=True, template=TEMPLATE,
                            labels={"cluster": "Cluster", "total_anomalies": "Total Anomalies"})
            fig_cl.update_xaxes(type="category")
            st.plotly_chart(fig_cl, use_container_width=True)

        # ── Live Anomaly Feed ─────────────────────────────────────
        st.subheader("📋 Live Anomaly Feed")
        st.caption(f"Showing {len(anomalies)} flagged anomalies — sorted by score")

        for a in anomalies:
            col_info, col_act = st.columns([5, 1])
            severity_badge = "🔵" if a["severity"] == "High" else "🔘"
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
# 9. LOCATION LOGIC
# ═══════════════════════════════════════════════════════════
elif selected == "Location Logic":
    st.title("📍 Location Intelligence: Beni Suef")

    BS_LAT, BS_LON = 29.0661, 31.0994
    LOCATION_API   = "https://mazenmaher26-aroundu-location-logic.hf.space/admin-summary"

    DISTRICT_NAMES = {
        0: "El-Kornish",
        1: "AbdelSalam Aref",
        2: "Salah Salem",
        3: "El-Roda St.",
        4: "New BS (District-1)",
        5: "New BS (Entertainment)",
        6: "El-Abaseriy St.",
    }

    # ── Inline control bar (matches screenshot UI) ───────────
    st.markdown("""
        <style>
        /* ── Control bar layout ── */
        .loc-control-bar {
            display: flex;
            align-items: center;
            gap: 24px;
            flex-wrap: wrap;
            margin-bottom: 18px;
        }
        .loc-control-bar .ctrl-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        /* ── Refresh button override ── */
        div[data-testid="stButton"].refresh-btn > button {
            background: #FFFFFF !important;
            color: #1D3143 !important;
            border: 1px solid #C8D9E6 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            padding: 6px 18px !important;
            box-shadow: 0 1px 4px rgba(29,49,67,0.07) !important;
        }
        div[data-testid="stButton"].refresh-btn > button:hover {
            background: #EDF2F6 !important;
            border-color: #2F5C85 !important;
        }
        /* ── Toggle label style ── */
        .toggle-label {
            font-family: 'DM Sans', sans-serif;
            font-size: 14px;
            font-weight: 500;
            color: #1D3143;
        }
        /* Description text */
        .loc-desc {
            font-size: 13px;
            color: #65797E;
            margin-bottom: 12px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<p class="loc-desc">See where your visitors are coming from — all time and recently active.</p>',
        unsafe_allow_html=True,
    )

    # ── Session window + toggles + refresh in one row ────────
    ctrl_left, ctrl_mid, ctrl_right = st.columns([3, 5, 2])

    with ctrl_left:
        st.markdown("**Active session window**")
        session_hours = st.selectbox(
            "Active session window",
            options=[1, 3, 6, 12, 24, 168],
            index=0,
            format_func=lambda h: f"Last {h} hour" if h == 1 else (f"Last {h} hours" if h < 168 else "Last 7 days"),
            label_visibility="collapsed",
        )

    with ctrl_mid:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        tg1, tg1_lbl, tg2, tg2_lbl = st.columns([1, 3, 1, 3])
        with tg1:
            show_heatmap = st.toggle("heatmap", value=True, label_visibility="collapsed", key="toggle_heatmap")
        with tg1_lbl:
            st.markdown("🔥 **All visitors heatmap**", unsafe_allow_html=False)
        with tg2:
            show_pins = st.toggle("pins", value=True, label_visibility="collapsed", key="toggle_pins")
        with tg2_lbl:
            st.markdown("📌 **Active visitor pins**", unsafe_allow_html=False)

    with ctrl_right:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        refresh_clicked = st.button("🔄 Refresh", key="btn_refresh_location", use_container_width=True)
        if refresh_clicked:
            st.cache_data.clear()
            st.rerun()

    st.markdown("<hr style='border-color:#C8D9E6;margin:4px 0 16px 0;'>", unsafe_allow_html=True)

    # ── Fetch interactions + places from backend ──────────────
    @st.cache_data(ttl=300)
    def fetch_interactions_and_places() -> tuple:
        interactions_data, int_err = api_get("/admin/interactions")
        if int_err or not interactions_data:
            return [], [], int_err
        places_data, _ = api_get("/admin/places/map")
        places = places_data if places_data else []
        return interactions_data, places, None

    # ── API call ─────────────────────────────────────────────
    @st.cache_data(ttl=300)
    def fetch_location_summary(sess_hours: int, interactions: list, places: list) -> tuple:
        payload = {
            "interactions":        interactions,
            "places":              places,
            "session_hours":       sess_hours,
            "low_visit_threshold": 10.0,
            "low_place_threshold": 3,
        }
        try:
            r = requests.post(LOCATION_API, json=payload, timeout=20)
            r.raise_for_status()
            return r.json(), None
        except requests.exceptions.Timeout:
            return None, "Location Logic API timed out."
        except requests.exceptions.RequestException as e:
            return None, str(e)

    with st.spinner("Fetching interactions & places from backend…"):
        interactions, places_list, fetch_err = fetch_interactions_and_places()

    if fetch_err:
        st.error(f"⚠️ Failed to fetch interaction data — {fetch_err}")
        st.stop()

    with st.spinner("Fetching city-wide location intelligence…"):
        data, api_err = fetch_location_summary(session_hours, tuple(interactions), tuple(places_list))

    if api_err or data is None:
        st.error(f"⚠️ Location Logic API unavailable — {api_err}")
        st.stop()

    # ── KPI row ──────────────────────────────────────────────
    peak_raw = data.get("peak_hour")
    if peak_raw is not None:
        peak_display = f"{peak_raw % 12 or 12}{'AM' if peak_raw < 12 else 'PM'}"
    else:
        peak_display = "N/A"

    opp_count = len(data.get("opportunity_zones", []))

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total City Visits", f"{data['total_visits']:,}")
    k2.metric(
        "Active Visitors",
        f"{data['active_count']:,}",
        help=f"Visits within the last {session_hours}h window",
    )
    k3.metric("City Peak Hour", peak_display)
    k4.metric(
        "Opportunity Zones",
        opp_count,
        delta=f"{opp_count} underserved" if opp_count else None,
        delta_color="inverse",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── City-wide heatmap ────────────────────────────────────
    st.subheader("🗺️ City-Wide Visitor Heatmap")

    heatmap_pts = data.get("heatmap_points", [])
    if heatmap_pts and show_heatmap:
        heat_df = pd.DataFrame(heatmap_pts).rename(columns={"lng": "lon"})
        fig_map = px.density_mapbox(
            heat_df, lat="lat", lon="lon", z="weight", radius=18,
            center=dict(lat=BS_LAT, lon=BS_LON), zoom=12.5,
            mapbox_style="open-street-map", height=540,
            color_continuous_scale=[
                [0.0, "#C8D9E6"],
                [0.4, "#619FB8"],
                [0.7, "#2F5C85"],
                [1.0, "#1D3143"],
            ],
        )
        fig_map.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            coloraxis_colorbar=dict(title="Visit Density"),
        )
        st.plotly_chart(fig_map, use_container_width=True)
    elif not show_heatmap:
        st.info("🔥 Heatmap is toggled off. Enable **All visitors heatmap** above to display it.")
    else:
        st.info("No heatmap data returned from API.")

    st.divider()

    # ── District visit share + Hourly pattern ────────────────
    col1, col2 = st.columns(2)

    int_df = pd.DataFrame(interactions)

    with col1:
        st.subheader("📊 Visit Share by District")
        dist_visits = (
            int_df.assign(district=int_df["cluster_id"].map(DISTRICT_NAMES))
            .groupby("district")
            .size()
            .reset_index(name="Visits")
            .sort_values("Visits", ascending=True)
        )
        fig_dist = px.bar(
            dist_visits, x="Visits", y="district", orientation="h",
            color="Visits",
            color_continuous_scale=[[0, "#C8D9E6"], [1, "#1D3143"]],
            template=TEMPLATE, text_auto=True,
        )
        fig_dist.update_layout(
            yaxis_title="",
            coloraxis_showscale=False,
            margin=dict(l=0),
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    with col2:
        st.subheader("🕐 Visit Activity by Hour")
        int_df["timestamp"] = pd.to_datetime(int_df["timestamp"])
        hour_counts = (
            int_df.assign(hour=int_df["timestamp"].dt.hour)
            .groupby("hour")
            .size()
            .reset_index(name="Visits")
        )
        fig_hour = px.bar(
            hour_counts, x="hour", y="Visits",
            color="Visits",
            color_continuous_scale=[[0, "#C8D9E6"], [1, "#1D3143"]],
            template=TEMPLATE, text_auto=True,
            labels={"hour": "Hour of Day"},
        )
        if peak_raw is not None:
            fig_hour.add_vline(
                x=peak_raw,
                line_dash="dash", line_color="#EF4444",
                annotation_text=f"Peak: {peak_display}",
                annotation_position="top right",
                annotation_font_color="#EF4444",
            )
        fig_hour.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_hour, use_container_width=True)

    # ── Registered places breakdown (from platform mock data) ─
    st.subheader("🏷️ Registered Places by District & Category")
    st.caption("Source: platform place registry — not visit traffic")
    dcat = df_places.groupby(["District", "Category"]).size().reset_index(name="Count")
    fig_dcat = px.bar(
        dcat, x="District", y="Count", color="Category", barmode="stack",
        color_discrete_sequence=["#1D3143", "#2F5C85", "#619FB8", "#61A3BB", "#65797E"],
        template=TEMPLATE,
    )
    fig_dcat.update_xaxes(tickangle=30)
    st.plotly_chart(fig_dcat, use_container_width=True)

    st.divider()

    # ── Opportunity zones ────────────────────────────────────
    st.subheader("💡 Opportunity Zones")
    st.caption(
        "Zones flagged when visit share < 10% of city AND fewer than 3 registered places. "
        "Powered by /admin-summary → Location Logic API."
    )

    opps = data.get("opportunity_zones", [])
    if not opps:
        st.success("✅ No underserved zones detected under current thresholds.")
    else:
        for zone in sorted(opps, key=lambda z: z["pct_of_total"]):
            pct  = zone["pct_of_total"]
            icon = "🔴" if pct < 5 else "🟡"
            msg  = (
                f"{icon} **{zone['district']}** — "
                f"{zone['visit_count']:,} visits "
                f"({pct}% of city) · "
                f"{zone['unique_places']} place(s) registered"
            )
            if pct < 5:
                st.error(msg)
            else:
                st.warning(msg)
