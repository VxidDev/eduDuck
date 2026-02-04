from authlib.integrations.flask_client import OAuth
from flask import Blueprint, redirect, url_for, flash, render_template
from flask_login import login_user, current_user
from routes.utils import LoadUser, GetMongoClient, User
from authlib.integrations.base_client.errors import OAuthError
import secrets, os
from datetime import date
from dotenv import load_dotenv
from jwt import decode as jwt_decode

load_dotenv()

oauth = OAuth()

google = oauth.register(
    name='google',
    client_id=os.environ['GOOGLE_CLIENT_ID'],
    client_secret=os.environ['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

github = oauth.register(
    name='github',
    client_id=os.environ['GITHUB_CLIENT_ID'],
    client_secret=os.environ['GITHUB_CLIENT_SECRET'],
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'read:user user:email'},
)

discord = oauth.register(
    name='discord',
    client_id=os.environ['DISCORD_CLIENT_ID'],
    client_secret=os.environ['DISCORD_CLIENT_SECRET'],
    access_token_url='https://discord.com/api/oauth2/token',
    authorize_url='https://discord.com/oauth2/authorize',
    api_base_url='https://discord.com/api/',
    client_kwargs={'scope': 'identify email'},
)

microsoft = oauth.register(
    name='microsoft',
    client_id=os.environ['MICROSOFT_CLIENT_ID'],
    client_secret=os.environ['MICROSOFT_CLIENT_SECRET'],
    server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
    },
    authorize_params={
        'response_type': 'code',
    },
    token_endpoint_auth_method='client_secret_post',
)

oauthBp = Blueprint("oauth", __name__)

@oauthBp.route("/login/google")
def loginGoogle():
    if current_user.is_authenticated:
        return redirect(url_for("root"))
    redirectUri = url_for("oauth.authorizeGoogle", _external=True)
    return google.authorize_redirect(redirectUri)

@oauthBp.route("/authorize/google")
def authorizeGoogle():
    try:
        token = google.authorize_access_token()
    except OAuthError as e:
        if e.error == 'access_denied':
            flash('Google login was cancelled.', 'warning')
        else:
            flash(f'Google login failed: {e.description or e.error}', 'error')
        return redirect(url_for("login"))
    
    info = google.userinfo()
    googleId = info['sub']

    usersCollection = GetMongoClient()["EduDuck"]["users"]

    userDoc = LoadUser(googleId=googleId)

    if userDoc:
        if userDoc.get("deletedAt"):
            flash('This account has been deleted. Please contact support to restore it.', 'error')
            return redirect(url_for("login"))
        user = User(userDoc)
    else:
        userDoc = usersCollection.find_one({
            "email": info.get("email").lower(),
            "deletedAt": {"$exists": False}
        })
        if not userDoc:
            userDoc = {
                "username": info.get("name").lower() if info.get("name") else info.get("email").split("@")[0],
                "email": info.get("email").lower(),
                "password": None,
                "googleId": googleId,
                "needs_password_setup": True, 
                "daily_usage": {
                    "date": date.today().isoformat(),
                    "timesUsed": 0
                }
            }
            result = usersCollection.insert_one(userDoc)
        else:
            usersCollection.update_one(
                {"_id": userDoc["_id"]},
                {"$set": {"googleId": googleId}}
            )

        user = User(userDoc)

    login_user(user)
    return redirect(url_for("root"))

@oauthBp.route("/login/github")
def loginGithub():
    if current_user.is_authenticated:
        return redirect(url_for("root"))
    redirectUri = url_for("oauth.authorizeGithub", _external=True)
    return github.authorize_redirect(redirectUri)

@oauthBp.route("/authorize/github")
def authorizeGithub():
    try:
        token = github.authorize_access_token()
    except OAuthError as e:
        if e.error == 'access_denied':
            flash('GitHub login was cancelled.', 'warning')
        else:
            flash(f'GitHub login failed: {e.description or e.error}', 'error')
        return redirect(url_for("login"))
    
    try:
        resp = github.get('user', token=token)
        resp.raise_for_status()
        info = resp.json()

        emailResp = github.get('user/emails', token=token)
        emailResp.raise_for_status()
        emails = emailResp.json()
        primaryEmail = next((e['email'] for e in emails if e['primary']), None)
    except Exception as e:
        flash(f'Failed to fetch GitHub user data: {str(e)}', 'error')
        return redirect(url_for("login"))
    
    githubId = str(info['id'])

    usersCollection = GetMongoClient()["EduDuck"]["users"]

    userDoc = LoadUser(githubId=githubId)

    if userDoc:
        if userDoc.get("deletedAt"):
            flash('This account has been deleted. Please contact support to restore it.', 'error')
            return redirect(url_for("login"))
        user = User(userDoc)
    else:
        userDoc = usersCollection.find_one({
            "email": primaryEmail.lower(), 
            "deletedAt": {"$exists": False}
        }) if primaryEmail else None
        if not userDoc:
            userDoc = {
                "username": info.get("login").lower(),
                "email": primaryEmail.lower() if primaryEmail else None,
                "password": None,
                "githubId": githubId,
                "needs_password_setup": True,
                "daily_usage": {
                    "date": date.today().isoformat(),
                    "timesUsed": 0
                }
            }
            result = usersCollection.insert_one(userDoc)
        else:
            usersCollection.update_one(
                {"_id": userDoc["_id"]},
                {"$set": {"githubId": githubId}}
            )

        user = User(userDoc)

    login_user(user)
    return redirect(url_for("root"))

