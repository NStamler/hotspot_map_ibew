from flask import Flask, jsonify, send_from_directory
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

@app.route('/')
def serve_map():
    #return send_from_directory('.', 'map.html')  # serve the map.html file
    
    # Get the absolute path of the directory where app.py is located
    dir_path = os.path.abspath(os.path.dirname(__file__))
    
    #return send_from_directory(dir_path, 'map.html')
    return send_from_directory(
            directory=dir_path,
            path='map.html',
            mimetype='text/html'
        )

# Mapbox Geocoding API setup
MAPBOX_API_KEY = 'pk.eyJ1Ijoic3RhbWxlcm4iLCJhIjoiY2l3MnkwZ2tnMDEwejJ6anZtM240c2d3byJ9.ZTqhEH-1r0WelPq2n0rshQ'
geocoding_url = "https://api.mapbox.com/geocoding/v5/mapbox.places/{city}.json?access_token=" + MAPBOX_API_KEY

# Scrape hot spots from Where2Bro
def scrape_hot_spots():
    url = "https://where2bro.com/hot-spots/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    hot_spots = []

    for li in soup.find_all('li'):
        text = li.get_text(strip=True)
        if '(' in text and ')' in text:
            city, hot_spot = text.split('(')
            city = city.strip()
            hot_spot = hot_spot.replace(')', '').strip()

            # Fetch coordinates using Mapbox Geocoding API
            coordinates = get_coordinates(city)

            hot_spots.append({
                "name": hot_spot,
                "city": city,
                "coordinates": coordinates
            })

    return hot_spots

# Fetch coordinates for a city using Mapbox Geocoding API
def get_coordinates(city):
    geocoding_url_full = geocoding_url.format(city=city)
    response = requests.get(geocoding_url_full)
    data = response.json()
    if data['features']:
        coordinates = data['features'][0]['geometry']['coordinates']
        return coordinates
    else:
        return [0, 0]  # Default coordinates if not found

# Define an API endpoint to serve the hot spots data as JSON
@app.route('/hot_spots', methods=['GET'])
def hot_spots():
    hot_spots = scrape_hot_spots()
    return jsonify(hot_spots)

if __name__ == '__main__':
    app.run(debug=True)
