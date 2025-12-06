import flask , requests

app = flask.Flask(__name__)

@app.route("/" , methods=['GET'])
def root():
    return flask.render_template("index.html")

@app.route("/keyAccess")
def keyAccess():
    return flask.render_template("keyAccess.html")

@app.route("/generate" , methods=['POST'])

def generate():
    data = flask.request.get_json()
    NOTES = data["notes"]

    API_KEY = data["apiKey"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    PROMPT =  f"Create 10 quiz questions with this format, Format must be (question number). (question) <newline> answers separated by newline each having a number a, b, c, d then,after 2 newlines there has to be a **1 correct answer to this question**. dont include greeting at start and finish just do this format.from these notes: {NOTES}"
    
    payload = {
        "messages": [{
            "role": "user",
            "content": PROMPT
        }],
        "model": "openai/gpt-oss-20b"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            quiz = result["choices"][0]['message']['content'] if result else "Quiz generated!"
            return flask.jsonify({'quiz': quiz})
        else:
            return flask.jsonify({'quiz': f'API error {response.status_code}'}), 400
            
    except Exception as e:
        return flask.jsonify({'quiz': f'Request failed: {str(e)}'}), 500

if __name__ == "__main__":
    app.run()