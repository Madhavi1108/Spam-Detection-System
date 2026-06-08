from flask import Flask, request, jsonify
import joblib
import os
from dotenv import load_dotenv
from flask_cors import CORS
from translator import translate_to_english

from pathlib import Path
import google.generativeai as genai
import os

load_dotenv(Path(__file__).parent / ".env")
print("MODEL_PATH =", os.getenv("MODEL_PATH"))
print("VECTORIZER_PATH =", os.getenv("VECTORIZER_PATH"))
print("LABEL_ENCODER_PATH =", os.getenv("LABEL_ENCODER_PATH"))
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

ai_model = genai.GenerativeModel("gemini-2.5-flash")

app = Flask(__name__)
CORS(app)
CORS(
    app,
    resources={
        r"/*": {
            "origins": ["http://localhost:5173"]
        }
    }
)


MODEL_PATH = os.getenv("MODEL_PATH")
VECTORIZER_PATH = os.getenv("VECTORIZER_PATH")
LABEL_ENCODER_PATH = os.getenv("LABEL_ENCODER_PATH")

if not MODEL_PATH or not VECTORIZER_PATH or not LABEL_ENCODER_PATH:
    raise ValueError("Required environment variables are missing")

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)
label_encoder = joblib.load(LABEL_ENCODER_PATH)


@app.route("/")
def home():
    return "ML API Running 🚀"

def generate_ai_suggestion(text, prediction):

    prompt = f"""
    Message:

    {text}

    Prediction: {prediction}

    Respond in the same language as the message.

    Give only one short recommendation (under 20 words).

    Examples:

    Safe:
    This message appears safe.

    Spam:
    Do not click links or share personal information.
    """

    try:
        response = ai_model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"AI suggestion unavailable: {str(e)}"
def get_safe_message(language):
    safe_messages = {
        "en": "This message appears safe.",
        "de": "Diese Nachricht scheint sicher zu sein.",
        "fr": "Ce message semble sûr.",
        "es": "Este mensaje parece seguro.",
        "it": "Questo messaggio sembra sicuro.",
        "ta": "இந்த செய்தி பாதுகாப்பானதாக தெரிகிறது.",
        "ja": "このメッセージは安全と思われます。",
        "ko": "이 메시지는 안전한 것으로 보입니다.",
        "zh-cn": "此消息似乎是安全的。",
        "hi": "यह संदेश सुरक्षित प्रतीत होता है।"
    }

    return safe_messages.get(
        language,
        "This message appears safe."
    )
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        print("Received:", data)

        text = data.get("text")

        print("Text:", text)
        translated_text, detected_language = translate_to_english(text)

        text_vector = vectorizer.transform([translated_text])

        prediction = model.predict(text_vector)

        final_output = label_encoder.inverse_transform(prediction)[0]

        final_output = label_encoder.inverse_transform(prediction)[0]

        if final_output in ["spam","smishing"]:
            suggestion = generate_ai_suggestion(
                text,
                final_output
            )
        else:
            suggestion = get_safe_message(detected_language)

        return jsonify({
            "input": text,
            "prediction": final_output,
            "suggestion": suggestion
    })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
    


if __name__ == "__main__":
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)
