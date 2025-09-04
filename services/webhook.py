from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    event = request.headers.get("X-GitHub-Event")
    payload = request.json
    
    if payload:
        thread = threading.Thread(
            target=process_comment_async, 
        )
        thread.start()
    
    return "OK", 200
    
def process_comment_async():
    try:
        response = requests.post(
            "http://localhost:5001/process", 
        )
        print(f"Comment processor response: {response.status_code}")
    except Exception as e:
        print(f"Error processing comment: {e}")

if __name__ == "__main__":
    app.run(port=5000)