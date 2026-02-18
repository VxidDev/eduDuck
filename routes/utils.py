from requests import post
from pypdf import PdfReader
from flask import request , jsonify , render_template , url_for , redirect
from PIL import Image
from pymongo import MongoClient , ReturnDocument
import os
import urllib.parse
from datetime import date , datetime
from pymongo.server_api import ServerApi
import certifi
from bson.objectid import ObjectId 
from flask_login import login_user , UserMixin , current_user
from werkzeug.security import generate_password_hash , check_password_hash
import secrets
from rich.console import Console
from typing import Optional , Union , Dict , Any
import base64
import io
import httpx
import msgspec
from functools import wraps
import re
from datetime import datetime, timedelta, date
from collections import defaultdict
import math
from collections import defaultdict , Counter
import random

from uuid import uuid4
import time

console = Console()
_client = None

_httpxclient = httpx.Client(
    timeout=httpx.Timeout(60.0, connect=10.0),
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    http2=True  # HTTP/2 support for better performance
)

def Log(text , status) -> None:
    colors = {
        'error': 'red',
        'fatal': 'magenta',
        'warn': 'yellow',
        'success': 'green',
        'info': 'white'
    }

    color = colors.get(status , 'err')

    if color == 'err':
        console.print("[bold red] Unknown color! [/bold red]")
        return

    console.print(f"[bold {color}][ {status} ][/bold {color}] {text} - {datetime.now().time()}")

class User(UserMixin):
    def __init__(self, userDoc):
        self.id = str(userDoc["_id"])
        self.username = userDoc["username"]

def GetMongoURI() -> str:
    RawUri = os.getenv("MONGODB_URI")
    if not RawUri: raise ValueError("No MONGODB_URI found.")
    
    Parts = urllib.parse.urlparse(RawUri)
    SafePass = urllib.parse.quote_plus(Parts.password)
    SafeUri = RawUri.replace(Parts.password, SafePass, 1)
    return SafeUri

def GetMongoClient() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
        GetMongoURI(),  
        serverSelectionTimeoutMS=10000, 
    )
    return _client

def IncrementUsage():
    if not current_user.is_authenticated:
        return jsonify({"error": "Not logged in"}), 401
    
    today = date.today().isoformat()
    users = GetMongoClient()["EduDuck"]["users"]
    
    users.update_one(
        {"_id": ObjectId(current_user.id), 
         "deleted": {"$ne": True}, 
         "daily_usage.date": {"$ne": today}},  
        {"$set": {"daily_usage": {"date": today, "timesUsed": 0}}}
    )
    
    result = users.find_one_and_update(
        {"_id": ObjectId(current_user.id), "deleted": {"$ne": True}},
        {"$inc": {"daily_usage.timesUsed": 1}}, 
        return_document=ReturnDocument.AFTER
    )
    
    if not result:
        return jsonify({"error": "User not found"}), 404
    
    timesUsed = result["daily_usage"]["timesUsed"]
    return jsonify({"timesUsed": timesUsed, "remaining": max(3-timesUsed, 0)})

def GetUsage():
    if not current_user.is_authenticated:
        return jsonify({"timesUsed": 3, "remaining": 0})
    
    users = GetMongoClient()["EduDuck"]["users"]
    user = users.find_one({"_id": ObjectId(current_user.id), "deleted": {"$ne": True}})
    today = date.today().isoformat()
    
    usage = user.get("daily_usage", {"date": today, "timesUsed": 0})
    if usage["date"] != today:
        timesUsed = 0
    else:
        timesUsed = usage["timesUsed"]
    
    remaining = max(3 - timesUsed, 0)
    return jsonify({"timesUsed": timesUsed, "remaining": remaining})

def LoadUser(userID=None, googleId=None, githubId=None, discordId=None, microsoftId=None):
    query = {"deleted": {"$ne": True}}  

    if userID:
        try:
            objId = ObjectId(userID)
            query["_id"] = objId
        except Exception:
            return None
    elif googleId:
        query["googleId"] = googleId
    elif githubId:
        query["githubId"] = githubId
    elif discordId:
        query["discordId"] = discordId
    elif microsoftId:
        query["microsoftId"] = microsoftId

    if len(query) == 1:  
        return None

    userDoc = GetMongoClient()["EduDuck"]["users"].find_one(query)
    return userDoc

