from flask import Flask , render_template , send_from_directory , redirect , url_for , request , jsonify , Response, abort
from flask_wtf.csrf import CSRFProtect
from json import load , JSONDecodeError
from functools import wraps
from dotenv import load_dotenv
import os
from uuid import uuid4

load_dotenv()

from routes.utils import ( 
    LoginUser , RegisterUser , User , LoadUser, SendEmail, VerifyEmail, UserProfile, GetMongoClient, GetUserPFP, LoadUserByMail , LoadUserByUsername, CheckPasswordSetup, GetStudyStreakData, GetNextAction, # Accounts
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
from routes.noteAnalyzer import (
    NoteAnalyzer as NoteAnalyzerRoute,
    NoteAnalyzerPage as NoteAnalyzerPageRoute,
    NoteAnalysisResult as NoteAnalysisResultRoute,
    ImportNoteAnalysis as ImportNoteAnalysisRoute,
    ExportNoteAnalysis as ExportNoteAnalysisRoute,
)

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
from botocore.exceptions import ClientError
from botocore.client import Config
import datetime

import atexit

atexit.register(cleanup)

notes = {}
quizzes = {}
flashcards = {}
studyPlans = {}
quizResults = {}
noteAnalyses = {}

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
R2_ENDPOINT_URL = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

s3 = boto3.client(
    "s3",
    region_name=R2_REGION,
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4")
)

def SetupTTLIndexes():
    db = GetMongoClient()["EduDuck"]
    
    collections = ["users", "quizzes", "study-plans", "flashcards",
               "enhanced-notes", "duck-ai", "note-analysis"]
    
    for collection_name in collections:
        try:
            db[collection_name].create_index(
                "deletedAt",
                expireAfterSeconds=2592000
            )
            Log(f"TTL index created for {collection_name}", "info")
        except Exception as e:
            if "already exists" in str(e):
                Log(f"TTL index already exists for {collection_name}", "info")
            else:
                Log(f"Failed to create TTL index for {collection_name}: {str(e)}", "warn")

SetupTTLIndexes()

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
    userDoc = LoadUser(userID=userID)

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

@app.route("/setup-password", methods=['GET', 'POST'])
@login_required
def setupPassword():
    if request.method == 'POST':
        data = request.get_json()
        new_password = data.get('password', '').strip()
        confirm = data.get('confirm', '').strip()
        
        if len(new_password) < 8:
            return jsonify({"message": "Password must be at least 8 characters"}), 400
        if new_password != confirm:
            return jsonify({"message": "Passwords do not match"}), 400
            
        hashed = generate_password_hash(new_password)
        usersCollection = GetMongoClient()["EduDuck"]["users"]
        usersCollection.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": {"password": hashed, "needs_password_setup": False}}
        )

        skip_url = request.args.get("skip", "/")
        return jsonify({
            "message": "Password set successfully",
            "redirect": f"{skip_url}?IGNORE=1" 
        }), 200

    skip_url = request.args.get("skip", "/")
    return render_template("pages/setupPassword.html", url=f"{skip_url}?IGNORE=1")

@app.route("/register", methods=["GET", "POST"])
@limiter.exempt
def register():
    if current_user.is_authenticated:
        return redirect(url_for("root"))
        
    if request.method == "POST":
        result = RegisterUser()

        if isinstance(result, tuple) and isinstance(result[0], tuple):
            msg, email = result
            
            try:
                SendEmail(
                    msg[1],  # to_email
                    msg[0],  # subject
                    msg[2],  # verification_link
                    "EduDuck Verification <no-reply@mg.eduduck.app>",
                    render_template("pages/email.html", VERIFY_URL=msg[2])
                )
                
                return jsonify({
                    "success": True,
                    "redirect": f"/check-email?email={email}"
                })
            except Exception as e:
                Log(f"Failed to send verification email: {str(e)}", "error")
                return jsonify({"error": "Failed to send verification email."}), 500
   
        return result
    
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

@app.route("/api/study-streak", methods=["GET"])
@login_required
@limiter.limit("60 per hour")
def getStudyStreak():
    days = request.args.get("days", 365, type=int)
    data = GetStudyStreakData(current_user.id, days)
    return jsonify(data)

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

        file.seek(0)
        content_type = file.content_type or 'application/octet-stream'

        s3.upload_fileobj(
            Fileobj=file,
            Bucket=R2_BUCKET_NAME,
            Key=key,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'public-read' 
            }
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

@app.route("/settings" , methods=['GET'] , endpoint='userSettings')
@CheckPasswordSetup
@login_required
@limiter.exempt
def userSettings():
    return render_template("pages/userSettings.html")

