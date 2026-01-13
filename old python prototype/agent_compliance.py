import requests
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

app = FastAPI()

# --- CONFIGURATION ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:1b" # Replace with 'gemma3:1b' if available

# --- MODELS ---
class TaskDefinition(BaseModel):
    name: str
    desc: Optional[str] = None
    capabilities: Optional[List[str]] = None

class MarkingEntry(BaseModel):
    place_id: str
    data: Dict[str, Any]

class PlaceDefinition(BaseModel):
    id: str
    name: str

class ExecuteRequest(BaseModel):
    task: TaskDefinition
    input_tokens: List[MarkingEntry]
    output_places: List[PlaceDefinition]

# --- LLM FUNCTION ---
def ask_ollama_compliance(order_data):
    prompt = f"""
    You are a Compliance Officer. Analyze this order JSON:
    {json.dumps(order_data)}
    
    Rules:
    1. Reject orders with 'Luxury' items going to 'Paris'.
    2. Reject orders with 'T-Shirt' quantity > 400.
    3. Approve everything else.
    
    Respond ONLY with a JSON object: {{"status": "APPROVED"}} or {{"status": "FLAGGED", "reason": "..."}}.
    Do not add markdown formatting.
    """
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json" # Forces valid JSON output
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload)
        resp_json = resp.json()
        result_text = resp_json.get("response", "{}")
        return json.loads(result_text)
    except Exception as e:
        print(f"   ⚠️ LLM Error: {e}")
        return {"status": "FLAGGED", "reason": "AI Error"}

# --- ENDPOINT ---
@app.post("/execute")
async def execute_compliance_check(req: ExecuteRequest):
    print(f"\n🧠 AI Compliance Agent Processing Task...")
    
    if not req.input_tokens:
        raise HTTPException(status_code=400, detail="No input tokens provided")
    
    order_data = req.input_tokens[0].data
    print(f"   📦 Analyzing Order: {order_data.get('order_id')}")

    # CALL OLLAMA
    decision = ask_ollama_compliance(order_data)
    
    status = decision.get("status", "FLAGGED")
    reason = decision.get("reason", "No reason provided")
    
    print(f"   🤖 AI Decision: {status}")
    if status == "FLAGGED":
        print(f"      Reason: {reason}")

    # Update Data
    order_data["status"] = status
    order_data["compliance_note"] = reason

    # Route to Output
    target_place = next((p for p in req.output_places if p.name == "P_Approved"), None)
    
    response_data = []
    # Only forward if approved (Simulation logic) - or forward anyway with FLAGGED status
    if target_place:
        response_data.append({
            "place_id": target_place.id,
            "data": order_data
        })
    
    return {"data": response_data}

if __name__ == "__main__":
    print(f"🧠 AI Compliance Agent Started (Model: {MODEL_NAME})")
    uvicorn.run(app, host="0.0.0.0", port=8080)