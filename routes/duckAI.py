from routes.utils import AiReq , IncrementUsage , GetMongoClient , GetQueryFromDB , Log
from flask import render_template , jsonify , request , current_app
from flask_login import current_user
from bson import ObjectId
import os

standardApiErrors = {
    "API error 402": "API error 402 occurred. Payment required - add credits to your account.",
    "API error 401": "API error 401 occurred. Invalid or missing API key. Check your token settings."
}

moreApiErrors = {
    "API error 429": "API error 429 occurred. Rate limit exceeded. Wait 1-5 minutes before retrying.",
    "API error 503": "API error 503 occurred. Service temporarily unavailable. Try again in a few minutes.",
    "Model not loaded": "Model not loaded error occurred. AI model still initializing. Wait 30-60 seconds and retry.",
    "Request timeout": "Request timeout occurred. Server too slow. Simplify notes or try shorter prompts.",
    "API error 400": "API error 400 occurred. Bad request format. Check JSON payload and parameters."
}

def GenerateResponse(prompts: dict):
    data: dict = request.get_json()
    MESSAGE = data["message"]
    API_MODE = data["apiMode"]
    MODEL = data.get("model" , False)
    IS_FREE = data.get("isFree" , False)
    LANGUAGE = data.get("language" , "en")

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
    
    PROMPT = prompts['generateResponse']

    if PROMPT == None:
        return jsonify({'response': 'Internal Error: PROMPT NOT FOUND'})
    else:
        PROMPT = PROMPT.format(MESSAGE=MESSAGE)

    languages = {
        "en": "English",
        "pl": "Polish",
        "ru": "Russian",
        "de": "German",
        "ua": "Ukrainian",
        "fr": "French"
    }
    language_name = languages.get(LANGUAGE, "English")
    PROMPT += f"\n\nPlease respond in {language_name}."

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

    if API_MODE != "Gemini" and payload.get("model" , None) is None:
        payload["model"] = "openai/gpt-oss-20b"

    if payload and API_MODE == "Hugging Face": print(f"Model: {payload["model"]}") 

    output = AiReq(API_URL , headers , payload , API_MODE)

    if (output is None):
        return jsonify({"response": "Internal Error."})

    print(f"Output: {output}")

    if output in standardApiErrors:
        output = standardApiErrors[output]
    elif output in moreApiErrors:
        output = moreApiErrors[output]
    else:
        print("Successfully generated response. Parsing...")
        
    print(output)

    return jsonify({'response': output})

def DuckAI():
    if not current_user.is_authenticated:
        return render_template("DuckAI/DuckAI.html" , chat=[] , prefill_topic=request.args.get('topic', '').strip())
    else:
        chatID = request.args.get('id')

        chat = GetQueryFromDB(chatID , 'duck-ai') or []

        Log(f"Got query from mongoDB. (id: {chatID} , collection: study-plans)\nLength: {len(chat)}" , "info")

        return render_template("DuckAI/DuckAI.html" , chat=chat , prefill_topic=request.args.get('topic', '').strip())
