import datetime
import os

# Making Folders if not already exists
os.makedirs("log/log_bio_sensor", exist_ok=True)
os.makedirs("log/log_chem_sensor", exist_ok=True)

payload = []

# For saving Bio - log
def save_bio(payload):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    clock = now.strftime("%H:%M:%S")

    filename = f"log/log_bio_sensor/Bio_Sensor_1_{date}.txt"

    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"{date},{clock},{payload}\n")

# For savinf Chem - log
def save_chem(payload):
    date = payload.split(",")[0]  # already has dafe & time

    filename = f"log/log_chem_sensor/Chem_Sensor_1_{date}.txt"

    with open(filename, "a", encoding="utf-8") as file:
        file.write(payload + "\n")


# check krne be baad length of payload
save_bio(payload)
save_chem(payload)