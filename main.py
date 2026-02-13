# Standard library imports
import os
import secrets
import atexit
import datetime
from json import load, JSONDecodeError
from functools import wraps
from uuid import uuid4
import re

# Third-party library imports
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, send_from_directory, redirect, url_for, request, jsonify, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, login_required, current_user, logout_user
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel, get_locale
from flask_babel import gettext as _
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

# Local application imports
from routes.utils import (
    LoginUser, RegisterUser, User, LoadUser, SendEmail, VerifyEmail, UserProfile,
    GetMongoClient, GetUserPFP, LoadUserByMail, LoadUserByUsername, CheckPasswordSetup,
    GetStudyStreakData, GetNextAction, IncrementUsage, GetUsage, uploadNotes,
    StoreQuery, StoreDuckAIConversation, GetQueryFromDB, Log, cleanup
)
from routes.quiz import (
    QuizGenerator, quiz, submitResult, QuizGen, ImportQuiz, ExportQuiz, QuizResult
)
from routes.noteEnhancer import (
    EnhanceNotes, NoteEnhancer, EnhancedNotes, ImportNotes as ImportEnhancedNotes,
    ExportNotes as ExportEnhancedNotes
)
from routes.flashcardGenerator import (
    FlashCardGenerator, FlashcardGenerator, FlashCardResult,
    ImportFlashcards, ExportFlashcards
)
from routes.duckAI import GenerateResponse, DuckAI
from routes.studyPlanGenerator import StudyPlanGen, StudyPlan, ExportStudyPlan, ImportStudyPlan
from routes.noteAnalyzer import (
    NoteAnalyzer, NoteAnalyzerPage, NoteAnalysisResult,
    ImportNoteAnalysis, ExportNoteAnalysis
)
from routes.oauth import oauthBp, oauth

load_dotenv()

#
# Core App Setup
#

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2.5 * 1024 * 1024
app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key or len(app.secret_key) < 32:
    raise RuntimeError("Invalid SECRET_KEY")

csrf = CSRFProtect(app)

def determine_request_locale():
    # Try to get the language from a cookie
    lang = request.cookies.get('lang')
    Log(f"determine_request_locale called. Cookie 'lang' value: {lang}", "info")
    if lang:
        return lang
    # Try to guess the language from the user accept header first
    # Otherwise, use a default language (e.g., 'en')
    return request.accept_languages.best_match(['en', 'pl', 'uk', 'fr', 'ru', 'de'])

babel = Babel(app , locale_selector=determine_request_locale)
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

@app.context_processor
def inject_babel_globals():
    current_locale = get_locale()
    Log(f"inject_babel_globals: Setting template 'locale' to: {current_locale}", "info")
    return dict(_=_, locale=current_locale)

# In-memory data stores (temporary solution)
notes = {}
quizzes = {}
flashcards = {}
studyPlans = {}
quizResults = {}
noteAnalyses = {}

#
# Rate Limiting
#

def rate_limit_key() -> str:
    if current_user.is_authenticated:
        return f"user:{current_user.get_id()}"
    return get_remote_address()

limiter = Limiter(
    app=app,
    key_func=rate_limit_key,
    default_limits=[],
    storage_uri="memory://"
)

#
# Middleware and Blueprints
#

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
oauth.init_app(app)
csrf.exempt(oauthBp)
app.register_blueprint(oauthBp)

#
# Login Manager
#

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    user_doc = LoadUser(userID=user_id)
    if not user_doc:
        return None
    return User(user_doc)

#
# Prompts
#

try:
    with open("prompts.json", "r") as file:
        prompts = load(file)
except (FileNotFoundError, JSONDecodeError):
    prompts = None
    print("Failed to load prompts.")

if not prompts:
    raise RuntimeError("Failed to load prompts.")

#
# Cloudflare R2 Configuration
#

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

#
# Database TTL Indexes
#

def setup_ttl_indexes():
    db = GetMongoClient()["EduDuck"]
    collections = [
        "users", "quizzes", "study-plans", "flashcards",
        "enhanced-notes", "duck-ai", "note-analysis"
    ]
    for collection_name in collections:
        try:
            db.collection.create_index(
                [("deletedAt", 1)], 
                expireAfterSeconds=2592000,
                partialFilterExpression={"deleted": True},  # Matches existing
                name="deletedAt_1"
            )
            Log(f"TTL index created for {collection_name}", "info")
        except Exception as e:
            if "already exists" in str(e):
                Log(f"TTL index already exists for {collection_name}", "info")
            else:
                Log(f"Failed to create TTL index for {collection_name}: {str(e)}", "warn")

