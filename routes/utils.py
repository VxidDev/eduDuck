from requests import post
from pypdf import PdfReader
from flask import request , jsonify , render_template , url_for
from pytesseract import image_to_string
from PIL import Image, ImageFilter, ImageEnhance
from pymongo import MongoClient
import os
import urllib.parse
from datetime import date
from pymongo.server_api import ServerApi
import certifi
from bson.objectid import ObjectId 
from flask_login import login_user , UserMixin , current_user
from werkzeug.security import generate_password_hash , check_password_hash

from uuid import uuid4

_client = None

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

def LoadUser(userID):
    try:
        obj_id = ObjectId(userID)
    except Exception:
        return None

    userDoc = GetMongoClient()["EduDuck"]["users"].find_one({"_id": obj_id})
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
            
            "daily_usage": {
                "date": date.today().isoformat(),
                "timesUsed": 0
            }
        }

        result = usersCollection.insert_one(userDoc)

        user = User({"_id": result.inserted_id, "username": username})
        login_user(user)

        return jsonify({"success": True, "redirect": url_for("root")})

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

    if ext == 'txt':
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