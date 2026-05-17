import json
import os
import random
from flask import Flask, render_template, request, jsonify
from difflib import SequenceMatcher

app = Flask(__name__)
MEMORY_FILE = "brain.json"
KNOWLEDGE_DIR = "knowledge"

# Ensure knowledge folder exists
if not os.path.exists(KNOWLEDGE_DIR):
    os.makedirs(KNOWLEDGE_DIR)

def load_memory():
    default_structure = {
        "personality": "student",
        "metadata": {"version": "4.0.0", "hallucinations": 0}
    }
    
    if not os.path.exists(MEMORY_FILE):
        return default_structure
    
    try:
        with open(MEMORY_FILE, "r") as f:
            content = json.load(f)
            
            # --- EVOLUTIONARY PATCHING ---
            # If the user is upgrading from Gen-3 to Gen-4
            if "metadata" not in content:
                content["metadata"] = default_structure["metadata"]
            
            # Specifically check for the 'hallucinations' key to prevent KeyErrors
            if "hallucinations" not in content["metadata"]:
                content["metadata"]["hallucinations"] = 0
                
            return content
    except Exception as e:
        print(f"Brain Corruption: {e}. Starting fresh.")
        return default_structure

def save_memory(mem):
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=4)

brain = load_memory()

def get_knowledge_base():
    facts = []
    if not os.path.exists(KNOWLEDGE_DIR):
        return facts
    for filename in os.listdir(KNOWLEDGE_DIR):
        if filename.endswith(".txt"):
            # Added 'errors="ignore"' to skip characters it doesn't understand
            # This prevents the 'UnicodeDecodeError' from crashing the server
            try:
                with open(os.path.join(KNOWLEDGE_DIR, filename), "r", encoding="utf-8", errors="ignore") as f:
                    facts.extend([line.strip() for line in f.readlines() if line.strip()])
            except Exception as e:
                print(f"Skipping {filename} due to read error: {e}")
    return facts

def get_similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def simulate_hallucination(facts):
    """Mixes existing knowledge to create a fake answer."""
    if not facts:
        return "I... I don't know anything yet."
    
    # Grab fragments of real facts to build a fake one
    frag1 = random.choice(facts).split()[:3]
    frag2 = random.choice(facts).split()[-3:]
    brain["metadata"]["hallucinations"] += 1
    save_memory(brain)
    return f"I think it's something about {' '.join(frag1)} and {' '.join(frag2)}."

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").lower().strip()
    if not user_input:
        return jsonify({"reply": "...", "status": "idle"})

    facts = get_knowledge_base()
    
    # Handle Yes/No questions specifically
    is_yes_no = any(user_input.startswith(w) for w in ["is", "can", "do", "does", "will", "are"])
    
    best_fact = ""
    max_score = 0
    
    for fact in facts:
        score = get_similarity(user_input, fact)
        if score > max_score:
            max_score = score
            best_fact = fact

    # Decision Logic (The "Student" Brain)
    if max_score > 0.6:
        # Found it! (High Confidence)
        reply = best_fact
        if is_yes_no:
            reply = f"Yes, based on my notes: {best_fact}"
        status = "learned"
    elif 0.2 < max_score <= 0.6:
        # The "Hallucination" Zone (Medium-Low Confidence)
        reply = simulate_hallucination(facts)
        status = "confused"
    else:
        # Total blank (Very Low Confidence)
        reply = "I haven't studied that yet. Can you put it in a .txt file for me?"
        status = "clueless"

    return jsonify({
        "reply": reply,
        "status": status,
        "confidence": f"{int(max_score*100)}%"
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)