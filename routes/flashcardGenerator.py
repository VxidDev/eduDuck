from routes.utils import AiReq , IncrementUsage , StoreQuery , Log , GetQueryFromDB , StoreTempQuery , GetMongoClient
from flask_login import current_user
from requests import post
from flask import render_template , jsonify , request , send_file , url_for , current_app
from json import load , JSONDecodeError , dumps
from uuid import uuid4
from io import BytesIO
from bson import ObjectId
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
    if not fc: return []
    output = []
    
    for flashcard in fc.split("~"):
        try:
            question, answer = flashcard.split("|", 1) 
            question, answer = question.strip(), answer.strip()
            if question and answer:  
                output.append({'question': question, 'answer': answer})
        except ValueError:
            continue  
    
    return output

def FlashcardGenerator(prompts: dict , flashcardDict: dict):
    data: dict = request.get_json()
    IS_FREE = data.get("isFree" , False)
    NOTES = data["notes"]
    LANGUAGE = data["language"]
    API_MODE = data["apiMode"]
    AMOUNT = data["amount"]
    MODEL = data.get("model" , False)

    IsReasoning = False

    if IS_FREE:
        with current_app.app_context():
            if not current_user.is_authenticated:
                Log("User not logined in." , "error")
                return render_template("pages/loginRequired.html")

            userData = GetMongoClient()["EduDuck"]["users"].find_one({"_id": ObjectId(current_user.id)})
            if not userData:
                Log("User account not found." , "error")
                return render_template("pages/loginRequired.html")

            times_used = userData.get("daily_usage", {}).get("timesUsed", 0)
            if times_used >= 3:
                Log("Daily limit reached." , "error")
                return render_template("pages/dailyLimit.html", remaining=0)

        IncrementUsage()

    if MODEL:
        MODEL = MODEL.strip()
        IsReasoning = any(x in MODEL.lower() for x in ["gpt-5", "o1"])

    API_KEY = data["apiKey"] if not IS_FREE else os.getenv("FREE_TIER_API_KEY")

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

    Log("Got AI response, checking if success..." , "info")

    if output in standardApiErrors:
        output = standardApiErrors[output]
    elif output in moreApiErrors:
        output = moreApiErrors[output]
    else:
        Log("Generated flashcards. Parsing..." , "success")

    Log("Got AI response, checking if success..." , "info")

    flashcards = ParseFlashcards(output)

    if len(flashcards) == 0:
        Log("Failed to parse flashcards. (empty)" , "error")
    else:
        if current_user.is_authenticated:
            queryRes = StoreQuery("flashcards" , flashcards)
        else:
            queryRes = StoreTempQuery(flashcards , flashcardDict)

    return jsonify({'id': queryRes})

def FlashCardGenerator():
    return render_template("Flashcard Generator/flashCardGenerator.html")

def FlashCardResult(flashcards: dict) -> None:
    flashcardId = request.args.get('id')

    if current_user.is_authenticated:
        Flashcards = GetQueryFromDB(flashcardId , 'flashcards') or ''
        db = "mongoDB"

        if not Flashcards:
            Flashcards = flashcards.get(flashcardId, '') if flashcardId else ''
            db = "session-storage (fallback from mongoDb)"
    else:
        Flashcards = flashcards.get(flashcardId, '') if flashcardId else ''
        db = "session-storage"

    if not Flashcards:
        Log(f"Failed to get flashcards from {db}. (empty)" , "error")
    else:
        Log(f"Got query from {db}. (id: {flashcardId} , collection: flashcards)\nLength: {len(Flashcards)}" , "info")

    return render_template("Flashcard Generator/flashcards.html", flashcards=Flashcards)

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

