import streamlit as st
import pandas as pd
import requests
import json

# --- CONFIGURATION ---
N8N_WEBHOOK_URL = "https://lisaselma.app.n8n.cloud/webhook-test/process-batch"
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOjM-l1OUaciaFdaFfuLOazhfPiiWWwgjAGB_kToeFq-fY--LyljT3m_uhDCKZicGfyQSsMXDEpVHd/pub?gid=0&single=true&output=csv"

# --- PAGE SETUP ---
st.set_page_config(page_title="Logistics Decision Dashboard", layout="wide", page_icon="📦")

st.title("📦 Logistics Decision Dashboard")
st.markdown("Upload batch data and route information to process shipments through compliance and routing agents.")

# --- SESSION STATE ---
if 'batch_data' not in st.session_state:
    st.session_state.batch_data = None
if 'route_data' not in st.session_state:
    st.session_state.route_data = None
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = None

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📤 Upload Data", "📊 Processing Results", "✅ Human Judgment"])

# --- TAB 1: UPLOAD DATA ---
with tab1:
    st.subheader("Upload Data")
    st.markdown("Upload batch data and route information separately.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Batch Data")
        st.caption("Upload JSON with batch data (orders, garments, DPP information)")
        batch_file = st.file_uploader("Upload Batch Data JSON", type=['json'], key="batch_upload")
        
        if batch_file is not None:
            try:
                batch_data = json.load(batch_file)
                st.session_state.batch_data = batch_data
                
                # Validate batch data structure
                if isinstance(batch_data, dict):
                    if 'batches' in batch_data:
                        batch_count = len(batch_data['batches']) if isinstance(batch_data['batches'], list) else 1
                        st.success(f"✅ Loaded batch data with {batch_count} batch(es)")
                    elif 'orders' in batch_data:
                        st.success(f"✅ Loaded batch data (single batch)")
                    else:
                        st.warning("⚠️ Batch data structure may be incomplete")
                elif isinstance(batch_data, list):
                    st.success(f"✅ Loaded {len(batch_data)} batch(es)")
                else:
                    st.error("❌ Invalid batch data structure")
                    
                with st.expander("📋 Preview Batch Data"):
                    if isinstance(batch_data, dict) and 'batches' in batch_data:
                        st.json(batch_data['batches'][0] if isinstance(batch_data['batches'], list) else batch_data)
                    elif isinstance(batch_data, list):
                        st.json(batch_data[0] if len(batch_data) > 0 else batch_data)
                    else:
                        st.json(batch_data)
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON file")
                st.session_state.batch_data = None
            except Exception as e:
                st.error(f"❌ Error loading file: {str(e)}")
                st.session_state.batch_data = None
    
    with col2:
        st.markdown("### Route Data")
        st.caption("Enter shipment route information")
        
        # Input fields for route data
        shipment_id = st.text_input("Shipment ID", key="shipment_id", placeholder="e.g., SHIP-001")
        origin = st.text_input("Origin", key="origin", placeholder="e.g., Antwerp-Bruges")
        destination = st.text_input("Destination", key="destination", placeholder="e.g., Bremerhaven")
        priority = st.selectbox("Priority", ["Express", "High", "Medium", "Low"], key="priority", index=2)
        
        # Create route data JSON from inputs
        if shipment_id and origin and destination and priority:
            route_data = {
                "shipmentId": shipment_id,
                "origin": origin,
                "destination": destination,
                "priority": priority
            }
            st.session_state.route_data = route_data
            st.success(f"✅ Route data ready for shipment: {shipment_id}")
            
            with st.expander("📋 Preview Route Data (JSON)"):
                st.json(route_data)
        else:
            st.session_state.route_data = None
            st.info("ℹ️ Fill in all route fields above")
    
    # Combine and send data
    st.divider()
    
    if st.session_state.batch_data and st.session_state.route_data:
        st.markdown("### Start Processing")
        
        if st.button("🚀 Start N8N Flow", type="primary", use_container_width=True):
            # Combine batch and route data
            combined_data = {
                "shipments": [st.session_state.route_data] if isinstance(st.session_state.route_data, dict) else st.session_state.route_data,
                "batches": st.session_state.batch_data.get('batches', []) if isinstance(st.session_state.batch_data, dict) else st.session_state.batch_data
            }
            
            # Ensure shipments have batches
            if isinstance(combined_data['shipments'], list) and len(combined_data['shipments']) > 0:
                if 'batches' not in combined_data['shipments'][0]:
                    combined_data['shipments'][0]['batches'] = combined_data['batches']
            
            status_container = st.empty()
            
            with status_container.container():
                st.info("🔄 Validating data and preparing for processing...")
            
            try:
                with status_container.container():
                    st.info("📤 Sending data to workflow...")
                
                response = requests.post(N8N_WEBHOOK_URL, json=combined_data, timeout=30)
                status_container.empty()
                
                try:
                    response_data = response.json()
                    status = response_data.get('status', 'unknown')
                    message = response_data.get('message', '')
                    
                    if response.status_code == 200 and status == 'success':
                        st.balloons()
                        st.success(f"✅ {message}")
                        st.session_state.processing_status = "processing"
                        st.info("📊 Processing is running in the background. Check the **Processing Results** tab to see agent reasoning and outputs.")
                        st.markdown("💡 **Tip:** Click on the '📊 Processing Results' tab above to view the processing results.")
                        
                    elif response.status_code == 400 and status == 'error':
                        missing_fields = response_data.get('missing_fields', [])
                        missing_count = response_data.get('missing_count', len(missing_fields) if missing_fields else 0)
                        
                        st.error(f"❌ {message}")
                        st.session_state.processing_status = "error"
                        
                        if missing_fields:
                            st.warning(f"⚠️ Found {missing_count} missing data field(s). Please re-upload the file with all required data.")
                            with st.expander("📋 View missing fields details"):
                                for field in missing_fields[:20]:
                                    st.text(f"• {field}")
                                if len(missing_fields) > 20:
                                    st.text(f"... and {len(missing_fields) - 20} more")
                        else:
                            st.warning("⚠️ Please re-upload the file with all required data.")
                    else:
                        st.error(f"❌ Error {response.status_code}: {message or response.text}")
                        st.session_state.processing_status = "error"
                        
                except (ValueError, KeyError):
                    status_container.empty()
                    if response.status_code == 200:
                        st.balloons()
                        st.success("✅ Upload successful! Data is complete. Processing has started.")
                        st.session_state.processing_status = "processing"
                        st.info("📊 Check the **Processing Results** tab to see results as they become available.")
                    else:
                        st.error(f"❌ Error {response.status_code}: {response.text}")
                        st.session_state.processing_status = "error"
                
            except requests.exceptions.Timeout:
                status_container.empty()
                st.error("⏱️ Request timed out. The workflow may still be processing. Check the Processing Results tab.")
                st.session_state.processing_status = "timeout"
            except requests.exceptions.ConnectionError:
                status_container.empty()
                st.error(f"❌ Could not connect to n8n at {N8N_WEBHOOK_URL}. Is the service running?")
                st.session_state.processing_status = "error"
            except Exception as e:
                status_container.empty()
                st.error(f"❌ An error occurred: {str(e)}")
                st.session_state.processing_status = "error"
    
    elif not st.session_state.batch_data:
        st.info("📤 Please upload batch data to continue")
    elif not st.session_state.route_data:
        st.info("🗺️ Please upload route data to continue")

