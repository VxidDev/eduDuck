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
    
    score = sum(1 for num in quiz if user_answers.get(num) == quiz[num].get('correct'))
    total = len(quiz)
    percentage = round((score / total) * 100, 1) if total > 0 else 0
    
    result_data = {
        'score': score,
        'total': total,
        'percentage': percentage,
        'results': {num: {
            'correct': q.get('correct'), 
            'user': user_answers.get(num), 
            'right': user_answers.get(num) == q.get('correct')
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

def ParseQuiz(quiz):
    questions = {}
    
    quiz = (quiz
        .replace('_', ' ')
        .replace('\n', ' ')
        .replace('  ', ' ')
        .replace('question?', '')
        .replace('a)', 'a ')
        .replace('b)', 'b ')
        .replace('c)', 'c ')
        .replace('d)', 'd ')
        .strip())
    
    blocks = quiz.split('|')
    
    i = 0
    while i < len(blocks):
        block = blocks[i].strip()
        if not block or len(block.split()) < 9:
            i += 1
            continue
        
        parts = block.split()
        try:
            q_num = parts[0]
            a_idx = next(idx for idx, p in enumerate(parts) if p == 'a')
            
            question = ' '.join(parts[1:a_idx]).strip(' ?.,:;-')
            
            b_idx = next(idx for idx, p in enumerate(parts[a_idx+1:], a_idx+1) if p == 'b')
            c_idx = next(idx for idx, p in enumerate(parts[b_idx+1:], b_idx+1) if p == 'c')
            d_idx = next(idx for idx, p in enumerate(parts[c_idx+1:], c_idx+1) if p == 'd')
            
            answers = {
                'a': ' '.join(parts[a_idx+1:b_idx]).strip(),
                'b': ' '.join(parts[b_idx+1:c_idx]).strip(),
                'c': ' '.join(parts[c_idx+1:d_idx]).strip(),
                'd': ' '.join(parts[d_idx+1:]).strip()
            }
            
            correct = None
            if i+1 < len(blocks) and blocks[i+1].strip().upper().startswith('CORRECT:'):
                correct = blocks[i+1].split(':')[1].strip().upper()
                i += 2
            else:
                i += 1
            
            questions[q_num] = {
                'question': question or f"Question {q_num}",  # Fallback
                'answers': answers,
                'correct': correct
            }
            
        except (ValueError, IndexError, StopIteration):
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

    PROMPT = f"""You are a quiz generator. FORMAT IS CRITICAL.

Create EXACTLY 10 multiple-choice questions from these notes. INCLUDE CORRECT ANSWER FOR EACH.

OUTPUT THIS EXACT FORMAT BUT FILLED, DONT DO EXACTLY "WRONG" or "CORRECT" ONLY - NO EXCEPTIONS:
1 question? a wrong b wrong c correct d wrong|CORRECT:c|2 question? a wrong b correct c wrong d wrong|CORRECT:b|3 question? a wrong b wrong c correct d wrong|CORRECT:c|4 question? a correct b wrong c wrong d wrong|CORRECT:a|5 question? a wrong b wrong c wrong d correct|CORRECT:d|6 question? a wrong b correct c wrong d wrong|CORRECT:b|7 question? a wrong b wrong c correct d wrong|CORRECT:c|8 question? a correct b wrong c wrong d wrong|CORRECT:a|9 question? a wrong b wrong c wrong d correct|CORRECT:d|10 question? a wrong b correct c wrong d wrong|CORRECT:b|

RULES - VIOLATE AND FAIL:
- Single line per question. |CORRECT:x| after EACH question.
- Space after EVERY token: number question a option b option c option d option|CORRECT:x|
- END EVERY question block with |CORRECT:[a/b/c/d]|
- NO markdown. NO bullets. NO *. NO underscores _
- Questions MUST be short and clear.
- Exactly ONE correct answer per question (a, b, c, or d).

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
            return flask.jsonify(ParseQuiz(quiz))
        else:
            return flask.jsonify({'quiz': f'API error {response.status_code}'}), 400
            
    except Exception as e:
        return flask.jsonify({'quiz': f'Request failed: {str(e)}'}), 500

if __name__ == "__main__":
    app.run()