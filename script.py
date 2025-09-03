import requests
import subprocess
import sys
import os
from dotenv import load_dotenv
from flask import Flask, request
from threading import Thread

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    event = request.headers.get("X-GitHub-Event")
    payload = request.json
    print(f"Received event: {event}")
    print(payload)

    if payload:
        thread = Thread(target=main, args=())
        thread.start()

    print("POTATOOOO")
    return "OK", 200

def main():
    load_dotenv()
    
    owner = "kennywchen"
    repo = "mentored-fa22-rampup"
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        print("Error: GITHUB_TOKEN not found in environment variables")
        print("Please create a .env file with your GitHub token")
        return

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/comments"
    headers = {"Authorization": f"token {token}"}

    resp = requests.get(url, headers=headers)
    # for comment in resp.json():
    #     print(f"Body: {comment['body']}")
    #     print(f"File: {comment['path']}")
    #     print(f"Line range: {comment['start_line']}-{comment['line']}")

    #     prompt = f"What directory am I in right now?"
    #     #prompt = f"You are a helpful assistant that can help me write and fix code. I have the following review for a code file: {comment['body']}. Please write the code for me. The file is {comment['path']} and the line range is {comment['start_line']}-{comment['line']}. Please write understand the code review and make the proper adjustments for me."
        
    #     with open("commands.txt", "a") as f:
    #         f.write(prompt + "\n")
    
    # Spawn cursor-agent CLI
    prompts = ["I have a bug in toFix.py. I want to print numbers 1 to 15. Please fix it.", "I have a bug in toFix2.py. I want to print the numbers 0 to 16. Please fix it."]
    
    try:
        # Send each prompt to a new cursor-agent process
        for i, prompt in enumerate(prompts):
            print(f"\n--- Processing prompt {i+1}: {prompt[:50]}... ---")
            
            # Create a new process for each command
            process = subprocess.Popen(
                ["cursor-agent"], 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send the command and EOF in one go
            input_data = prompt + "\n"
            stdout, stderr = process.communicate(input=input_data)
            
            # Extract the result from the JSON output
            try:
                if '{"type":"result' in stdout:
                    result_start = stdout.index('{"type":"result')
                    result_json = stdout[result_start:]
                    print(f"Result: {result_json}")
                else:
                    print(f"Full output: {stdout}")
            except ValueError:
                print(f"Full output: {stdout}")
                
            if stderr:
                print("STDERR:", stderr)
        
            process.terminate()

        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", "Automatically fixed bugs"])
        subprocess.run(["git", "push"])

            
    except Exception as e:
        print(f"Error: {e}")
        return
            

if __name__ == "__main__":
    app.run(port=5000)