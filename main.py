import flask , requests , pypdf
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import os
from uuid import uuid4
import re

notes_store = {}
quiz_store = {}

app = flask.Flask(__name__)

prompts = {
    "quiz": """Quiz generator ONLY. NO OTHER TEXT.

            MANDATORY REQUIREMENTS (confirm each before output):
            1. Output EXACTLY 10 questions in ONE continuous line
            2. ALL TEXT SHOULD BE IN {LANGUAGE}. (Questions, answers, EVERYTHING!)
            3. NO "Question", "Q", headers, markdown, bullets, newlines
            4. Format: 1 question? a opt b opt c opt d opt|CORRECT:x| NO spaces before |
            5. Replace "wrong"/"correct" with REAL notes content
            6. Vary correct answers across a/b/c/d
            7. Short, clear questions from {NOTES} ONLY

            Follow this EXACT sequence:
            1. Read notes
            2. Generate 10 questions 
            3. Output ONLY in specified format

            EXAMPLE (copy this structure exactly but use notes):
            1 What color grass? a) blue b) red c) green d) yellow|CORRECT:c|2 What 2+2? a) 3 b) 4 c) 5 d) 6|CORRECT:b|3 Sky color? a) green b) blue c) red d) yellow|CORRECT:b|4 Sun rises? a) west b) south c) north d) east|CORRECT:a|5 Moon phase? a) full b) new c) half d) quarter|CORRECT:d|6 Earth shape? a) flat b) round c) square d) triangle|CORRECT:b|7 Water state? a) solid b) liquid c) gas d) plasma|CORRECT:c|8 Fire needs? a) water b) oxygen c) earth d) air|CORRECT:b|9 Light speed? a) slow b) fast c) medium d) stop|CORRECT:b|10 Gravity pulls? a) up b) down c) side d) none|CORRECT:b|

            NOTES: {NOTES}""",
    "enhanceNotes": """Enhance these notes for optimal learning. Output ONLY the enhanced content.

            NOTES:
            {NOTES}

            REQUIREMENTS:
            1. Use clean Markdown formatting:
            - Headings with #, ##, ### etc.
            - Bullet lists with - or *.
            - Numbered lists with 1., 2., 3.
            - Tables using standard Markdown table syntax.
            2. ALL TEXT SHOULD BE IN {LANGUAGE}. (EVERYTHING!)
            3. Do NOT wrap the entire output in quotes or code blocks.
            4. Do NOT use any HTML tags (no <p>, <strong>, <br>, etc.).
            5. Organize into clear sections with headings.
            6. Add explanations for complex concepts in simple terms.
            7. Include examples where concepts would benefit.
            8. Highlight key terms and definitions (with **bold**).
            9. Add connections between related ideas.
            10. Suggest mnemonics or memory aids.
            11. Identify gaps and recommend what to learn next.

            Use active voice. Prioritize clarity. No introductions, conclusions, or meta‑comments.
            """
}

def AiReq(API_URL, headers, payload, timeout=15):
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            result = response.json()
            data = result["choices"][0]['message']['content'] if result else "Content Generated!"
            return data
        else:
            return f'API error {response.status_code}'
            
    except Exception as e:
        print("WRONG API KEY.")

    return None

