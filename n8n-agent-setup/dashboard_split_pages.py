import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px
import time
import os
import base64
from streamlit_extras.stylable_container import stylable_container
from PIL import Image # <--- ADD THIS IMPORT

# --- CONFIGURATION ---
N8N_WEBHOOK_URL = "https://lisaselma.app.n8n.cloud/webhook-test/98f01249-5cf6-4626-b4aa-755fdba9fb98"
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1zXKdsqy5nrp48mZJR23q_vmQj4gGVM01fgmIZZTMpWw/gviz/tq?tqx=out:csv&sheet=Sheet1"

# --- BRANDING COLORS (Updated to match design) ---
COLOR_BG_MAIN = "#FFFFFD"
COLOR_SIDEBAR_BG = "#351C27"  # Deep maroon/purple sidebar
COLOR_ACCENT_BG = "#d7cccc"
COLOR_PRIMARY = "#351C27"  # Dark maroon/purple for headers and buttons
COLOR_TEXT = "#10324D"  # Dark grey for body text
COLOR_SIDEBAR_TEXT = "#D7CCCC"  # Light off-white for sidebar text
COLOR_CARD_BG = "#fffffd"

# --- STATUS COLOR MAP (decisions / flags) ---
color_map = {
    'FLAGGED AS PROCEED': '#7A98AF',
    'FLAGGED AS DELAY': '#C68A8A',
    'FLAGGED AS BLOCK': '#69002E',
    'GOOD': '#2E7D32',
    'Unknown': '#455A64'
}

# --- LOAD ICON (Robust Method) ---
# Get the absolute path to the image to ensure Streamlit finds it
script_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(script_dir, "logo.png")

# Load the image using PIL if it exists, otherwise use emoji fallback
if os.path.exists(icon_path):
    app_icon = Image.open(icon_path)
else:
    app_icon = "🧶"

# --- PAGE SETUP ---
# Pass the actual image object, not the filename string
st.set_page_config(page_title="FiberTrace", layout="wide", page_icon=app_icon)

# --- SESSION STATE FOR TAB NAVIGATION ---
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Home"

# Selected shipment for the detail view
if "selected_shipment_id" not in st.session_state:
    st.session_state.selected_shipment_id = None

# When True, Shipment Overview opens the most recent row in the sheet
if "open_last_shipment" not in st.session_state:
    st.session_state.open_last_shipment = False

