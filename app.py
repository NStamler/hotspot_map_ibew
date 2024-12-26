from flask import Flask, jsonify, send_from_directory
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

# Mapbox Geocoding API setup
MAPBOX_API_KEY = "pk.eyJ1Ijoic3RhbWxlcm4iLCJhIjoiY2l3MnkwZ2tnMDEwejJ6anZtM240c2d3byJ9.ZTqhEH-1r0WelPq2n0rshQ"
GEOCODING_URL_TEMPLATE = "https://api.mapbox.com/geocoding/v5/mapbox.places/{city}.json?access_token={}"

# ===========================================================
#                  UPDATED SCRAPING LOGIC
# ===========================================================
def scrape_hot_spots():
    url = "https://where2bro.com/hot-spots/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    hot_spots = []

    # Loop through all paragraph tags
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        # We want lines like: "LU-237 NIAGARA FALLS, NY (ALBION PRISON)"
        # Check if the line starts with 'LU-' and contains parentheses
        if text.startswith("LU-") and "(" in text and ")" in text:
            # Example: "LU-237 NIAGARA FALLS, NY (ALBION PRISON)"
            # Split around '('
            parts = text.split("(", 1)  # ["LU-237 NIAGARA FALLS, NY ", "ALBION PRISON)"]
            city_part = parts[0].strip()  # "LU-237 NIAGARA FALLS, NY"
            extra_info = parts[1].replace(")", "").strip()  # "ALBION PRISON"

            # city_part often looks like "LU-237 NIAGARA FALLS, NY"
            # So remove the "LU-xxx" portion
            city_parts = city_part.split(" ", 1)  # ["LU-237", "NIAGARA FALLS, NY"]
            if len(city_parts) > 1:
                city = city_parts[1].strip()
            else:
                city = city_part  # fallback if format is unexpected

            # Fetch coordinates for the city using Mapbox
            coords = get_coordinates(city)

            hot_spots.append({
                "city": city,
                "name": extra_info,       # the portion in parentheses
                "coordinates": coords     # [lng, lat]
            })

    return hot_spots

def get_coordinates(city):
    # Build the geocoding URL
    url = GEOCODING_URL_TEMPLATE.format(city, MAPBOX_API_KEY)
    response = requests.get(url)
    data = response.json()
    if data.get('features'):
        return data['features'][0]['geometry']['coordinates']  # [lng, lat]
    else:
        return [0, 0]  # If no results, fallback to [0,0]

@app.route('/')
def serve_map():
    # Serve your map.html from the same directory
    dir_path = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(
        directory=dir_path,
        path='map.html',
        mimetype='text/html'
    )

@app.route('/hot_spots', methods=['GET'])
def hot_spots():
    spots = scrape_hot_spots()
    return jsonify(spots)

if __name__ == '__main__':
    # If running locally, set debug=True for development
    app.run(debug=True)