@oauthBp.route("/login/discord")
def loginDiscord():
    if current_user.is_authenticated:
        return redirect(url_for("root"))
    redirectUri = url_for("oauth.authorizeDiscord", _external=True)
    return discord.authorize_redirect(redirectUri)

@oauthBp.route("/authorize/discord")
def authorizeDiscord():
    try:
        token = discord.authorize_access_token()
    except OAuthError as e:
        if e.error == 'access_denied':
            flash('Discord login was cancelled.', 'warning')
        else:
            flash(f'Discord login failed: {e.description or e.error}', 'error')
        return redirect(url_for("login"))
    
    try:
        resp = discord.get('users/@me', token=token)
        resp.raise_for_status()
        info = resp.json()
    except Exception as e:
        flash(f'Failed to fetch Discord user data: {str(e)}', 'error')
        return redirect(url_for("login"))
    
    discordId = str(info['id'])
    email = info.get('email')
    username = info.get('username')

    usersCollection = GetMongoClient()["EduDuck"]["users"]

    userDoc = LoadUser(discordId=discordId)

    if userDoc:
        if userDoc.get("deletedAt"):
            flash('This account has been deleted. Please contact support to restore it.', 'error')
            return redirect(url_for("login"))
        user = User(userDoc)
    else:
        userDoc = usersCollection.find_one({
            "email": email.lower(),
            "deletedAt": {"$exists": False}
        }) if email else None
        if not userDoc:
            userDoc = {
                "username": username.lower() if username else f"discord_{discordId[:8]}",
                "email": email.lower() if email else None,
                "password": None,
                "discordId": discordId,
                "needs_password_setup": True,
                "daily_usage": {
                    "date": date.today().isoformat(),
                    "timesUsed": 0
                }
            }
            result = usersCollection.insert_one(userDoc)
        else:
            usersCollection.update_one(
                {"_id": userDoc["_id"]},
                {"$set": {"discordId": discordId}}
            )

        user = User(userDoc)

    login_user(user)
    return redirect(url_for("root"))

@oauthBp.route("/login/microsoft")
def loginMicrosoft():
    if current_user.is_authenticated:
        return redirect(url_for("root"))
    redirectUri = url_for("oauth.authorizeMicrosoft", _external=True)
    return microsoft.authorize_redirect(redirectUri)

@oauthBp.route("/authorize/microsoft")
def authorizeMicrosoft():
    try:
        token = microsoft.authorize_access_token(
            claims_options={
                'iss': {'essential': False} 
            }
        )
    except OAuthError as e:
        if e.error == 'access_denied':
            flash('Microsoft login was cancelled.', 'warning')
        else:
            flash(f'Microsoft login failed: {e.description or e.error}', 'error')
        return redirect(url_for("login"))
    
    try:
        info = microsoft.parse_id_token(token, claims_options={'iss': {'essential': False}})
    except Exception:
        info = jwt_decode(token['id_token'], options={"verify_signature": False})
    
    microsoftId = info['sub']

    usersCollection = GetMongoClient()["EduDuck"]["users"]

    userDoc = LoadUser(microsoftId=microsoftId)

    if userDoc:
        if userDoc.get("deletedAt"):
            flash('This account has been deleted. Please contact support to restore it.', 'error')
            return redirect(url_for("login"))
        user = User(userDoc)
    else:
        userDoc = usersCollection.find_one({
            "email": info.get("email").lower(),
            "deletedAt": {"$exists": False}
        })
        if not userDoc:
            userDoc = {
                "username": info.get("name").lower() if info.get("name") else info.get("email").split("@")[0],
                "email": info.get("email").lower(),
                "password": None,
                "microsoftId": microsoftId,
                "needs_password_setup": True,
                "daily_usage": {
                    "date": date.today().isoformat(),
                    "timesUsed": 0
                }
            }
            result = usersCollection.insert_one(userDoc)
        else:
            usersCollection.update_one(
                {"_id": userDoc["_id"]},
                {"$set": {"microsoftId": microsoftId}}
            )

        user = User(userDoc)

    login_user(user)
    return redirect(url_for("root"))
