import os
import requests
import secrets
import base64
import hashlib
from flask import Blueprint, redirect, request, session, url_for
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "http://127.0.0.1:5000/callback"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

auth = Blueprint("auth", __name__)

# Generate PKCE Code Verifier & Code Challenge
def generate_pkce_pair():
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")
    return code_verifier, code_challenge

@auth.route("/login")
def login():
    code_verifier, code_challenge = generate_pkce_pair()
    session["code_verifier"] = code_verifier  # Store code_verifier in session

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
        f"&access_type=offline"
        f"&prompt=consent"
    )

    return redirect(google_auth_url)

@auth.route("/callback")
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

    access_token = token_data["access_token"]

    # Fetch user info from Google
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_info_response = requests.get(user_info_url, headers=headers)
    user_data = user_info_response.json()

    # Store user info in session
    session["user"] = user_data

    # Save to Supabase
    user_entry = {
        "google_id": user_data["id"],
        "name": user_data["name"],
        "email": user_data["email"],
        "picture": user_data["picture"],
    }

    # Check if user already exists
    existing_user = (
        supabase.table("chaakri")
        .select("id")
        .eq("google_id", user_data["id"])
        .execute()
    )

    if not existing_user.data:  # Insert only if user does not exist
        supabase.table("chaakri").insert(user_entry).execute()

    return redirect(url_for("home"))

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


