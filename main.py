import flask , requests , pypdf
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import os

app = flask.Flask(__name__)

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

@app.route('/result')
def result_page():
    return flask.render_template('result.html')

@app.route("/" , methods=['GET'])
def root():
    return flask.render_template("index.html")

@app.route("/keyAccess")
def keyAccess():
    return flask.render_template("keyAccess.html")

@app.route("/quiz")
def quiz():
    return flask.render_template("quiz.html")

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

    quiz = (
        quiz.replace('_', ' ')
            .replace('\n', ' ')
            .replace('  ', ' ')
            .replace('question?', '')
            .replace('a)', 'a ')
            .replace('b)', 'b ')
            .replace('c)', 'c ')
            .replace('d)', 'd ')
            .strip()
    )

    raw_blocks = [b.strip() for b in quiz.split('|') if b.strip()]

    i = 0
    while i < len(raw_blocks):
        block = raw_blocks[i]

        if block.lower().startswith('correct:'):
            i += 1
            continue

        parts = block.split()
        if len(parts) < 9:
            i += 1
            continue

        try:
            q_num = parts[0]
            a_idx = parts.index('a')

            question = ' '.join(parts[1:a_idx]).strip(' ?.,:;-')

            b_idx = parts.index('b', a_idx + 1)
            c_idx = parts.index('c', b_idx + 1)
            d_idx = parts.index('d', c_idx + 1)

            answers = {
                'a': ' '.join(parts[a_idx + 1:b_idx]).strip(),
                'b': ' '.join(parts[b_idx + 1:c_idx]).strip(),
                'c': ' '.join(parts[c_idx + 1:d_idx]).strip(),
                'd': ' '.join(parts[d_idx + 1:]).strip(),
            }

            correct = None
            if i + 1 < len(raw_blocks) and raw_blocks[i + 1].lower().startswith('correct:'):
                correct = raw_blocks[i + 1].split(':', 1)[1].strip().lower()
                i += 2
            else:
                i += 1

            questions[q_num] = {
                'question': question or f'Question {q_num}',
                'answers': answers,
                'correct': correct,
            }

        except (ValueError, IndexError):
            i += 1
            continue

    return questions

@app.route("/generate" , methods=['POST'])
def generate():
    data: dict = flask.request.get_json()
    NOTES = data["notes"]

    API_KEY = data["apiKey"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    PROMPT = f"""Quiz generator ONLY. NO OTHER TEXT.

MANDATORY REQUIREMENTS (confirm each before output):
1. Output EXACTLY 10 questions in ONE continuous line
2. NO "Question", "Q", headers, markdown, bullets, newlines
3. Format: 1 question? a opt b opt c opt d opt|CORRECT:x| NO spaces before |
4. Replace "wrong"/"correct" with REAL notes content
5. Vary correct answers across a/b/c/d
6. Short, clear questions from {NOTES} ONLY

Follow this EXACT sequence:
1. Read notes
2. Generate 10 questions 
3. Output ONLY in specified format

EXAMPLE (copy this structure exactly but use notes):
1 What color grass? a blue b red c green d yellow|CORRECT:c|2 What 2+2? a 3 b 4 c 5 d 6|CORRECT:b|3 Sky color? a green b blue c red d yellow|CORRECT:b|4 Sun rises? a west b south c north d east|CORRECT:a|5 Moon phase? a full b new c half d quarter|CORRECT:d|6 Earth shape? a flat b round c square d triangle|CORRECT:b|7 Water state? a solid b liquid c gas d plasma|CORRECT:c|8 Fire needs? a water b oxygen c earth d air|CORRECT:b|9 Light speed? a slow b fast c medium d stop|CORRECT:b|10 Gravity pulls? a up b down c side d none|CORRECT:b|

NOTES: {NOTES}"""

    payload = {
        "messages": [{
            "role": "user",
            "content": PROMPT
        }],
        "model": data.get("model" , "openai/gpt-oss-20b")
    }

    print(f"Model: {payload["model"]}")

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            quiz = result["choices"][0]['message']['content'] if result else "Quiz generated!"
            print("RAW QUIZ >>>", repr(quiz))  # DEBUG
            parsed = ParseQuiz(quiz)
            print("PARSED >>>", parsed)
            return flask.jsonify(parsed)
        else:
            return flask.jsonify({'quiz': f'API error {response.status_code}'}), 400
            
    except Exception as e:
        return flask.jsonify({'quiz': f'Request failed: {str(e)}'}), 500

if __name__ == "__main__":
    app.run()