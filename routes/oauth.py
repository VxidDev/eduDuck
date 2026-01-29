from authlib.integrations.flask_client import OAuth
from flask import Blueprint, redirect, url_for
from flask_login import login_user, current_user
from routes.utils import LoadUser, GetMongoClient, User
import secrets, os
from datetime import date

oauth = OAuth()

google = oauth.register(
    name='google',
    client_id=os.environ['GOOGLE_CLIENT_ID'],
    client_secret=os.environ['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
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
    token = google.authorize_access_token()
    info = google.userinfo()
    googleId = info['sub']

    usersCollection = GetMongoClient()["EduDuck"]["users"]

    userDoc = LoadUser(googleId=googleId)

    if userDoc:
        user = User(userDoc)
    else:
        userDoc = usersCollection.find_one({"email": info.get("email").lower()})
        if not userDoc:
            userDoc = {
                "username": info.get("name").lower() if info.get("name") else info.get("email").split("@")[0],
                "email": info.get("email").lower(),
                "password": None,
                "googleId": googleId,
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