# --- TAB 2: PROCESSING RESULTS ---
with tab2:
    st.subheader("Processing Results")
    st.caption("View agent reasoning, compliance assessments, routing decisions, and final outputs from the workflow.")
    
    col_refresh, col_info = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    try:
        # Load data from Google Sheets
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        
        if df.empty:
            st.info("📭 No processing results yet. Upload data and start processing to see results here.")
        else:
            # Search functionality
            search_term = st.text_input("🔍 Search Results", placeholder="Enter Batch ID, Shipment ID, or Status...")
            if search_term:
                df = df[df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]
            
            # Display results with styling
            st.markdown("### Compliance & Decision Results")
            
            # Status styling
            def style_status(val):
                color = "#930b19" if str(val).upper() == 'FLAGGED' else "#0f6f13" if str(val).upper() == 'GOOD' else ''
                return f'background-color: {color}'
            
            styled_df = df.style.map(style_status, subset=['Status'] if 'Status' in df.columns else [])
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # Show detailed reasoning if available
            if 'Rationale' in df.columns:
                st.markdown("### Agent Reasoning")
                for idx, row in df.iterrows():
                    with st.expander(f"📋 {row.get('BatchID', 'Unknown')} - {row.get('Status', 'Unknown')}"):
                        st.markdown(f"**Rationale:** {row.get('Rationale', 'N/A')}")
                        if 'Constraints' in row and pd.notna(row['Constraints']):
                            st.markdown(f"**Constraints:** {row.get('Constraints', 'N/A')}")
            
    except Exception as e:
        st.warning("⚠️ Could not load data. Did you 'Publish to Web' as CSV in Google Sheets?")
        st.code(GOOGLE_SHEET_CSV_URL)
        st.error(f"Error: {str(e)}")