# --- HELPER: ROBUST LOGO LOADER ---
def get_base64_image(filename):
    # 1. Get the absolute path of the folder containing this script (dashboard.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Join it with the filename to get the full absolute path
    file_path = os.path.join(script_dir, filename)
    
    # 3. Check if file exists at that specific path
    if os.path.exists(file_path):
        with open(file_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    else:
        # debugger: This will print to your terminal (where you run streamlit run)
        # so you can see exactly where it is looking for the file.
        print(f"LOGO ERROR: Could not find file at: {file_path}")
        return None

# Load the logo
logo_b64 = get_base64_image("logotype.png")

# --- CUSTOM CSS ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    @import url('https://fonts.googleapis.com/css2?family=Gabarito:wght@400..900&family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap');
    
    /* 1. GENERAL APP STYLING */
    .stApp {{
        background-color: {COLOR_BG_MAIN};
    }}
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 5rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1200px;
    }}

    /* 2. HIDE HEADER */
    # [data-testid="stHeaderActionElements"] {{ display: none !important; }}
    # header[data-testid="stHeader"] {{
    #     display: none;
    # }}l
    header[data-testid="stHeader"] {{
        height: 0;
        overflow: visible;
        background: transparent;
    }}


    /* 3. STYLE STREAMLIT SIDEBAR */
    [data-testid="stSidebar"] {{
        background-color: {COLOR_SIDEBAR_BG} !important;
        /* width: 280px !important; */
        width: 280px;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 5px;
        padding-left: 30px;
        padding-right: 30px;
    }}
    .sidebar-logo {{
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        font-size: 28px;
        color: {COLOR_SIDEBAR_TEXT};
        margin-bottom: 60px;
        letter-spacing: 1px;
        user-select: none;
    }}
    
    .sidebar-nav-item {{
        font-family: 'Montserrat', sans-serif;
        font-weight: 400;
        font-size: 16px;
        color: {COLOR_SIDEBAR_TEXT};
        text-decoration: none;
        cursor: pointer;
        transition: all 0.2s ease;
        letter-spacing: 0.5px;
        padding: 12px 0;
        user-select: none;
        display: block;
        border-bottom: 1px solid rgba(224, 224, 224, 0.1);
    }}
    .sidebar-nav-item:hover {{
        opacity: 0.8;
        transform: translateX(5px);
    }}
    .sidebar-nav-item.active {{
        font-weight: 600;
        opacity: 1;
    }}
    /* Style sidebar buttons */

    /* Override Streamlit's internal flex centering */
    [data-testid="stSidebar"] button > div {{
        justify-content: flex-start !important;
        align-items: center !important;
    }}


    [data-testid="stSidebar"] button {{
        background-color: transparent !important;
        color: {COLOR_SIDEBAR_TEXT} !important;
        border: none !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
        font-size: 16px !important;
        letter-spacing: 0.5px !important;
        padding: 12px 0 !important;
        width: 100% !important;
        text-align: left !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        border-bottom: 1px solid rgba(224, 224, 224, 0.1) !important;
        justify-content: flex-start !important;
    }}
    [data-testid="stSidebar"] button:hover {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        transform: translateX(5px);
    }}
    [data-testid="stSidebar"] button:focus {{
        box-shadow: none !important;
    }}
    [data-testid="stSidebar"] button p {{
        color: {COLOR_SIDEBAR_TEXT} !important;
        margin: 0 !important;
        text-align: left !important;
        width: 100% !important;
    }}
    /* Active state for sidebar buttons */
    [data-testid="stSidebar"] button[kind="secondary"] {{
        font-weight: 600 !important;
    }}

    /* 4. TYPOGRAPHY */

    .hero-headline {{
        font-family: 'Montserrat', sans-serif !important;
        font-size: 7rem !important;
        font-weight: 600px
    }}
    .main-headline {{
        font-family: 'Montserrat', sans-serif !important;
        font-size: 3rem !important;
        font-weight: 300px
    }}
    .main-description {{
        font-family: 'Montserrat', sans-serif !important;
    }}

    h1, h2, h3, h4, h5, h6, strong {{
        font-family: 'Montserrat', sans-serif !important;
        color: {COLOR_PRIMARY} !important;
    }}
    html, body, p, label, li, .stMarkdown {{
        font-family: 'Montserrat', sans-serif !important;
        color: {COLOR_TEXT} !important;
        line-height: 1.6;
    }}

    /* 5. MAIN CONTENT CENTERING */
    .main-content-wrapper {{
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }}

    /* 6. HEADER STYLING */
    .hero-headline {{
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 500;
        font-size: 5rem;
        color: {COLOR_TEXT};
        margin-bottom: 20px;
        text-align: center;
        padding-bottom: 40px;
    }}
    .main-headline {{
        font-family: 'Montserrat', sans-serif;
        font-weight: 300;
        font-size: 1.8rem;
        color: {COLOR_TEXT};
        margin-bottom: 15px;
        text-align: center;
        line-height: 1.3;
        padding-bottom: 20px;
    }}
    .main-description {{
        font-family: 'Montserrat', sans-serif;
        font-weight: 400;
        font-size: 1rem;
        color: {COLOR_TEXT};
        max-width: 600px;
        margin: 0 auto 0px auto;
        text-align: center;
        line-height: 1.6;
    }}
    
    /* 8. UI ELEMENTS */
    div[data-testid="metric-container"] {{
        background-color: {COLOR_ACCENT_BG};
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid {COLOR_PRIMARY};
    }}
    
    input[type="text"], div[data-baseweb="select"] > div {{
        background-color: #ffffff !important;
        color: {COLOR_TEXT} !important;
        border: 1px solid {COLOR_ACCENT_BG} !important;
    }}

    /* 9. BUTTON STYLING */
    .stButton > button {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease !important;
    }}
    .stButton > button:hover {{
        background-color: #6A3C5A !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
    }}
    .stButton > button p {{
        color: white !important;
        margin: 0;
    }}
    
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    # st.markdown(f'<div class="sidebar-logo">FT.</div>', unsafe_allow_html=True)
    if logo_b64:
        st.markdown(
            f"""
            <div style="margin-bottom: 60px; padding:12px 15px;">
                <img src="data:image/png;base64,{logo_b64}"
                    style="width: 90px; height: auto; display: block;" />
            </div>
            """,
            unsafe_allow_html=True
        )
        
    else:
        st.markdown(
            '<div class="sidebar-logo">FT.</div>',
            unsafe_allow_html=True
        )

    if st.button("HOME", use_container_width=True, key="nav_home"):
        st.session_state.active_tab = "Home"
        st.rerun()
    if st.button("UPLOAD & EXECUTE", use_container_width=True, key="nav_upload"):
        st.session_state.active_tab = "Upload & Execute"
        st.rerun()
    if st.button("SHIPMENTS", use_container_width=True, key="nav_shipments"):
        st.session_state.active_tab = "Shipments"
        st.rerun()
    

