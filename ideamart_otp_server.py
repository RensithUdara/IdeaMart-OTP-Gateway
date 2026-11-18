from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os, random, time
import requests

app = Flask(__name__)
load_dotenv()

APP_ID = os.getenv("IDEAMART_APP_ID")
APP_PASSWORD = os.getenv("IDEAMART_APP_PASSWORD")
REGISTERED_PHONE = os.getenv("REGISTERED_PHONE")  # Format: tel:947XXXXXXXX

OTP_STORE = {}
OTP_EXPIRY = 300  # seconds

def generate_otp():
    return str(random.randint(100000, 999999))

@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    phone = data.get("phone")

    if not phone:
        return jsonify({"error": "Phone number required"}), 400

    otp = generate_otp()
    OTP_STORE[phone] = (otp, int(time.time()))

    payload = {
        "applicationId": APP_ID,
        "password": APP_PASSWORD,
        "message": f"Your OTP is: {otp}",
        "destinationAddresses": [f"tel:{phone}"]
    }

    try:
        res = requests.post("https://api.dialog.lk/sms/send", json=payload)
        res_json = res.json()

        if res.status_code == 200:
            return jsonify({"message": "OTP sent", "otp": otp})  # Show OTP in dev only
        else:
            return jsonify({"error": res_json.get("statusDetail", "SMS failed")}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    phone = data.get("phone")
    otp_input = data.get("otp")

    record = OTP_STORE.get(phone)
    if not record:
        return jsonify({"error": "No OTP found"}), 404

    stored_otp, timestamp = record
    if int(time.time()) - timestamp > OTP_EXPIRY:
        del OTP_STORE[phone]
        return jsonify({"error": "OTP expired"}), 400

    if otp_input != stored_otp:
        return jsonify({"error": "Invalid OTP"}), 401

    del OTP_STORE[phone]
    return jsonify({"message": "OTP verified successfully!"})

if __name__ == "__main__":
    app.run(debug=True)