def LoadUserByUsername(username: str):
    pattern = re.compile(f"^{re.escape(username)}$", re.IGNORECASE)
    return GetMongoClient()["EduDuck"]["users"].find_one({
        "username": pattern,
        "deleted": {"$ne": True}
    })

def LoadUserByMail(email: str):
    pattern = re.compile(f"^{re.escape(email)}", re.IGNORECASE)
    return GetMongoClient()["EduDuck"]["users"].find_one({
        "email": pattern,
        "deleted": {"$ne": True}
    })

def LoginUser(UserClass, data=None):
    if data:
        username_or_email = data.get("username")
        password = data.get("password")
    else:
        username_or_email = request.form.get("username")
        password = request.form.get("password")
    
    if not username_or_email or not password:
        return jsonify({"error": "Missing credentials"}), 400

    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_email = re.fullmatch(email_pattern, username_or_email.strip()) is not None

    if is_email:
        userDoc = LoadUserByMail(username_or_email)
    else:
        userDoc = LoadUserByUsername(username_or_email)

    if not userDoc:
        return jsonify({"error": "Invalid username or password"}), 401

    if not userDoc.get("password"):
        return jsonify({"error": "Password login not available for this account"}), 403

    if not check_password_hash(userDoc["password"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    if not userDoc.get("verified", False) and userDoc.get("verified") != None:
        return jsonify({"error": "Email not verified. Check your inbox."}), 403

    if userDoc.get("deletedAt") is not None:
        return jsonify({"error": "Account was deleted. Recover within 30 days by reaching out to support."}) , 403

    user = UserClass(userDoc)
    login_user(user)

    return None

def RegisterUser():
    if request.method == "POST":
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        email: str = data.get("email")
        confirm = data.get("confirm")


        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not username or not password or not email or not confirm:
            return jsonify({"error": "All fields are required"}), 400

        if password != confirm:
            return jsonify({"error": "Passwords do not match"}), 400

        if not bool(re.fullmatch(pattern, email)):
            return jsonify({"error": "Invalid email address."}), 400

        existingUser = LoadUserByUsername(username)
        if existingUser:
            return jsonify({"error": "Username already taken"}), 409

        existingMail = LoadUserByMail(email.lower())
        if existingMail:
            return jsonify({"error": "Email already taken."}), 409

        hashedPassword = generate_password_hash(password)

        usersCollection = GetMongoClient()["EduDuck"]["users"]

        userDoc = {
            "username": username.lower(),
            "email": email.lower(), 
            "password": hashedPassword,
            "verified": False,
            
            "daily_usage": {
                "date": date.today().isoformat(),
                "timesUsed": 0
            },

            "verification_token": secrets.token_urlsafe(32),
            "verification_token_expires": datetime.utcnow().timestamp() + 86400  
        }

        result = usersCollection.insert_one(userDoc)

        verification_link = url_for("verify_email", token=userDoc["verification_token"], _external=True)

        msg = (
            "Verify Your Email", # subject
            email,               # target
            verification_link # body
        )

        return msg , email

    return render_template("pages/register.html")

# Define response schemas for even faster parsing (optional but recommended)
class OpenAIChoice(msgspec.Struct):
    message: dict

class OpenAIResponse(msgspec.Struct):
    choices: list[OpenAIChoice]

decoder = msgspec.json.Decoder()  # Reusable decoder

def AiReq(API_URL, headers, payload, mode="OpenAI", timeout=60, extract_text=False):
    try:
        start = time.perf_counter()
        client_timeout = httpx.Timeout(timeout, connect=10.0) if timeout != 60 else None
        
        response = _httpxclient.post(
            API_URL, 
            headers=headers, 
            json=payload,
            timeout=client_timeout
        )
        
        if response.status_code != 200:
            print(decoder.decode(response.content))
            return f'API error {response.status_code}'
        end = time.perf_counter()

        Log(f"API request to {API_URL} took {end - start:.4f} seconds", "info")

        start = time.perf_counter()
        result = decoder.decode(response.content)

        if extract_text:
            output_texts = [
                content.get("text", "")
                for item in result.get("output", [])
                for content in item.get("content", [])
                if content.get("type") == "output_text"
            ]
            data = "\n".join(output_texts).strip() or "API returned no text."
        else:
            if mode in ("OpenAI", "Hugging Face"):
                try:
                    data = result["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError) as e:
                    print(f"Error parsing {mode} response: {e}")
                    data = f"Error parsing {mode} response."
            else:
                try:
                    parts = result["candidates"][0]["content"]["parts"]
                    data = "".join(part["text"] for part in parts)
                except (KeyError, IndexError, TypeError):
                    data = "Unknown API format."

        end = time.perf_counter()
        Log(f"Parsing response took: {end - start:.4f} seconds", "info")

        return data

    except httpx.TimeoutException:
        print(f"Request timeout after {timeout}s")
        return None
    except httpx.RequestError as err:
        print(f"Network error: {str(err)}")
        return None
    except Exception as err:
        print(f"Internal Error: {str(err)}")
        return None

def cleanup():
    if _httpxclient: _httpxclient.close()

def uploadNotes():
    file = request.files.get("notesFile")
    supportedImageFormats = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'ppm', 'pbm', 'pgm', 'jp2', 'j2k']
    supportedTextFormats = ['txt', 'md', 'csv', 'json', 'log', 'py', 'js', 'html', 'css', 'xml', 'yml', 'yaml', 'ini', 'cfg', 'tex']

    if not file:
        return jsonify({"notes": "No file received."})

    ext = file.filename.split('.')[-1].lower()

    if ext in supportedTextFormats:
        return jsonify({"notes": file.read().decode("utf-8")})

    elif ext == 'pdf':
        reader_pdf = PdfReader(file)
        textChunks = [page.extract_text() or "" for page in reader_pdf.pages]
        return jsonify({"notes": "\n".join(textChunks)})

    elif ext in supportedImageFormats:
        try:
            image = Image.open(file.stream).convert('RGB')

            base_width = 1800
            wpercent = (base_width / float(image.size[0]))
            hsize = int(float(image.size[1]) * wpercent)
            image = image.resize((base_width, hsize), Image.Resampling.LANCZOS)

            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

            API_URL = "https://api.openai.com/v1/responses" 
            headers = {"Authorization": f"Bearer {os.getenv("FREE_TIER_API_KEY")}"}
            payload = {
                "model": "gpt-4.1-nano",
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_image", "image_url": f"data:image/png;base64,{img_str}"},
                            {"type": "input_text", "text": "Please extract all text from this image."}
                        ]
                    }
                ]
            }

            text = AiReq(API_URL, headers, payload, mode="OpenAI" , extract_text=True)
            return jsonify({"notes": text.strip() if text else "OCR API returned nothing."})

        except Exception as e:
            print(str(e))
            return jsonify({"notes": "OCR error."})

    else:
        return jsonify({"notes": "Unsupported file type."})

