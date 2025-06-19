import requests
import time
import datetime
import random
import os
import csv
import logging
import signal
import sys
import numpy as np
from statsmodels.tsa.seasonal import STL

# Constants for location and API endpoint
LATITUDE = 38.8719  # Pentagon latitude
LONGITUDE = -77.0563  # Pentagon longitude
SEARCH_RADIUS_METERS = 2000  # Search radius in meters
OVERPASS_API_URL = "http://overpass-api.de/api/interpreter"

# File paths for persistent storage
PIZZERIA_LIST_FILE = "pizzerias_seen.txt"
CSV_STATS_FILE = "pizza_stats.csv"
LOG_FILE = "logs.txt"

# Logging configuration
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Global flag for graceful shutdown
should_exit = False

def handle_termination_signal(signum, frame):
    """
    Signal handler to catch termination signals and set exit flag.
    """
    global should_exit
    logging.info(f"Received termination signal ({signum}). Preparing to exit gracefully.")
    should_exit = True

# Register termination signal handlers (Ctrl+C and SIGTERM)
signal.signal(signal.SIGINT, handle_termination_signal)
signal.signal(signal.SIGTERM, handle_termination_signal)

def fetch_pizzerias():
    """
    Fetch pizza-serving establishments within SEARCH_RADIUS_METERS of the Pentagon.
    Uses Overpass API with tags 'cuisine=pizza' and amenity filters.
    Returns:
        List of tuples: (id, latitude, longitude, name)
    """
    query = f"""
    [out:json][timeout:25];
    (
      node["cuisine"="pizza"](around:{SEARCH_RADIUS_METERS},{LATITUDE},{LONGITUDE});
      way["cuisine"="pizza"](around:{SEARCH_RADIUS_METERS},{LATITUDE},{LONGITUDE});
      relation["cuisine"="pizza"](around:{SEARCH_RADIUS_METERS},{LATITUDE},{LONGITUDE});

      node["amenity"="restaurant"]["cuisine"="pizza"](around:{SEARCH_RADIUS_METERS},{LATITUDE},{LONGITUDE});
      way["amenity"="restaurant"]["cuisine"="pizza"](around:{SEARCH_RADIUS_METERS},{LATITUDE},{LONGITUDE});
      relation["amenity"="restaurant"]["cuisine"="pizza"](around:{SEARCH_RADIUS_METERS},{LATITUDE},{LONGITUDE});

      node["amenity"="fast_food"]["cuisine"="pizza"](around:{SEARCH_RADIUS_METERS},{LATITUDE},{LONGITUDE});
      way["amenity"="fast_food"]["cuisine"="pizza"](around:{SEARCH_RADIUS_METERS},{LATITUDE},{LONGITUDE});
      relation["amenity"="fast_food"]["cuisine"="pizza"](around:{SEARCH_RADIUS_METERS},{LATITUDE},{LONGITUDE});
    );
    out body;
    """
    try:
        response = requests.post(OVERPASS_API_URL, data={'data': query}, timeout=30)
        response.raise_for_status()
        data = response.json()

        unique_pizzerias = {}
        for element in data.get('elements', []):
            unique_pizzerias[element['id']] = element

        results = []
        for el in unique_pizzerias.values():
            pid = el['id']
            lat = el.get('lat')
            lon = el.get('lon')
            name = el.get('tags', {}).get('name', 'Unknown')
            results.append((pid, lat, lon, name))

        return results

    except requests.exceptions.RequestException as e:
        logging.error(f"Overpass API request failed: {e}")
    except ValueError as e:
        logging.error(f"JSON decoding failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in fetch_pizzerias: {e}")

    return []

def load_known_pizzerias():
    """
    Load previously known pizzeria IDs from file.
    Returns:
        Set of string IDs.
    """
    if not os.path.exists(PIZZERIA_LIST_FILE):
        return set()
    try:
        with open(PIZZERIA_LIST_FILE, 'r') as file:
            return set(line.strip() for line in file)
    except Exception as e:
        logging.error(f"Failed to load known pizzerias: {e}")
        return set()

def save_known_pizzerias(pizzeria_ids):
    """
    Save known pizzeria IDs to file, one ID per line.
    Args:
        pizzeria_ids (set): Set of string IDs.
    """
    try:
        with open(PIZZERIA_LIST_FILE, 'w') as file:
            for pid in pizzeria_ids:
                file.write(f"{pid}\n")
    except Exception as e:
        logging.error(f"Failed to save known pizzerias: {e}")

