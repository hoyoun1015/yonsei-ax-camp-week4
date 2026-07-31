from flask import Flask, jsonify, send_from_directory
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "transcripts.json")
STATS_PATH = os.path.join(BASE_DIR, "data", "stats.json")

app = Flask(__name__, static_folder="static", template_folder="templates")


def load_transcripts():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/api/tasks")
def list_tasks():
    data = load_transcripts()
    summary = [
        {"id": t["task"]["id"], "k": t["task"]["k"], "title": t["task"]["title"]}
        for t in data
    ]
    return jsonify(summary)


@app.route("/api/tasks/<task_id>")
def get_task(task_id):
    data = load_transcripts()
    for t in data:
        if t["task"]["id"] == task_id:
            return jsonify(t)
    return jsonify({"error": "not found"}), 404


@app.route("/api/stats")
def get_stats():
    with open(STATS_PATH, encoding="utf-8") as f:
        return jsonify(json.load(f))


if __name__ == "__main__":
    app.run(debug=True, port=5050)