setup_ttl_indexes()

#
# Cleanup
#

atexit.register(cleanup)

#
# Helper Functions
#

def remaining_usage():
    return GetUsage().get_json().get("remaining", 3) if current_user.is_authenticated else 3

def allowed_profile_pic_extensions(filename):
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def api_login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify(error="Unauthorized"), 401
        return func(*args, **kwargs)
    return wrapper

#
# Core Routes
#

@app.route("/", methods=['GET'])
@limiter.exempt
def root():
    return render_template("pages/index.html", remaining=remaining_usage())

@app.route("/upload-notes", methods=['POST'], endpoint='upload_notes')
@limiter.exempt
def upload_notes():
    return uploadNotes()

#
# Authentication
#

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
        if isinstance(result, tuple) and isinstance(result[0], tuple):
            msg, email = result
            try:
                SendEmail(
                    to_email=msg[1],
                    subject=msg[0],
                    verification_link=msg[2],
                    from_email="EduDuck Verification <no-reply@mg.eduduck.app>",
                    html_content=render_template("pages/email.html", VERIFY_URL=msg[2])
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

@app.route("/logout", methods=["GET"])
@limiter.exempt
def logout():
    logout_user()
    return redirect(url_for("root"))

@app.route("/verify-email/<token>")
@limiter.exempt
def verify_email(token):
    return VerifyEmail(token)

@app.route("/check-email")
@limiter.exempt
def check_email():
    email = request.args.get("email", "")
    return render_template("pages/checkEmail.html", email=email)

@app.route("/is-logined-in", methods=["GET"])
@limiter.exempt
def check_login():
    return jsonify({"login": current_user.is_authenticated})

#
# Password Management
#

@app.route("/setup-password", methods=['GET', 'POST'])
@login_required
def setup_password():
    if request.method == 'POST':
        data = request.get_json()
        new_password = data.get('password', '').strip()
        confirm = data.get('confirm', '').strip()

        if len(new_password) < 8:
            return jsonify({"message": "Password must be at least 8 characters"}), 400
        if new_password != confirm:
            return jsonify({"message": "Passwords do not match"}), 400

        hashed = generate_password_hash(new_password)
        users_collection = GetMongoClient()["EduDuck"]["users"]
        users_collection.update_one(
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


@app.route("/reset-password", methods=['GET', 'POST'])
@limiter.exempt
def reset_password():
    if request.method == 'POST':
        data = request.get_json()
        username_or_email = data.get('username_email', '').strip()

        if not username_or_email:
            return jsonify({"message": "Please provide a username or email"}), 400

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_email_input = re.fullmatch(email_pattern, username_or_email) is not None

        user = LoadUserByMail(username_or_email) if is_email_input else LoadUserByUsername(username_or_email)

        if not user:
            return jsonify({"message": "If an account exists, a reset link has been sent."}), 200

        reset_token = secrets.token_urlsafe(32)
        users_collection = GetMongoClient()["EduDuck"]["users"]
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "reset_token": reset_token,
                    "reset_token_expires": datetime.datetime.now(datetime.UTC).timestamp() + 3600
                }
            }
        )

        reset_url = url_for('reset_password_confirm', token=reset_token, _external=True)

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

        return jsonify({"message": "If an account exists, a reset link has been sent."}), 200

    return render_template("pages/resetPassword.html")


@app.route("/reset-password/<token>", methods=['GET', 'POST'])
@limiter.exempt
def reset_password_confirm(token):
    users_collection = GetMongoClient()["EduDuck"]["users"]

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

        user = users_collection.find_one({
            "reset_token": token,
            "reset_token_expires": {"$gt": datetime.datetime.now(datetime.UTC).timestamp()}
        })

        if not user:
            return jsonify({"message": "Invalid or expired reset token"}), 400

        hashed_password = generate_password_hash(new_password)
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"password": hashed_password},
                "$unset": {"reset_token": "", "reset_token_expires": ""}
            }
        )

        Log(f"Password reset successful for user {user['username']}", "success")
        return jsonify({"message": "Password reset successful. You can now log in."}), 200

    user = users_collection.find_one({
        "reset_token": token,
        "reset_token_expires": {"$gt": datetime.datetime.now(datetime.UTC).timestamp()}
    })

    return render_template("pages/resetPasswordConfirm.html", valid=bool(user), token=token)

