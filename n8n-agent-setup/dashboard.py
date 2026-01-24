import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px

import time

# --- CONFIGURATION ---
# 1. Cloud n8n Webhook
N8N_WEBHOOK_URL = "https://lisaselma.app.n8n.cloud/webhook-test/dd3f2c82-8bbd-4a2b-87c3-81f1b58bde06"

# 2. Google Sheet CSV Link
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOjM-l1OUaciaFdaFfuLOazhfPiiWWwgjAGB_kToeFq-fY--LyljT3m_uhDCKZicGfyQSsMXDEpVHd/pub?gid=0&single=true&output=csv"

# --- PAGE SETUP ---
st.set_page_config(page_title="DPP Command Center", layout="wide", page_icon="📦")

# Custom CSS to make metrics look nicer
st.markdown("""
<style>
    div[data-testid="stMetricValue"] {
        font-size: 24px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📦 Logistics Decision Dashboard")
st.markdown("Monitor and control the **Decision Agent** (Petri Net Transition).")

# --- TABS ---
tab1, tab2 = st.tabs(["🚀 Upload & Execute", "📊 Analytics & History"])

# ==========================================
# TAB 1: UPLOAD & PROCESS
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Upload Batch")
        st.info("Supported format: JSON (Single Object or Array)")
        
        uploaded_file = st.file_uploader("Drop Batch File Here", type=['json'])
        
        if uploaded_file is not None:
            batch_data = json.load(uploaded_file)
            is_valid = False
            
            # Validation Logic
            if isinstance(batch_data, list):
                count = len(batch_data)
                st.success(f"✅ Loaded {count} Batches")
                is_valid = True
            elif isinstance(batch_data, dict):
                batch_id = batch_data.get('batch_id', 'Unknown')
                st.success(f"✅ Loaded Batch: {batch_id}")
                is_valid = True
            else:
                st.error("❌ Invalid JSON structure")

            # Execution Button
            if is_valid:
                st.markdown("---")
                if st.button("🚀 Send to Agent", type="primary", use_container_width=True):
                    with st.spinner('Agent is evaluating compliance & semantics...'):
                        try:
                            # Send to n8n
                            response = requests.post(N8N_WEBHOOK_URL, json=batch_data)
                            
                            if response.status_code == 200:
                                st.balloons()
                                st.success("✅ Decision Processed! Check the Analytics tab.")
                            else:
                                st.error(f"❌ Error {response.status_code}: {response.text}")
                                
                        except requests.exceptions.ConnectionError:
                            st.error(f"❌ Connection Failed. Check your internet or n8n URL.")

    with col2:
        st.subheader("Payload Preview")
        if uploaded_file:
            with st.expander("View Raw JSON", expanded=True):
                # If huge list, limit preview
                if isinstance(batch_data, list) and len(batch_data) > 3:
                    st.warning(f"Showing first 3 of {len(batch_data)} items")
                    st.json(batch_data[:3])
                else:
                    st.json(batch_data)
        else:
            st.markdown(
                """
                <div style="padding: 20px; border: 1px dashed #ccc; border-radius: 10px; text-align: center; color: #666;">
                    Waiting for file upload...
                </div>
                """, unsafe_allow_html=True
            )

# ==========================================
# TAB 2: ANALYTICS & HISTORY
# ==========================================
with tab2:
    # Top Control Bar
    col_refresh, col_filter = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Refresh Live Data"):
            st.cache_data.clear()
            st.rerun()

    try:
        # --- CACHE BUSTING FIX ---
        # We append a unique timestamp (&t=...) to the URL to force Google 
        # to give us the freshest data instead of a cached version.
        cache_buster_url = f"{GOOGLE_SHEET_CSV_URL}&t={int(time.time())}"
        
        # Load Data
        df = pd.read_csv(cache_buster_url)
        
        # Clean Headers & Handle Empty Data
        df.columns = df.columns.str.strip()
        df.fillna("", inplace=True) # Fixes "NaN" errors in the table

        # --- SIDEBAR FILTERS (Only visible on this tab effectively) ---
        with col_filter:
            # Check if 'Status' exists for filtering
            if 'Status' in df.columns:
                status_options = ['All'] + sorted(df['Status'].unique().tolist())
                selected_status = st.selectbox("Filter by Status:", status_options)
                
                if selected_status != 'All':
                    df = df[df['Status'] == selected_status]

        # --- KPI CARDS ---
        st.markdown("### 📈 Performance Metrics")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        total_batches = len(df)
        # Calculate Good vs Flagged if column exists
        if 'Status' in df.columns:
            flagged_count = len(df[df['Status'].str.upper() == 'FLAGGED'])
            good_count = len(df[df['Status'].str.upper() == 'GOOD'])
            flagged_rate = round((flagged_count / total_batches * 100), 1) if total_batches > 0 else 0
        else:
            flagged_count = 0
            good_count = 0
            flagged_rate = 0

        kpi1.metric("Total Processed", total_batches)
        kpi2.metric("✅ Approved (Good)", good_count)
        kpi3.metric("🚩 Rejected (Flagged)", flagged_count)
        kpi4.metric("Flag Rate", f"{flagged_rate}%")

        st.markdown("---")

        # --- CHARTS SECTION ---
        chart_col1, chart_col2 = st.columns(2)

        # Chart 1: Status Distribution
        with chart_col1:
            if 'Status' in df.columns and not df.empty:
                st.subheader("Compliance Overview")
                fig_pie = px.pie(df, names='Status', title='Batch Status Distribution', 
                                 color='Status',
                                 color_discrete_map={'GOOD':'#00CC96', 'FLAGGED':'#EF553B', 'Pending':'#AB63FA'},
                                 hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No Status data available for charts.")

        # Chart 2: Timeline or Category Breakdown
        with chart_col2:
            st.subheader("Recent Activity")
            # If there is a Date column, use it. If not, use index as proxy for time.
            if not df.empty:
                # Create a synthetic index for "Batch Number" in sequence
                df['Sequence'] = df.index + 1
                fig_bar = px.bar(df, x='Sequence', y='Status', 
                                 title="Process Stream (Recent Batches)",
                                 color='Status',
                                 color_discrete_map={'GOOD':'#00CC96', 'FLAGGED':'#EF553B'})
                st.plotly_chart(fig_bar, use_container_width=True)

        # --- DATA TABLE ---
        st.markdown("### 📝 Detailed Log")
        
        # Search Functionality
        search_term = st.text_input("🔍 Search Logs", placeholder="Enter Batch ID, Supplier, or Keywords...")
        if search_term:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]

        # Styling Logic
        def style_status(val):
            val_str = str(val).upper()
            # Check for various flag keywords found in your 'decision' column
            if any(x in val_str for x in ['FLAGGED', 'BLOCK', 'DELAY']):
                return 'background-color: #ffebee; color: #c62828; font-weight: bold' # Light Red
            elif 'GOOD' in val_str or 'PROCEED' in val_str:
                return 'background-color: #e8f5e9; color: #2e7d32; font-weight: bold' # Light Green
            return ''

        # Display Dataframe
        # We now apply the style to BOTH 'decision' and 'Status' columns so you don't miss anything
        cols_to_style = [c for c in ['decision', 'Status'] if c in df.columns]
        
        st.dataframe(
            df.style.map(style_status, subset=cols_to_style),
            use_container_width=True,
            height=400
        )

    except Exception as e:
        st.error(f"⚠️ Data Error: {e}")
        st.warning("Ensure your Google Sheet headers are correct and the CSV is published.")