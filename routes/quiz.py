import re
from flask import render_template , request , jsonify , send_file , url_for , current_app
from flask_login import current_user
from quiz_parser import parse_quiz # Rust Function
from routes.utils import AiReq , IncrementUsage , StoreTempQuery, StoreQuery , GetQueryFromDB , Log , GetMongoClient
from json import load , JSONDecodeError , dumps
from uuid import uuid4
from io import BytesIO
from requests import post
from bson import ObjectId
import os
import submit_quiz

import time

standardApiErrors = {
    "API error 402": "1 What does API error 402 mean? a) Payment error b) Deposit needed c) Free credits exhausted d) Invalid API key |CORRECT:c",
    "API error 401": "1 What does API error 401 mean? a) Invalid or missing API key b) Not enough credits c) Server is down d) Quiz parsing failed |CORRECT:a"
}

moreApiErrors = {
    "API error 429": "1 What does API error 429 mean? a) Rate limit exceeded b) Invalid request c) Server error d) Model not found |CORRECT:a",
    "API error 503": "1 What does API error 503 mean? a) Service unavailable b) Payment required c) Bad request d) Unauthorized |CORRECT:a",
    "Model not loaded": "1 What does 'Model not loaded' mean? a) Model still loading b) Invalid model name c) No internet d) API key expired |CORRECT:a",
    "Request timeout": "1 What does 'Request timeout' mean? a) Server too slow b) Invalid payload c) Rate limited d) Wrong endpoint |CORRECT:a",
    "API error 400": "1 What does API error 400 mean? a) Bad request b) Payment required c) Unauthorized d) Rate limited |CORRECT:a"
}

def QuizGenerator(RemainingUsage):
    return render_template('Quiz Generator/QuizGenerator.html', remaining=RemainingUsage() , prefill_topic=request.args.get('topic', '').strip())

def quiz(quizzes, RemainingUsage):
    quizID = request.args.get('id')
    
    if current_user.is_authenticated:
        quiz = GetQueryFromDB(quizID , 'quizzes') or ''
        db = "mongoDB"

        if not quiz:
            quiz = quizzes.get(quizID, '') if quizID else ''
            db = "session-storage (fallback from mongoDb)"
    else:
        quiz = quizzes.get(quizID, '') if quizID else ''
        db = "session-storage"

    Log(f"Got query from {db}. (id: {quizID} , collection: quizzes)\nLength: {len(quiz)}" , "info")

    return render_template("Quiz Generator/Quiz.html" , quiz=quiz, remaining=RemainingUsage())

def QuizResult(quizResults, RemainingUsage):
    quizResultID = request.args.get('result')
    results = quizResults.get(quizResultID , '') if quizResultID else ''
    print("READ", quizResultID, "found:", bool(results))
    return render_template("Quiz Generator/QuizResult.html" , results=results, remaining=RemainingUsage())

def submitResult(quizResults: dict):
    start = time.perf_counter()
    data = request.get_json()
    quiz = data.get('quiz', {})
    user_answers = data.get('answers', {})
    
    if not quiz:
        return jsonify({'error': 'No quiz data'}), 400
    
    result_data = submit_quiz.submit_quiz.submit_result(quiz, user_answers)
    end = time.perf_counter()
    Log(f"Parsing Time: {end - start:0.6f}s" , "info")
    
    return jsonify({"id": StoreTempQuery(result_data , quizResults)})

def QuizGen(prompts: dict , quizzes: dict):
    data: dict = request.get_json()
    IS_FREE = data["isFree"]
    NOTES = data["notes"]
    LANGUAGE = data["language"]
    AMOUNT = data["questionCount"]
    API_MODE = data["apiMode"]
    DIFFICULTY = data["difficulty"]
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

    PROMPT = prompts['quiz']

    if PROMPT == None:
        return jsonify({'quiz': 'Internal Error: PROMPT NOT FOUND'})
    else:
        PROMPT = PROMPT.format(NOTES=NOTES , LANGUAGE=LANGUAGE, AMOUNT=AMOUNT , DIFFICULTY=DIFFICULTY)

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

    start = time.perf_counter()
    output = AiReq(API_URL , headers , payload , API_MODE)
    end = time.perf_counter()

    if (output is None):
        return jsonify({"quiz": "Internal Error."})

    Log(f"Got AI response, time: {end - start:.6f}s. checking if success..." , "info")

    if output in standardApiErrors:
        output = standardApiErrors[output]
    elif output in moreApiErrors:
        output = moreApiErrors[output]
    else:
        Log("Generated quiz. Parsing..." , "success")

    start = time.perf_counter()
    quiz = parse_quiz(output)
    end = time.perf_counter()

    Log(f"Parsing Time: {end - start:0.6f}s" , "info")

    queryRes = None

    if len(quiz) == 0:
        Log("Failed to parse quiz. (empty)" , "error")
    else:
        if current_user.is_authenticated:
            queryRes = StoreQuery("quiz" , quiz)
        else:
            queryRes = StoreTempQuery(quiz , quizzes)

    return jsonify({'id': queryRes})

def ImportQuiz(quizzes: dict) -> None:
    file = request.files.get("quizFile")      
    file.stream.seek(0)

    try:                
        data = load(file.stream)
    except JSONDecodeError:
        return jsonify({"err": "Invalid Quiz!"})

    quizID = str(uuid4())
    quizzes[quizID] = data
    print("STORED", quizID, "len:", len(data))

    return jsonify({'id': quizID , "err": None})

def ExportQuiz(quizzes: dict) -> None:
    quizID = request.args.get("quiz")

    if current_user.is_authenticated:
        quiz = GetQueryFromDB(quizID, 'quizzes') or ''

        if not quiz:
            quiz = quizzes.get(quizID, '') if quizID else ''
    else:
        quiz = quizzes.get(quizID, '') if quizID else ''

    buffer = BytesIO(dumps(quiz, indent=2).encode("utf-8"))
    buffer.seek(0)
        
    return send_file(
        buffer, as_attachment=True,
        download_name=f"EduDuck-Quiz_{quizID}.json",
        mimetype="application/json"
    )

    