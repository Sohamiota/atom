
import json
import os
from datetime import datetime

from flask import Flask, jsonify, request

app = Flask(__name__)

#@app.route("/")
#def home():
#    return "<h2>Welcome to the Health Monitor API!</h2><p>Use <code>/health</code> for GET and POST requests.</p>"

LOG_FILE = "health_logs.json"


if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        json.dump([], f)


@app.route("/health", methods=["POST"])
def receive_health_log():
    try:
        print("Received POST /health request")
        data = request.get_json()
        print(f"Request JSON: {data}")

        if not data:
            print("No JSON data received")
            return jsonify({"error": "No JSON data received"}), 400

        data["timestamp"] = datetime.utcnow().isoformat()
        print(f"Timestamp added: {data['timestamp']}")

        # Save to file
        with open(LOG_FILE, "r+") as f:
            logs = json.load(f)
            logs.append(data)
            f.seek(0)
            json.dump(logs, f, indent=4)
        print("Health log saved to file.")

        return jsonify({"message": "Health log received successfully"}), 200

    except Exception as e:
        print(f"Error in POST /health: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def get_health_logs():
    try:
        print("Received GET /health request")
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
        print(f"Returning {len(logs)} health logs.")
        return jsonify(logs), 200
    except Exception as e:
        print(f"Error in GET /health: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