def StoreQuery(qName , query=None) -> Optional[str]:
    if not current_user.is_authenticated:
        return "forbidden" , 401

    if not query:
        query = request.get_json(silent=True).get(qName , '') or {}

    if not query:
        Log("Empty query payload", "error")
        return "empty query payload"

    QueryID = str(uuid4())

    dbNames = {
        "quiz": "quizzes",
        "plan": "study-plans",
        "flashcards": "flashcards",
        "notes": "enhanced-notes",
        "note-analysis": "note-analysis",
    }

    collection = dbNames.get(qName , 'err')

    if collection == 'err':
        Log("Unknown qName @ StoreQuery" , "error")
        return "unknown qName"

    GetMongoClient()["EduDuck"][collection].insert_one({
        "userID": current_user.id,
        "queryID": QueryID,
        "queryType": qName,
        "query": query,
        "createdAt": datetime.utcnow() 
    })

    Log("Added query to mongoDB. ID: " + QueryID , "info")

    return QueryID

def StoreDuckAIConversation(messages: list , QueryID = None):
    db = GetMongoClient()["EduDuck"]["duck-ai"]

    if not QueryID:
        QueryID = str(uuid4())

    doc = db.find_one_and_update(
        {"userID": current_user.id, "queryID": QueryID},
        {
            "$setOnInsert": {
                "userID": current_user.id,
                "queryID": QueryID,
                "queryType": "duckAI",
                "createdAt": datetime.utcnow()
            },
            "$set": {
                "lastEditedAt": datetime.utcnow()
            },
            "$push": {"queries": {"$each": messages}}
        },
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    return doc["queryID"]

def GetQueryFromDB(queryID: str, collection: str) -> Union[Dict[str, Any], str, None]:
    Entry = GetMongoClient()["EduDuck"][collection].find_one({
        "queryID": queryID,
        "userID": current_user.id
    })

    if not Entry:
        return None

    if collection == "duck-ai":
        return Entry.get("queries", [])
    else:
        return Entry.get("query", "")

def StoreTempQuery(query: Union[str , dict], collection: dict) -> str:
    queryID = str(uuid4())

    collection[queryID] = query
    Log(f"Added query to temp collection. Length: {len(collection)} , ID: {queryID}" , "info")

    return queryID

def SendEmail(toEmail, subject, body, email , html):
    response = post(
        "https://api.eu.mailgun.net/v3/mg.eduduck.app/messages",
        auth=("api", os.getenv('MAILGUN_API_KEY')),
        data={
            "from": email,  # e.g. "EduDuck Verification <no-reply@mg.eduduck.app>"
            "to": toEmail,
            "subject": subject,
            "text": body,
            "html": html
        }
    )

    if not response.ok:
        raise RuntimeError(f"Mailgun API error: {response.status_code}, {response.text}")

    return response

def VerifyEmail(token):
    usersCollection = GetMongoClient()["EduDuck"]["users"]
    
    user = usersCollection.find_one({
        "verification_token": token,
        "verification_token_expires": {"$gt": datetime.utcnow().timestamp()}
    })

    if not user:
        expired_user = usersCollection.find_one({"verification_token": token})
        
        if expired_user:
            usersCollection.delete_one({"_id": expired_user["_id"]})
            return render_template("pages/emailVerified.html", success=False)
    
        return render_template("pages/emailVerified.html", success=False)

    usersCollection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"verified": True}, 
            "$unset": {"verification_token": "", "verification_token_expires": ""}
        }
    )

    login_user(User(user))

    return render_template("pages/emailVerified.html", success=True, email=user["email"])

