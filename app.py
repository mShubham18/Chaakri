import os
from flask import Flask, session, render_template
from flask import redirect, request, session, url_for
from auth import auth  # Import the auth blueprint
from dotenv import load_dotenv
import requests
# Load environment variables
load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

# Register blueprints
app.register_blueprint(auth)

@app.route("/")
def home():
    if "user" in session:
        user = session["user"]
        return render_template("dashboard.html", user=user)
    return render_template("login.html")

@app.route('/jobs')
def jobs():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    keyword = request.args.get("keyword", "developer")
    location = request.args.get("location", "remote")
    
    url = f"https://api.adzuna.com/v1/api/jobs/us/search/1?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_API_KEY}&what={keyword}&where={location}"
    response = requests.get(url)
    data = response.json()
    
    job_listings = []
    for job in data.get("results", []):
        job_listings.append({
            "title": job.get("title", "Unknown"),
            "company": job.get("company", {}).get("display_name", "Unknown"),
            "location": job.get("location", {}).get("display_name", "Unknown"),
            "url": job.get("redirect_url", "#")
        })
    
    return render_template("dashboard.html", jobs=job_listings)

if __name__ == "__main__":
    app.run(debug=True)
