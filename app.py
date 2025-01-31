from flask import Flask, jsonify, send_from_directory
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

# ===========================================================
#   1) Replace with your actual Mapbox Access Token:
# ===========================================================
MAPBOX_API_KEY = "pk.eyJ1Ijoic3RhbWxlcm4iLCJhIjoiY2l3MnkwZ2tnMDEwejJ6anZtM240c2d3byJ9.ZTqhEH-1r0WelPq2n0rshQ"

# ===========================================================
#   2) Use positional placeholders:
#      {} for city, {} for token
# ===========================================================
GEOCODING_URL_TEMPLATE = (
    "https://api.mapbox.com/geocoding/v5/mapbox.places/{}.json?access_token={}"
)

def get_coordinates(city):
    # Build the URL with .format(city, MAPBOX_API_KEY)
    url = GEOCODING_URL_TEMPLATE.format(city, MAPBOX_API_KEY)
    print(f"[DEBUG] Geocoding URL: {url}")  # For debugging

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if 4xx/5xx
        data = response.json()
        
        if data.get('features'):
            # Return [lng, lat] from the first match
            return data['features'][0]['geometry']['coordinates']
        else:
            print(f"[DEBUG] No features returned for city={city}")
            return [0, 0]
    except Exception as e:
        print(f"[ERROR] get_coordinates failed for city={city}: {e}")
        return [0, 0]

# ===========================================================
#   3) Updated scraping logic to parse <p> tags
#      that look like "LU-237 NIAGARA FALLS, NY (ALBION PRISON)"
# ===========================================================
def scrape_hot_spots():
    url = "https://where2bro.com/hot-spots/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    hot_spots = []

    # Look for paragraphs that start with "LU-" and contain parentheses
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        
        if text.startswith("LU-") and "(" in text and ")" in text:
            # Example: "LU-237 NIAGARA FALLS, NY (ALBION PRISON)"
            parts = text.split("(", 1)  # ["LU-237 NIAGARA FALLS, NY ", "ALBION PRISON)"]
            city_part = parts[0].strip()  # "LU-237 NIAGARA FALLS, NY"
            extra_info = parts[1].replace(")", "").strip()  # "ALBION PRISON"

            # city_part -> "LU-237 NIAGARA FALLS, NY"
            # Remove the "LU-xxx" portion
            city_parts = city_part.split(" ", 1)  # ["LU-237", "NIAGARA FALLS, NY"]
            if len(city_parts) > 1:
                city = city_parts[1].strip()
            else:
                city = city_part  # fallback if format is unexpected

            coords = get_coordinates(city)

            hot_spots.append({
                "city": city,
                "name": extra_info,
                "coordinates": coords
            })

    return hot_spots

# ===========================================================
#   4) Routes
# ===========================================================
@app.route('/')
def serve_map():
    # Serve your map.html from the same directory as app.py
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
