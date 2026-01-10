from flask import render_template , request , jsonify , send_file
from io import BytesIO
from uuid import uuid4
from routes.utils import AiReq

def NoteEnhancer():
    return render_template('noteEnhancer.html')

def EnhanceNotes(prompts: dict):
    data: dict = request.get_json()
    NOTES = data["notes"]
    LANGUAGE = data["language"]
    API_MODE = data["apiMode"]
    MODEL = data.get("model")

    IsReasoning = False
    if MODEL:
        MODEL = MODEL.strip()
        IsReasoning = any(x in MODEL.lower() for x in ["gpt-5", "o1"])

    API_KEY = data["apiKey"]

    if API_MODE == "Hugging Face": 
        API_URL = "https://router.huggingface.co/v1/chat/completions" 
    elif API_MODE == "Gemini":
        API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    else:
        API_URL = "https://api.openai.com/v1/chat/completions"

    if API_MODE == "Hugging Face":
        headers = {"Authorization": f"Bearer {API_KEY}"}
    elif API_MODE == "OpenAI":
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    else: 
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY
        }
    
    PROMPT = prompts['enhanceNotes']

    if PROMPT == None:
        return jsonify({'notes': 'Internal Error: PROMPT NOT FOUND'})
    else:
        PROMPT = PROMPT.format(NOTES=NOTES , LANGUAGE=LANGUAGE)

    if API_MODE == "Hugging Face":
        payload = {
            "messages": [{"role": "user", "content": PROMPT}],
            "model": data.get("model") or "openai/gpt-oss-20b"
        }
    elif API_MODE == "OpenAI":
        payload = {
            "model": MODEL if MODEL else "gpt-4.1-nano",
            "messages": [{"role": "user", "content": PROMPT}],
        }
    elif API_MODE == "Gemini":
        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": PROMPT}]
            }]
        }

    if IsReasoning:
        payload["max_completion_tokens"] = 4096  
    else:
        payload["max_tokens"] = 4096
        payload["temperature"] = data.get("temperature", 0.3)
        payload["top_p"] = data.get("top_p", 0.9)

    if API_MODE != "Gemini" and payload.get("model" , None) is None:
        payload["model"] = "openai/gpt-oss-20b"

    if payload and API_MODE == "Hugging Face": print(f"Model: {payload["model"]}") 

    notes = AiReq(API_URL , headers , payload , API_MODE)

    if (notes is None):
        return jsonify({"notes": "Internal Error."})

    return jsonify({'notes': notes})

def EnhancedNotes(notes: dict):
    noteID = request.args.get('notes')
    notes = notes.get(noteID, '') if noteID else ''
    print("READ", noteID, "found:", bool(notes))
    return render_template('enhancedNotes.html', notes=notes)

def ImportNotes(notes: dict) -> None:
    file = request.files.get("noteFile")      
    file.stream.seek(0)

    data = file.read().decode("utf-8")

    noteID = str(uuid4())
    notes[noteID] = data
    print("STORED", noteID, "len:", len(data))

    return jsonify({"id": noteID})

def ExportNotes(notes: dict) -> None:
    notesID = request.args.get("notes")

    Notes = notes.get(notesID)

    buffer = BytesIO(Notes.encode("utf-8"))
    buffer.seek(0)
        
    return send_file(
        buffer, as_attachment=True,
        download_name=f"EduDuck-EnhancedNotes_{notesID}.txt",
        mimetype="text/plain"
    )