def UserProfile():
    db = GetMongoClient()["EduDuck"]
    userid = current_user.id
    streakdata = GetStudyStreakData(userid)
    filter = {"userID": userid, "deleted": {"$ne": True}}
    
    quizzes = list(db["quizzes"].find(filter).sort("createdAt", -1))
    plans = list(db["study-plans"].find(filter).sort("createdAt", -1))
    flashcards = list(db["flashcards"].find(filter).sort("createdAt", -1))
    notes = list(db["enhanced-notes"].find(filter).sort("createdAt", -1))
    duckai = list(db["duck-ai"].find(filter).sort("lastEditedAt", -1))
    noteanalyses = list(db["note-analysis"].find(filter).sort("createdAt", -1))  
    
    return render_template(
        "pages/profile.html",
        quizzes=quizzes,
        plans=plans,
        flashcards=flashcards,
        notes=notes,
        duckai=duckai,
        streakdata=streakdata,
        noteanalyses=noteanalyses  
    )


def GetUserPFP():
    try:
        user_doc = GetMongoClient()["EduDuck"]["users"].find_one({"_id": ObjectId(current_user.id)})
        if not user_doc:
            return jsonify({"error": "User not found"}), 404

        key = user_doc.get("profilePicture")
        if key:
            url = f"https://avatars.eduduck.app/{key}"
        else:
            url = url_for("static", filename="img/default-profile.png") 

        return jsonify({"url": url})
    except Exception as e:
        Log(f"Failed to get user profile picture -> {str(e)}" , "error")
        return jsonify({"error": str(e)}), 500

