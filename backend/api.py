from flask import Flask, request, jsonify
import csv
import joblib
import os
import re
from urllib.parse import urlparse
from dotenv import load_dotenv
from domain_checker import analyze_text
from email_header_analyzer import analyze_headers
from pathlib import Path
from flask_cors import CORS
import sys
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent / "email_connectors"))
from gmail_connector import get_gmail_auth_url, get_gmail_tokens, refresh_gmail_token, fetch_gmail_emails
from outlook_connector import get_outlook_auth_url, get_outlook_tokens, refresh_outlook_token, fetch_outlook_emails
from email_scanner import scan_emails_with_model
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

MODEL_PATH = os.getenv("MODEL_PATH", "linear_svm_model.pkl")
VECTORIZER_PATH = os.getenv("VECTORIZER_PATH", "tfidf_vectorizer.pkl")
LABEL_ENCODER_PATH = os.getenv("LABEL_ENCODER_PATH", "label_encoder.pkl")

if not MODEL_PATH or not VECTORIZER_PATH or not LABEL_ENCODER_PATH:
    raise ValueError("Required environment variables are missing")

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)
label_encoder = joblib.load(LABEL_ENCODER_PATH)

app.model = model
app.vectorizer = vectorizer
app.label_encoder = label_encoder

from bulk_predict import bulk_predict_bp
app.register_blueprint(bulk_predict_bp)
BASE_DIR = Path(__file__).resolve().parent
URL_MODEL_PATH = os.getenv(
    "URL_MODEL_PATH",
    str(BASE_DIR / "url_detector.pkl")
)

URL_VECTORIZER_PATH = os.getenv(
    "URL_VECTORIZER_PATH",
    str(BASE_DIR / "url_vectorizer.pkl")
)
url_model = joblib.load(URL_MODEL_PATH)
url_vectorizer = joblib.load(URL_VECTORIZER_PATH)
# url_detector.pkl predicts numeric classes with no bundled label encoder
URL_LABELS = {0: "malicious", 1: "safe"}

# Heuristic checks to catch obviously malicious URL patterns that the
# model is too biased toward "safe" to flag on its own.
SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq", "xyz", "top", "work", "click", "loan", "men", "review",
}
IPV4_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def heuristic_url_is_malicious(url):
    candidate = url if "://" in url else f"http://{url}"
    host = urlparse(candidate).hostname or ""

    if "@" in url:
        return True
    if IPV4_RE.match(host):
        return True
    if host.startswith("xn--") or ".xn--" in host:
        return True
    if host.count("-") >= 3:
        return True
    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    return tld in SUSPICIOUS_TLDS


FEEDBACK_FILE = "feedback_store.csv"
FEEDBACK_LABELS = set(label_encoder.classes_)


@app.route("/")
def home():
    return "ML API Running 🚀"


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        text = data.get("text")
        
        input_type = data.get("type", "message")
        if not text:
            with open("api.log", "a") as f:
                f.write(f"WARNING: No text provided at {__import__('datetime').datetime.now()}\n")
            return jsonify({"error": "No text provided"}), 400

        # Get spam prediction
        text_vector = vectorizer.transform([text])
        prediction = model.predict(text_vector)
        final_output = label_encoder.inverse_transform(prediction)[0]
        
        # Get domain analysis
        domain_analysis = analyze_text(text)
        if input_type == "url":
            text_vector = url_vectorizer.transform([text])
            prediction = url_model.predict(text_vector)
            final_output = URL_LABELS.get(int(prediction[0]), "unknown")
            if final_output == "safe" and heuristic_url_is_malicious(text):
                final_output = "malicious"
        else:
            text_vector = vectorizer.transform([text])
            prediction = model.predict(text_vector)
            final_output = label_encoder.inverse_transform(prediction)[0]

        # Log prediction
        text_preview = text[:50] + "..." if len(text) > 50 else text
        with open("api.log", "a") as f:
            from datetime import datetime
            f.write(f"{datetime.now()} - Prediction: '{text_preview}' -> {final_output}\n")
        
        # Return response with domain analysis
        return jsonify({
            "input": text,
            "prediction": final_output,
            "domain_analysis": domain_analysis
        })

    except Exception as e:
        with open("api.log", "a") as f:
            from datetime import datetime
            f.write(f"{datetime.now()} - ERROR: {str(e)}\n")
        return jsonify({"error": str(e)}), 500


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json(silent=True) or {}

    text = str(data.get("text", "")).strip()
    predicted_label = str(data.get("predicted_label", "")).strip()
    correct_label = str(data.get("correct_label", "")).strip()

    if not text or correct_label not in FEEDBACK_LABELS:
        return jsonify({"error": "Invalid feedback data"}), 400

    file_exists = os.path.isfile(FEEDBACK_FILE)
    with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["text", "predicted_label", "correct_label", "submitted_at"])
        from datetime import datetime, timezone
        writer.writerow([text, predicted_label, correct_label, datetime.now(timezone.utc).isoformat()])

    return jsonify({"message": "Feedback recorded. Thank you!"}), 201


