import json
import time
from datetime import datetime
from pathlib import Path
import paho.mqtt.client as mqtt

PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_DIR / "Config.txt"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)

GLOBAL = CONFIG["global"]
LOG_DIR = PROJECT_DIR / "log"


def save_data(location, sensor_type, sensor_id, payload):
    folder = LOG_DIR / location / sensor_type
    folder.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d")
    path = folder / f"{sensor_id}_{date}.txt"

    with open(path, "a", encoding="utf-8") as file:
        file.write(f"{datetime.now():%Y-%m-%d,%H:%M:%S},{payload}\n")


def display_bio(data):
    if len(data) != 6:
        raise ValueError("Bio data should have 6 fields")
    print(f"Sample Type                       : {data[0]}")
    print(f"Small Particle Count              : {data[1]}")
    print(f"Large Particle Count              : {data[2]}")
    print(f"Small Particle Biological Load    : {data[3]}")
    print(f"Large Particle Biological Load    : {data[4]}")
    print(f"Alarm                             : {data[5]}")


def display_chem(data):
    if len(data) != 5:
        raise ValueError("Chem data should have 5 fields")
    print(f"Date                              : {data[0]}")
    print(f"Time                              : {data[1]}")
    print(f"G Value                           : {data[2]}")
    print(f"H Value                           : {data[3]}")
    print(f"Mode                              : {data[4]}")


def display_fcad(data):
    if len(data) != 9:
        raise ValueError("FCAD data should have 9 fields")
    print(f"Sensor Name                       : {data[0]}")
    print(f"G Value                           : {data[1]}")
    print(f"H Value                           : {data[2]}")
    print(f"Atmospheric Pressure G            : {data[3]}")
    print(f"Atmospheric Pressure H            : {data[4]}")
    print(f"G Pressure                        : {data[5]}")
    print(f"H Pressure                        : {data[6]}")
    print(f"Battery                           : {data[7]}")
    print(f"Mode                              : {data[8]}")


def on_message(client, userdata, message):
    try:
        # Topic format: sensors/location/type/sensor-id
        topic_parts = message.topic.split("/")
        if len(topic_parts) != 4 or topic_parts[0] != "sensors":
            print(f"Ignored topic: {message.topic}")
            return

        location = topic_parts[1]
        sensor_type = topic_parts[2]
        sensor_id = topic_parts[3]
        payload = message.payload.decode("utf-8")
        data = payload.split(",")

        print("\n" + "=" * 55)
        print(f"Location                           : {location}")
        print(f"Sensor Type                        : {sensor_type}")
        print(f"Sensor ID                          : {sensor_id}")

        if sensor_type == "bio":
            display_bio(data)
        elif sensor_type == "chem":
            display_chem(data)
        elif sensor_type == "fcad":
            display_fcad(data)
        else:
            print(f"Raw data                           : {payload}")

        save_data(location, sensor_type, sensor_id, payload)
        print("=" * 55)

    except (UnicodeDecodeError, ValueError, OSError) as error:
        print(f"Data error: {error}")


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        # # means every location, every sensor type and every sensor ID.
        client.subscribe("sensors/#")
        print("Subscribed to all sensor topics: sensors/#")
    else:
        print(f"MQTT connection failed: {reason_code}")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(GLOBAL["ip_broker"], GLOBAL["port_broker"], keepalive=GLOBAL["broker_keep_alive"])
    client.loop_start()

    print("Subscriber started.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping subscriber...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
