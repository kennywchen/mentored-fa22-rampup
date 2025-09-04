from flask import Flask, request
import requests
import json
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

def process_comment_async(comment):
    try:
        response = requests.post(
            "http://localhost:5002/call-agent",
            json={
                "comment_id": comment.get("id"),
                "file_path": comment.get("path"),
                "line_start": comment.get("start_line"),
                "line_end": comment.get("line"),
                "body": comment.get("body")
            },
        )
        return response.json()
    except Exception as e:
        return {"status": "failed", "error": str(e)}

@app.route("/process", methods=["POST"])
def process():
    load_dotenv()
    
    owner = "kennywchen"
    repo = "mentored-fa22-rampup"
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        print("Error: GITHUB_TOKEN not found in environment variables")
        return

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/comments"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    ids = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for comment in resp.json():
            if comment['start_line'] is None and comment['line'] is None:
                continue

            if comment['start_line'] is None:
                comment['start_line'] = comment['line']

            ids.append(comment['id'])
            future = executor.submit(process_comment_async, comment)
            futures.append(future)

        for future in futures:
            future.result()
        
        git_response = requests.post(
            "http://localhost:5003/git-service",
            json={
                "ids": ids
            }
        )
        print(f"Git manager response: {git_response.status_code}")
    
    return "Processing started", 202

if __name__ == "__main__":
    app.run(port=5001)