#
# User Profile & Settings
#

@app.route("/profile")
@limiter.exempt
@CheckPasswordSetup
@login_required
def profile():
    return UserProfile()

@app.route("/profile/upload-profile-picture", methods=['POST'])
@limiter.limit("30 per hour")
@login_required
def upload_profile_picture():
    if 'profile_picture' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['profile_picture']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_profile_pic_extensions(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 2.5 * 1024 * 1024:  # 2.5 MB
        return jsonify({"error": "File too large, max 2.5 MB"}), 400

    user_id = current_user.id
    filename = f"{uuid4().hex}_{secure_filename(file.filename)}"
    key = f"users/{user_id}/{filename}"

    try:
        user = GetMongoClient()["EduDuck"]["users"].find_one({"_id": ObjectId(user_id)})
        if user and "profilePicture" in user:
            try:
                s3.delete_object(Bucket=R2_BUCKET_NAME, Key=user["profilePicture"])
            except ClientError as ce:
                Log(f"Failed to delete old profile picture -> {str(ce)}", "warning")

        file.seek(0)
        s3.upload_fileobj(
            Fileobj=file,
            Bucket=R2_BUCKET_NAME,
            Key=key,
            ExtraArgs={'ContentType': file.content_type or 'application/octet-stream', 'ACL': 'public-read'}
        )
    except Exception as e:
        Log(f"Failed to upload profile picture to R2 -> {str(e)}", "error")
        return jsonify({"error": f"Failed to upload file: {str(e)}"}), 500

    try:
        GetMongoClient()["EduDuck"]["users"].find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": {"profilePicture": key}}
        )
    except Exception as e:
        Log(f"Failed to update user profile picture URL in MongoDB -> {str(e)}", "error")
        try:
            s3.delete_object(Bucket=R2_BUCKET_NAME, Key=key)
        except ClientError as ce:
            Log(f"Failed to delete orphaned R2 file -> {str(ce)}", "error")
        return jsonify({"error": f"Failed to update database: {str(e)}"}), 500

    return jsonify({"url": f"{R2_ENDPOINT_URL}/{key}"})


@app.route("/profile/user-pfp", methods=['GET'])
@limiter.limit("60 per hour")
@login_required
def get_user_pfp():
    return GetUserPFP()

@app.route("/settings", methods=['GET'])
@CheckPasswordSetup
@login_required
@limiter.exempt
def user_settings():
    return render_template("pages/userSettings.html")

