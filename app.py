import os
from flask import Flask, session, render_template
from auth import auth  # Import the auth blueprint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

if __name__ == "__main__":
    app.run(debug=True)
