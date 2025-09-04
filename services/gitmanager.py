from flask import Flask, request
import subprocess
import requests
import os

app = Flask(__name__)

@app.route("/git-service", methods=["POST"])
def git_setup():
    try:
        ids = request.json.get("ids")
        print(f"Git manager called with IDs: {ids}")
        subprocess.run(["ls"])
        subprocess.run(["git", "add", "."])
        commit_message = f"Fixed comments {ids}"
        print(f"Commit message: {commit_message}")
        subprocess.run(["git", "commit", "-m", commit_message])
        subprocess.run(["git", "push"])
        return "OK", 200
    except Exception as e:
        return {"status": "error", "error": str(e)}, 500

if __name__ == "__main__":
    app.run(port=5003)