@app.route('/quiz-generator/gen-quiz' , methods=['POST'])
def QuizGen():
    data: dict = flask.request.get_json()
    NOTES = data["notes"]
    LANGUAGE = data["language"]

    API_KEY = data["apiKey"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    PROMPT = prompts['quiz']

    if PROMPT == None:
        return flask.jsonify({'quiz': 'Internal Error: PROMPT NOT FOUND'})
    else:
        PROMPT = PROMPT.format(NOTES=NOTES , LANGUAGE=LANGUAGE)

    payload = {
        "messages": [{
            "role": "user",
            "content": PROMPT
        }],
        "model": data.get("model" , "openai/gpt-oss-20b")
    }

    if payload["model"] is None:
        payload["model"] = "openai/gpt-oss-20b"

    print(f"Model: {payload["model"]}")

    output = AiReq(API_URL , headers , payload)

    if (output is None):
        return flask.jsonify({"quiz": "Internal Error."})

    quiz = ParseQuiz(output)

    return flask.jsonify({'quiz': quiz})

@app.route('/store-notes', methods=['POST'])
def store_notes():
    data = flask.request.get_json()
    notes = data.get('notes', '')
    note_id = str(uuid4())
    notes_store[note_id] = notes
    print("STORED", note_id, "len:", len(notes))
    return flask.jsonify({'id': note_id})

@app.route('/quiz-generator/store-quiz', methods=['POST'])
def store_quiz():
    data = flask.request.get_json()
    quiz = data.get('quiz', '')
    quiz_id = str(uuid4())
    quiz_store[quiz_id] = quiz
    print("STORED", quiz_id, "len:", len(quiz))
    return flask.jsonify({'id': quiz_id})

@app.route('/note-enhancer/result')
def EnhancedNotes():
    note_id = flask.request.args.get('notes')
    notes = notes_store.get(note_id, '') if note_id else ''
    print("READ", note_id, "found:", bool(notes))
    return flask.render_template('enhancedNotes.html', notes=notes)

@app.route('/note-enhancer')
def NoteEnhance():
    return flask.render_template('noteEnhancer.html')

@app.route('/note-enhancer/enhance' , methods=['POST'])
def NoteEnhancer():
    data: dict = flask.request.get_json()
    NOTES = data["notes"]
    LANGUAGE = data["language"]

    API_KEY = data["apiKey"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    PROMPT = prompts['enhanceNotes']

    if PROMPT == None:
        return flask.jsonify({'notes': 'Internal Error: PROMPT NOT FOUND'})
    else:
        PROMPT = PROMPT.format(NOTES=NOTES , LANGUAGE=LANGUAGE)

    payload = {
        "messages": [{
            "role": "user",
            "content": PROMPT
        }],
        "model": data.get("model" , "openai/gpt-oss-20b")
    }

    if payload["model"] is None:
        payload["model"] = "openai/gpt-oss-20b"

    print(f"Model: {payload["model"]}")

    notes = AiReq(API_URL , headers , payload)

    if (notes is None):
        return flask.jsonify({"notes": "Internal Error."})

    return flask.jsonify({'notes': notes})

@app.route('/result', methods=['POST'])
def submit_result():
    data = flask.request.get_json()
    quiz = data.get('quiz', {})
    user_answers = data.get('answers', {})
    
    if not quiz:
        return flask.jsonify({'error': 'No quiz data'}), 400
    
    score = sum(1 for num in quiz if (user_answers.get(num) or '').lower() == (quiz[num].get('correct') or '').lower())
    total = len(quiz)
    percentage = round((score / total) * 100, 1) if total > 0 else 0
    
    result_data = {
        'score': score,
        'total': total,
        'percentage': percentage,
        'results': {num: {
            'correct': q.get('correct'), 
            'user': user_answers.get(num), 
            'right': (user_answers.get(num) or '').lower() == (q.get('correct') or '').lower()
        } for num, q in quiz.items()}
    }
    
    return flask.jsonify(result_data)

@app.route('/flashcards')
def flashCards():
    return "Unsupported."

@app.route('/quiz-generator/quiz/result')
def result_page():
    return flask.render_template('QuizResult.html')

@app.route("/" , methods=['GET'])
def root():
    return flask.render_template("index.html")

@app.route("/keyAccess")
def keyAccess():
    return flask.render_template("keyAccess.html")

@app.route("/quiz-generator/quiz")
def quiz():
    quiz_id = flask.request.args.get('quiz')
    quiz = quiz_store.get(quiz_id, '') if quiz_id else ''
    print("READ", quiz_id, "found:", bool(quiz))
    return flask.render_template("Quiz.html" , quiz=quiz)

@app.route("/upload-notes" , methods=['POST'])
def uploadNotes():
    file = flask.request.files.get("notesFile")
    supportedImageFormats = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif', 
    'webp', 'ppm', 'pbm', 'pgm', 'jp2', 'j2k']

    if not file:
        return flask.jsonify({"notes": "no file."})

    ext: str = file.filename.split('.')[-1]
    if ext == 'txt':
        return flask.jsonify({"notes": file.read().decode("utf-8")})
    elif ext == 'pdf':
        reader = pypdf.PdfReader(file)
        textChunks = []
        for page in reader.pages:
            textChunks.append(page.extract_text() or "")   
        
        return flask.jsonify({"notes": "\n".join(textChunks)})
    elif ext in supportedImageFormats:
        try:
            image = Image.open(file.stream)
            file.stream.seek(0)
        
            image = image.convert('L')
            image = image.filter(ImageFilter.MedianFilter(size=3))
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
        
            text = pytesseract.image_to_string(image, config='--psm 6')

            return flask.jsonify({"notes": text.strip()})
        except Exception as e:
            print(str(e))
            return flask.jsonify({"notes": "OCR error."})
    else:
        return flask.jsonify({"notes": "Unsupported file type."})

def ParseQuiz(quiz: str):
    questions = {}
    
    text = re.sub(r'[\u2013\u2014\u2015\u2011‑–—]', '-', quiz)
    text = re.sub(r'\s+', ' ', text).strip()
    
    pattern = r'(\d+)\s+([^|]+?a\)[^|]*?b\)[^|]*?c\)[^|]*?d\)[^|]*?)\|?CORRECT:([abcd])'
    matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
    
    for match in matches:
        q_num, full_text, correct = match.groups()
        correct = correct.lower()
        
        a_pos = re.search(r'a\)', full_text)
        if not a_pos:
            continue
        question = full_text[:a_pos.start()].strip(' ?.,:;-?!0123456789')
        options_text = full_text[a_pos.start():].strip()
        
        answers = {}
        opt_patterns = [
            (r'a\)\s*([^b][^.?!,]*?)(?=\s*b\)|$)', 'a'),
            (r'b\)\s*([^c][^.?!,]*?)(?=\s*c\)|$)', 'b'),
            (r'c\)\s*([^d][^.?!,]*?)(?=\s*d\)|$)', 'c'),
            (r'd\)\s*([^.!?]+)', 'd')
        ]
        
        for pat, key in opt_patterns:
            m = re.search(pat, options_text, re.I)
            if m:
                answers[key] = m.group(1).strip()
        
        if len(answers) == 4:
            questions[q_num] = {
                'question': question,
                'answers': answers,
                'correct': correct
            }
    
    return questions

@app.route("/generate" , methods=['POST'])
def generate():
    data: dict = flask.request.get_json()
    supportedModes = ["quiz" , "enhanceNotes"]
    NOTES = data["notes"]
    MODE = data["mode"]
    LANGUAGE = data["language"]

    API_KEY = data["apiKey"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    if MODE not in supportedModes:
        return flask.jsonify({"notes": "Unsupported Mode.",
        "quiz": "Unsupported Mode.",
        "studyPlan": "Unsupported Mode.",
        "flashCards": "Unsupported Mode."})
        return
    
    PROMPT = prompts.get(MODE , None)

    if PROMPT == None:
        return flask.jsonify({"notes": "Internal Error: Unknown prompt.",
        "quiz": "Internal Error: Unknown prompt.",
        "studyPlan": "Internal Error: Unknown prompt.",
        "flashCards": "Internal Error: Unknown prompt."})
    else:
        PROMPT = PROMPT.format(NOTES=NOTES , LANGUAGE=LANGUAGE)

    payload = {
        "messages": [{
            "role": "user",
            "content": PROMPT
        }],
        "model": data.get("model" , "openai/gpt-oss-20b")
    }

    if payload["model"] is None:
        payload["model"] = "openai/gpt-oss-20b"

    print(f"Model: {payload["model"]}")

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            data = result["choices"][0]['message']['content'] if result else "Content Generated!"
            if MODE == "quiz":
                print("RAW QUIZ >>>", repr(data))  # DEBUG
                parsed = ParseQuiz(data)
                print("PARSED >>>", parsed)
                return flask.jsonify(parsed)
            else:
                return flask.jsonify({"notes": data,
                "flashCards": data,
                "studyPlan": data})
        else:
            return flask.jsonify({'quiz': f'API error {response.status_code}'}), 400
            
    except Exception as e:
        print("WRONG API KEY.")
        return flask.jsonify({
            'quiz': f'Request failed: {str(e)}',
            'notes': f'Request failed: {str(e)}'}), 500

@app.route('/quiz-generator')
def QuizGenerator():
    return flask.render_template('QuizGenerator.html')

if __name__ == "__main__":
    app.run()
