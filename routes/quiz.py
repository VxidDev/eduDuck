import re
from flask import render_template , request , jsonify , send_file
from routes.utils import AiReq , IncrementUsage
from json import load , JSONDecodeError , dumps
from uuid import uuid4
from io import BytesIO
import os

standardApiErrors = {
    "API error 402": "1 What does API error 402 mean? a) Payment error b) Deposit needed c) Free credits exhausted d) Invalid API key |CORRECT:c",
    "API error 401": "1 What does API error 401 mean? a) Invalid or missing API key b) Not enough credits c) Server is down d) Quiz parsing failed |CORRECT:a"
}

moreApiErrors = {
    "API error 429": "1 What does API error 429 mean? a) Rate limit exceeded b) Invalid request c) Server error d) Model not found |CORRECT:a",
    "API error 503": "1 What does API error 503 mean? a) Service unavailable b) Payment required c) Bad request d) Unauthorized |CORRECT:a",
    "Model not loaded": "1 What does 'Model not loaded' mean? a) Model still loading b) Invalid model name c) No internet d) API key expired |CORRECT:a",
    "Request timeout": "1 What does 'Request timeout' mean? a) Server too slow b) Invalid payload c) Rate limited d) Wrong endpoint |CORRECT:a",
    "API error 400": "1 What does API error 400 mean? a) Bad request b) Payment required c) Unauthorized d) Rate limited |CORRECT:a"
}


def ParseQuiz(quiz: str):
    questions = {}
    
    text = re.sub(r'[\u2013\u2014\u2015\u2011‑–—]', '-', quiz)
    text = re.sub(r'\s+', ' ', text).strip()
    
    blocks = re.split(r'(\|\s*CORRECT\s*:\s*[a-dA-D]\|)', text)
    
    i = 0
    while i < len(blocks):
        if re.match(r'^\d+\s', blocks[i].strip()):
            q_num_match = re.match(r'(\d+)\s', blocks[i])
            if not q_num_match:
                i += 1
                continue
            q_num = q_num_match.group(1)
            
            j = i + 1
            question_end = len(blocks)
            while j < len(blocks):
                if re.match(r'^\|\s*CORRECT\s*:', blocks[j]):
                    question_end = j
                    break
                j += 1
            
            full_text = ''.join(blocks[i:question_end]).strip()
            
            correct_match = re.search(r'\|\s*CORRECT\s*:\s*([a-dA-D])', ''.join(blocks[question_end-1:question_end+1]))
            if not correct_match:
                i = question_end
                continue
            correct = correct_match.group(1).lower()
            
            a_pos = re.search(r'\ba\)\s', full_text, re.I)
            if not a_pos:
                i = question_end
                continue
            
            question = full_text[:a_pos.start()].strip(' ?.,:;-?!0123456789 \t')
            options_text = full_text[a_pos.start():].strip()
            
            label_pattern = r'(?i)\b([a-d])\)\s*'
            opt_splits = re.split(label_pattern, options_text)
            
            answers = {}
            current_label = None
            current_opt = ''
            
            for part in opt_splits:
                label_match = re.match(r'(?i)^([a-d])$', part)
                if label_match:
                    if current_label:
                        answers[current_label.lower()] = current_opt.strip(' .,!?;:')
                    current_label = label_match.group(1).lower()
                    current_opt = ''
                else:
                    current_opt += part
            
            if current_label:
                answers[current_label.lower()] = current_opt.strip(' .,!?;:')
            
            if set('abcd') <= set(answers.keys()):
                questions[q_num] = {
                    'question': question,
                    'answers': answers,
                    'correct': correct
                }
        
        i += 2
    
    return questions

def QuizGenerator():
    return render_template('QuizGenerator.html')

def quiz(quizzes):
    quizID = request.args.get('quiz')
    quiz = quizzes.get(quizID, '') if quizID else ''
    print("READ", quizID, "found:", bool(quiz))
    return render_template("Quiz.html" , quiz=quiz)

def submitResult():
    data = request.get_json()
    quiz = data.get('quiz', {})
    user_answers = data.get('answers', {})
    
    if not quiz:
        return jsonify({'error': 'No quiz data'}), 400
    
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
    
    return jsonify(result_data)

def QuizGen(prompts: dict):
    data: dict = request.get_json()
    IS_FREE = data["isFree"]
    NOTES = data["notes"]
    LANGUAGE = data["language"]
    AMOUNT = data["questionCount"]
    API_MODE = data["apiMode"]
    DIFFICULTY = data["difficulty"]
    MODEL = data.get("model" , False)

    IsReasoning = False

    if IS_FREE: IncrementUsage()

    if MODEL:
        MODEL = MODEL.strip()
        IsReasoning = any(x in MODEL.lower() for x in ["gpt-5", "o1"])

    API_KEY = data["apiKey"] if not IS_FREE else os.getenv("GEMINI_API_KEY")
    
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

    PROMPT = prompts['quiz']

    if PROMPT == None:
        return jsonify({'quiz': 'Internal Error: PROMPT NOT FOUND'})
    else:
        PROMPT = PROMPT.format(NOTES=NOTES , LANGUAGE=LANGUAGE, AMOUNT=AMOUNT , DIFFICULTY=DIFFICULTY)

    if API_MODE == "Hugging Face":
        payload = {
            "messages": [{"role": "user", "content": PROMPT}],
            "model": data.get("model") or "openai/gpt-oss-20b"
        }
    elif API_MODE == "OpenAI":
        payload = {
            "model": MODEL if MODEL else "gpt-4.1-nano",
            "messages": [{"role": "user", "content": PROMPT}],
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
    elif API_MODE == "Gemini":
        pass  
    else:
        payload["max_tokens"] = 4096
        payload["temperature"] = data.get("temperature", 0.3)
        payload["top_p"] = data.get("top_p", 0.9)

    if payload and API_MODE == "Hugging Face": print(f"Model: {payload["model"]}") 

    output = AiReq(API_URL , headers , payload , API_MODE)

    if (output is None):
        return jsonify({"quiz": "Internal Error."})

    print(f"Output: {output}")

    if output in standardApiErrors:
        output = standardApiErrors[output]
    elif output in moreApiErrors:
        output = moreApiErrors[output]
    else:
        print("Successfully generated quiz. Parsing...")
        
    print(output)

    quiz = ParseQuiz(output)

    if len(quiz) == 0:
        print("Empty quiz.")
    
    print(quiz)

    return jsonify({'quiz': quiz})

def ImportQuiz(quizzes: dict) -> None:
    file = request.files.get("quizFile")      
    file.stream.seek(0)

    try:                
        data = load(file.stream)
    except JSONDecodeError:
        return jsonify({"err": "Invalid Quiz!"})

    quizID = str(uuid4())
    quizzes[quizID] = data
    print("STORED", quizID, "len:", len(data))

    return jsonify({'id': quizID , "err": None})

def ExportQuiz(quizzes: dict) -> None:
    quizID = request.args.get("quiz")

    quiz = quizzes.get(quizID)

    buffer = BytesIO(dumps(quiz, indent=2).encode("utf-8"))
    buffer.seek(0)
        
    return send_file(
        buffer, as_attachment=True,
        download_name=f"EduDuck-Quiz_{quizID}.json",
        mimetype="application/json"
    )

    