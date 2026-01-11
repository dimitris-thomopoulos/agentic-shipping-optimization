import streamlit as st
import json
import requests
import time

# --- CONFIGURATION ---
COMPLIANCE_URL = "http://localhost:8080/execute"
LOGISTICS_URL = "http://localhost:8081/execute"

# --- PAGE SETUP (CHANGED to 'wide') ---
st.set_page_config(
    page_title="Orders AI Manager",
    page_icon="🤖",
    layout="wide"  # <--- Key change for desktop views
)

# Custom CSS for a cleaner look
st.markdown("""
<style>
    .stDeployButton {display:none;}
    .block-container {padding-top: 2rem;}
    /* Add a light border to containers for better separation */
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stVerticalBlockBorderWrapper"]) {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("Orders Optimizer for Global Fashion Supply Chain")
st.markdown("#### A Compliance & Logistics Multi-Agent System")
st.info("Upload your **orders** file to start optimizing your orders.")

# --- HELPERS ---
def call_agent(url, payload, agent_name):
    """Generic function to call an agent with error handling."""
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Status {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": "Connection Failed", "details": str(e)}

def construct_payload(order_data):
    """Constructs the specific JSON structure the agents expect."""
    return {
        "task": {
            "name": "Frontend_Task",
            "desc": "Processed via Streamlit",
            "capabilities": ["frontend_trigger"]
        },
        "input_tokens": [{"place_id": "start", "data": order_data}],
        "output_places": [
            {"id": "out_1", "name": "P_Approved"},
            {"id": "out_2", "name": "P_Shipped"}
        ]
    }

# --- MAIN INTERFACE ---
uploaded_file = st.file_uploader("Drop your Order Data here", type=["json"])

if uploaded_file is not None:
    # Load Data
    try:
        all_orders = json.load(uploaded_file)
        st.success(f"Loaded {len(all_orders)} orders successfully!")
    except json.JSONDecodeError:
        st.error("Invalid JSON file.")
        st.stop()

    if st.button("🚀 Process Orders", type="primary"):
        st.markdown("---")
        
        # --- PROCESSING LOOP ---
        for i, entry in enumerate(all_orders):
            order_data = entry.get('data', entry)
            order_id = order_data.get('order_id', f'Order-{i+1}')
            item_name = order_data.get('items', ['Unknown'])[0] if isinstance(order_data.get('items'), list) else order_data.get('items', 'Unknown')
            destination = order_data.get('destination', 'Unknown')
            total_value = order_data.get('total_value', 'N/A')

            # Create a distinct row for each order
            with st.container(border=True): # Adds a nice box around the row
                # Layout: Info (20%) | Compliance (40%) | Logistics (40%)
                col_info, col_comp, col_log = st.columns([1, 2, 2])
                
                # --- COLUMN 1: ORDER INFO ---
                with col_info:
                    st.subheader(f"📦 {order_id}")
                    st.markdown(f"**Item:** {item_name}")
                    st.markdown(f"**Dest:** {destination}")
                    st.caption(f"Value: ${total_value}")

                # --- COLUMN 2: COMPLIANCE ---
                with col_comp:
                    status_box = st.status("Compliance Check...", expanded=True)
                    with status_box:
                        st.write("🔍 Analyzing restrictions...")
                        
                        # Prepare Payload
                        payload = construct_payload(order_data)
                        
                        # Call Agent
                        time.sleep(0.5) 
                        comp_result = call_agent(COMPLIANCE_URL, payload, "Compliance")
                        
                        if "error" in comp_result:
                            status_box.update(label="Compliance Error", state="error")
                            st.error(comp_result['details'])
                            compliance_status = "ERROR"
                        else:
                            out_data = comp_result.get('data', [{}])[0].get('data', {})
                            compliance_status = out_data.get('status', 'UNKNOWN')
                            reason = out_data.get('compliance_note', '')

                            if compliance_status == "APPROVED":
                                status_box.update(label="✅ Approved", state="complete", expanded=False)
                                st.success(f"**Decision: Approved**")
                            else:
                                status_box.update(label="🛑 Flagged", state="error", expanded=True)
                                st.error(f"**Flagged**: {reason}")

                # --- COLUMN 3: LOGISTICS ---
                with col_log:
                    if compliance_status == "APPROVED":
                        log_box = st.status("Logistics Planning...", expanded=True)
                        with log_box:
                            # st.write("🚚 Calculating route...")
                            
                            log_result = call_agent(LOGISTICS_URL, payload, "Logistics")
                            
                            if "error" in log_result:
                                log_box.update(label="Logistics Error", state="error")
                                st.error(log_result['details'])
                            else:
                                out_data = log_result.get('data', [{}])[0].get('data', {})
                                note = out_data.get('customer_note', 'N/A')
                                label = out_data.get('shipping_label', 'N/A')
                                
                                log_box.update(label=f"Shipped: {label}", state="complete", expanded=True)
                                st.info(f"**Note**: \"{note}\"")
                    
                    elif compliance_status == "ERROR":
                        st.warning("⚠️ Waiting (Agent Error)")
                    else:
                        st.markdown("")
                        st.caption("🔒 *Blocked by Compliance*")