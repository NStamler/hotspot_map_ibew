import os
import json
import requests
import datetime
from flask import Flask, jsonify, send_from_directory
from bs4 import BeautifulSoup

app = Flask(__name__)

# Your Mapbox Access Token
MAPBOX_API_KEY = "pk.eyJ1Ijoic3RhbWxlcm4iLCJhIjoiY2l3MnkwZ2tnMDEwejJ6anZtM240c2d3byJ9.ZTqhEH-1r0WelPq2n0rshQ"

# Use positional placeholders for city, token
GEOCODING_URL_TEMPLATE = (
    "https://api.mapbox.com/geocoding/v5/mapbox.places/{}.json?access_token={}"
)

# Directory to store daily snapshots
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data")

def get_coordinates(city):
    """Use Mapbox Geocoding to get [lng, lat] for a given city string."""
    url = GEOCODING_URL_TEMPLATE.format(city, MAPBOX_API_KEY)
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if data.get('features'):
        return data['features'][0]['geometry']['coordinates']  # [lng, lat]
    return [0, 0]

def scrape_hot_spots():
    """Scrape https://where2bro.com/hot-spots/ for lines like 'LU-237 NIAGARA FALLS, NY (ALBION PRISON)'."""
    url = "https://where2bro.com/hot-spots/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    hot_spots = []
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        # Looking for lines that start with "LU-" and contain parentheses
        if text.startswith("LU-") and "(" in text and ")" in text:
            # e.g. "LU-237 NIAGARA FALLS, NY (ALBION PRISON)"
            parts = text.split("(", 1)  # ["LU-237 NIAGARA FALLS, NY ", "ALBION PRISON)"]
            city_part = parts[0].strip()  # "LU-237 NIAGARA FALLS, NY"
            extra_info = parts[1].replace(")", "").strip()  # "ALBION PRISON"

            # Remove "LU-xxx" from the beginning of city_part
            city_parts = city_part.split(" ", 1)  # ["LU-237", "NIAGARA FALLS, NY"]
            if len(city_parts) > 1:
                city = city_parts[1].strip()
            else:
                city = city_part

            coords = get_coordinates(city)
            hot_spots.append({
                "city": city,
                "name": extra_info,
                "coordinates": coords
            })
    return hot_spots

@app.route('/')
def serve_map():
    """
    Serve the main HTML file (map_with_slider.html).
    """
    dir_path = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(
        directory=dir_path,
        path='map_with_slider.html',
        mimetype='text/html'
    )

@app.route('/trigger_scrape')
def trigger_scrape():
    """
    Called by cron-job.org each morning.
    Scrapes the site, saves to data/hot_spots_YYYY-MM-DD.json.
    """
    spots = scrape_hot_spots()

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"hot_spots_{today_str}.json"

    # Ensure data folder exists
    os.makedirs(DATA_FOLDER, exist_ok=True)

    filepath = os.path.join(DATA_FOLDER, filename)
    with open(filepath, 'w') as f:
        json.dump(spots, f, indent=2)

    return jsonify({
        "status": "ok",
        "saved_file": filename,
        "count": len(spots)
    })

@app.route('/hot_spots/dates', methods=['GET'])
def list_dates():
    """
    Returns a JSON array of all YYYY-MM-DD dates for which we have data files.
    E.g. ["2024-12-28","2024-12-29"].
    """
    if not os.path.exists(DATA_FOLDER):
        return jsonify([])

    files = os.listdir(DATA_FOLDER)
    dates = []
    for fname in files:
        if fname.startswith("hot_spots_") and fname.endswith(".json"):
            # Extract the date, e.g. "2024-12-29" from "hot_spots_2024-12-29.json"
            date_part = fname.replace("hot_spots_", "").replace(".json", "")
            dates.append(date_part)

    dates.sort()
    return jsonify(dates)

@app.route('/hot_spots/<date_str>', methods=['GET'])
def hot_spots_for_date(date_str):
    """
    Return the data for a specific date_str (YYYY-MM-DD).
    e.g. GET /hot_spots/2024-12-29
    """
    filename = f"hot_spots_{date_str}.json"
    filepath = os.path.join(DATA_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": f"No data found for date {date_str}"}), 404

    with open(filepath, 'r') as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == '__main__':
    # Run locally for testing
    app.run(debug=True)