# --- TAB 3: HUMAN JUDGMENT ---
with tab3:
    st.subheader("Human Judgment & Approval")
    st.caption("Review agent decisions and make final shipping approvals.")
    
    try:
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        
        if df.empty:
            st.info("📭 No results available for judgment. Process some shipments first.")
        else:
            # Filter for items that need judgment
            if 'Status' in df.columns:
                flagged_items = df[df['Status'].str.upper() == 'FLAGGED'] if 'Status' in df.columns else df
                
                if flagged_items.empty:
                    st.success("✅ No flagged items requiring judgment at this time.")
                else:
                    st.markdown(f"### {len(flagged_items)} Item(s) Requiring Judgment")
                    
                    for idx, row in flagged_items.iterrows():
                        with st.container():
                            st.divider()
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**Batch ID:** {row.get('BatchID', 'Unknown')}")
                                st.markdown(f"**Status:** {row.get('Status', 'Unknown')}")
                                st.markdown(f"**Rationale:** {row.get('Rationale', 'N/A')}")
                                if 'Constraints' in row and pd.notna(row['Constraints']):
                                    st.markdown(f"**Constraints:** {row.get('Constraints', 'N/A')}")
                                if 'Timestamp' in row:
                                    st.caption(f"Processed: {row.get('Timestamp', 'N/A')}")
                            
                            with col2:
                                judgment_key = f"judgment_{row.get('BatchID', idx)}"
                                judgment = st.radio(
                                    "Decision:",
                                    ["Approve", "Reject", "Review"],
                                    key=judgment_key,
                                    horizontal=False
                                )
                                
                                if judgment == "Approve":
                                    st.success("✅ Approved for shipping")
                                elif judgment == "Reject":
                                    st.error("❌ Rejected")
                                else:
                                    st.warning("⚠️ Needs review")
                    
                    # Summary
                    st.divider()
                    st.markdown("### Judgment Summary")
                    judgments = {}
                    for idx, row in flagged_items.iterrows():
                        key = f"judgment_{row.get('BatchID', idx)}"
                        if key in st.session_state:
                            judgment = st.session_state[key]
                            judgments[judgment] = judgments.get(judgment, 0) + 1
                    
                    if judgments:
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Approved", judgments.get("Approve", 0))
                        col2.metric("Rejected", judgments.get("Reject", 0))
                        col3.metric("Under Review", judgments.get("Review", 0))
            
            # Show all items summary
            st.divider()
            st.markdown("### All Processed Items")
            if 'Status' in df.columns:
                status_counts = df['Status'].value_counts()
                col1, col2 = st.columns(2)
                col1.metric("Good", status_counts.get('GOOD', 0))
                col2.metric("Flagged", status_counts.get('FLAGGED', 0))
    
    except Exception as e:
        st.warning("⚠️ Could not load data for judgment.")
        st.error(f"Error: {str(e)}")
