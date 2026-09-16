import json
import time
from datetime import datetime
from pathlib import Path
import paho.mqtt.client as mqtt

# -----------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
CONFIG_PATH = PROJECT_DIR / "Config.txt"

# Load JSON Dictionary Config
with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)

BROKER_HOST = CONFIG["global"]["ip_broker"]
BROKER_PORT = CONFIG["global"]["port_broker"]
KEEPALIVE = CONFIG["global"]["broker_keep_alive"]

# Extract Topics directly from configuration
BIO_TOPIC = CONFIG["sensors"]["bio_sensor"]["topic"]
CHEM_TOPIC = CONFIG["sensors"]["chem_sensor"]["topic"]
FCAD_TOPIC = CONFIG["sensors"]["fcad_sensor"]["topic"]

# -----------------------------------------------------------
LOG_DIR = PROJECT_DIR / "log"
BIO_LOG_DIR = LOG_DIR / "log_bio_sensor"
CHEM_LOG_DIR = LOG_DIR / "log_chem_sensor"
FCAD_LOG_DIR = LOG_DIR / "log_fcad_sensor"

BIO_LOG_DIR.mkdir(parents=True, exist_ok=True)
CHEM_LOG_DIR.mkdir(parents=True, exist_ok=True)
FCAD_LOG_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------
# Logging Helpers
# -----------------------------------------------------------
def save_bio(payload):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    clock = now.strftime("%H:%M:%S")
    filepath = BIO_LOG_DIR / f"Bio_Sensor_1_{date}.txt"
    with open(filepath, "a", encoding="utf-8") as file:
        file.write(f"{date},{clock},{payload}\n")


def save_chem(payload):
    date = payload.split(",")[0]
    filepath = CHEM_LOG_DIR / f"Chem_Sensor_1_{date}.txt"
    with open(filepath, "a", encoding="utf-8") as file:
        file.write(payload + "\n")


def save_fcad(payload):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    clock = now.strftime("%H:%M:%S")
    filepath = FCAD_LOG_DIR / f"fcad_Sensor_{date}.txt"
    with open(filepath, "a", encoding="utf-8") as file:
        file.write(f"{date},{clock},{payload}\n")


# -----------------------------------------------------------
# MQTT Callbacks
# -----------------------------------------------------------
def on_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode("utf-8")

    print("\n" + "=" * 55)
    print(f"Message received from: {topic}")

    try:
        if topic == BIO_TOPIC:
            data = payload.split(",")
            if len(data) != 6:
                raise ValueError("Invalid biological sensor data")

            print(f"Sample Type                       : {data[0]}")
            print(f"Small Particle Count              : {data[1]}")
            print(f"Large Particle Count              : {data[2]}")
            print(f"Small Particle Biological Load    : {data[3]}")
            print(f"Large Particle Biological Load    : {data[4]}")
            print(f"Alarm                             : {data[5]}")
            save_bio(payload)

        elif topic == FCAD_TOPIC:
            data = payload.split(",")
            if len(data) != 9:
                raise ValueError("Invalid FCAD sensor data")

            print(f"Sensor Name                       : {data[0]}")
            print(f"G Value                           : {data[1]}")
            print(f"H Value                           : {data[2]}")
            print(f"Atmospheric Pressure G            : {data[3]}")
            print(f"Atmospheric Pressuer H            : {data[4]}")
            print(f"G Pressure                        : {data[5]}")
            print(f"H Pressure                        : {data[6]}")
            print(f"Battery                           : {data[7]}")
            print(f"Mode                              : {data[8]}")
            save_fcad(payload)

        elif topic == CHEM_TOPIC:
            data = payload.split(",")
            if len(data) != 5:
                raise ValueError("Invalid chemical sensor data")

            print(f"Date                              : {data[0]}")
            print(f"Time                              : {data[1]}")
            print(f"G Value                           : {data[2]}")
            print(f"H Value                           : {data[3]}")
            print(f"Mode                              : {data[4]}")
            save_chem(payload)

        else:
            print(f"Unknown topic: {topic}")
            print(f"Raw data: {payload}")

    except ValueError as error:
        print(f"Data parsing error: {error}")
        print(f"Raw payload: {payload}")
    finally:
        print("=" * 55)


def main():
    print("Initializing MQTT Subscriber...")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message

    client.connect(BROKER_HOST, BROKER_PORT, keepalive=KEEPALIVE)

    print(f"Connected to MQTT Broker at {BROKER_HOST}:{BROKER_PORT}")

    # Subscribe using values directly loaded from Config.txt
    client.subscribe(BIO_TOPIC)
    client.subscribe(CHEM_TOPIC)
    client.subscribe(FCAD_TOPIC)

    print(f"Subscribed to: {BIO_TOPIC}")
    print(f"Subscribed to: {CHEM_TOPIC}")
    print(f"Subscribed to: {FCAD_TOPIC}")

    client.loop_start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping subscriber...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Subscriber stopped.")


if __name__ == "__main__":
    main()
