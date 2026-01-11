from flask import Flask , render_template , send_from_directory
from json import load , JSONDecodeError

from routes.utils import uploadNotes as _uploadNotes_
from routes.utils import storeNotes as _storeNotes_
from routes.utils import storeQuiz as _storeQuiz_
from routes.utils import storeFlashcards as _storeFlashcards_
from routes.utils import GetUsage as _GetUsage_
from routes.utils import IncrementUsage as _IncrementUsage_

from routes.quiz import ParseQuiz
from routes.quiz import QuizGenerator as _QuizGenerator_
from routes.quiz import quiz as _quiz_
from routes.quiz import submitResult as _submitResult_
from routes.quiz import QuizGen as _QuizGen_
from routes.quiz import ImportQuiz as _ImportQuiz_
from routes.quiz import ExportQuiz as _ExportQuiz_

from routes.noteEnhancer import EnhanceNotes as _EnhanceNotes_
from routes.noteEnhancer import NoteEnhancer as _NoteEnhancer_
from routes.noteEnhancer import EnhancedNotes as _EnhancedNotes_
from routes.noteEnhancer import ImportNotes as _ImportEnhancedNotes_
from routes.noteEnhancer import ExportNotes as _ExportEnhancedNotes_

from routes.flashcardGenerator import FlashCardGenerator as _FlashCardGenerator_
from routes.flashcardGenerator import FlashcardGenerator as _FlashcardGenerator_
from routes.flashcardGenerator import FlashCardResult as _FlashCardResult_
from routes.flashcardGenerator import ImportFlashcards as _ImportFlashcards_
from routes.flashcardGenerator import ExportFlashcards as _ExportFlashcards_

from routes.duckAI import DuckAI as _DuckAI_
from routes.duckAI import GenerateResponse as _GenerateResponse_

from werkzeug.middleware.proxy_fix import ProxyFix

notes = {}
quizzes = {}
flashcards = {}

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

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
@app.route("/upload-notes", methods=['POST'], endpoint='uploadNotes')
def uploadNotes():
    return _uploadNotes_()

@app.route('/store-notes', methods=['POST'], endpoint='storeNotes')
def storeNotes():
    return _storeNotes_(notes)

# ---------------- Quiz Generator ------------------------
@app.route('/quiz-generator/store-quiz', methods=['POST'], endpoint='storeQuiz')
def storeQuiz():
    return _storeQuiz_(quizzes)

@app.route('/quiz-generator/quiz/result', methods=['POST'], endpoint='submitQuizResult')
def submitResult():
    return _submitResult_()

@app.route('/quiz-generator/gen-quiz', methods=['POST'], endpoint='generateQuiz')
def QuizGen():
    return _QuizGen_(prompts)

@app.route('/quiz-generator/import-quiz' , methods=['POST'] , endpoint='importQuiz')
def ImportQuiz():
    return _ImportQuiz_(quizzes)

@app.route('/quiz-generator/export-quiz' , endpoint='exportQuiz')
def ExportQuiz():
    return _ExportQuiz_(quizzes)

@app.route('/quiz-generator/quiz/result', endpoint='quizResultPage')
def result_page():
    return render_template('QuizResult.html')

@app.route("/quiz-generator/quiz", endpoint='showQuiz')
def quiz():
    return _quiz_(quizzes)

@app.route('/quiz-generator', endpoint='quizGeneratorPage')
def QuizGenerator():
    return _QuizGenerator_()

# ---------------- Note Enhancer ------------------------
@app.route('/note-enhancer/result', endpoint='enhancedNotes')
def EnhancedNotes():
    return _EnhancedNotes_(notes)

@app.route('/note-enhancer', endpoint='noteEnhancer')
def NoteEnhance():
    return _NoteEnhancer_()

@app.route('/note-enhancer/import-notes' , methods=['POST'] , endpoint='importEnhancedNotes')
def ImportEnhancedNotes():
    return _ImportEnhancedNotes_(notes)

@app.route('/note-enhancer/export-notes' , endpoint='exportEnhancedNotes')
def ExportEnhancedNotes():
    return _ExportEnhancedNotes_(notes)

@app.route('/note-enhancer/enhance', methods=['POST'], endpoint='enhanceNotes')
def EnhanceNotes():
    return _EnhanceNotes_(prompts)

# ---------------- FlashCard Generator ------------------
@app.route('/flashcard-generator' , endpoint='flashCardGenerator')
def flashCards():
    return _FlashCardGenerator_()

@app.route('/flashcard-generator/generate' , endpoint='flashcardGenerator' , methods=['POST'])
def flashCards():
    return _FlashcardGenerator_(prompts)

@app.route('/store-flashcards' , methods=['POST'], endpoint='storeflashCards')
def storeFlashcards():
    return _storeFlashcards_(flashcards)

@app.route('/flashcard-generator/result' , endpoint='flashCardResult')
def flashCardResult():
    return _FlashCardResult_(flashcards)

@app.route('/flashcard-generator/import-flashcards' , methods=['POST'] , endpoint='flashCardImport')
def ImportFlashcards():
    return _ImportFlashcards_(flashcards)

@app.route('/flashcard-generator/export-flashcards' , endpoint='flashCardExport')
def ExportFlashcards():
    return _ExportFlashcards_(flashcards)

# -------------- DuckAI -----------------------------------
@app.route('/duck-ai' , endpoint='DuckAI')
def DuckAI():
    return _DuckAI_()

@app.route('/duck-ai/generate' , endpoint='DuckAIResponse' , methods=['POST'])
def GenerateResponse():
    return _GenerateResponse_(prompts)

# ---------------- Miscellanious ------------------------
@app.route("/keyAccess")
def keyAccess():
    return render_template("keyAccess.html")

@app.route("/get-usage")
def GetUsage():
    return _GetUsage_()

@app.route("/increment-usage")
def IncrementUsage():
    return _IncrementUsage_()

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory('static' , 'robots.txt')

if __name__ == "__main__":
    app.run()