# ==========================================
# PAGE 1: HOME
# ==========================================
if st.session_state.active_tab == "Home":
    st.markdown(f"""
    <div class="main-content-wrapper" style="margin-bottom: 60px;">
        <div class="hero-headline">FiberTrace.</div>
        <div class="main-headline">Supply Chain Compliance,<br>Automated.</div>
        <div class="main-description">
            Leverage AI agents and Digital Product Passports (DPP) to audit textile shipments in real-time.
        </div>
    </div>
    """, unsafe_allow_html=True)

    #st.markdown("<br><br>", unsafe_allow_html=True)
    
    # CTA Button
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with stylable_container(
            key="start_btn",
            css_styles=f"""
                button {{
                    background-color: {COLOR_PRIMARY} !important;
                    color: white !important;
                    border: none !important;
                    border-radius: 90px !important;
                    font-family: 'Montserrat', sans-serif !important;
                    font-weight: 400 !important;
                    font-size: 16px !important;
                    padding-top: 12px !important;
                    padding-bottom: 12px !important;
                    padding-left: 10px !important;
                    padding-right: 10px !important;
                    transition: all 0.3s ease !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    gap: 8px !important;
                }}
                button p {{
                    color: #FFFFFD !important;
                    margin: 0 !important;
                    font-weight: 600 !important;
                    text-transform: uppercase !important;
                }}
                button:hover {{
                    background-color: #6A3C5A !important;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
                }}
            """
        ):
            if st.button("Get started →", use_container_width=True):
                st.session_state.active_tab = "Upload & Execute"
                st.rerun()


