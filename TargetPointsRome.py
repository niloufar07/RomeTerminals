import streamlit as st
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.extra.rate_limiter import RateLimiter
from streamlit_folium import st_folium
import time

# Load the data
health = pd.read_csv(r"https://raw.githubusercontent.com/niloufar07/RomeTerminals/main/170424_Roma_PuntiInteresse.csv")

# Filter the Rome dataset for BUS == 1
rome = pd.read_csv(r"https://raw.githubusercontent.com/niloufar07/RomeTerminals/main/okrome.csv")
rome = rome[rome['BUS'] == 1]

# List of railway stations
stations = [
    "Termini",
    "Tiburtina",
    "Ostiense",
    "Monte Mario",
    "Balduina",
    "Trastevere",
    "Tuscolana"
]

# Initialize the geolocator
geolocator = Nominatim(user_agent="rome_stations")

# Cache for station coordinates
station_coordinates = {}

# Function to get coordinates with retry mechanism
def get_coordinates(station):
    retries = 3
    for _ in range(retries):
        try:
            location = geolocator.geocode(station + ", Rome, Italy")
            if location:
                return (location.latitude, location.longitude)
        except GeocoderTimedOut:
            time.sleep(1)
    return None

# Get coordinates for each station
for station in stations:
    if station not in station_coordinates:
        coordinates = get_coordinates(station)
        if coordinates:
            station_coordinates[station] = coordinates
        else:
            st.error(f"Failed to get coordinates for {station}")

# Print station coordinates
for station, coordinates in station_coordinates.items():
    print(f"{station}: {coordinates}")

# Drop unnecessary columns from the health dataset
columns_to_drop = ['country_code', 'country', 'state', 'city', 'original_Comune', 'original_Tipo Azienda',
                   'original_Codice Azienda', 'original_Codice struttura', 'original_Descrizione Regione',
                   'original_Codice Comune', 'district', 'confidence', 'original_Tipo di Disciplina',
                   'original_Codice tipo struttura', 'original_Sigla Provincia', 'original_Codice disciplina',
                   'country', 'original_Subcodice', 'county_code', 'county', 'state_code', 'confidence_city_level',
                   'confidence_street_level']
health_filtered = health.drop(columns=columns_to_drop)

# Define IDs to be deleted
ids_to_delete = [303, 322, 196, 321, 302, 197, 195, 320, 194, 193, 192, 191]
health_filtered = health_filtered[~health_filtered['ID'].isin(ids_to_delete)]

# Function to calculate distance between two points using the haversine formula
from math import radians, sin, cos, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# Define points and their coordinates
points = {
    "Roma Termini": (41.9016577, 12.5007858),
    "Roma Tiburtina": (41.9332728, 12.6014069),
    "Roma Ostiense": (41.85728265, 12.477881265979732),
    "Roma Trastevere": (41.8911586, 12.466845904466918),
    "Roma Tuscolana": (41.8420355, 12.5925967),
    "Roma San Pietro": (41.8958, 12.4537),
    "Roma Ostia Antica": (41.7568, 12.2911),
    "Roma Valle Aurelia": (41.9051, 12.4395),
    "Roma Nomentana": (41.9205, 12.5248),
    "Roma Prenestina": (41.9021, 12.5521)
}

# Find the nearest hospital for each point
for point_name, (point_lat, point_lon) in points.items():
    nearest_hospital = None
    min_distance = float('inf')
    
    for idx, row in health_filtered.iterrows():
        hospital_lat = row['lat']
        hospital_lon = row['lon']
        distance = calculate_distance(point_lat, point_lon, hospital_lat, hospital_lon)
        
        if distance < min_distance:
            min_distance = distance
            nearest_hospital = row['original_Denominazione Struttura/Stabilimento']
    
    print(f"For {point_name}: Nearest hospital is {nearest_hospital} at a distance of {min_distance} km.")

# Initialize the map
m = folium.Map(location=[41.895266, 12.482324], zoom_start=12)

# Add markers for railway stations
for station, (lat, lon) in station_coordinates.items():
    folium.Marker(location=[lat, lon], popup=station, icon=folium.Icon(color='blue')).add_to(m)

# Add markers for nearest hospitals to each station and connect with dashed lines
for station_name, (station_lat, station_lon) in station_coordinates.items():
    nearest_hospital = None
    min_distance = float('inf')
    
    for idx, row in health_filtered.iterrows():
        hospital_lat = row['lat']
        hospital_lon = row['lon']
        distance = calculate_distance(station_lat, station_lon, hospital_lat, hospital_lon)
        
        if distance < min_distance:
            min_distance = distance
            nearest_hospital_lat = hospital_lat
            nearest_hospital_lon = hospital_lon
            nearest_hospital_name = row['original_Denominazione Struttura/Stabilimento']
    
    # Add marker for nearest hospital with distance in popup
    popup_content = f"Nearest hospital: {nearest_hospital_name}<br>Distance: {min_distance:.2f} km"
    folium.Marker(location=[nearest_hospital_lat, nearest_hospital_lon], popup=popup_content, icon=folium.Icon(color='red')).add_to(m)
    
    # Connect station to nearest hospital with dashed line
    folium.PolyLine(locations=[[station_lat, station_lon], [nearest_hospital_lat, nearest_hospital_lon]],
                    color="red", weight=2, opacity=0.5).add_to(m)

# Display the map in Streamlit
st_folium(m)
