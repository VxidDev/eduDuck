from flask import render_template , request , jsonify , send_file , url_for
from flask_login import current_user
from routes.utils import AiReq , IncrementUsage , StoreQuizResult , StoreQuery , GetQueryFromDB , Log , storeQuiz
import os , re
from io import BytesIO
from json import dumps , JSONDecodeError , load
from uuid import uuid4
from requests import post

standardApiErrors = {
    "API error 402": "Payment required or free credits exhausted.",
    "API error 401": "Invalid or missing API key."
}

moreApiErrors = {
    "API error 429": "Rate limit exceeded. Too many requests in a short time.",
    "API error 503": "Service unavailable. The API is temporarily down.",
    "Model not loaded": "The AI model is still loading or unavailable.",
    "Request timeout": "The request took too long to process. Try again later.",
    "API error 400": "Bad request. The input data may be malformed or missing required fields."
}

def ParseStudyPlan(planText: str):
    parts = re.split(r'(Day \d+:)', planText)
    studyPlan = []

    for i in range(1, len(parts), 2):
        dayLabel = parts[i].strip()
        dayContent = parts[i + 1].strip() if i + 1 < len(parts) else ""
        studyPlan.append({"day": dayLabel, "tasks": dayContent})

    return studyPlan

def StudyPlanGen(prompts: dict):
    data = request.get_json()
    
    IS_FREE = data["isFree"]
    NOTES = data["notes"]
    LANGUAGE = data["language"]
    API_MODE = data["apiMode"]
    MODEL = data.get("model", False)

    START_DATE = data.get("startDate")
    END_DATE = data.get("endDate")
    HOURS_PER_DAY = data.get("hoursPerDay")
    LEARNING_STYLES = data.get("learningStyles", [])
    GOAL = data.get("goal", "")

    IsReasoning = False

    if IS_FREE:
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
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    else:
        headers = {"Content-Type": "application/json", "x-goog-api-key": API_KEY}

    PROMPT = prompts.get("studyPlan")
    if PROMPT is None:
        return jsonify({"plan": "Internal Error: PROMPT NOT FOUND"})
    else:
        PROMPT = PROMPT.format(
            NOTES=NOTES,
            LANGUAGE=LANGUAGE,
            START_DATE=START_DATE,
            END_DATE=END_DATE,
            HOURS_PER_DAY=HOURS_PER_DAY,
            LEARNING_STYLES=", ".join(LEARNING_STYLES),
            GOAL=GOAL
        )

    if API_MODE == "Hugging Face":
        payload = {
            "messages": [{"role": "user", "content": PROMPT}],
            "model": MODEL or "openai/gpt-oss-20b"
        }
    elif API_MODE == "OpenAI":
        payload = {
            "model": MODEL or "gpt-4.1-nano",
            "messages": [{"role": "user", "content": PROMPT}],
        }
    elif API_MODE == "Gemini":
        payload = {
            "contents": [{"role": "user", "parts": [{"text": PROMPT}]}]
        }

    if IsReasoning:
        payload["max_completion_tokens"] = 4096
    elif API_MODE == "Gemini":
        pass
    else:
        payload["max_tokens"] = 4096
        payload["temperature"] = data.get("temperature", 0.3)
        payload["top_p"] = data.get("top_p", 0.9)

    if payload and API_MODE == "Hugging Face":
        print(f"Model: {payload['model']}")

    output = AiReq(API_URL, headers, payload, API_MODE)

    if output is None:
        return jsonify({"plan": "Internal Error."})

    Log("Got AI response, checking if success..." , "info")

    if output in standardApiErrors:
        output = standardApiErrors[output]
    elif output in moreApiErrors:
        output = moreApiErrors[output]
    else:
        Log("Generated study plan. Parsing..." , "success")

    plan = ParseStudyPlan(output)

    if (len(plan) == 0): 
        Log("Failed to parse study plan. (empty)" , "error")
    else:
        if current_user.is_authenticated:
            queryRes = StoreQuery("plan" , plan)
        else:
            queryRes = post(url_for("storeStudyPlan" , _external=True) , json={"plan": plan})

    return jsonify({'id': queryRes.json().get('id') if not current_user.is_authenticated else queryRes})

def StudyPlan(studyPlans):
    planID = request.args.get('id')

    if current_user.is_authenticated:
        plan = GetQueryFromDB(planID , 'study-plans') or ''
        db = "mongoDB"
    else:
        plan = studyPlans.get(planID, '') if planID else ''
        db = "session-storage"

    Log(f"Got query from {db}. (id: {planID} , collection: study-plans)\nLength: {len(plan)}" , "info")

    return render_template("Study Plan Generator/StudyPlan.html" , plan=plan)

def ExportStudyPlan(studyPlans: dict) -> None:
    planID = request.args.get("plan")

    plan = studyPlans.get(planID)

    buffer = BytesIO(dumps(plan , indent=2).encode("utf-8"))
    buffer.seek(0)
        
    return send_file(
        buffer, as_attachment=True,
        download_name=f"EduDuck-Study-Plan_{planID}.json",
        mimetype="application/json"
    )

def ImportStudyPlan(studyPlans: dict) -> None:
    file = request.files.get("planFile")      
    file.stream.seek(0)

    try:                
        data = load(file.stream)
    except JSONDecodeError:
        return jsonify({"err": "Invalid Study Plan!"})

    planID = str(uuid4())
    studyPlans[planID] = data
    print("STORED", planID, "len:", len(data))

    return jsonify({'id': planID , "err": None})