def CheckPasswordSetup(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            user = GetMongoClient()["EduDuck"]["users"].find_one({
                "_id": ObjectId(current_user.id),
                "deleted": {"$ne": True}
            })
            if user and user.get("needs_password_setup") and not request.args.get("IGNORE"):
                return redirect(f"{url_for('setup_password')}?skip={request.path}")
        return func(*args, **kwargs)
    return wrapper

def GetStudyStreakData(user_id: str, days: int = 365):
    try:
        db = GetMongoClient()["EduDuck"]
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Map of collections and their query type identifiers
        collection_mapping = {
            "duck-ai": "duckAI",
            "enhanced-notes": "notes",
            "quizzes": "quiz",
            "flashcards": "flashcards",
            "study-plans": "studyPlan",
            "note-analysis": "note-analysis" 
        }

        
        daily_counts = defaultdict(int)
        
        # Aggregate from all collections
        for collection_name, query_type in collection_mapping.items():
            try:
                pipeline = [
                    {
                        "$match": {
                            "userID": user_id,
                            "createdAt": {
                                "$gte": start_date,
                                "$lte": end_date
                            },
                            "deleted": {"$ne": True}
                        }
                    },
                    {
                        "$group": {
                            "_id": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": "$createdAt"
                                }
                            },
                            "count": {"$sum": 1}
                        }
                    }
                ]
                
                results = db[collection_name].aggregate(pipeline)
                for doc in results:
                    daily_counts[doc["_id"]] += doc["count"]
                    
            except Exception as e:
                Log(f"Error aggregating {collection_name}: {str(e)}", "warning")
                continue
        
        # Also count lastEditedAt for duck-ai conversations (chat activity)
        try:
            pipeline_edits = [
                {
                    "$match": {
                        "userID": user_id,
                        "lastEditedAt": {
                            "$gte": start_date,
                            "$lte": end_date,
                            "$ne": "$createdAt"
                        },
                        "deleted": {"$ne": True}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$lastEditedAt"
                            }
                        },
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            results = db["duck-ai"].aggregate(pipeline_edits)
            for doc in results:
                daily_counts[doc["_id"]] += doc["count"]
                
        except Exception as e:
            Log(f"Error aggregating duck-ai edits: {str(e)}", "warning")
        
        # Build complete date map
        date_map = {}
        current = start_date.date()
        while current <= end_date.date():
            date_str = current.isoformat()
            date_map[date_str] = {
                "date": date_str,
                "count": daily_counts.get(date_str, 0),
                "weekday": current.weekday()
            }
            current += timedelta(days=1)
        
        # Calculate streaks
        sorted_dates = sorted(date_map.keys())
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        for date_str in sorted_dates:
            if date_map[date_str]["count"] > 0:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
        
        # Calculate current streak
        today = date.today()
        temp_streak = 0
        check_date = today
        
        while check_date >= start_date.date():
            date_str = check_date.isoformat()
            if date_map.get(date_str, {}).get("count", 0) > 0:
                temp_streak += 1
                check_date -= timedelta(days=1)
            else:
                if temp_streak == 0 and check_date == today - timedelta(days=1):
                    check_date -= timedelta(days=1)
                    continue
                break
        
        current_streak = temp_streak
        
        # Calculate total activities
        total_activities = sum(daily_counts.values())
        
        return {
            "data": list(date_map.values()),
            "currentStreak": current_streak,
            "longestStreak": longest_streak,
            "totalDays": sum(1 for d in date_map.values() if d["count"] > 0),
            "totalActivities": total_activities  # Add this
        }
        
    except Exception as e:
        Log(f"Failed to get study streak data: {str(e)}", "error")
        return {
            "data": [],
            "currentStreak": 0,
            "longestStreak": 0,
            "totalDays": 0,
            "totalActivities": 0
        }


def CalculateIntensity(count: int, max_count: int) -> float:
    if count == 0:
        return 0.0
    if max_count == 0:
        return 0.0
    
    return math.sqrt(count / max_count)

_user_history = {}

def extract_topic(query_data, qtype):
    if not query_data:
        return 'General'
    
    topic = 'General'
    
    if isinstance(query_data, dict):
        # Strip generic prefixes first
        raw_topic = query_data.get('topic', '')
        if isinstance(raw_topic, str):
            raw_topic = raw_topic.strip()
        else:
            raw_topic = ''
        prefixes = ['Enhanced Study Notes on ', 'Quiz on ', 'Flashcards for ', 'Study Plan: ']
        for prefix in prefixes:
            if raw_topic.startswith(prefix):
                raw_topic = raw_topic[len(prefix):].strip()
        
        if raw_topic and len(raw_topic) > 3:
            return raw_topic[:55]
        
        # Quiz: smart question parsing
        first_q = next(iter(query_data.values()), {})
        if isinstance(first_q, dict) and 'question' in first_q:
            question = (first_q.get('question') or '').strip()
            question_lower = question.lower()
            common_words = {
                'how', 'what', 'why', 'when', 'where', 'which', 'the', 'a', 'an', 
                'is', 'are', 'does', 'do', 'did', 'can', 'will', 'would'
            }
            
            words = re.findall(r'\b[a-zA-Z]{4,}\b', question_lower)
            words = [w.capitalize() for w in words if w not in common_words and len(w) > 2]
            
            if words:
                topic_words = []
                preview = ''
                for word in words:
                    test = f"{preview} {word}".strip()
                    if len(test) <= 55:
                        topic_words.append(word)
                        preview = test
                    else:
                        break
                topic = ' '.join(topic_words)
            else:
                words = question.split()[:8]
                topic = ' '.join(words)[:55]
            return topic
        
        # Content/notes – add isinstance(first_q, dict) guard
        if isinstance(first_q, dict) and 'content' in first_q:
            content = (first_q.get('content') or '').strip()
            sentences = re.split(r'[.!?]+', content)
            topic = (sentences[0] or '').strip() if sentences else ''
            if len(topic) > 55:
                words = topic.split()
                topic = ' '.join(words[:10])
            return topic or 'General'
        
        # Generic dict first value
        first_key = next(iter(query_data), None)
        if first_key is not None and isinstance(query_data[first_key], str):
            return query_data[first_key][:55].rsplit(' ', 1)[0]
    
    elif isinstance(query_data, str):
        lines = [line.strip('# \n\t*-') for line in query_data.split('\n') if line.strip()]
        if lines:
            topic = lines[0]
            if len(topic) > 55:
                words = topic.split()
                topic = ' '.join(words[:10])
            return topic
    
    return 'General'

def GetNextAction(_user_history=None):
    if _user_history is None:
        _user_history = {}
    
    if not current_user.is_authenticated:
        raise ValueError("Unauthorized")
    
    today_str = date.today().isoformat()
    user_id = current_user.id
    
    # Avoid repeats from history
    last_rec = _user_history.get(user_id)
    avoid_action = last_rec['action_type'] if last_rec else None
    avoid_topic = last_rec['topic'] if last_rec else None
    
    # Collections mapping
    collections = {
        "quizzes": "quiz",
        "enhanced-notes": "notes", 
        "flashcards": "flashcards",
        "study-plans": "studyPlan",
        "duck-ai": "chat",
        "note-analysis": "analysis"
    }
    
    all_queries = []
    db = GetMongoClient()['EduDuck']
    
    for coll_name, qtype in collections.items():
        query_filter = {
            'userID': user_id,
            '$or': [
                {'deletedAt': {'$exists': False}},
                {'deletedAt': None}
            ]
        }
        cursor = db[coll_name].find(query_filter).sort([('createdAt', -1)]).limit(50)
        
        for doc in cursor:
            # Robust date parsing with fallback
            created_at = None
            created_at_raw = doc.get('createdAt') or doc.get('lastEditedAt')
            
            try:
                if isinstance(created_at_raw, dict) and '$date' in created_at_raw:
                    created_at = datetime.fromisoformat(created_at_raw['$date'].replace('Z', '+00:00'))
                elif isinstance(created_at_raw, str):
                    created_at = datetime.fromisoformat(created_at_raw.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                created_at = datetime.utcnow()
            
            q_date = created_at.date().isoformat()
            topic = extract_topic(doc.get('query'), qtype) or 'General'
            
            # Chat topic extraction
            if qtype == 'chat' and 'queries' in doc:
                for msg in doc['queries']:
                    if msg.get('role') == 'user' and msg.get('content'):
                        content = msg['content'].strip()
                        if len(content) > 10:
                            words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
                            words = [w.capitalize() for w in words[:3] 
                                   if w not in {'How', 'What', 'Why', 'When'}]
                            if words:
                                topic = ' '.join(words)
                                break
            
            all_queries.append({'date': q_date, 'type': qtype, 'topic': topic})
    
    today_queries = [q for q in all_queries if q['date'] == today_str]
    
    def get_recommendation(all_queries, today_queries, avoid_action, avoid_topic):
        # Rule 1: No activity today - Balanced starters
        if len(today_queries) == 0:
            starters = [
                ("flashcards", "Quick Review", "5 flashcards to kickstart studying.", 3),
                ("notes", "Today's Focus", "Notes for today's main topic.", 5),
                ("quiz", "Warmup Quiz", "Short 5-question warmup.", 4),
                ("chat", "Ask DuckAI", "Chat with DuckAI about your study plan.", 2),
                ("study plan", "Daily Plan", "Create a study plan for today.", 4),
            ]
            filtered = [(a,t,r,m) for a,t,r,m in starters 
                       if a != avoid_action and t != avoid_topic]
            if not filtered: 
                filtered = starters
            act, top, reason, time = random.choice(filtered)
            return {"action_type": act, "topic": top, "reason": reason, "estimated_time_minutes": time}
        
        # Track coverage per topic
        topic_data = defaultdict(lambda: {
            "notes": False, "quiz": False, "flashcards": False,
            "studyplan": False, "chat": False, "analysis": False
        })
        
        for q in all_queries:
            norm_topic = q['topic'] if len(q['topic']) > 3 else 'General'
            topic_data[norm_topic][q['type']] = True
        
        # Rule 2: Notes done - Suggest quiz
        for topic, data in topic_data.items():
            if topic != avoid_topic and data['notes'] and not data['quiz']:
                return {
                    "action_type": "quiz", "topic": topic,
                    "reason": f"Quiz '{topic}' from your notes.", "estimated_time_minutes": 5
                }
        
        # Rule 3: Quiz done - Flashcards
        for topic, data in topic_data.items():
            if topic != avoid_topic and data['quiz'] and not data['flashcards']:
                return {
                    "action_type": "flashcards", "topic": topic,
                    "reason": f"Flashcards for '{topic}'.", "estimated_time_minutes": 3
                }
        
        # Rule 4: Quiz - Chat discussion
        for topic, data in topic_data.items():
            if topic != avoid_topic and data['quiz'] and not data['chat']:
                return {
                    "action_type": "chat", "topic": topic,
                    "reason": f"Chat about '{topic}' quiz.", "estimated_time_minutes": 2
                }
        
        # Rule 5: Content exists - Study plan
        for topic, data in topic_data.items():
            if (topic != avoid_topic and 
                (data['notes'] or data['quiz'] or data['flashcards']) and 
                not data['study plan']):
                return {
                    "action_type": "study plan", "topic": topic,
                    "reason": f"Study plan for '{topic}'.", "estimated_time_minutes": 4
                }
        
        # Rule 6: Review old topics (>2 days)
        old_queries = [q for q in all_queries 
                      if (date.today() - date.fromisoformat(q['date'])).days > 2]
        recent_topics = Counter(q['topic'] for q in old_queries[:10] if len(q['topic']) > 3)
        candidates = [(t, c) for t, c in recent_topics.items() if t != avoid_topic]
        if candidates:
            old_topic = candidates[0][0]
            types = random.choice(['quiz', 'flashcards', 'chat'])
            reasons = {
                'quiz': f"Review '{old_topic}' with quiz.",
                'flashcards': f"Flashcard review for '{old_topic}'.",
                'chat': f"Discuss '{old_topic}' with DuckAI."
            }
            return {
                "action_type": types, "topic": old_topic,
                "reason": reasons[types],
                "estimated_time_minutes": 4 if types != 'chat' else 3
            }
        
        # Rule 7: Fallback to recent/general
        recent_topic = 'General'
        if all_queries:
            counts = Counter(q['topic'] for q in all_queries[:20] if len(q['topic']) > 3)
            if counts:
                recent_topic = counts.most_common(1)[0][0]
        
        fallbacks = [
            ("chat", f"DuckAI {recent_topic}", f"Ask DuckAI about {recent_topic}.", 2),
            ("study plan", f"Plan {recent_topic}", f"Study plan for {recent_topic}.", 4),
            ("flashcards", recent_topic, f"More {recent_topic} flashcards.", 3),
            ("notes", f"Deep Dive {recent_topic}", f"Deep notes on {recent_topic}.", 5),
            ("analysis", f"Analyze {recent_topic}", f"Deep analysis of {recent_topic} notes.", 4),
        ]
        filtered_fallbacks = [(a,t,r,m) for a,t,r,m in fallbacks if a != avoid_action]
        if not filtered_fallbacks:
            filtered_fallbacks = fallbacks
        act, top, reason, time = random.choice(filtered_fallbacks)
        
        return {
            "action_type": act, "topic": top,
            "reason": reason, "estimated_time_minutes": time
        }
    
    result = get_recommendation(all_queries, today_queries, avoid_action, avoid_topic)
    _user_history[user_id] = result
    return result
