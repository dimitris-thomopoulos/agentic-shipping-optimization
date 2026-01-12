import requests
import json
import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

app = FastAPI()

# --- CONFIGURATION ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:1b" 

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
def ask_ollama_logistics(order_data):
    city = order_data.get("destination", "Unknown City")
    item = order_data.get("items", ["Package"])[0]
    
    prompt = f"""
    Write a short product description for the {item}. Keep it under 15 words.
    
    Respond ONLY with a single sentence.
    
    Do not add any text formatting such as asterisks. Do not ask any questions about the prompt or the request.
    """
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload)
        return resp.json().get("response", "Shipping Label Generated").strip()
    except Exception as e:
        print(f"   ⚠️ LLM Error: {e}")
        return f"Standard Label for {city}"

# --- ENDPOINT ---
@app.post("/execute")
async def execute_task(req: ExecuteRequest):
    print(f"\n🚚 AI Logistics Agent Processing Task...")

    if not req.input_tokens:
        raise HTTPException(status_code=400, detail="No input tokens provided")
    
    order_data = req.input_tokens[0].data
    order_id = order_data.get("order_id", "Unknown")
    
    print(f"   📦 Shipping Order: {order_id}")

    # CALL OLLAMA
    custom_message = ask_ollama_logistics(order_data)
    print(f"   📝 AI Note: \"{custom_message}\"")
    
    # Update Data
    order_data["shipping_label"] = f"SHP-{order_id}"
    order_data["customer_note"] = custom_message
    order_data["shipped_at"] = datetime.datetime.now().isoformat()

    # Route to Output
    target_place_name = "P_Shipped"
    target_place = next((p for p in req.output_places if p.name == target_place_name), None)
    
    response_data = []
    if target_place:
        response_data.append({
            "place_id": target_place.id,
            "data": order_data
        })
        print("   ✅ Task Complete.")

    return {"data": response_data}

if __name__ == "__main__":
    print(f"🚚 AI Logistics Agent Started (Model: {MODEL_NAME})")
    uvicorn.run(app, host="0.0.0.0", port=8081)