@app.route("/analyze-email-header", methods=["POST"])
def analyze_email_header():
    try:
        headers = None
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename != "":
                try:
                    headers = file.read().decode("utf-8")
                except Exception as e:
                    return jsonify({"error": f"Failed to read EML file: {str(e)}"}), 400
            else:
                return jsonify({"error": "No email headers provided"}), 400
        else:
            data = request.get_json(silent=True) or {}
            headers = data.get("headers", "")

        if not headers or not headers.strip():
            return jsonify({"error": "No email headers provided"}), 400
            
        analysis = analyze_headers(headers)
        return jsonify({
            "success": True,
            "trust_level": analysis.get("trust_level", "Suspicious"),
            "risk_score": analysis.get("risk_score", 0),
            "findings": analysis.get("findings", []),
            "status": analysis.get("risk_level", "Suspicious"),
            "analysis": analysis
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/spam-insights", methods=["GET"])
def get_insights():
    try:
        limit = request.args.get("limit", default=10, type=int)
        category = request.args.get("category", default=None, type=str)
        
        from spam_insights import get_spam_insights
        insights = get_spam_insights(limit=limit, category=category)
        return jsonify(insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


TOKEN_STORE = {}

@app.route("/gmail/auth-url", methods=["GET"])
def gmail_auth_url():
    redirect_uri = request.args.get("redirect_uri") or "http://localhost:3000/gmail/callback"
    url = get_gmail_auth_url(redirect_uri)
    return jsonify({"auth_url": url})

@app.route("/gmail/callback", methods=["GET"])
def gmail_callback():
    code = request.args.get("code")
    redirect_uri = request.args.get("redirect_uri") or "http://localhost:3000/gmail/callback"
    username = request.headers.get("X-User-Username", "default_user")
    
    if not code:
        return jsonify({"error": "Authorization code is missing"}), 400
        
    try:
        tokens = get_gmail_tokens(code, redirect_uri)
        if username not in TOKEN_STORE:
            TOKEN_STORE[username] = {}
        TOKEN_STORE[username]["gmail"] = tokens
        return jsonify({"message": "Gmail connected successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to exchange Google code: {str(e)}"}), 500

@app.route("/gmail/emails", methods=["GET"])
def gmail_emails():
    username = request.headers.get("X-User-Username", "default_user")
    user_tokens = TOKEN_STORE.get(username, {}).get("gmail")
    
    if not user_tokens:
        return jsonify({"error": "Gmail account not connected"}), 401
        
    try:
        try:
            emails = fetch_gmail_emails(user_tokens.get("access_token"), limit=50)
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 401 and user_tokens.get("refresh_token"):
                new_tokens = refresh_gmail_token(user_tokens["refresh_token"])
                user_tokens["access_token"] = new_tokens["access_token"]
                if "refresh_token" in new_tokens:
                    user_tokens["refresh_token"] = new_tokens["refresh_token"]
                emails = fetch_gmail_emails(user_tokens["access_token"], limit=50)
            else:
                raise err
        return jsonify({"emails": emails})
    except Exception as e:
        return jsonify({"error": f"Failed to fetch Gmail emails: {str(e)}"}), 500

@app.route("/outlook/auth-url", methods=["GET"])
def outlook_auth_url():
    redirect_uri = request.args.get("redirect_uri") or "http://localhost:3000/outlook/callback"
    url = get_outlook_auth_url(redirect_uri)
    return jsonify({"auth_url": url})

@app.route("/outlook/callback", methods=["GET"])
def outlook_callback():
    code = request.args.get("code")
    redirect_uri = request.args.get("redirect_uri") or "http://localhost:3000/outlook/callback"
    username = request.headers.get("X-User-Username", "default_user")
    
    if not code:
        return jsonify({"error": "Authorization code is missing"}), 400
        
    try:
        tokens = get_outlook_tokens(code, redirect_uri)
        if username not in TOKEN_STORE:
            TOKEN_STORE[username] = {}
        TOKEN_STORE[username]["outlook"] = tokens
        return jsonify({"message": "Outlook connected successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to exchange Outlook code: {str(e)}"}), 500

@app.route("/outlook/emails", methods=["GET"])
def outlook_emails():
    username = request.headers.get("X-User-Username", "default_user")
    user_tokens = TOKEN_STORE.get(username, {}).get("outlook")
    
    if not user_tokens:
        return jsonify({"error": "Outlook account not connected"}), 401
        
    try:
        try:
            emails = fetch_outlook_emails(user_tokens.get("access_token"), limit=50)
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 401 and user_tokens.get("refresh_token"):
                new_tokens = refresh_outlook_token(user_tokens["refresh_token"])
                user_tokens["access_token"] = new_tokens["access_token"]
                if "refresh_token" in new_tokens:
                    user_tokens["refresh_token"] = new_tokens["refresh_token"]
                emails = fetch_outlook_emails(user_tokens["access_token"], limit=50)
            else:
                raise err
        return jsonify({"emails": emails})
    except Exception as e:
        return jsonify({"error": f"Failed to fetch Outlook emails: {str(e)}"}), 500

@app.route("/scan-emails", methods=["POST"])
def scan_emails_route():
    data = request.get_json(silent=True) or {}
    provider = data.get("provider", "").lower()
    username = request.headers.get("X-User-Username", "default_user")
    
    if provider not in ("gmail", "outlook"):
        return jsonify({"error": "Invalid provider. Must be 'gmail' or 'outlook'."}), 400
        
    user_tokens = TOKEN_STORE.get(username, {}).get(provider)
    if not user_tokens:
        return jsonify({"error": f"{provider.capitalize()} account not connected."}), 401
        
    try:
        if provider == "gmail":
            try:
                emails = fetch_gmail_emails(user_tokens.get("access_token"), limit=50)
            except requests.exceptions.HTTPError as err:
                if err.response.status_code == 401 and user_tokens.get("refresh_token"):
                    new_tokens = refresh_gmail_token(user_tokens["refresh_token"])
                    user_tokens["access_token"] = new_tokens["access_token"]
                    emails = fetch_gmail_emails(user_tokens["access_token"], limit=50)
                else:
                    raise err
        else:
            try:
                emails = fetch_outlook_emails(user_tokens.get("access_token"), limit=50)
            except requests.exceptions.HTTPError as err:
                if err.response.status_code == 401 and user_tokens.get("refresh_token"):
                    new_tokens = refresh_outlook_token(user_tokens["refresh_token"])
                    user_tokens["access_token"] = new_tokens["access_token"]
                    emails = fetch_outlook_emails(user_tokens["access_token"], limit=50)
                else:
                    raise err
                    
        scan_results = scan_emails_with_model(emails)
        return jsonify(scan_results)
    except Exception as e:
        return jsonify({"error": f"Email scan execution failed: {str(e)}"}), 500


if __name__ == "__main__":
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)