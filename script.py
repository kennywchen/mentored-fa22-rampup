import requests
import subprocess
import sys
import os
from dotenv import load_dotenv
from flask import Flask, request
from threading import Thread

app = Flask(__name__)


def main():
    pass

if __name__ == "__main__":
    app.run(port=5000)