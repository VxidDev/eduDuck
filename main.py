from flask import Flask , render_template , send_from_directory , redirect , url_for , request , jsonify , Response, abort
from flask_wtf.csrf import CSRFProtect
from json import load , JSONDecodeError
from functools import wraps
from dotenv import load_dotenv
import os
from uuid import uuid4

load_dotenv()

from routes.utils import ( 
    LoginUser , RegisterUser , User , LoadUser, sendVerificationEmail, VerifyEmail, UserProfile, GetMongoClient, GetUserPFP, # Accounts
    IncrementUsage , GetUsage, # Free Usage Logic
    uploadNotes, # Storing (temp)
    StoreQuery , StoreDuckAIConversation , GetQueryFromDB, # Storing ("perm"),
    Log, # Logging
    cleanup # Cleanup
)

from routes.quiz import QuizGenerator as _QuizGenerator_
from routes.quiz import quiz as _quiz_
from routes.quiz import submitResult as _submitResult_
from routes.quiz import QuizGen as _QuizGen_
from routes.quiz import ImportQuiz as _ImportQuiz_
from routes.quiz import ExportQuiz as _ExportQuiz_
from routes.quiz import QuizResult

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
from routes.duckAI import DuckAI

from routes.studyPlanGenerator import StudyPlanGen , StudyPlan , ExportStudyPlan , ImportStudyPlan

from routes.oauth import oauthBp , oauth

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash , generate_password_hash
from werkzeug.utils import secure_filename
from bson import ObjectId

import os
import secrets

from flask_login import LoginManager , UserMixin , login_required , current_user , logout_user
from threading import Thread

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import boto3
from botocore.client import Config

import atexit

atexit.register(cleanup)

notes = {}
quizzes = {}
flashcards = {}
studyPlans = {}
quizResults = {}

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2.5 * 1024 * 1024

csrf = CSRFProtect(app)

def RateLimitKey() -> str:
    if current_user.is_authenticated:
        return f"user:{current_user.get_id()}"

    return get_remote_address()

limiter = Limiter(
    app=app,
    key_func=RateLimitKey,
    default_limits=[], 
    storage_uri="memory://"
)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
oauth.init_app(app)
csrf.exempt(oauthBp)
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

# Cloudflare R2 credentials
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_REGION = os.getenv("R2_REGION", "auto")
R2_ENDPOINT_URL = f"https://avatars.eduduck.app"

s3 = boto3.client(
    "s3",
    region_name=R2_REGION,
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4")
)

def RemainingUsage():
    return GetUsage().get_json().get("remaining", 3) if current_user.is_authenticated else 3

def allowedProfilePicExtensions(filename):
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/" , methods=['GET'])
@limiter.exempt
def root():
    return render_template("pages/index.html" , remaining=RemainingUsage())

# ---------------- Utils ----------------------------------
@app.route("/upload-notes", methods=['POST'], endpoint='uploadNotes')
@limiter.exempt
def UploadNotes():
    return uploadNotes()

@login_manager.user_loader
def loadUser(userID):
    userDoc = LoadUser(userID)

    if not userDoc:
        return None
    
    return User(userDoc)

@app.route("/login", methods=["GET", "POST"])
@limiter.exempt
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
@limiter.exempt
def register():
    if current_user.is_authenticated:
        return redirect(url_for("root"))
        
    if request.method == "POST":
        result = RegisterUser()

        if isinstance(result, tuple):
            msg, email = result
            sendVerificationEmail(app , msg[1], msg[0] , msg[2] , "EduDuck Verification <no-reply@mg.eduduck.app>")

            return jsonify({
                "success": True,
                "redirect": f"/check-email?email={email}"
            })

        return jsonify({"error": "Registration failed"}), 500
    else:
        return render_template("pages/register.html")

@app.route("/verify-email/<token>")
@limiter.exempt
def verifyEmail(token):
    return VerifyEmail(token)

@app.route("/check-email")
@limiter.exempt
def CheckEmail():
    email = request.args.get("email", "")
    return render_template("pages/checkEmail.html", email=email)

@app.route("/logout" , methods=["GET"])
@limiter.exempt
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

@app.route("/store-query" , endpoint="storeQuery")
@limiter.limit("100 per hour")
def storeQuery():
    if not current_user.is_authenticated:
        return jsonify({"error": "unauthorized"}) , 401

    data = request.get_json()

    response = StoreQuery(data.get("queryName") , data.get(data.get("queryName")))

    if response not in ["unknown qName" , "empty query payload"]:
        return jsonify({"id": response})

    return jsonify({"error": response})

