import streamlit as st
import pandas as pd
import requests
import json
import time

# --- CONFIGURATION ---
# 1. Check your Docker port! (It's likely 9090 or 5679 based on your history)
N8N_PORT = "9090" 
N8N_WEBHOOK_URL = f"http://localhost:{N8N_PORT}/webhook/process-batch"

# 2. REPLACE THIS LINK! 
# Go to Google Sheet -> File -> Share -> Publish to Web -> Select "Sheet1" and "CSV" -> Click Publish -> Copy Link
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOjM-l1OUaciaFdaFfuLOazhfPiiWWwgjAGB_kToeFq-fY--LyljT3m_uhDCKZicGfyQSsMXDEpVHd/pub?gid=0&single=true&output=csv"

# --- PAGE SETUP ---
st.set_page_config(page_title="DPP Decision Agent", layout="wide", page_icon="📦")

st.title("📦 Logistics Decision Dashboard")
st.markdown("Monitor and control the **Decision Agent** (Petri Net Transition).")

# --- TABS ---
tab1, tab2 = st.tabs(["🚀 Upload Batch", "📊 Batch History"])

# --- TAB 1: UPLOAD & PROCESS ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Upload Batch")
        uploaded_file = st.file_uploader("Upload Batch JSON", type=['json'])
        
        if uploaded_file is not None:
            batch_data = json.load(uploaded_file)
            
            # --- NEW LOGIC: Check if it's a List or a Single Object ---
            if isinstance(batch_data, list):
                # It's a list (like your new test file)
                count = len(batch_data)
                st.success(f"✅ Loaded {count} Batches")
                is_valid = True
            elif isinstance(batch_data, dict):
                # It's a single object (like your old test file)
                batch_id = batch_data.get('batch_id', 'Unknown')
                st.success(f"✅ Loaded Batch: {batch_id}")
                is_valid = True
            else:
                st.error("❌ Invalid JSON structure")
                is_valid = False

            if is_valid and st.button("🚀 Send to Agent", type="primary"):
                with st.spinner('Agent is evaluating compliance & semantics...'):
                    try:
                        # Send to n8n
                        response = requests.post(N8N_WEBHOOK_URL, json=batch_data)
                        
                        if response.status_code == 200:
                            st.balloons()
                            st.success("✅ Decision Processed! Check the History tab.")
                        else:
                            st.error(f"❌ Error {response.status_code}: {response.text}")
                            
                    except requests.exceptions.ConnectionError:
                        st.error(f"❌ Could not connect to n8n at {N8N_WEBHOOK_URL}. Is Docker running?")

    with col2:
        st.subheader("Payload Preview")
        if uploaded_file:
            # If it's a huge list, only show the first 2 items to save space
            if isinstance(batch_data, list) and len(batch_data) > 2:
                st.info(f"Showing first 2 of {len(batch_data)} items:")
                st.json(batch_data[:2])
            else:
                st.json(batch_data)
        else:
            st.info("Upload a JSON file to see the payload structure.")

# --- TAB 2: HISTORY (GOOGLE SHEETS) ---
with tab2:
    st.subheader("Live Decision Log")
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()

    try:
        # Load data directly from Google Sheets CSV feed
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        
        # SEARCH
        search_term = st.text_input("🔍 Search Logs", placeholder="Enter Batch ID or Status...")
        if search_term:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]

        # STYLING
        def style_status(val):
            color = "#930b19" if str(val).upper() == 'FLAGGED' else "#0f6f13" if str(val).upper() == 'GOOD' else ''
            return f'background-color: {color}'
            
        st.dataframe(df.style.map(style_status, subset=['Status']), use_container_width=True)
        
    except Exception as e:
        st.warning("⚠️ Could not load data. Did you 'Publish to Web' as CSV in Google Sheets?")
        st.code(GOOGLE_SHEET_CSV_URL)