import requests
import subprocess
import sys
import os
from dotenv import load_dotenv

def main():
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
    for comment in resp.json():
        if comment['start_line'] is None and comment['line'] is None:
            continue

        print(f"Body: {comment['body']}")
        print(f"File: {comment['path']}")
        print(f"Line range: {comment['start_line']}-{comment['line']}")

        if comment['start_line'] is None:
            comment['start_line'] = comment['line']


        # prompt = f"You are a helpful assistant that can help me write and fix code. I have the following review for a code file: {comment['body']}. Please write the code for me. The file is {comment['path']} and the line range is {comment['start_line']}-{comment['line']}. Please write understand the code review and make the proper adjustments for me."
        
        # with open("commands.txt", "a") as f:
        #     f.write(prompt + "\n")

if __name__ == "__main__":
    main()