@app.route("/get-query" , endpoint="getQuery" , methods=['POST'])
@limiter.limit("200 per hour")
def getQuery():
    if not current_user.is_authenticated:
        return jsonify({"error": "unauthorized"}) , 401

    data = request.get_json()

    return GetQueryFromDB(data.get('queryID' , None) , data.get('collection' , None))

@app.route("/is-logined-in" , endpoint="checkLogin" , methods=["GET"])
@limiter.exempt
def checkLogin():
    return jsonify({"login": current_user.is_authenticated})

@app.route("/profile/upload-profile-picture" , methods=['POST'] , endpoint="uploadProfilePicture")
@limiter.limit("30 per hour")
def uploadProfilePicture():
    if 'profile_picture' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['profile_picture']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowedProfilePicExtensions(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    file.seek(0, 2)  # Move to end
    size = file.tell()
    file.seek(0)  # Reset to start
    MAX_PROFILE_PIC_SIZE = int(2.5 * 1024 * 1024)  # 2.5 MB
    if size > MAX_PROFILE_PIC_SIZE:
        return jsonify({"error": "File too large, max 2.5 MB"}), 400

    userId = current_user.id

    filename = f"{uuid4().hex}_{secure_filename(file.filename)}"
    key = f"users/{userId}/{filename}"

    try:
        user = GetMongoClient()["EduDuck"]["users"].find_one({"_id": ObjectId(userId)})

        if user and "profilePicture" in user:
            oldKey = user["profilePicture"]
            try:
                s3.delete_object(Bucket=R2_BUCKET_NAME, Key=oldKey)
            except ClientError as ce:
                Log(f"Failed to delete old profile picture -> {str(ce)}", "warning")

        s3.upload_fileobj(
            Fileobj=file,
            Bucket=R2_BUCKET_NAME,
            Key=key,
        )
    except Exception as e:
        Log(f"Failed to upload profile picture to Cloudflare R2 -> {str(e)}", "error")
        return jsonify({"error": f"Failed to upload file: {str(e)}"}), 500

    try:
        GetMongoClient()["EduDuck"]["users"].find_one_and_update(
            {"_id": ObjectId(userId)},
            {"$set": {"profilePicture": key}},
            upsert=False
        )
    except Exception as e:
        Log(f"Failed to upload add profile picture URL to MongoDB -> {str(e)}" , "error")
        try:
            s3.delete_object(Bucket=R2_BUCKET_NAME, Key=key)
        except ClientError as ce:
            Log(f"Failed to delete orphaned R2 file -> {str(ce)}", "error")
        return jsonify({"error": f"Failed to update MongoDB: {str(e)}"}), 500

    return jsonify({"url": f"{R2_ENDPOINT_URL}/users/{userId}/{key}"})

@app.route("/profile/user-pfp" , methods=['GET'] , endpoint="getUserProfilePicture")
@limiter.limit("60 per hour")
def getUserPFP():
    if not current_user.is_authenticated:
        return jsonify({"error": "unauthorized"}) , 401

    return GetUserPFP()

# ---------------- Quiz Generator ------------------------
@app.route('/quiz-generator/store-quiz', methods=['POST'], endpoint='storeQuiz')
@limiter.limit("100 per hour")
def StoreQuiz():
    return storeQuiz(quizzes)

@app.route('/quiz-generator/quiz/result', methods=['POST' , 'GET'], endpoint='QuizResult')
@limiter.exempt
def submitResult():
    if request.method == 'POST':
        return _submitResult_(quizResults)

    return QuizResult(quizResults)

@app.route('/quiz-generator/gen-quiz', methods=['POST'], endpoint='generateQuiz')
@limiter.limit("30 per hour")
def QuizGen():
    return _QuizGen_(prompts , quizzes)

@app.route('/quiz-generator/import-quiz' , methods=['POST'] , endpoint='importQuiz')
@limiter.exempt
def ImportQuiz():
    return _ImportQuiz_(quizzes)

@app.route('/quiz-generator/export-quiz' , endpoint='exportQuiz')
@limiter.exempt
def ExportQuiz():
    return _ExportQuiz_(quizzes)

@app.route("/quiz-generator/quiz", endpoint='showQuiz')
@limiter.exempt
def quiz():
    return _quiz_(quizzes)

@app.route('/quiz-generator', endpoint='quizGeneratorPage')
@limiter.exempt
def QuizGenerator():
    return _QuizGenerator_()

# ---------------- Note Enhancer ------------------------
@app.route('/note-enhancer/result', endpoint='enhancedNotes')
@limiter.exempt
def EnhancedNotes():
    return _EnhancedNotes_(notes)

@app.route('/note-enhancer', endpoint='noteEnhancer')
@limiter.exempt
def NoteEnhance():
    return _NoteEnhancer_()

@app.route('/note-enhancer/import-notes' , methods=['POST'] , endpoint='importEnhancedNotes')
@limiter.exempt
def ImportEnhancedNotes():
    return _ImportEnhancedNotes_(notes)

@app.route('/note-enhancer/export-notes' , endpoint='exportEnhancedNotes')
@limiter.exempt
def ExportEnhancedNotes():
    return _ExportEnhancedNotes_(notes)

@app.route('/note-enhancer/enhance', methods=['POST'], endpoint='enhanceNotes')
@limiter.limit("30 per hour")
def EnhanceNotes():
    return _EnhanceNotes_(prompts , notes)

# ---------------- FlashCard Generator ------------------
@app.route('/flashcard-generator' , endpoint='flashCardGenerator')
@limiter.exempt
def flashCards():
    return _FlashCardGenerator_()

@app.route('/flashcard-generator/generate' , endpoint='flashcardGenerator' , methods=['POST'])
@limiter.limit("30 per hour")
def generateFlashCards():
    return _FlashcardGenerator_(prompts , flashcards)

@app.route('/store-flashcards' , methods=['POST'], endpoint='storeflashCards')
@limiter.limit("100 per hour")
def StoreFlashcards():
    return storeFlashcards(flashcards)

@app.route('/flashcard-generator/result' , endpoint='flashCardResult')
@limiter.exempt
def flashCardResult():
    return _FlashCardResult_(flashcards)

@app.route('/flashcard-generator/import-flashcards' , methods=['POST'] , endpoint='flashCardImport')
@limiter.exempt
def ImportFlashcards():
    return _ImportFlashcards_(flashcards)

@app.route('/flashcard-generator/export-flashcards' , endpoint='flashCardExport')
@limiter.exempt
def ExportFlashcards():
    return _ExportFlashcards_(flashcards)

# -------------- DuckAI -----------------------------------
@app.route('/duck-ai' , endpoint='DuckAI')
@limiter.exempt
def duckAI():
    return DuckAI()

@app.route('/duck-ai/store-conversation' , endpoint='DuckAIStoreConversation' , methods=['POST'])
@login_required
@limiter.limit("100 per hour")
def StoreConversation():
    data = request.get_json()

    return jsonify({ "queryID": StoreDuckAIConversation(data.get("messages") , data.get("queryID" , None))})

@app.route('/duck-ai/generate' , endpoint='DuckAIResponse' , methods=['POST'])
@limiter.limit("30 per hour")
def GenerateResponse():
    return _GenerateResponse_(prompts)

# -------------- Study Plan Generator ---------------------
@app.route('/study-plan-generator' , endpoint='StudyPlanGenerator')
@limiter.exempt
def StudyPlanGenerator():
    return render_template("Study Plan Generator/studyPlanGenerator.html")

@app.route('/study-plan-generator/generate' , endpoint='StudyPlanGenerate' , methods=['POST'])
@limiter.limit("30 per hour")
def studyPlanGen():
    return StudyPlanGen(prompts , studyPlans)

@app.route('/study-plan-generator/result' , endpoint='StudyPlanResult')
@limiter.exempt
def StudyPlanResult():
    return StudyPlan(studyPlans)

@app.route('/study-plan-generator/export-plan' , endpoint='studyPlanExport')
@limiter.exempt
def ExportPlan():
    return ExportStudyPlan(studyPlans)

@app.route('/study-plan-generator/import-plan' , methods=['POST'] , endpoint='StudyPlanImport')
@limiter.exempt
def ImportPlan():
    return ImportStudyPlan(studyPlans)

# ---------------- Miscellanious ------------------------
@app.route("/keyAccess")
@limiter.exempt
def keyAccess():
    return render_template("pages/keyAccess.html")

@app.route("/profile")
@limiter.exempt
def profile():
    return UserProfile()

@app.route("/get-usage")
@apiLoginRequired
@limiter.limit("200 per hour")
def getUsage():
    return GetUsage()

@app.route("/increment-usage")
@apiLoginRequired
@limiter.limit("200 per hour")
def incrementUsage():
    return IncrementUsage()

@app.route('/sitemap.xml')
@limiter.exempt
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/robots.txt')
@limiter.exempt
def robots():
    return send_from_directory('static' , 'robots.txt')

@app.route('/privacy')
@limiter.exempt
def privacy():
    return render_template('pages/privacy.html')

@app.route('/terms')
@limiter.exempt
def terms():
    return render_template('pages/terms.html')

if __name__ == "__main__":
    app.run()