# ==========================================
# PAGE 2: UPLOAD & EXECUTE
# ==========================================
elif st.session_state.active_tab == "Upload & Execute":
    st.subheader("Shipment Processing")
    st.markdown("Upload your shipment manifest JSON below.")

    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        with st.container():
            uploaded_file = st.file_uploader("Drop Shipment JSON Data Here", type=['json'])
        
        if uploaded_file is not None:
            batch_data = json.load(uploaded_file)
            is_valid = False
            
            if isinstance(batch_data, list):
                count = len(batch_data)
                st.success(f"Loaded {count} Batches")
                is_valid = True
            elif isinstance(batch_data, dict):
                try:
                    batch_id = batch_data['shipments'][0]['batches'][0]['shipmentId']
                except (KeyError, IndexError, TypeError):
                    batch_id = batch_data.get('shipmentId', 'Unknown')

                st.success(f"Loaded Shipment: {batch_id}")
                is_valid = True
            else:
                st.error("Unsupported JSON format")

            if is_valid:
                st.markdown("<br>", unsafe_allow_html=True)
                
                # --- FIXED: STYLABLE BUTTON WITH HIGHER SPECIFICITY CSS ---
                with stylable_container(
                    key="run_compliance_btn",
                    css_styles=f"""
                        button {{
                            background-color: {COLOR_PRIMARY} !important;
                            color: white !important;
                            border: none !important;
                            border-radius: 8px !important;
                            font-family: 'Montserrat', sans-serif !important;
                            font-weight: 400 !important;
                            padding: 12px 24px !important;
                            transition: all 0.3s ease !important;
                        }}
                        button:hover {{
                            background-color: #6A3C5A !important;
                            color: white !important;
                            box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
                        }}
                        button p {{
                            color: white !important;
                            margin: 0 !important;
                        }}
                    """
                ):
                    # if st.button("RUN COMPLIANCE CHECK", use_container_width=True):
                    #     # --- NEW: PROGRESS STATUS ---
                    #     status_container = st.status("Initializing Multi-Agent System...", expanded=True)
                    #     try:
                    #         status_container.write("🔍 Analyzing DPP Metadata...")
                    #         time.sleep(1) # Simulate slight delay for UX
                            
                    #         status_container.write("🌍 Checking Route Constraints...")
                    #         # Send to n8n
                    #         response = requests.post(N8N_WEBHOOK_URL, json=batch_data)
                            
                    #         status_container.write("🤖 Generating Final Decision...")
                            
                    #         if response.status_code == 200:
                    #             status_container.update(label="✅ Compliance Check Complete!", state="complete", expanded=False)
                    #             st.balloons()
                    #             time.sleep(1)
                                
                    #             # --- AUTO-SWITCH TAB ---
                    #             st.session_state.active_tab = "Analytics"
                    #             st.rerun()
                                
                    #         else:
                    #             status_container.update(label="Error Occurred", state="error")
                    #             st.error(f"Error {response.status_code}: {response.text}")
                                
                    #     except requests.exceptions.ConnectionError:
                    #         status_container.update(label="Connection Failed", state="error")
                    #         st.error("Connection Failed.")
                    if st.button("RUN COMPLIANCE CHECK", use_container_width=True):
                        status_container = st.status("Initializing Multi-Agent System...", expanded=True)
                        time.sleep(1.5)
                        status_container.write("Analyzing DPP Metadata...")
                        time.sleep(1.5) # Simulate slight delay for UX
                        status_container.write("Checking Route Constraints...")
                        time.sleep(1.5) # Simulate slight delay for UX
                        status_container.write("Generating Final Decision...")
                        time.sleep(1.5)
                        st.session_state.open_last_shipment = True
                        st.session_state.selected_shipment_id = None
                        st.session_state.active_tab = "Shipment Overview"
                        st.rerun()
                        

    with col2:
        st.markdown("##### Data Preview")
        if uploaded_file:
            with st.expander("View Raw Content", expanded=True):
                if isinstance(batch_data, list) and len(batch_data) > 3:
                    st.warning(f"Showing first 3 of {len(batch_data)} items")
                    st.json(batch_data[:3])
                else:
                    st.json(batch_data)
        else:
            st.markdown(
                f"""
                <div style="
                    padding: 40px; 
                    border: 2px dashed {COLOR_ACCENT_BG}; 
                    border-radius: 10px; 
                    text-align: center; 
                    color: {COLOR_PRIMARY};
                    background-color: #fcfcfc;">
                    <p style="color: #aaa;">Waiting for file...</p>
                </div>
                """, unsafe_allow_html=True
            )

# ==========================================

# ==========================================
# PAGE 3: SHIPMENTS
# ==========================================

