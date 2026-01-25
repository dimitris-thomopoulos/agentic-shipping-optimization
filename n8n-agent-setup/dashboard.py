import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px
import time
import os
import base64
import streamlit_antd_components as sac
from streamlit_extras.stylable_container import stylable_container
from PIL import Image # <--- ADD THIS IMPORT

# --- CONFIGURATION ---
N8N_WEBHOOK_URL = "https://lisaselma.app.n8n.cloud/webhook-test/98f01249-5cf6-4626-b4aa-755fdba9fb98"
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOjM-l1OUaciaFdaFfuLOazhfPiiWWwgjAGB_kToeFq-fY--LyljT3m_uhDCKZicGfyQSsMXDEpVHd/pub?gid=0&single=true&output=csv"

# --- BRANDING COLORS ---
COLOR_BG_MAIN = "#fffffd"
COLOR_ACCENT_BG = "#d7cccc"
COLOR_PRIMARY = "#10324d"
COLOR_TEXT = "#351c27"
COLOR_CARD_BG = "#ffffff"

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
        print(f"⚠️ LOGO ERROR: Could not find file at: {file_path}")
        return None

# Load the logo
logo_b64 = get_base64_image("logotype.png")

# --- CUSTOM CSS ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Gabarito:wght@400;700&family=Montserrat:wght@400;600&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');

    /* 1. GENERAL APP STYLING */
    .stApp {{
        background-color: {COLOR_BG_MAIN};
    }}
    .block-container {{
        padding-top: 1rem;
        padding-bottom: 5rem;
    }}

    /* 2. REMOVE SIDEBAR & HEADER ANCHORS */
    [data-testid="stSidebar"] {{ display: none; }}
    [data-testid="stHeaderActionElements"] {{ display: none !important; }}
    
    /* HIDE STREAMLIT APP HEADER */
    header[data-testid="stHeader"] {{
        display: none;
    }}

    /* 3. TYPOGRAPHY */
    h1, h2, h3, h4, h5, h6, strong {{
        font-family: 'Gabarito', sans-serif !important;
        color: {COLOR_PRIMARY} !important;
    }}
    html, body, p, label, li, .stMarkdown {{
        font-family: 'Montserrat', sans-serif !important;
        color: {COLOR_TEXT} !important;
        line-height: 1.6;
    }}

    /* 4. HEADER (Logo Only) */
    .header-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 10px 0 20px 0;
        width: 100%;
    }}
    .header-logo {{
        height: 80px; /* Force height */
        max-width: 300px;
        object-fit: contain;
    }}

    /* 5. CARD STYLING */
    .card-container {{
        background-color: {COLOR_CARD_BG};
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        overflow: hidden;
        border: 1px solid #eee;
        height: 100%;
        transition: transform 0.2s;
    }}
    .card-container:hover {{
        transform: translateY(-5px);
    }}
    .card-img {{
        width: 100%;
        height: 180px;
        object-fit: cover;
    }}
    .card-content {{
        padding: 20px;
    }}
    
    /* 6. UI ELEMENTS */
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

    /* Remove border from navigation */
    .mantine-SegmentedControl-control {{
        border: none !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- HEADER (Logo + Title) ---
with st.container():
    if logo_b64:
        img_html = f'<img src="data:image/png;base64,{logo_b64}" class="header-logo">'
    else:
        img_html = f'<h1 style="color:{COLOR_TEXT}; font-size: 40px;">FiberTrace</h1>'
    
    st.markdown(f"""
        <div class="header-container">
            {img_html}
        </div>
    """, unsafe_allow_html=True)

# --- NAVIGATION (SAC Segmented Control) ---
nav_c1, nav_c2, nav_c3 = st.columns([1, 2, 1])
with nav_c2:
    # Use session state to control the selected item
    selected_page = sac.segmented(
        items=[
            sac.SegmentedItem(label='Home', icon='house'),
            sac.SegmentedItem(label='Upload & Execute', icon='cloud-upload'),
            sac.SegmentedItem(label='Analytics', icon='bar-chart-line'),
        ],
        index=[
            'Home', 
            'Upload & Execute', 
            'Analytics'
        ].index(st.session_state.active_tab),
        align='center',
        size='md',
        radius='lg',
        color='#351c27',  
        bg_color='rgba(215, 204, 204, 0.4)', 
        return_index=False
    )

    # Sync selection to session state (manual click handling)
    if selected_page != st.session_state.active_tab:
        st.session_state.active_tab = selected_page
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# PAGE 1: HOME
# ==========================================
if st.session_state.active_tab == "Home":
    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px; padding: 0 10px;">
        <h1 style="font-size: 2.5rem; margin-bottom: 10px;">Supply Chain Compliance, Automated.</h1>
        <p style="font-size: 1.1rem; max-width: 700px; margin: 0 auto; color: #555;">
            Leverage AI agents and Digital Product Passports (DPP) to audit textile shipments in real-time.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.markdown(f"""
        <div class="card-container">
            <img src="https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&q=80&w=800" style="object-fit: cover;" class="card-img">
            <div class="card-content">
                <h3>Shipment Logistics</h3>
                <p>Shipments move through multiple jurisdictions, requiring strict adherence to material certifications (GOTS, BCI) to avoid customs blockages.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card-container">
            <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=800" style="object-fit: cover;" class="card-img">
            <div class="card-content">
                <h3>AI Analysis</h3>
                <p>Our Intelligent Agents ingest complex JSON manifests, cross-referencing DPP metadata against regulatory requirements to detect non-compliance.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="card-container">
            <img src="https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&q=80&w=800" style="object-fit: cover;" class="card-img">
            <div class="card-content">
                <h3>Decision Gate</h3>
                <p>Acting as a Petri Net transition, FiberTrace automatically authorizes "Good" batches while flagging risky ones for immediate human intervention.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # CTA
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with stylable_container(
            key="start_btn",
            css_styles=f"""
                button {{
                    background-color: {COLOR_PRIMARY} !important;
                    color: white !important;
                    border: none;
                    border-radius: 8px;
                }}
                /* This forces the text inside the button to be white */
                button p {{
                    color: white !important;
                }}
                button:hover {{
                    background-color: #1a4a6e !important;
                    color: white !important;
                }}
            """
        ):
            # use_container_width=True ensures the button fills the column, centering it perfectly
            if st.button("Start Processing ➔", use_container_width=True):
                st.session_state.active_tab = "Upload & Execute"
                st.rerun()

# ==========================================
# PAGE 2: UPLOAD & EXECUTE
# ==========================================
elif st.session_state.active_tab == "Upload & Execute":
    st.subheader("🚀 Shipment Processing")
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
                st.success(f"✅ Loaded {count} Batches")
                is_valid = True
            elif isinstance(batch_data, dict):
                try:
                    batch_id = batch_data['shipments'][0]['batches'][0]['shipmentId']
                except (KeyError, IndexError, TypeError):
                    batch_id = batch_data.get('shipmentId', 'Unknown')

                st.success(f"✅ Loaded Shipment: {batch_id}")
                is_valid = True
            else:
                st.error("❌ Unsupported JSON format")

            if is_valid:
                st.markdown("<br>", unsafe_allow_html=True)
                
                # --- FIXED: STYLABLE BUTTON WITH HIGHER SPECIFICITY CSS ---
                with stylable_container(
                    key="run_compliance_btn",
                    css_styles=f"""
                        button {{
                            background-color: {COLOR_PRIMARY} !important;
                            color: white !important; /* Force white text */
                            border: none !important;
                            border-radius: 8px !important;
                            font-family: 'Montserrat', sans-serif !important;
                            font-weight: 600 !important;
                            padding: 0.5rem 1rem !important;
                            transition: all 0.3s ease !important;
                        }}
                        button:hover {{
                            background-color: #1a4a6e !important; /* Lighter Blue */
                            color: white !important;
                            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                        }}
                        /* Target the paragraph inside the button specifically */
                        button p {{
                            color: white !important;
                        }}
                    """
                ):
                    if st.button("RUN COMPLIANCE CHECK", use_container_width=True):
                        # --- NEW: PROGRESS STATUS ---
                        status_container = st.status("Initializing Multi-Agent System...", expanded=True)
                        try:
                            status_container.write("🔍 Analyzing DPP Metadata...")
                            time.sleep(1) # Simulate slight delay for UX
                            
                            status_container.write("🌍 Checking Route Constraints...")
                            # Send to n8n
                            response = requests.post(N8N_WEBHOOK_URL, json=batch_data)
                            
                            status_container.write("🤖 Generating Final Decision...")
                            
                            if response.status_code == 200:
                                status_container.update(label="✅ Compliance Check Complete!", state="complete", expanded=False)
                                st.balloons()
                                time.sleep(1)
                                
                                # --- AUTO-SWITCH TAB ---
                                st.session_state.active_tab = "Analytics"
                                st.rerun()
                                
                            else:
                                status_container.update(label="❌ Error Occurred", state="error")
                                st.error(f"❌ Error {response.status_code}: {response.text}")
                                
                        except requests.exceptions.ConnectionError:
                            status_container.update(label="❌ Connection Failed", state="error")
                            st.error(f"❌ Connection Failed.")

    with col2:
        st.markdown("##### Data Preview")
        if uploaded_file:
            with st.expander("📄 View Raw Content", expanded=True):
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
# PAGE 3: ANALYTICS
# ==========================================
elif st.session_state.active_tab == "Analytics":
    st.subheader("📊 Operational Analytics")
    
    try:
        cache_buster_url = f"{GOOGLE_SHEET_CSV_URL}&t={int(time.time())}"
        df = pd.read_csv(cache_buster_url)
        df.columns = df.columns.str.strip()
        df.fillna("Unknown", inplace=True) 

        status_col = 'decision' if 'decision' in df.columns else 'Status'
        
        c1, c2 = st.columns([1, 4])
        with c1:
            # --- FIXED: REFRESH BUTTON TEXT COLOR ---
            with stylable_container(
                key="refresh_btn",
                css_styles=f"""
                    button {{
                        background-color: {COLOR_PRIMARY} !important;
                        color: white !important;
                        border-radius: 8px;
                        border: none;
                    }}
                    button p {{ color: white !important; }}
                    button:hover {{
                        background-color: #1a4a6e !important;
                    }}
                """
            ):
                if st.button("🔄 Refresh", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
                    
        with c2:
            if status_col in df.columns:
                opts = ['All'] + sorted(df[status_col].unique().tolist())
                sel = st.selectbox("Filter Status", opts, label_visibility="collapsed")
                if sel != 'All':
                    df = df[df[status_col] == sel]

        st.markdown("<br>", unsafe_allow_html=True)

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        total_batches = len(df)
        proceed_count = len(df[df[status_col].astype(str).str.contains("PROCEED|GOOD", case=False)])
        block_count = len(df[df[status_col].astype(str).str.contains("BLOCK|FLAGGED", case=False)])
        delay_count = len(df[df[status_col].astype(str).str.contains("DELAY", case=False)])
        issue_rate = round(((block_count + delay_count) / total_batches * 100), 1) if total_batches > 0 else 0

        kpi1.metric("Total Shipments", total_batches)
        kpi2.metric("✅ Proceed", proceed_count)
        kpi3.metric("⚠️ Issues", block_count + delay_count)
        kpi4.metric("Intervention Rate", f"{issue_rate}%")

        st.markdown("---")

        chart_col1, chart_col2 = st.columns(2)
        color_map = {
            'FLAGGED AS PROCEED': '#2E7D32', 
            'FLAGGED AS DELAY': '#E65100', 
            'FLAGGED AS BLOCK': '#C62828',
            'GOOD': '#2E7D32', 
            'Unknown': '#455A64'
        }

        with chart_col1:
            if status_col in df.columns and not df.empty:
                st.markdown("##### Distribution")
                fig_pie = px.pie(df, names=status_col, color=status_col,
                                 color_discrete_map=color_map, hole=0.5)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                      font={'family': "Montserrat", 'color': COLOR_TEXT})
                st.plotly_chart(fig_pie, use_container_width=True)

        with chart_col2:
            st.markdown("##### Activity Stream")
            if not df.empty:
                df['Sequence'] = df.index + 1
                fig_bar = px.bar(df, x='Sequence', y=status_col, color=status_col,
                                 color_discrete_map=color_map)
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                      font={'family': "Montserrat", 'color': COLOR_TEXT},
                                      xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#eee'))
                st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("### Detailed Logs")
        search_term = st.text_input("Search", placeholder="Shipment ID, Supplier...", label_visibility="collapsed")
        if search_term:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]

        def style_status(val):
            val_str = str(val).upper()
            if 'DELAY' in val_str: return 'background-color: #FFF3E0; color: #E65100; font-weight: 700;' 
            elif 'BLOCK' in val_str: return 'background-color: #FFEBEE; color: #C62828; font-weight: 700;' 
            elif 'PROCEED' in val_str or 'GOOD' in val_str: return 'background-color: #E8F5E9; color: #2E7D32; font-weight: 700;' 
            return ''

        cols_to_style = [c for c in ['decision', 'Status'] if c in df.columns]
        st.dataframe(df.style.map(style_status, subset=cols_to_style), use_container_width=True, height=500)

    except Exception as e:
        st.error(f"Data Error: {e}")