@app.route("/reset-password", methods=['GET', 'POST'], endpoint='resetPassword')
@limiter.exempt
def resetPassword():
    if request.method == 'POST':
        data = request.get_json()
        username_or_email = data.get('username_email', '').strip()
        
        if not username_or_email:
            return jsonify({"message": "Please provide a username or email"}), 400
   
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_email_input = re.fullmatch(email_pattern, username_or_email) is not None
    
        if is_email_input:
            user = LoadUserByMail(username_or_email)
        else:
            user = LoadUserByUsername(username_or_email)
  
        if not user:
            return jsonify({
                "message": "If an account exists with that username or email, a password reset link has been sent."
            }), 200
 
        reset_token = secrets.token_urlsafe(32)

        usersCollection = GetMongoClient()["EduDuck"]["users"]
        usersCollection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "reset_token": reset_token,
                    "reset_token_expires": datetime.datetime.now(datetime.UTC).timestamp() + 3600  
                }
            }
        )
    
        reset_url = url_for('resetPasswordConfirm', token=reset_token, _external=True)

        try:
            SendEmail(
                user["email"],
                "Reset Password",
                f"Click here to reset your password: {reset_url}",
                "EduDuck Password Reset <no-reply@mg.eduduck.app>",
                render_template("pages/resetPasswordEmail.html", RESET_URL=reset_url)
            )
            Log(f"Password reset email sent to {user['email']}", "success")
        except Exception as e:
            Log(f"Failed to send reset email: {str(e)}", "error")
            return jsonify({"message": "Failed to send email. Please try again later."}), 500
        
        return jsonify({
            "message": "If an account exists with that username or email, a password reset link has been sent."
        }), 200
    
    return render_template("pages/resetPassword.html")

@app.route("/reset-password/<token>", methods=['GET', 'POST'], endpoint='resetPasswordConfirm')
@limiter.exempt
def resetPasswordConfirm(token):
    usersCollection = GetMongoClient()["EduDuck"]["users"]
    
    if request.method == 'POST':
        data = request.get_json()
        new_password = data.get('password', '').strip()
        confirm_password = data.get('confirm', '').strip()
        
        if not new_password or not confirm_password:
            return jsonify({"message": "Both password fields are required"}), 400
        
        if new_password != confirm_password:
            return jsonify({"message": "Passwords do not match"}), 400
        
        if len(new_password) < 8:
            return jsonify({"message": "Password must be at least 8 characters long"}), 400

        user = usersCollection.find_one({
            "reset_token": token,
            "reset_token_expires": {"$gt": datetime.datetime.now(datetime.UTC).timestamp()}
        })
        
        if not user:
            return jsonify({"message": "Invalid or expired reset token"}), 400
     
        hashed_password = generate_password_hash(new_password)
        usersCollection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"password": hashed_password},
                "$unset": {"reset_token": "", "reset_token_expires": ""}
            }
        )
        
        Log(f"Password reset successful for user {user['username']}", "success")
        
        return jsonify({"message": "Password reset successful. You can now log in."}), 200
  
    user = usersCollection.find_one({
        "reset_token": token,
        "reset_token_expires": {"$gt": datetime.datetime.now(datetime.UTC).timestamp() }
    })
    
    if not user:
        return render_template("pages/resetPasswordConfirm.html", valid=False)
    
    return render_template("pages/resetPasswordConfirm.html", valid=True, token=token)

@app.route('/api/next-action', methods=['GET'])
@login_required
@limiter.limit("30 per hour")
def nextAction():
    try:
        return jsonify(GetNextAction())
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

@app.route('/dist/<path:filename>')
def serveDist(filename):
    dist_folder = os.path.join(app.root_path, 'dist')
    return send_from_directory(dist_folder, filename)

