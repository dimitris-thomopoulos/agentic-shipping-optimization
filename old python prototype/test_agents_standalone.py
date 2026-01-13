import requests
import json
import time

# --- CONFIGURATION ---
COMPLIANCE_URL = "http://localhost:8080/execute"
LOGISTICS_URL = "http://localhost:8081/execute"
DATA_FILE = "orders.json"

def test_all_orders():
    print("🧪 Starting BATCH Test for ALL Orders...\n")

    # 1. Load All Orders
    try:
        with open(DATA_FILE, 'r') as f:
            all_orders = json.load(f)
            print(f"🔹 Loaded {len(all_orders)} orders from {DATA_FILE}")
    except FileNotFoundError:
        print("❌ Error: orders.json not found.")
        return

    # 2. Iterate through each order
    for i, entry in enumerate(all_orders):
        order_data = entry['data']
        order_id = order_data.get('order_id', 'Unknown')
        
        print("\n" + "="*60)
        print(f"📦 Processing Order #{i+1}: {order_id}")
        print(f"   Details: {order_data.get('items')} -> {order_data.get('destination')}")
        print("="*60)

        # Construct Payload for this specific order
        mock_payload = {
            "task": {
                "name": "Batch_Test_Task",
                "desc": "Automated batch testing",
                "capabilities": ["test_capability"]
            },
            "input_tokens": [
                {
                    "place_id": "mock_place_id",
                    "data": order_data
                }
            ],
            "output_places": [
                {"id": "out_1", "name": "P_Approved"}, 
                {"id": "out_2", "name": "P_Shipped"}   
            ]
        }

        # --- Test Compliance Agent ---
        print(f"1️⃣  Asking Compliance Agent...")
        try:
            resp = requests.post(COMPLIANCE_URL, json=mock_payload)
            if resp.status_code == 200:
                result = resp.json()
                out_data = result.get('data', [{}])[0].get('data', {})
                status = out_data.get('status', 'UNKNOWN')
                reason = out_data.get('compliance_note', 'N/A')
                print(f"   🤖 Decision: {status}")
                if status == 'FLAGGED':
                    print(f"      Reason: {reason}")
            else:
                print(f"   ❌ Error: {resp.status_code}")
        except Exception as e:
            print(f"   ❌ Connection Failed: {e}")

        # --- Test Logistics Agent ---
        print(f"2️⃣  Asking Logistics Agent...")
        try:
            resp = requests.post(LOGISTICS_URL, json=mock_payload)
            if resp.status_code == 200:
                result = resp.json()
                out_data = result.get('data', [{}])[0].get('data', {})
                note = out_data.get('customer_note', 'N/A')
                print(f"   📝 Shipping Note: \"{note}\"")
            else:
                print(f"   ❌ Error: {resp.status_code}")
        except Exception as e:
            print(f"   ❌ Connection Failed: {e}")

        # Small pause between orders to keep output readable
        time.sleep(1.5)

if __name__ == "__main__":
    test_all_orders()