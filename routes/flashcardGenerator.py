from routes.utils import AiReq
from flask import render_template , request , jsonify , send_file
from json import load , JSONDecodeError , dumps
from uuid import uuid4
from io import BytesIO

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
    NOTES = data["notes"]
    LANGUAGE = data["language"]
    API_MODE = data["apiMode"]
    AMOUNT = data["amount"]

    API_KEY = data["apiKey"]
    API_URL = "https://router.huggingface.co/v1/chat/completions" if API_MODE == "Hugging Face" else f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_MODE == "Hugging Face" else  {
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY,
    }
    
    PROMPT = prompts['flashcard']

    if PROMPT == None:
        return jsonify({'flashcards': 'Internal Error: PROMPT NOT FOUND'})
    else:
        PROMPT = PROMPT.format(NOTES=NOTES , LANGUAGE=LANGUAGE , AMOUNT=AMOUNT)

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

