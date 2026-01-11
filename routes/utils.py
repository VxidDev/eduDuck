from requests import post
from pypdf import PdfReader
from flask import request , jsonify
from pytesseract import image_to_string
from PIL import Image, ImageFilter, ImageEnhance
from pymongo import MongoClient
import os
import urllib.parse
from datetime import date
from pymongo.server_api import ServerApi
import certifi 

from uuid import uuid4

_client = None

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
        server_api=ServerApi('1'), 
        tls=True,
        tlsCAFile=certifi.where(),  
        serverSelectionTimeoutMS=10000, 
        connectTimeoutMS=10000,
        socketTimeoutMS=20000,
        heartbeatFrequencyMS=10000,
        maxPoolSize=10,
        retryWrites=True
    )
    return _client

def IncrementUsage():
    ip = request.remote_addr
    
    usage = GetMongoClient()["EduDuck"]["daily_usage"].find_one_and_update(
        {"ip": ip, "date": today},  
        {"$inc": {"timesUsed": 1}},                    
        upsert=True,                                   
        return_document=True                           
    )
    return jsonify({"timesUsed": usage["timesUsed"], "ip": ip})

def GetUsage():
    today = date.today().isoformat()
    ip = request.remote_addr

    usage = GetMongoClient()["EduDuck"]["daily_usage"].find_one({"ip": ip , "date": today})

    return jsonify({"timesUsed": usage["timesUsed"] if usage else 0})

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
