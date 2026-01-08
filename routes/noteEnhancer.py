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

    API_KEY = data["apiKey"]
    API_URL = "https://router.huggingface.co/v1/chat/completions" if API_MODE == "Hugging Face" else f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_MODE == "Hugging Face" else  {
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY,
    }
    
    PROMPT = prompts['enhanceNotes']

    if PROMPT == None:
        return jsonify({'notes': 'Internal Error: PROMPT NOT FOUND'})
    else:
        PROMPT = PROMPT.format(NOTES=NOTES , LANGUAGE=LANGUAGE)

    payload = {
        "messages": [{
            "role": "user",
            "content": PROMPT
        }],
        "model": data.get("model" , "openai/gpt-oss-20b")
    } if API_MODE == "Hugging Face" else {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": PROMPT}
                ],
            }
        ]
    }

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