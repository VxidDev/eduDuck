from requests import post
from pypdf import PdfReader
from flask import request , jsonify , render_template , url_for
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

    result = users.find_one_and_update(
        {"_id": ObjectId(current_user.id)},
        [
            {
                "$set": {
                    "daily_usage": {
                        "date": today,
                        "timesUsed": {
                            "$cond": [
                                {"$eq": ["$daily_usage.date", today]},
                                {"$add": ["$daily_usage.timesUsed", 1]},
                                1
                            ]
                        }
                    }
                }
            }
        ],
        return_document=True
    )

    timesUsed = result["daily_usage"]["timesUsed"]
    return jsonify({"timesUsed": timesUsed})

def GetUsage():
    if not current_user.is_authenticated:
        return jsonify({"timesUsed": 0, "remaining": 3})

    users = GetMongoClient()["EduDuck"]["users"]
    user = users.find_one({"_id": ObjectId(current_user.id)})

    today = date.today().isoformat()
    usage = user.get("daily_usage", {"date": today, "timesUsed": 0})

    if usage["date"] != today:
        timesUsed = 0
    else:
        timesUsed = usage["timesUsed"]

    remaining = max(3 - timesUsed, 0)
    return jsonify({"timesUsed": timesUsed, "remaining": remaining})

def LoadUser(userID=None, googleId=None):
    query = {}

    if userID:
        try:
            objId = ObjectId(userID)
            query["_id"] = objId
        except Exception:
            return None

    elif googleId:
        query["googleId"] = googleId

    if not query:
        return None

    userDoc = GetMongoClient()["EduDuck"]["users"].find_one(query)
    return userDoc

def LoadUserByUsername(username: str):
    return GetMongoClient()["EduDuck"]["users"].find_one({
        "username": {"$regex": f"^{username}$", "$options": "i"}
    })

def LoadUserByMail(mail: str):
    return GetMongoClient()["EduDuck"]["users"].find_one({
        "email": {"$regex": f"^{mail}$", "$options": "i"}
    })


def LoginUser(UserClass, data=None):
    if data:
        username = data.get("username")
        password = data.get("password")
    else:
        username = request.form.get("username")
        password = request.form.get("password")

    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    userDoc = LoadUserByUsername(username)
    if not userDoc:
        return jsonify({"error": "Invalid username or password"}), 401

    if not check_password_hash(userDoc["password"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    if not userDoc.get("verified", False):
        return jsonify({"error": "Email not verified. Check your inbox."}), 403

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

        if not username or not password or not email or not confirm:
            return jsonify({"error": "All fields are required"}), 400

        if password != confirm:
            return jsonify({"error": "Passwords do not match"}), 400

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

            "verification_token": secrets.token_urlsafe(32)
        }

        result = usersCollection.insert_one(userDoc)

        verification_link = url_for("verifyEmail", token=userDoc["verification_token"], _external=True)

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

    dbNames = {'quiz': 'quizzes' , 
               'plan': 'study-plans' , 
               'flashcards': 'flashcards' ,
               'notes': 'enhanced-notes'}

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

def sendVerificationEmail(app , toEmail, subject, body, email):
    with app.app_context():
        response = post(
            "https://api.eu.mailgun.net/v3/mg.eduduck.app/messages",
            auth=("api", os.getenv('MAILGUN_API_KEY')),
            data={
                "from": email,  # e.g. "EduDuck Verification <no-reply@mg.eduduck.app>"
                "to": toEmail,
                "subject": subject,
                "text": body,
                "html": render_template("pages/email.html" , VERIFY_URL=body)
            }
        )

        if not response.ok:
            raise RuntimeError(f"Mailgun API error: {response.status_code}, {response.text}")

    return response

def VerifyEmail(token):
    usersCollection = GetMongoClient()["EduDuck"]["users"]
    user = usersCollection.find_one({"verification_token": token})

    if not user:
        return "Invalid or expired token", 400

    usersCollection.update_one(
        {"_id": user["_id"]},
        {"$set": {"verified": True}, "$unset": {"verification_token": ""}}
    )

    login_user(User(user))

    return render_template("pages/emailVerified.html" , success=True , email=user["email"])

def UserProfile():
    db = GetMongoClient()["EduDuck"]

    quizzes = list(db["quizzes"].find({"userID": current_user.id}).sort("createdAt", -1))
    plans = list(db["study-plans"].find({"userID": current_user.id}).sort("createdAt", -1))
    flashcards = list(db["flashcards"].find({"userID": current_user.id}).sort("createdAt", -1))
    notes = list(db["enhanced-notes"].find({"userID": current_user.id}).sort("createdAt", -1))
    duckai = list(db["duck-ai"].find({"userID": current_user.id}).sort("lastEditedAt", -1))

    return render_template(
        "pages/profile.html",
        quizzes=quizzes,
        plans=plans,
        flashcards=flashcards,
        notes=notes,
        duckai=duckai
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