elif st.session_state.active_tab == "Shipments":

    def _norm_cols(df_):
        df_ = df_.copy()
        df_.columns = [str(c).strip() for c in df_.columns]
        rename_map = {
            "ShipmentID": "shipmentId",
            "shipmentID": "shipmentId",
            "ShipmentId": "shipmentId",
            "TimeStamp": "timestamp",
            "Timestamp": "timestamp",
            "Decision": "decision",
            "Risk": "risk",
            "Reason": "reason",
            "Recommendations": "recommendations",
            "route": "route",
            "Route": "route",
            "route_edges": "route_edges",
            "routeEdges": "route_edges",
        }
        df_ = df_.rename(columns={k: v for k, v in rename_map.items() if k in df_.columns})
        df_.fillna("", inplace=True)
        return df_

    def _decision_bucket(x):
        s = str(x or "").upper()
        if "BLOCK" in s:
            return "BLOCK"
        if "DELAY" in s:
            return "DELAY"
        if "PROCEED" in s:
            return "PROCEED"
        return "Unknown"

    try:
        cache_buster_url = f"{GOOGLE_SHEET_CSV_URL}&t={int(time.time())}"
        df_raw = pd.read_csv(cache_buster_url)
        df = _norm_cols(df_raw)

        if "shipments_df" not in st.session_state:
            df_raw = pd.read_csv(cache_buster_url)
            st.session_state.shipments_df = _norm_cols(df_raw)


        EXTRA_COL = "STATUS"

        if "shipments_df" not in st.session_state:
            st.session_state.shipments_df = df.copy()

        df = st.session_state.shipments_df

        if EXTRA_COL not in df.columns:
            df[EXTRA_COL] = ""
            st.session_state.shipments_df = df

        st.subheader("All Shipments")

        df = st.session_state.shipments_df

        if df.empty:
            st.info("No rows found.")
        else:
            # Requested columns for overview table (+ STATUS)
            overview_cols = [c for c in ["shipmentId", "timestamp", "decision", "risk", EXTRA_COL] if c in df.columns]
            df_overview = df[overview_cols].copy() if overview_cols else df.copy()

            # Search + filter
            c1, c2 = st.columns([2, 1])
            with c1:
                q = st.text_input(
                    "Search",
                    placeholder="ShipmentID, decision, reason…",
                    label_visibility="collapsed",
                )
            with c2:
                if "decision" in df_overview.columns:
                    opts = ["All"] + sorted(
                        [x for x in df_overview["decision"].astype(str).unique().tolist() if str(x).strip()]
                    )
                    sel = st.selectbox("Filter Decision", opts, label_visibility="collapsed")
                else:
                    sel = "All"

            if q:
                df_overview = df_overview[
                    df_overview.astype(str)
                    .apply(lambda x: x.str.contains(q, case=False, na=False))
                    .any(axis=1)
                ]

            if sel != "All" and "decision" in df_overview.columns:
                df_overview = df_overview[df_overview["decision"].astype(str) == sel]

            # Editable table (notes column editable)
            edited = st.data_editor(
                df_overview,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                disabled=[c for c in df_overview.columns if c != EXTRA_COL],
                column_config={
                    "notes": st.column_config.TextColumn(
                        "Notes",
                        help="Free-form user notes",
                        width="medium",
                    )
                },
                height=min(520, 45 + 35 * max(1, len(df_overview))),
                key="shipments_editor",
            )

            # Write edits back to master dataframe (by shipmentId)
            if "shipmentId" in edited.columns:
                base = df.set_index("shipmentId")
                edited = edited.set_index("shipmentId")

                for col in edited.columns:
                    base.loc[edited.index, col] = edited[col]

                st.session_state.shipments_df = base.reset_index()


        # st.subheader("All Shipments")

        # if df.empty:
        #     st.info("No rows found.")
        # else:

        #     # Requested columns for overview table
        #     overview_cols = [c for c in ["shipmentId", "timestamp", "decision", "risk"] if c in df.columns]
        #     df_overview = df[overview_cols].copy() if overview_cols else df.copy()

        #     # Search + filter
        #     c1, c2 = st.columns([2, 1])
        #     with c1:
        #         q = st.text_input("Search", placeholder="ShipmentID, decision, reason…", label_visibility="collapsed")
        #     with c2:
        #         if "decision" in df_overview.columns:
        #             opts = ["All"] + sorted([x for x in df_overview["decision"].astype(str).unique().tolist() if str(x).strip()])
        #             sel = st.selectbox("Filter Decision", opts, label_visibility="collapsed")
        #         else:
        #             sel = "All"

        #     if q:
        #         df_overview = df_overview[df_overview.astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)]
        #     if sel != "All" and "decision" in df_overview.columns:
        #         df_overview = df_overview[df_overview["decision"].astype(str) == sel]

        #     # Display table (styled) + selection control to open overview
        #     def style_status(val):
        #         s = str(val or "").strip()
        #         up = s.upper()
        #         if "PROCEED" in up:
        #             bg = color_map.get("FLAGGED AS PROCEED", color_map["Unknown"])
        #             return f"background-color: {bg}; color: #ffffff; font-weight: 700;"
        #         if "DELAY" in up:
        #             bg = color_map.get("FLAGGED AS DELAY", color_map["Unknown"])
        #             return f"background-color: {bg}; color: #ffffff; font-weight: 700;"
        #         if "BLOCK" in up:
        #             bg = color_map.get("FLAGGED AS BLOCK", color_map["Unknown"])
        #             return f"background-color: {bg}; color: #ffffff; font-weight: 700;"
        #         if up == "GOOD":
        #             bg = color_map.get("GOOD", color_map["Unknown"])
        #             return f"background-color: {bg}; color: #ffffff; font-weight: 700;"
        #         bg = color_map["Unknown"]
        #         return f"background-color: {bg}; color: #ffffff; font-weight: 700;"

        #     styled_subset = ["decision"] if "decision" in df_overview.columns else None
        #     st.dataframe(
        #         df_overview.style.map(style_status, subset=styled_subset) if styled_subset else df_overview,
        #         use_container_width=True,
        #         hide_index=True,
        #         height=min(520, 45 + 35 * max(1, len(df_overview))),
        #     )
            
            st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

            # Open a shipment (best-effort "click"): dropdown selection
            if "shipmentId" in df.columns:
                ids = [x for x in df["shipmentId"].astype(str).tolist() if str(x).strip()]
                if ids:
                    st.markdown("##### Open shipment")
                    chosen = st.selectbox("Shipment", options=list(dict.fromkeys(ids)), label_visibility="collapsed")
                    if st.button("View shipment overview", use_container_width=False):
                        st.session_state.selected_shipment_id = chosen
                        st.session_state.open_last_shipment = False
                        st.session_state.active_tab = "Shipment Overview"
                        st.rerun()

            st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)


            # --- Pie + bar overview ---
            left, right = st.columns(2)

            # PIE: decisions overview
            with left:
                if "decision" in df.columns:
                    df_pie = df.copy()
                    df_pie["bucket"] = df_pie["decision"].apply(_decision_bucket)
                    counts = df_pie["bucket"].value_counts().reset_index()
                    counts.columns = ["bucket", "count"]

                    pie_color_map = {
                        "PROCEED": color_map.get("FLAGGED AS PROCEED", color_map["Unknown"]),
                        "DELAY": color_map.get("FLAGGED AS DELAY", color_map["Unknown"]),
                        "BLOCK": color_map.get("FLAGGED AS BLOCK", color_map["Unknown"]),
                        "Unknown": color_map["Unknown"],
                    }

                    fig_pie = px.pie(
                        counts,
                        names="bucket",
                        values="count",
                        title="Shipment Decisions",
                        color="bucket",
                        color_discrete_map=pie_color_map,
                    )
                    fig_pie.update_layout(height=320, margin=dict(l=10, r=10, t=60, b=10))
                    st.plotly_chart(fig_pie, use_container_width=True)

            # BAR: risk distribution
            with right:
                if "risk" in df.columns:
                    sev = df.copy()
                    sev["risk"] = sev["risk"].astype(str).str.strip()
                    sev = sev[sev["risk"] != ""]
                    sev_counts = sev["risk"].value_counts().reset_index()
                    sev_counts.columns = ["risk", "count"]

                    risk_color_map = {
                        "Low": "#CF8CA9",
                        "Moderate": "#69002E",
                        "High": "#351C27",
                    }
                    fig_bar = px.bar(
                        sev_counts,
                        x="risk",
                        y="count",
                        title="Risk Distribution",
                        color="risk",
                        color_discrete_map=risk_color_map,
                    )
                    fig_bar.update_layout(height=320, margin=dict(l=10, r=10, t=60, b=10))
                    st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        st.error(f"Data Error: {e}")

