import logging
import os
import time
from datetime import datetime

import pytz
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logging.info("Application started successfully.")
start_time = time.time()
city_bike_station_information = 'https://gbfs.citibikenyc.com/gbfs/en/station_information.json'
city_bike_station_status = "https://gbfs.citibikenyc.com/gbfs/en/station_status.json"

# Fetch the response
try:
    response = requests.get(city_bike_station_status)
    response.raise_for_status()
    data = response.json()
    logging.info(f"Obtained response successfully. {data}")
except requests.exceptions.RequestException as e:
    logging.error(f"Failed to fetch data: {e}")
    data = {}

# Get the current date and time in New York timezone
ny_tz = pytz.timezone("America/New_York")
current_time = datetime.now(ny_tz)
date_str = current_time.strftime("%d-%m-%Y")
time_str = current_time.strftime("%H")

# Create a folder for the current date if it doesn't exist
folder_name = date_str
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

# Save the response to a text file
file_name = f"{folder_name}/{date_str}_Hour-{time_str}.txt"
with open(file_name, "w") as file:
    file.write(str(data))

end_time = time.time()
logging.info(f"Total time taken: {end_time - start_time}")
