import json
import os
import random
from flask import Flask, render_template, request, jsonify
from difflib import SequenceMatcher

app = Flask(__name__)
MEMORY_FILE = "brain.json"
KNOWLEDGE_DIR = "knowledge"

if not os.path.exists(KNOWLEDGE_DIR):
    os.makedirs(KNOWLEDGE_DIR)

def load_memory():
    default_structure = {
        "personality": "focused",
        "metadata": {"version": "4.1.0", "hallucinations": 0}
    }
    if not os.path.exists(MEMORY_FILE):
        return default_structure
    try:
        with open(MEMORY_FILE, "r") as f:
            content = json.load(f)
            # Patching supaya gak KeyError lagi
            if "metadata" not in content:
                content["metadata"] = default_structure["metadata"]
            if "hallucinations" not in content["metadata"]:
                content["metadata"]["hallucinations"] = 0
            return content
    except:
        return default_structure

def save_memory(mem):
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=4)

brain = load_memory()

def get_knowledge_base():
    facts = []
    for filename in os.listdir(KNOWLEDGE_DIR):
        if filename.endswith(".txt"):
            try:
                # Ditambah errors='ignore' biar gak kena UnicodeDecodeError lagi
                with open(os.path.join(KNOWLEDGE_DIR, filename), "r", encoding="utf-8", errors="ignore") as f:
                    facts.extend([line.strip() for line in f.readlines() if line.strip()])
            except Exception as e:
                print(f"Gagal baca {filename}: {e}")
    return facts

def get_similarity(a, b):
    # Menggunakan SequenceMatcher buat bandingin input vs teks di file
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").lower().strip()
    if not user_input:
        return jsonify({"reply": "...", "status": "idle"})

    facts = get_knowledge_base()
    
    # Deteksi pertanyaan Yes/No
    is_yes_no = any(user_input.startswith(w) for w in ["is", "can", "do", "does", "will", "are", "apakah"])
    
    best_fact = ""
    max_score = 0
    
    for fact in facts:
        score = get_similarity(user_input, fact)
        if score > max_score:
            max_score = score
            best_fact = fact

    # --- LOGIKA BARU: BIAR GAK NGASAL ---
    # Score 0.4 itu lumayan tinggi, kalau di bawah itu mending dia jujur gak tau
    if max_score > 0.45:
        reply = best_fact
        if is_yes_no:
            reply = f"Yes. According to my notes: {best_fact}"
        status = "accurate"
    else:
        # Daripada halusinasi parah, mending minta belajar lagi
        reply = "I don't recall seeing that in my files. Can you explain more?"
        status = "searching"

    return jsonify({
        "reply": reply,
        "status": status,
        "confidence": f"{int(max_score*100)}%"
    })

if __name__ == "__main__":
    # Tetap di port 5000 buat Windows 7 kamu
    app.run(host='0.0.0.0', port=5000, debug=True)