@app.route("/delete-account", methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def delete_account():
    data = request.get_json()
    password = data.get('password', '').strip()
    confirm_text = data.get('confirm', '').strip()

    if not password:
        return jsonify({"error": "Password is required"}), 400
    if confirm_text != "DELETE":
        return jsonify({"error": "Please type DELETE to confirm"}), 400

    user = GetMongoClient()["EduDuck"]["users"].find_one({"_id": ObjectId(current_user.id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.get("password") or not check_password_hash(user["password"], password):
        return jsonify({"error": "Incorrect password or password not set for OAuth user"}), 401

    try:
        db = GetMongoClient()["EduDuck"]
        user_id = current_user.id
        now = datetime.datetime.now(datetime.UTC)
        deletion_update = {"$set": {"deletedAt": now}}

        db["users"].update_one({"_id": ObjectId(user_id)}, deletion_update)
        db["quizzes"].update_many({"userID": user_id}, deletion_update)
        db["study-plans"].update_many({"userID": user_id}, deletion_update)
        db["flashcards"].update_many({"userID": user_id}, deletion_update)
        db["enhanced-notes"].update_many({"userID": user_id}, deletion_update)
        db["duck-ai"].update_many({"userID": user_id}, deletion_update)

        if user.get("profilePicture"):
            try:
                s3.delete_object(Bucket=R2_BUCKET_NAME, Key=user["profilePicture"])
            except Exception as e:
                Log(f"Failed to delete profile picture during account deletion: {str(e)}", "warning")

        Log(f"Account soft-deleted: {user['username']}", "info")
        logout_user()
        return jsonify({"success": True, "message": "Account deleted. Data will be retained for 30 days."}), 200

    except Exception as e:
        Log(f"Failed to soft-delete account: {str(e)}", "error")
        return jsonify({"error": "Failed to delete account"}), 500

#
# API & Data Routes
#

@app.route("/set-language", methods=["POST"])
@limiter.exempt
def set_language():
    lang = request.form.get("lang")
    if lang in ['en', 'pl', 'uk', 'fr', 'ru', 'de']: # Ensure lang is valid
        Log(f"Attempting to set language cookie to: {lang}", "info")
        response = make_response(redirect(request.referrer or url_for("root")))
        response.set_cookie("lang", lang, max_age=365 * 24 * 60 * 60, path='/')
        Log(f"Language cookie set for: {lang}", "info")
        return response
    return redirect(request.referrer or url_for("root"))

@app.route("/store-query", endpoint="store_query")
@limiter.limit("100 per hour")
@api_login_required
def store_query():
    data = request.get_json()
    query_name = data.get("queryName")
    response = StoreQuery(query_name, data.get(query_name))
    if response not in ["unknown qName", "empty query payload"]:
        return jsonify({"id": response})
    return jsonify({"error": response})

@app.route("/get-query", methods=['POST'])
@limiter.limit("200 per hour")
@api_login_required
def get_query():
    data = request.get_json()
    return GetQueryFromDB(data.get('queryID'), data.get('collection'))

@app.route("/api/study-streak", methods=["GET"])
@login_required
@limiter.limit("60 per hour")
def get_study_streak():
    days = request.args.get("days", 365, type=int)
    data = GetStudyStreakData(current_user.id, days)
    return jsonify(data)

@app.route('/api/next-action', methods=['GET'])
@login_required
@limiter.limit("30 per hour")
def next_action():
    try:
        return jsonify(GetNextAction())
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

@app.route("/get-usage")
@api_login_required
@limiter.limit("200 per hour")
def get_usage():
    return GetUsage()

@app.route("/increment-usage")
@api_login_required
@limiter.limit("200 per hour")
def increment_usage():
    return IncrementUsage()

#
# Quiz Generator
#

@app.route('/quiz-generator', endpoint='quiz_generator_page')
@limiter.exempt
def quiz_generator():
    return QuizGenerator(remaining_usage)

@app.route('/quiz-generator/gen-quiz', methods=['POST'], endpoint='generate_quiz')
@limiter.limit("30 per hour")
def quiz_gen():
    return QuizGen(prompts, quizzes)

@app.route("/quiz-generator/quiz", endpoint='show_quiz')
@limiter.exempt
def show_quiz():
    return quiz(quizzes, remaining_usage)

@app.route('/quiz-generator/quiz/result', methods=['POST', 'GET'], endpoint='quiz_result')
@limiter.exempt
def quiz_result():
    if request.method == 'POST':
        return submitResult(quizResults)
    return QuizResult(quizResults, remaining_usage)

@app.route('/quiz-generator/import-quiz', methods=['POST'], endpoint='import_quiz')
@limiter.exempt
def import_quiz():
    return ImportQuiz(quizzes)

@app.route('/quiz-generator/export-quiz', endpoint='export_quiz')
@limiter.exempt
def export_quiz():
    return ExportQuiz(quizzes)

#
# Note Enhancer
#

@app.route('/note-enhancer', endpoint='note_enhancer_page')
@limiter.exempt
def note_enhancer():
    return NoteEnhancer()

@app.route('/note-enhancer/enhance', methods=['POST'], endpoint='enhance_notes')
@limiter.limit("30 per hour")
def enhance_notes():
    return EnhanceNotes(prompts, notes)

@app.route('/note-enhancer/result', endpoint='enhanced_notes_result')
@limiter.exempt
def enhanced_notes():
    return EnhancedNotes(notes)

@app.route('/note-enhancer/import-notes', methods=['POST'], endpoint='import_enhanced_notes')
@limiter.exempt
def import_enhanced_notes():
    return ImportEnhancedNotes(notes)

@app.route('/note-enhancer/export-notes', endpoint='export_enhanced_notes')
@limiter.exempt
def export_enhanced_notes():
    return ExportEnhancedNotes(notes)

#
# FlashCard Generator
#

@app.route('/flashcard-generator', endpoint='flashcard_generator_page')
@limiter.exempt
def flashcard_generator_page():
    return FlashCardGenerator()

@app.route('/flashcard-generator/generate', methods=['POST'], endpoint='generate_flashcards')
@limiter.limit("30 per hour")
def generate_flashcards():
    return FlashcardGenerator(prompts, flashcards)

@app.route('/flashcard-generator/result', endpoint='flashcard_result')
@limiter.exempt
def flashcard_result():
    return FlashCardResult(flashcards)

@app.route('/flashcard-generator/import-flashcards', methods=['POST'], endpoint='import_flashcards')
@limiter.exempt
def import_flashcards():
    return ImportFlashcards(flashcards)

@app.route('/flashcard-generator/export-flashcards', endpoint='export_flashcards')
@limiter.exempt
def export_flashcards():
    return ExportFlashcards(flashcards)

#
# DuckAI
#

@app.route('/duck-ai', endpoint='duck_ai_page')
@limiter.exempt
def duck_ai_page():
    return DuckAI()

@app.route('/duck-ai/generate', methods=['POST'], endpoint='duck_ai_generate')
@limiter.limit("30 per hour")
def duck_ai_generate():
    return GenerateResponse(prompts)

@app.route('/duck-ai/store-conversation', methods=['POST'], endpoint='duck_ai_store_conversation')
@login_required
@limiter.limit("100 per hour")
def duck_ai_store_conversation():
    data = request.get_json()
    return jsonify({"queryID": StoreDuckAIConversation(data.get("messages"), data.get("queryID"))})

#
# Study Plan Generator
#

@app.route('/study-plan-generator', endpoint='study_plan_generator_page')
@limiter.exempt
def study_plan_generator_page():
    return render_template(
        "Study Plan Generator/studyPlanGenerator.html",
        remaining=remaining_usage(),
        prefill_topic=request.args.get('topic', '').strip()
    )

@app.route('/study-plan-generator/generate', methods=['POST'], endpoint='generate_study_plan')
@limiter.limit("30 per hour")
def generate_study_plan():
    return StudyPlanGen(prompts, studyPlans)

@app.route('/study-plan-generator/result', endpoint='study_plan_result')
@limiter.exempt
def study_plan_result():
    return StudyPlan(studyPlans, remaining_usage)

@app.route('/study-plan-generator/export-plan', endpoint='export_study_plan')
@limiter.exempt
def export_study_plan():
    return ExportStudyPlan(studyPlans)

@app.route('/study-plan-generator/import-plan', methods=['POST'], endpoint='import_study_plan')
@limiter.exempt
def import_study_plan():
    return ImportStudyPlan(studyPlans)

#
# Note Analyzer
#

@app.route("/note-analyzer", endpoint="note_analyzer_page")
@limiter.exempt
def note_analyzer_page():
    return NoteAnalyzerPage()

@app.route("/note-analyzer/analyze", methods=["POST"], endpoint="note_analyzer_analyze")
@limiter.limit("30 per hour")
def note_analyzer_analyze():
    return NoteAnalyzer(prompts, noteAnalyses)

@app.route("/note-analyzer/result", endpoint="note_analyzer_result")
@limiter.exempt
def note_analyzer_result():
    return NoteAnalysisResult(noteAnalyses)

@app.route("/note-analyzer/import-analysis", methods=["POST"], endpoint="note_analyzer_import")
@limiter.exempt
def note_analyzer_import():
    return ImportNoteAnalysis(noteAnalyses)

@app.route("/note-analyzer/export-analysis", endpoint="note_analyzer_export")
@limiter.exempt
def export_note_analysis():
    return ExportNoteAnalysis(noteAnalyses)

#
# Static & Miscellaneous Routes
#

@app.route('/dist/<path:filename>')
def serve_dist(filename):
    dist_folder = os.path.join(app.root_path, 'dist')
    return send_from_directory(dist_folder, filename)

@app.route("/keyAccess")
@limiter.exempt
def key_access():
    return render_template("pages/keyAccess.html")

@app.route('/sitemap.xml')
@limiter.exempt
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/robots.txt')
@limiter.exempt
def robots():
    # It's better to have a robots.txt file, but this is a simple alternative
    return "User-agent: *\nDisallow:"

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