@app.route("/delete-account", methods=['POST'], endpoint='deleteAccount')
@login_required
@limiter.limit("5 per hour")
def deleteAccount():
    data = request.get_json()
    password = data.get('password', '').strip()
    confirm_text = data.get('confirm', '').strip()
    
    if not password:
        return jsonify({"error": "Password is required"}), 400
    
    if confirm_text != "DELETE":
        return jsonify({"error": "Please type DELETE to confirm"}), 400
    
    user = GetMongoClient()["EduDuck"]["users"].find_one(
        {"_id": ObjectId(current_user.id)}
    )
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.get("password"):
        if not check_password_hash(user["password"], password):
            return jsonify({"error": "Incorrect password"}), 401
    else:
        return jsonify({"error": "OAuth users must set a password first"}), 403
    
    try:
        db = GetMongoClient()["EduDuck"]
        user_id = current_user.id
        now = datetime.datetime.now(datetime.UTC)
        
        db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"deletedAt": now}}
        )
        db["quizzes"].update_many(
            {"userID": user_id},
            {"$set": {"deletedAt": now}}
        )
        db["study-plans"].update_many(
            {"userID": user_id},
            {"$set": {"deletedAt": now}}
        )
        db["flashcards"].update_many(
            {"userID": user_id},
            {"$set": {"deletedAt": now}}
        )
        db["enhanced-notes"].update_many(
            {"userID": user_id},
            {"$set": {"deletedAt": now}}
        )
        db["duck-ai"].update_many(
            {"userID": user_id},
            {"$set": {"deletedAt": now}}
        )
      
        if user.get("profilePicture"):
            try:
                s3.delete_object(Bucket=R2_BUCKET_NAME, Key=user["profilePicture"])
            except Exception as e:
                Log(f"Failed to delete profile picture: {str(e)}", "warning")
        
        Log(f"Account soft-deleted: {user['username']}", "info")

        logout_user()
        
        return jsonify({"success": True, "message": "Account deleted successfully. Data retained for recovery."}), 200
        
    except Exception as e:
        Log(f"Failed to soft-delete account: {str(e)}", "error")
        return jsonify({"error": "Failed to delete account"}), 500

# ---------------- Quiz Generator ------------------------
@app.route('/quiz-generator/quiz/result', methods=['POST' , 'GET'], endpoint='QuizResult')
@limiter.exempt
def submitResult():
    if request.method == 'POST':
        return _submitResult_(quizResults)

    return QuizResult(quizResults, RemainingUsage)

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
    return _quiz_(quizzes, RemainingUsage)

@app.route('/quiz-generator', endpoint='quizGeneratorPage')
@limiter.exempt
def QuizGenerator():
    return _QuizGenerator_(RemainingUsage)

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
    return render_template("Study Plan Generator/studyPlanGenerator.html", remaining=RemainingUsage() , prefill_topic=request.args.get('topic', '').strip())

@app.route('/study-plan-generator/generate' , endpoint='StudyPlanGenerate' , methods=['POST'])
@limiter.limit("30 per hour")
def studyPlanGen():
    return StudyPlanGen(prompts , studyPlans)

@app.route('/study-plan-generator/result' , endpoint='StudyPlanResult')
@limiter.exempt
def StudyPlanResult():
    return StudyPlan(studyPlans, RemainingUsage)

@app.route('/study-plan-generator/export-plan' , endpoint='studyPlanExport')
@limiter.exempt
def ExportPlan():
    return ExportStudyPlan(studyPlans)

@app.route('/study-plan-generator/import-plan' , methods=['POST'] , endpoint='StudyPlanImport')
@limiter.exempt
def ImportPlan():
    return ImportStudyPlan(studyPlans)
# ---------------- Note Analyzer ------------------------

@app.route("/note-analyzer", endpoint="noteAnalyzerPage")
@limiter.exempt
def noteAnalyzerPage():
    return NoteAnalyzerPageRoute()

@app.route("/note-analyzer/analyze", methods=["POST"], endpoint="noteAnalyzerAnalyze")
@limiter.limit("30 per hour")
def noteAnalyzerAnalyze():
    return NoteAnalyzerRoute(prompts, noteAnalyses)

@app.route("/note-analyzer/result", endpoint="noteAnalyzerResult")
@limiter.exempt
def noteAnalyzerResult():
    return NoteAnalysisResultRoute(noteAnalyses)

@app.route("/note-analyzer/import-analysis", methods=["POST"], endpoint="noteAnalyzerImport")
@limiter.exempt
def noteAnalyzerImport():
    return ImportNoteAnalysisRoute(noteAnalyses)

@app.route("/note-analyzer/export-analysis", endpoint="noteAnalyzerExport")
@limiter.exempt
def noteAnalyzerExport():
    return ExportNoteAnalysisRoute(noteAnalyses)

# ---------------- Miscellanious ------------------------
@app.route("/keyAccess")
@limiter.exempt
def keyAccess():
    return render_template("pages/keyAccess.html")

@app.route("/profile")
@limiter.exempt
@CheckPasswordSetup
@login_required
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

@app.route('/.well-known/microsoft-identity-association.json')
@limiter.exempt
def microsoft_identity_association():
    return send_from_directory('static', 'microsoft-identity-association.json')

if __name__ == "__main__":
    app.run()
