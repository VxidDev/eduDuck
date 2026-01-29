from flask import Flask , render_template , send_from_directory , redirect , url_for , request , jsonify
from json import load , JSONDecodeError
from functools import wraps

from routes.utils import ( 
    LoginUser , RegisterUser , User , LoadUser, # Accounts
    IncrementUsage , GetUsage, # Free Usage Logic
    storeFlashcards, uploadNotes , storeNotes , storeQuiz , storeStudyPlan # Storing (temp)
)

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

from routes.duckAI import GenerateResponse as _GenerateResponse_

from routes.studyPlanGenerator import StudyPlanGen , StudyPlan , ExportStudyPlan , ImportStudyPlan

from routes.oauth import oauthBp , oauth

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash , generate_password_hash

import os
import secrets
from flask_login import LoginManager , UserMixin , login_required , current_user , logout_user

notes = {}
quizzes = {}
flashcards = {}
studyPlans = {}

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
oauth.init_app(app)
app.register_blueprint(oauthBp)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key or len(app.secret_key) < 32:
    raise RuntimeError("Invalid SECRET_KEY")

prompts = None

try:
    with open("prompts.json" , "r") as file:
        prompts = load(file)
except (FileNotFoundError , JSONDecodeError):
    print("Failed to load prompts.")

if not prompts:
    raise RuntimeError("Failed to load prompts.")

def RemainingUsage():
    return GetUsage().get_json().get("remaining", 3) if current_user.is_authenticated else 3

@app.route("/" , methods=['GET'])
def root():
    return render_template("pages/index.html" , remaining=RemainingUsage())

# ---------------- Utils ----------------------------------
@app.route("/upload-notes", methods=['POST'], endpoint='uploadNotes')
def UploadNotes():
    return uploadNotes()

@app.route('/store-notes', methods=['POST'], endpoint='storeNotes')
def StoreNotes():
    return storeNotes(notes)

@app.route('/store-study-plan', methods=['POST'], endpoint='storeStudyPlan')
def StoreStudyPlan():
    return storeStudyPlan(studyPlans)

@login_manager.user_loader
def loadUser(userID):
    userDoc = LoadUser(userID)

    if not userDoc:
        return None
    
    return User(userDoc)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("root"))

    if request.method == "POST":
        data = request.get_json() 
        result = LoginUser(User, data)

        if result:  
            return result

        return jsonify({"success": True})  

    return render_template("pages/login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("root"))
        
    return RegisterUser()

@app.route("/logout" , methods=["GET"])
def logout():
    logout_user()
    return redirect(url_for("root"))

def apiLoginRequired(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify(error = "Unauthorized"), 401

        return func(*args, **kwargs)
    return wrapper

# ---------------- Quiz Generator ------------------------
@app.route('/quiz-generator/store-quiz', methods=['POST'], endpoint='storeQuiz')
def StoreQuiz():
    return storeQuiz(quizzes)

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
    return render_template('Quiz Generator/QuizResult.html')

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
def generateFlashCards():
    return _FlashcardGenerator_(prompts)

@app.route('/store-flashcards' , methods=['POST'], endpoint='storeflashCards')
def StoreFlashcards():
    return storeFlashcards(flashcards)

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
    return render_template("DuckAI/DuckAI.html" , remaining=RemainingUsage())

@app.route('/duck-ai/generate' , endpoint='DuckAIResponse' , methods=['POST'])
def GenerateResponse():
    return _GenerateResponse_(prompts)

# -------------- Study Plan Generator ---------------------
@app.route('/study-plan-generator' , endpoint='StudyPlanGenerator')
def StudyPlanGenerator():
    return render_template("Study Plan Generator/studyPlanGenerator.html")

@app.route('/study-plan-generator/generate' , endpoint='StudyPlanGenerate' , methods=['POST'])
def studyPlanGen():
    return StudyPlanGen(prompts)

@app.route('/study-plan-generator/result' , endpoint='StudyPlanResult')
def StudyPlanResult():
    return StudyPlan(studyPlans)

@app.route('/study-plan-generator/export-plan' , endpoint='studyPlanExport')
def ExportPlan():
    return ExportStudyPlan(studyPlans)

@app.route('/study-plan-generator/import-plan' , methods=['POST'] , endpoint='StudyPlanImport')
def ImportPlan():
    return ImportStudyPlan(studyPlans)

# ---------------- Miscellanious ------------------------
@app.route("/keyAccess")
def keyAccess():
    return render_template("pages/keyAccess.html")

@app.route("/get-usage")
@apiLoginRequired
def getUsage():
    return GetUsage()

@app.route("/increment-usage")
@apiLoginRequired
def incrementUsage():
    return IncrementUsage()

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory('static' , 'robots.txt')

@app.route('/privacy')
def privacy():
    return render_template('pages/privacy.html')

@app.route('/terms')
def terms():
    return render_template('pages/terms.html')

if __name__ == "__main__":
    app.run()
