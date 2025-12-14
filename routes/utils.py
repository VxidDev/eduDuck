from requests import post
from pypdf import PdfReader
from flask import request , jsonify
from pytesseract import image_to_string
from PIL import Image, ImageFilter, ImageEnhance

from uuid import uuid4

def AiReq(API_URL, headers, payload, timeout=15):
    try:
        response = post(API_URL, headers=headers, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            result = response.json()
            data = result["choices"][0]['message']['content'] if result else "API error: Failed to extract JSON."
            return data
        else:
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
    notes = data.get('notes', '')
    noteID = str(uuid4())
    notes[noteID] = notes
    print("STORED", noteID, "len:", len(notes))
    return jsonify({'id': noteID})

def storeQuiz(quizzes: dict):
    data = request.get_json()
    quiz = data.get('quiz', '')
    quizID = str(uuid4())
    quizzes[quizID] = quiz
    print("STORED", quizID, "len:", len(quiz))
    return jsonify({'id': quizID})