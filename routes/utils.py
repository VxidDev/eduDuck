from requests import post
from pypdf import PdfReader
from flask import request , jsonify , render_template , url_for , render_template_string
from pytesseract import image_to_string
from PIL import Image, ImageFilter, ImageEnhance
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

from uuid import uuid4

console = Console()
_client = None

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

    # Update usage
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

def AiReq(API_URL, headers, payload, mode, timeout=60):
    try:
        response = post(API_URL, headers=headers, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            result = response.json()
            if not result:
                data = "API error: Failed to extract JSON."

            elif mode == "OpenAI":
                data = result["choices"][0]["message"]["content"]

            elif mode == "Hugging Face":
                data = result["choices"][0]["message"]["content"]

            else: 
                data = "".join(
                    part["text"]
                    for part in result["candidates"][0]["content"]["parts"]
                )
            return data
        else:
            print(response.json())
            return f'API error {response.status_code}'
            
    except Exception as err:
        print(f"Internal Error: {str(err)}")
        return None

def uploadNotes():
    file = request.files.get("notesFile")
    supportedImageFormats = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'ppm', 'pbm', 'pgm', 'jp2', 'j2k']

    if not file:
        return jsonify({"notes": "No file received."})

    ext: str = file.filename.split('.')[-1]

    if ext in ['txt', 'md', 'csv', 'json', 'log', 'py', 'js', 'html', 'css', 'xml', 'yml', 'yaml', 'ini', 'cfg', 'tex']:
        return jsonify({"notes": file.read().decode("utf-8")})
    elif ext == 'pdf':
        reader = PdfReader(file)
        textChunks = []
        for page in reader.pages:
            textChunks.append(page.extract_text() or "")   
        
        return jsonify({"notes": "\n".join(textChunks)})
    elif ext in supportedImageFormats:
        try:
            image = Image.open(file.stream)
            file.stream.seek(0)
        
            image = image.convert('L')
            image = image.filter(ImageFilter.MedianFilter(size=3))
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
        
            text = image_to_string(image, config='--psm 6')

            return jsonify({"notes": text.strip()})
        except Exception as e:
            print(str(e))
            return jsonify({"notes": "OCR error."})
    else:
        return jsonify({"notes": "Unsupported file type."})

def StoreQuery(qName , query=None) -> Optional[str]:
    if not current_user.is_authenticated:
        return "forbidden"

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

def storeNotes(notes: dict):
    data = request.get_json()
    Notes = data.get('notes', '')
    noteID = str(uuid4())
    notes[noteID] = Notes
    print("STORED", noteID, "len:", len(Notes))
    return jsonify({'id': noteID})

def storeQuiz(quizzes: dict):
    data = request.get_json()
    quiz = data.get('quiz', '')
    quizID = str(uuid4())
    quizzes[quizID] = quiz
    print("STORED", quizID, "len:", len(quiz))
    return jsonify({'id': quizID})

def storeFlashcards(flashcards: dict):
    data = request.get_json()
    Flashcards = data.get('flashcards' , '')
    flashcardID = str(uuid4())
    flashcards[flashcardID] = Flashcards
    print("STORED", flashcardID, "len:", len(Flashcards))
    return jsonify({'id': flashcardID})

def storeStudyPlan(studyPlans: dict):
    data = request.get_json()
    plan = data.get('plan' , '')
    planID = str(uuid4())
    studyPlans[planID] = plan
    print("STORED", planID, "len:", len(plan))
    return jsonify({'id': planID})

def StoreQuizResult(quizResults , quizResult) -> str:
    resultID = str(uuid4())
    quizResults[resultID] = quizResult
    print("STORED", resultID, "len:", len(quizResult))
    return jsonify({'id': resultID})

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
