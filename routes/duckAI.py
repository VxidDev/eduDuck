from routes.utils import AiReq
from flask import render_template , jsonify , request

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

def DuckAI():
    return render_template("DuckAI.html")

def GenerateResponse(prompts: dict):
    data: dict = request.get_json()
    MESSAGE = data["message"]
    API_MODE = data["apiMode"]

    API_KEY = data["apiKey"]
    API_URL = "https://router.huggingface.co/v1/chat/completions" if API_MODE == "Hugging Face" else f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_MODE == "Hugging Face" else  {
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY,
    }
    
    PROMPT = prompts['generateResponse']

    if PROMPT == None:
        return jsonify({'response': 'Internal Error: PROMPT NOT FOUND'})
    else:
        PROMPT = PROMPT.format(MESSAGE=MESSAGE)

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