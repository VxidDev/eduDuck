from routes.utils import AiReq , IncrementUsage
from flask import render_template , request , jsonify , send_file
from json import load , JSONDecodeError , dumps
from uuid import uuid4
from io import BytesIO
import os

standardApiErrors = {
    "API error 402": "What does API error 402 mean? | Free credits exhausted ~",
    "API error 401": "What does API error 401 mean? | Invalid or missing API key ~"
}

moreApiErrors = {
    "API error 429": "What does API error 429 mean? | Rate limit exceeded ~",
    "API error 503": "What does API error 503 mean? | Service unavailable ~",
    "Model not loaded": "What does 'Model not loaded' mean? | Model still loading ~",
    "Request timeout": "What does 'Request timeout' mean? | Server too slow ~",
    "API error 400": "What does API error 400 mean? | Bad request ~"
}

def ParseFlashcards(fc: str) -> dict:
    if not fc: return {}
    output = {}
    currFc = 0
    
    for flashcard in fc.split("~"):
        try:
            question, answer = flashcard.split("|", 1) 
            question, answer = question.strip(), answer.strip()
            if question and answer:  
                output[currFc] = {'question': question, 'answer': answer}
                currFc += 1 
        except ValueError:
            continue  
    
    return output

def FlashcardGenerator(prompts: dict):
    data: dict = request.get_json()
    IS_FREE = data["isFree"]
    NOTES = data["notes"]
    LANGUAGE = data["language"]
    API_MODE = data["apiMode"]
    AMOUNT = data["amount"]
    MODEL = data.get("model" , False)

    IsReasoning = False

    if IS_FREE: IncrementUsage()

    if MODEL:
        MODEL = MODEL.strip()
        IsReasoning = any(x in MODEL.lower() for x in ["gpt-5", "o1"])

    API_KEY = data["apiKey"] if not IS_FREE else os.getenv("GEMINI_API_KEY")

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
    
    PROMPT = prompts['flashcard']

    if PROMPT == None:
        return jsonify({'flashcards': 'Internal Error: PROMPT NOT FOUND'})
    else:
        PROMPT = PROMPT.format(NOTES=NOTES , LANGUAGE=LANGUAGE , AMOUNT=AMOUNT)

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
    elif API_MODE == "Gemini":
        pass  
    else:
        payload["max_tokens"] = 4096
        payload["temperature"] = data.get("temperature", 0.3)
        payload["top_p"] = data.get("top_p", 0.9)

    if payload and API_MODE == "Hugging Face": print(f"Model: {payload["model"]}") 

    output = AiReq(API_URL , headers , payload , API_MODE)

    if (output is None):
        return jsonify({"flashcards": "Internal Error."})

    print(f"Output: {output}")

    if output in standardApiErrors:
        output = standardApiErrors[output]
    elif output in moreApiErrors:
        output = moreApiErrors[output]
    else:
        print("Successfully generated flashcards. Parsing...")
    
    print(output)

    flashcards = ParseFlashcards(output)

    if len(flashcards) == 0:
        print("No flashcards.")
    
    print(flashcards)

    return jsonify({'flashcards': flashcards})

def FlashCardGenerator():
    return render_template("flashCardGenerator.html")

def FlashCardResult(flashcards: dict) -> None:
    flashcardId = request.args.get('id')
    Flashcards = flashcards.get(flashcardId)
    print("READ", flashcardId, "found:", bool(Flashcards))
    return render_template("flashcards.html", flashcards=Flashcards)

def ImportFlashcards(flashcards: dict) -> None:
    file = request.files.get("flashcardFile")      
    file.stream.seek(0)

    try:                
        data = load(file.stream)
    except JSONDecodeError:
        return jsonify({"err": "Invalid Flashcards!"})

    flashcardID = str(uuid4())
    flashcards[flashcardID] = data
    print("STORED", flashcardID, "len:", len(data))

    return jsonify({'id': flashcardID , "err": None})

def ExportFlashcards(flashcards: dict) -> None:
    flashcardID = request.args.get("id")
    Flashcards = flashcards.get(flashcardID)

    buffer = BytesIO(dumps(Flashcards, indent=2).encode("utf-8"))
    buffer.seek(0)
        
    return send_file(
        buffer, as_attachment=True,
        download_name=f"EduDuck-Flashcards_{flashcardID}.json",
        mimetype="application/json"
    )

