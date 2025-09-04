from flask import Flask, request
import subprocess
import requests
import os

app = Flask(__name__)

@app.route("/git-service", methods=["POST"])
def git_setup():
    try:
        ids = request.json.get("ids")
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", " Addressed comments: " + ", ".join(ids)])
        subprocess.run(["git", "push"])
        return "OK", 200
    except Exception as e:
        return {"status": "error", "error": str(e)}, 500

if __name__ == "__main__":
    app.run(port=5003)