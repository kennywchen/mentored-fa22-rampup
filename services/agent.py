from flask import Flask, request
import subprocess
import threading
from queue import Queue

app = Flask(__name__)

@app.route("/call-agent", methods=["POST"])
def call_agent():
    try:
        data = request.json
        prompt = f"You are a helpful assistant that can help me write and fix code. I have the following review for a code file: {data['body']}. Please write the code for me. The file is {data['path']} and the line range is {data['line_start']}-{data['line_end']}. Please write understand the code review and make the proper adjustments for me."
        process_prompt(prompt)

    except Exception as e:
        print(f"Error calling agent: {e}")
        return {"status": "error", "error": str(e)}, 500
    
    return {"status": "success"}, 200


def process_prompt(prompt):
    """Process a single prompt in a separate thread"""
    try:
        print(f"\n--- Processing prompt: {prompt[:50]}... ---")
        
        process = subprocess.Popen(
            ["cursor-agent"], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        input_data = prompt + "\n"
        stdout, stderr = process.communicate(input=input_data)
        
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
            print(f"STDERR: {stderr}")
            
    except Exception as e:
        print(f"Error processing prompt: {e}")

if __name__ == "__main__":
    app.run(port=5002)