import json
import os
import re
from flask import Flask, render_template, request, jsonify
from difflib import SequenceMatcher

app = Flask(__name__)
MEMORY_FILE = "brain.json"

# =========================
# BRAIN ARCHITECTURE (GEN-3.1)
# =========================
def load_memory():
    default_structure = {
        "data": {}, 
        "personality": "neutral",
        "metadata": {"interactions": 0, "version": "3.1.0"}
    }
    
    if not os.path.exists(MEMORY_FILE):
        return default_structure
    
    try:
        with open(MEMORY_FILE, "r") as f:
            content = json.load(f)
            
            # --- MIGRATION LOGIC (The Fix) ---
            # If metadata is missing from the old file, add it now
            if "metadata" not in content:
                content["metadata"] = default_structure["metadata"]
            if "data" not in content:
                content["data"] = {}
            return content
    except Exception as e:
        print(f"Critial Load Error: {e}. Resetting to default.")
        return default_structure

def save_memory(mem):
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=4)

# Initialize Brain
brain = load_memory()

def get_smart_ratio(user_input, known_question):
    seq_score = SequenceMatcher(None, user_input, known_question).ratio()
    u_set = set(user_input.split())
    k_set = set(known_question.split())
    if not u_set: return 0
    intersect = len(u_set.intersection(k_set)) / len(u_set)
    return (seq_score * 0.6) + (intersect * 0.4)

# =========================
# EVOLUTIONARY API
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").lower().strip()
    
    if not user_input:
        return jsonify({"reply": "Input stream empty.", "status": "idle"})

    best_score = 0
    best_answer = None
    
    # Process Memory
    for question, details in brain["data"].items():
        score = get_smart_ratio(user_input, question)
        if score > best_score:
            best_score = score
            best_answer = details["answer"]

    # Decision Matrix
    if best_score > 0.75:
        # This was the crash line - now protected by Migration Logic
        brain["metadata"]["interactions"] += 1
        save_memory(brain) 
        return jsonify({
            "reply": best_answer, 
            "status": "match",
            "confidence": f"{int(best_score*100)}%"
        })
    elif best_score > 0.4:
        return jsonify({
            "reply": f"I found a partial match: '{best_answer}'. Is this what you meant?",
            "status": "suggest"
        })
    else:
        return jsonify({
            "reply": "Neural entry not found. Please provide a definition for this concept.",
            "status": "learn"
        })

@app.route("/teach", methods=["POST"])
def teach():
    data = request.json
    question = data.get("question", "").lower().strip()
    answer = data.get("answer", "").strip()
    
    if question and answer:
        brain["data"][question] = {"answer": answer}
        brain["metadata"]["interactions"] += 1
        save_memory(brain)
        return jsonify({"reply": "Neural mapping successful. Data integrated.", "status": "success"})
    return jsonify({"reply": "Integration failed. Invalid data.", "status": "error"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)