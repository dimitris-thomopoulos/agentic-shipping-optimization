import json
import re

# 1. Grab the raw text coming from the AI Agent
# We use .get() to avoid errors if the field is missing
ai_text = items[0].json.get('output', '')

# 2. Clean up the markdown formatting (remove ```json and ```)
clean_text = re.sub(r'```json\n?|```', '', ai_text).strip()

# 3. Parse the text into a real JSON object
try:
    decision_data = json.loads(clean_text)
except json.JSONDecodeError:
    # Fallback if AI output bad JSON (prevents workflow crash)
    decision_data = {"final_decision": "ERROR", "rationale": "AI returned invalid JSON"}

# 4. Return the clean object to n8n
return [{"json": decision_data}]