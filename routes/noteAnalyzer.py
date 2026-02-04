from flask import render_template, request, jsonify, send_file, current_app
from flask_login import current_user
from routes.utils import AiReq, IncrementUsage, StoreQuery, StoreTempQuery, GetQueryFromDB, Log, GetMongoClient
from json import dumps, JSONDecodeError, load
from io import BytesIO
from uuid import uuid4
from bson import ObjectId
import os

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


def ParseNoteAnalysis(raw_output: str) -> dict:
    if not raw_output or not raw_output.strip():
        return {"overall_score": 0, "sections": []}

    result = {
        "overall_score": 0,
        "sections": []
    }

    lines = raw_output.strip().split("\n")
    current_section = None
    current_field = None

    for line in lines:
        line_stripped = line.strip()

        if line_stripped.startswith("OVERALL_SCORE:"):
            try:
                score_str = line_stripped.split(":", 1)[1].strip()
                result["overall_score"] = int(score_str)
            except (ValueError, IndexError):
                Log(f"Failed to parse OVERALL_SCORE: {line_stripped}", "warn")
                continue

        elif line_stripped.startswith("SECTION:"):
            if current_section:
                result["sections"].append(current_section)

            title = line_stripped.split(":", 1)[1].strip()
            current_section = {
                "title": title,
                "confidence": 0,
                "issues": [],
                "why_it_matters": [],
                "suggestions": []
            }
            current_field = None

        elif line_stripped.startswith("CONFIDENCE:") and current_section:
            try:
                conf_str = line_stripped.split(":", 1)[1].strip()
                current_section["confidence"] = int(conf_str)
            except (ValueError, IndexError):
                Log(f"Failed to parse CONFIDENCE: {line_stripped}", "warn")
            current_field = None

        elif line_stripped == "ISSUES:":
            current_field = "issues"
        elif line_stripped == "WHY_IT_MATTERS:":
            current_field = "why_it_matters"
        elif line_stripped == "SUGGESTIONS:":
            current_field = "suggestions"

        elif line_stripped.startswith("-") and current_section and current_field:
            item = line_stripped[1:].strip()
            if item:
                current_section[current_field].append(item)

    if current_section:
        result["sections"].append(current_section)

    return result


def NoteAnalyzer(prompts: dict, analyses: dict):
    data: dict = request.get_json()

    IS_FREE = data.get("isFree", False)
    NOTES = data["notes"]
    LANGUAGE = data["language"]
    API_MODE = data["apiMode"]
    MODEL = data.get("model", False)

    IsReasoning = False

    if IS_FREE:
        with current_app.app_context():
            if not current_user.is_authenticated:
                Log("User not logined in.", "error")
                return render_template("pages/loginRequired.html")

            userData = GetMongoClient()["EduDuck"]["users"].find_one(
                {"_id": ObjectId(current_user.id)}
            )
            if not userData:
                Log("User account not found.", "error")
                return render_template("pages/loginRequired.html")

            times_used = userData.get("daily_usage", {}).get("timesUsed", 0)
            if times_used >= 3:
                Log("Daily limit reached.", "error")
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

    PROMPT = prompts.get("noteAnalyzer")
    if PROMPT is None:
        return jsonify({"analysis": "Internal Error: PROMPT NOT FOUND"})

    PROMPT = PROMPT.format(
        NOTES=NOTES,
        LANGUAGE=LANGUAGE,
    )

    if API_MODE == "Hugging Face":
        payload = {
            "messages": [{"role": "user", "content": PROMPT}],
            "model": data.get("model") or "openai/gpt-oss-20b"
        }
    elif API_MODE == "OpenAI":
        payload = {
            "model": MODEL if MODEL else "gpt-4.1-nano",
            "messages": [{"role": "user", "content": PROMPT}]
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
    elif API_MODE != "Gemini":
        payload["max_tokens"] = 4096

    payload["temperature"] = data.get("temperature", 0.3)
    payload["top_p"] = data.get("top_p", 0.9)

    if payload and API_MODE == "Hugging Face":
        print(f"Model: {payload['model']}")

    output = AiReq(API_URL, headers, payload, API_MODE)

    if output is None:
        return jsonify({"analysis": "Internal Error."})

    Log("Got AI response, checking if success...", "info")

    if output in standardApiErrors:
        output = standardApiErrors[output]
        return jsonify({"analysis": output})

    if output in moreApiErrors:
        output = moreApiErrors[output]
        return jsonify({"analysis": output})

    Log("Generated note analysis. Parsing...", "success")

    parsed = ParseNoteAnalysis(output)

    if not parsed.get("sections"):
        Log("Failed to parse note analysis. (empty)", "error")
        return jsonify({"analysis": "Could not parse analysis output."})

    if current_user.is_authenticated:
        query_id = StoreQuery("note-analysis", parsed)
    else:
        query_id = StoreTempQuery(parsed, analyses)

    return jsonify({"id": query_id})


def NoteAnalyzerPage():
    """GET /note-analyzer"""
    return render_template(
        "Note Analyzer/noteAnalyzer.html",
        prefill_topic=request.args.get("topic", "").strip()
    )


def NoteAnalysisResult(analyses: dict):
    analysis_id = request.args.get("id")

    if current_user.is_authenticated:
        analysis = GetQueryFromDB(analysis_id, "note-analysis") or ""
        db_src = "mongoDB"
        if not analysis:
            analysis = analyses.get(analysis_id, "") if analysis_id else ""
            db_src = "session-storage (fallback from mongoDb)"
    else:
        analysis = analyses.get(analysis_id, "") if analysis_id else ""
        db_src = "session-storage"

    if not analysis:
        Log(f"Failed to get note analysis from {db_src}. (empty)", "error")
    else:
        Log(
            f"Got query from {db_src}. (id: {analysis_id} , collection: note-analysis)\n"
            f"Length: {len(analysis)}", "info"
        )

    return render_template(
        "Note Analyzer/noteAnalysisResult.html",
        analysis=analysis
    )


def ImportNoteAnalysis(analyses: dict):
    file = request.files.get("analysisFile")
    file.stream.seek(0)

    try:
        data = load(file.stream)
    except JSONDecodeError:
        return jsonify({"err": "Invalid Note Analysis!"})

    analysis_id = str(uuid4())
    analyses[analysis_id] = data

    print("STORED", analysis_id, "len:", len(data))
    return jsonify({"id": analysis_id, "err": None})


def ExportNoteAnalysis(analyses: dict):
    analysis_id = request.args.get("id")
    analysis = analyses.get(analysis_id)

    buffer = BytesIO(dumps(analysis, indent=2).encode("utf-8"))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"EduDuck-NoteAnalysis_{analysis_id}.json",
        mimetype="application/json"
    )
