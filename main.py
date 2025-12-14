from flask import Flask , render_template
from json import load , JSONDecodeError

from routes.utils import AiReq as _AiReq_
from routes.utils import uploadNotes as _uploadNotes_
from routes.utils import storeNotes as _storeNotes_
from routes.utils import storeQuiz as _storeQuiz_

from routes.quiz import ParseQuiz
from routes.quiz import QuizGenerator as _QuizGenerator_
from routes.quiz import quiz as _quiz_
from routes.quiz import submitResult as _submitResult_
from routes.quiz import QuizGen as _QuizGen_

from routes.noteEnhancer import EnhanceNotes as _EnhanceNotes_
from routes.noteEnhancer import NoteEnhancer as _NoteEnhancer_
from routes.noteEnhancer import EnhancedNotes as _EnhancedNotes_

notes = {}
quizzes = {}

app = Flask(__name__)

prompts = None

try:
    with open("prompts.json" , "r") as file:
        prompts = load(file)
except (FileNotFoundError , JSONDecodeError):
    print("Failed to load prompts.")

if not prompts:
    exit(0)

@app.route("/" , methods=['GET'])
def root():
    return render_template("index.html")

# ---------------- Utils ----------------------------------
@app.route("/upload-notes" , methods=['POST'])
def uploadNotes():
    return _uploadNotes_()

@app.route('/store-notes', methods=['POST'])
def storeNotes():
    return _storeNotes_(notes)

@app.route("/upload-notes" , methods=['POST'])
def aiReq(API_URL , headers , payload , timeout=15):
    return _AiReq_(API_URL , headers , payload , timeout)

# ---------------- Quiz Generator ------------------------
@app.route('/quiz-generator/store-quiz', methods=['POST'])
def storeQuiz():
    return _storeQuiz_(quizzes)

@app.route('/quiz-generator/quiz/result', methods=['POST'])
def submitResult():
    return _submitResult_()

@app.route('/quiz-generator/gen-quiz' , methods=['POST'])
def QuizGen():
    return _QuizGen_(prompts)

@app.route('/quiz-generator/quiz/result')
def result_page():
    return render_template('QuizResult.html')

@app.route("/quiz-generator/quiz")
def quiz():
    return _quiz_(quizzes)

@app.route('/quiz-generator')
def QuizGenerator():
    return _QuizGenerator_()

# ---------------- Note Enhancer ------------------------
@app.route('/note-enhancer/result')
def EnhancedNotes():
    return _EnhancedNotes_(notes)

@app.route('/note-enhancer')
def NoteEnhance():
    return _NoteEnhancer_()

@app.route('/note-enhancer/enhance' , methods=['POST'])
def EnhanceNotes():
    return _EnhanceNotes_(prompts)

# ---------------- FlashCard Generator ------------------
@app.route('/flashcards')
def flashCards():
    return "Unsupported."

# ---------------- Miscellanious ------------------------
@app.route("/keyAccess")
def keyAccess():
    return render_template("keyAccess.html")

@app.route('/quiz-generator')
def QuizGenerator():
    return flask.render_template('QuizGenerator.html')

if __name__ == "__main__":
    app.run()
