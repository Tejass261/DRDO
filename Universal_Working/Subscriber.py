import time
import os
import paho.mqtt.client as mqtt
from datetime import datetime


# ============================================================
# READ CONFIG FILE
# ============================================================

config = {}

with open("config.txt", "r") as file:

    for line in file:

        line = line.strip()

        if line and not line.startswith("#") and "=" in line:

            name, value = line.split("=", 1)

            config[name.strip()] = value.strip()


# ============================================================
# MQTT SETTINGS
# ============================================================

BROKER_HOST = config["broker_host"]
BROKER_PORT = int(config["broker_port"])


BIO_TOPIC = config["bio_topic"]
CHEM_TOPIC = config["chem_topic"]
FCAD_TOPIC = config["fcad_topic"]


# ============================================================
# LOG FOLDERS
# ============================================================

os.makedirs(
    "log/log_bio_sensor",
    exist_ok=True
)

os.makedirs(
    "log/log_chem_sensor",
    exist_ok=True
)

os.makedirs(
    "log/log_fcad_sensor",
    exist_ok=True
)


# ============================================================
# SAVE BIO DATA
# ============================================================

def save_bio(payload):

    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    clock = now.strftime("%H:%M:%S")

    filename = (
        f"log/log_bio_sensor/"
        f"Bio_Sensor_1_{date}.txt"
    )

    with open(filename, "a") as file:

        file.write(
            f"{date},{clock},{payload}\n"
        )


# ============================================================
# SAVE CHEM DATA
# ============================================================

def save_chem(payload):

    # Chem payload already contains date
    date = payload.split(",")[0]

    filename = (
        f"log/log_chem_sensor/"
        f"Chem_Sensor_1_{date}.txt"
    )

    with open(filename, "a") as file:

        file.write(
            payload + "\n"
        )


# ============================================================
# SAVE FCAD DATA
# ============================================================

def save_fcad(payload):

    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    clock = now.strftime("%H:%M:%S")

    filename = (
        f"log/log_fcad_sensor/"
        f"FCAD_Sensor_{date}.txt"
    )

    with open(filename, "a") as file:

        file.write(
            f"{date},{clock},{payload}\n"
        )


# ============================================================
# MQTT MESSAGE CALLBACK
# ============================================================

def on_message(client, userdata, message):

    topic = message.topic

    payload = message.payload.decode(
        "utf-8"
    ).strip()

    print("\n" + "=" * 55)

    print(
        f"Message received from: {topic}"
    )

    print(
        f"Payload: {payload}"
    )


    try:

        if topic == BIO_TOPIC:

            data = payload.split(",")

            if len(data) != 6:

                raise ValueError(
                    "Invalid Bio Sensor data"
                )

            print(
                f"Sample Type: {data[0]}"
            )

            print(
                f"Small Particle Count: {data[1]}"
            )

            print(
                f"Large Particle Count: {data[2]}"
            )

            print(
                f"Small Biological Load: {data[3]}"
            )

            print(
                f"Large Biological Load: {data[4]}"
            )

            print(
                f"Alarm: {data[5]}"
            )

            save_bio(payload)


        elif topic == CHEM_TOPIC:

            data = payload.split(",")

            if len(data) != 5:

                raise ValueError(
                    "Invalid Chem Sensor data"
                )

            print(
                f"Date: {data[0]}"
            )

            print(
                f"Time: {data[1]}"
            )

            print(
                f"G Value: {data[2]}"
            )

            print(
                f"H Value: {data[3]}"
            )

            print(
                f"Mode: {data[4]}"
            )

            save_chem(payload)


        elif topic == FCAD_TOPIC:

            data = payload.split(",")

            if len(data) != 9:

                raise ValueError(
                    "Invalid FCAD Sensor data"
                )

            print(
                f"Sensor Name: {data[0]}"
            )

            print(
                f"G Value: {data[1]}"
            )

            print(
                f"H Value: {data[2]}"
            )

            print(
                f"Atmospheric Pressure G: {data[3]}"
            )

            print(
                f"Atmospheric Pressure H: {data[4]}"
            )

            print(
                f"G Pressure: {data[5]}"
            )

            print(
                f"H Pressure: {data[6]}"
            )

            print(
                f"Battery: {data[7]}"
            )

            print(
                f"Mode: {data[8]}"
            )

            save_fcad(payload)


        else:

            print(
                "Unknown MQTT topic."
            )


    except ValueError as error:

        print(
            f"Data parsing error: {error}"
        )

        print(
            f"Raw payload: {payload}"
        )

    print("=" * 55)


# ============================================================
# MAIN
# ============================================================

def main():

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    client.on_message = on_message


    # Connect to broker

    client.connect(
        BROKER_HOST,
        BROKER_PORT,
        keepalive=60
    )


    # Subscribe to all sensors

    client.subscribe(BIO_TOPIC)
    client.subscribe(CHEM_TOPIC)
    client.subscribe(FCAD_TOPIC)


    print(
        "Connected to MQTT Broker."
    )

    print(
        f"Subscribed to: {BIO_TOPIC}"
    )

    print(
        f"Subscribed to: {CHEM_TOPIC}"
    )

    print(
        f"Subscribed to: {FCAD_TOPIC}"
    )


    # Start MQTT communication

    client.loop_start()


    try:

        while True:

            time.sleep(1)


    except KeyboardInterrupt:

        print(
            "\nStopping Subscriber..."
        )


    finally:

        client.loop_stop()

        client.disconnect()

        print(
            "Subscriber stopped."
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()