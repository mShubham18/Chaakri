import os
import requests
import secrets
import base64
import hashlib
from flask import Flask, redirect, request, session, url_for

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_CLIENT_ID = os.getenv("CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "http://127.0.0.1:5000/callback"


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")


# Generate PKCE Code Verifier & Code Challenge
def generate_pkce_pair():
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")
    return code_verifier, code_challenge

@app.route("/")
def home():
    print(f"🔎 Current session: {session}")  # Debugging
    if "user" in session:
        return f"✅ Logged in as {session['user']['email']}! <a href='/logout'>Logout</a>"
    return "<a href='/login'>Login with Google</a>"

@app.route("/login")
def login():
    code_verifier, code_challenge = generate_pkce_pair()
    session["code_verifier"] = code_verifier  # Store code_verifier in session

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"  # Ensuring it's Authorization Code Flow
        f"&scope=openid email profile"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
        f"&access_type=offline"  # Ensures we get a refresh token
        f"&prompt=consent"  # Forces user consent to avoid silent failures
    )

    return redirect(google_auth_url)


@app.route("/callback")
def callback():
    if "error" in request.args:
        return f"Error: {request.args['error']}", 400

    code = request.args.get("code")
    if not code:
        return "Authorization failed!", 400

    # Exchange authorization code for access token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code_verifier": session["code_verifier"],
    }

    response = requests.post(token_url, data=data)
    token_data = response.json()

    if "access_token" not in token_data:
        return f"Token exchange failed: {token_data}", 400

    # Store user session
    session["access_token"] = token_data["access_token"]
    session["id_token"] = token_data.get("id_token")
    session["refresh_token"] = token_data.get("refresh_token")

    return f"Login successful! Token: {token_data['access_token']}"

if __name__ == "__main__":
    app.run(debug=True)
