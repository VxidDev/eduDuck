import re
from flask import render_template , request , jsonify
from routes.utils import AiReq

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
    NOTES = data["notes"]
    LANGUAGE = data["language"]
    AMOUNT = data["questionCount"]
    API_MODE = data["apiMode"]

    API_KEY = data["apiKey"]
    API_URL = "https://router.huggingface.co/v1/chat/completions" if API_MODE == "Hugging Face" else f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_MODE == "Hugging Face" else  {
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY,
    }
    
    PROMPT = prompts['quiz']

    if PROMPT == None:
        return jsonify({'quiz': 'Internal Error: PROMPT NOT FOUND'})
    else:
        PROMPT = PROMPT.format(NOTES=NOTES , LANGUAGE=LANGUAGE, AMOUNT=AMOUNT)

    payload = {
        "messages": [{
            "role": "user",
            "content": PROMPT
        }],
        "model": data.get("model" , "openai/gpt-oss-20b")
    } if API_MODE == "Hugging Face" else {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": PROMPT}
                ],
            }
        ]
    }

    if API_MODE != "Gemini" and payload.get("model" , None) is None:
        payload["model"] = "openai/gpt-oss-20b"

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