# ==========================================
# PAGE 4: SHIPMENT OVERVIEW
# ==========================================

elif st.session_state.active_tab == "Shipment Overview":

    st.markdown(
    """
    <style>
    div[data-testid="stButton"] > button {
        padding: 6px 12px;
        font-size: 0.85rem;
        border-radius: 10px;
        min-height: 0;
        height: auto;
        line-height: 1.2;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


    def _norm_cols(df_):
        df_ = df_.copy()
        df_.columns = [str(c).strip() for c in df_.columns]
        rename_map = {
            "ShipmentID": "shipmentId",
            "shipmentID": "shipmentId",
            "ShipmentId": "shipmentId",
            "TimeStamp": "timestamp",
            "Timestamp": "timestamp",
            "Decision": "decision",
            "Risk": "risk",
            "Reason": "reason",
            "Recommendations": "recommendations",
            "route": "route",
            "Route": "route",
            "route_edges": "route_edges",
            "routeEdges": "route_edges",
        }
        df_ = df_.rename(columns={k: v for k, v in rename_map.items() if k in df_.columns})
        df_.fillna("", inplace=True)
        return df_

    def _parse_route(v):
        if v is None:
            return []
        s = str(v).strip()
        if not s:
            return []
        s = s.replace("\n", ",")
        parts = [p.strip() for p in s.split(",") if p.strip()]
        return parts

    def _parse_bullet_list(v):
        """Accepts a Python list, JSON list string, or free-text; returns list of bullet strings."""
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        s = str(v).strip()
        if not s:
            return []
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                try:
                    import ast
                    parsed = ast.literal_eval(s)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
        import re
        s2 = s.replace("\r", "\n")
        parts = re.split(r"(?:\n|;)+", s2)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) > 1:
            return [re.sub(r"^[-•\d\)\.\s]+", "", p).strip() for p in parts if p.strip()]
        return [s]

    def _render_bullets(title, items, empty_text):
        st.markdown(f"##### {title}")
        if not items:
            st.caption(empty_text)
            return
        st.markdown("\n".join([f"- {x}" for x in items]))

    def _route_figure(route_list):
        import plotly.graph_objects as go
        if not route_list or len(route_list) < 2:
            fig = go.Figure()
            fig.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10))
            return fig

        xs = list(range(len(route_list)))
        ys = [0] * len(route_list)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="lines+markers+text",
            text=route_list,
            textposition="top center",
            hovertext=route_list,
            hoverinfo="text",
        ))
        fig.update_yaxes(visible=False)
        fig.update_xaxes(visible=False)
        fig.update_layout(
            height=260,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Montserrat", color=COLOR_TEXT),
        )
        return fig

    

    st.subheader("Shipment Overview")


    with st.container():
        st.markdown('<div class="back-button">', unsafe_allow_html=True)
        if st.button("← All shipments", key="back_to_shipments"):
            st.session_state.active_tab = "Shipments"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


    try:
        cache_buster_url = f"{GOOGLE_SHEET_CSV_URL}&t={int(time.time())}"
        df_raw = pd.read_csv(cache_buster_url)
        df = _norm_cols(df_raw)
        if df.empty:
            st.info("No rows found.")
        else:
            # Choose which row to show
            row = None
            if st.session_state.open_last_shipment or not st.session_state.selected_shipment_id:
                row = df.iloc[-1]
            else:
                sid = str(st.session_state.selected_shipment_id)
                if "shipmentId" in df.columns:
                    matches = df[df["shipmentId"].astype(str) == sid]
                    if not matches.empty:
                        row = matches.iloc[-1]
                    else:
                        row = df.iloc[-1]
                else:
                    row = df.iloc[-1]

            # Reset the "open last" flag once used
            st.session_state.open_last_shipment = False

            shipment_id = str(row.get("shipmentId", "")).strip()
            decision = str(row.get("decision", "")).strip()
            risk = str(row.get("risk", "")).strip()
            route_list = _parse_route(row.get("route", ""))

            top1, top2, top3 = st.columns(3)
            top1.metric("ShipmentID", shipment_id or "—")
            decision_label = decision or "Unknown"
            top2.metric("Decision", decision_label)
            top3.metric("Risk", risk or "—")

            st.markdown("---")

            # use_cols = [c for c in st.session_state.shipments_df.columns if c not in ["shipmentId", "timestamp", "decision", "risk", "STATUS"]]
            # st.data_editor(st.session_state.shipments_df, use_container_width=True, hide_index=True)


            # --- Single-shipment row editor (only notes editable) ---
            EXTRA_COL = "STATUS"

            # Ensure source of truth exists + has notes column
            if "shipments_df" not in st.session_state:
                st.session_state.shipments_df = df.copy()

            master = st.session_state.shipments_df.copy()
            if EXTRA_COL not in master.columns:
                master[EXTRA_COL] = ""

            # Match the currently displayed shipmentId
            sid = shipment_id  # from your selected row above
            if "shipmentId" not in master.columns:
                st.error("shipments_df is missing 'shipmentId' column.")
            else:
                mask = master["shipmentId"].astype(str) == str(sid)

                if not mask.any():
                    st.info("Shipment not found in editable table.")
                else:
                    # Show only this shipment row (you can choose columns)
                    show_cols = [c for c in ["shipmentId", "timestamp", "decision", "risk", EXTRA_COL] if c in master.columns]
                    row_df = master.loc[mask, show_cols].copy()

                    edited_row = st.data_editor(
                        row_df,
                        use_container_width=True,
                        hide_index=True,
                        num_rows="fixed",
                        disabled=[c for c in row_df.columns if c != EXTRA_COL],  # only notes editable
                        column_config={
                            "notes": st.column_config.TextColumn(
                                "Notes",
                                help="Free-form notes for this shipment",
                                width="large",
                            )
                        },
                        key=f"shipment_row_editor_{sid}",
                    )

                    # Persist edited notes back to session_state dataframe
                    new_notes = edited_row.iloc[0][EXTRA_COL] if EXTRA_COL in edited_row.columns and len(edited_row) else ""
                    master.loc[mask, EXTRA_COL] = new_notes
                    st.session_state.shipments_df = master
            st.markdown(
                """
                <div style="
                    font-size: 0.8rem;
                    color: #6b7280;
                    text-align: right;
                    margin-top: -1.5rem;
                ">
                    *Change the status of shipment in the above table and press enter to save.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("---")

            left, right = st.columns([1, 2], gap="small")
            with left:
                reason_items = _parse_bullet_list(row.get("reason", ""))
                

                with stylable_container(
                    key="reason_card_detail",
                    css_styles="""
                        {
                          background-color: #ffffff;
                          border: 1px solid rgba(16,50,77,0.12);
                          border-radius: 16px;
                          padding: 14px 16px;
                        }
                    """,
                ):
                    _render_bullets("Decision reason", reason_items, "No reason available.")

                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

                # Route display
                st.markdown("##### Recommended route")
                if route_list:
                    st.plotly_chart(_route_figure(route_list), use_container_width=True)
                else:
                    st.caption("No route available.")
            with right:
                rec_items = _parse_bullet_list(row.get("recommendations", ""))
                with stylable_container(
                    key="recs_card_detail",
                    css_styles="""
                        {
                          background-color: #ffffff;
                          border: 1px solid rgba(16,50,77,0.12);
                          border-radius: 16px;
                          padding: 14px 16px;
                        }
                    """,
                ):
                    _render_bullets("Recommendations", rec_items, "No recommendations available.")

                


    except Exception as e:
        st.error(f"Data Error: {e}")