def simulate_visits(num_pizzerias):
    """
    Simulate the number of visits/orders for the given number of pizzerias.
    Args:
        num_pizzerias (int): Number of detected pizzerias.
    Returns:
        int: Simulated total visits.
    """
    return sum(random.randint(3, 15) for _ in range(num_pizzerias))

def save_to_csv(timestamp, num_pizzerias, num_visits, ratio):
    """
    Append a new row of stats to the CSV file, create file with header if needed.
    Args:
        timestamp (str): ISO formatted timestamp.
        num_pizzerias (int): Number of pizzerias detected.
        num_visits (int): Number of simulated visits.
        ratio (float): Visits per pizzeria ratio.
    """
    file_exists = os.path.exists(CSV_STATS_FILE)
    try:
        with open(CSV_STATS_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Timestamp", "Pizzerias", "Visits", "Visit/Pizzeria Ratio"])
            writer.writerow([timestamp, num_pizzerias, num_visits, f"{ratio:.2f}"])
    except Exception as e:
        logging.error(f"Failed to write to CSV: {e}")

def load_ratios_history():
    """
    Load the historical visit/pizzeria ratios from the CSV file.
    Returns:
        List of floats representing historical ratios.
    """
    ratios = []
    if not os.path.exists(CSV_STATS_FILE):
        return ratios
    try:
        with open(CSV_STATS_FILE, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ratio_str = row.get("Visit/Pizzeria Ratio")
                if ratio_str:
                    try:
                        ratio = float(ratio_str)
                        ratios.append(ratio)
                    except ValueError:
                        continue
        # Keep only the last 72 entries (~3 days of hourly data)
        return ratios[-72:]
    except Exception as e:
        logging.error(f"Failed to load ratios history: {e}")
        return []

def detect_anomaly(ratios, threshold=3.0):
    """
    Detect anomalies in the time series of visit/pizzeria ratios using STL decomposition.
    Args:
        ratios (list of float): Time series data of ratios.
        threshold (float): Number of standard deviations above which anomaly is flagged.
    Returns:
        tuple (bool, float): (is_anomaly_detected, anomaly_score)
    """
    if len(ratios) < 24:
        # Not enough data points to reliably detect anomalies
        return False, 0.0

    series = np.array(ratios)
    try:
        stl = STL(series, period=24, robust=True)
        result = stl.fit()
        residuals = result.resid
        latest_residual = residuals[-1]
        resid_std = np.std(residuals)
        if resid_std == 0:
            return False, 0.0

        anomaly_score = abs(latest_residual) / resid_std
        is_anomaly = anomaly_score > threshold
        return is_anomaly, anomaly_score

    except Exception as e:
        logging.error(f"Error during anomaly detection: {e}")
        return False, 0.0

def main():
    """
    Main execution loop: continuously monitor pizza orders, detect anomalies,
    and log results. Handles graceful shutdown on termination signals.
    """
    global should_exit

    # Load historical ratios for anomaly detection
    ratios_history = load_ratios_history()

    while not should_exit:
        known_pizzerias = load_known_pizzerias()
        current_pizzerias = fetch_pizzerias()
        current_ids = {str(pid) for pid, _, _, _ in current_pizzerias}

        # Detect new pizzerias
        new_pizzerias = current_ids - known_pizzerias
        if new_pizzerias:
            logging.info(f"New pizzerias detected: {new_pizzerias}")

        # Update known pizzerias list
        save_known_pizzerias(current_ids)

        num_pizzerias = len(current_pizzerias)
        num_visits = simulate_visits(num_pizzerias)
        ratio = (num_visits / num_pizzerias) if num_pizzerias > 0 else 0.0
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Append ratio to history and maintain fixed window size
        ratios_history.append(ratio)
        if len(ratios_history) > 72:
            ratios_history.pop(0)

        # Detect anomalies
        anomaly_detected, anomaly_score = detect_anomaly(ratios_history)

        # Log status
        status_msg = f"[{timestamp}] Pizzerias: {num_pizzerias}, Visits: {num_visits}, Ratio: {ratio:.2f}"
        print(status_msg)
        logging.info(status_msg)
        logging.info(f"Anomaly detection score: {anomaly_score:.2f}")

        if anomaly_detected:
            alert_msg = f"*** ALERT: Geopolitical crisis anomaly detected! Score: {anomaly_score:.2f}, Ratio: {ratio:.2f} ***"
            print(alert_msg)
            logging.info(alert_msg)

        # Save data for later analysis
        save_to_csv(timestamp, num_pizzerias, num_visits, ratio)

        # Wait for next hourly iteration, exit early if termination signal received
        for _ in range(3600):
            if should_exit:
                break
            time.sleep(1)

    logging.info("Program exited gracefully.")

if __name__ == "__main__":
    main()
