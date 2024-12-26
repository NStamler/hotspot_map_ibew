from flask import Flask, jsonify, send_from_directory
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

@app.route('/')
def serve_map():
    return send_from_directory('.', 'map.html')  # serve the map.html file

# [Your existing scraping code, hot_spots endpoint, etc.]

if __name__ == '__main__':
    app.run(debug=True)
