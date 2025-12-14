from flask import render_template , request , jsonify
from routes.utils import AiReq

def NoteEnhancer():
    return render_template('noteEnhancer.html')

def EnhanceNotes(prompts: dict):
    data: dict = request.get_json()
    NOTES = data["notes"]
    LANGUAGE = data["language"]

    API_KEY = data["apiKey"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
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
    }

    if payload["model"] is None:
        payload["model"] = "openai/gpt-oss-20b"

    print(f"Model: {payload["model"]}")

    notes = AiReq(API_URL , headers , payload)

    if (notes is None):
        return jsonify({"notes": "Internal Error."})

    return jsonify({'notes': notes})

def EnhancedNotes(notes: dict):
    noteID = flask.request.args.get('notes')
    notes = notes.get(noteID, '') if noteID else ''
    print("READ", noteID, "found:", bool(notes))
    return render_template('enhancedNotes.html', notes=notes)