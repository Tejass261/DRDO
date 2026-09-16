import time
import os
import paho.mqtt.client as mqtt
from datetime import datetime
values = []

with open("config.txt", "r") as file:
    for line in file:
        line = line.strip()

        if line and "=" in line:
            name, value = line.split("=", 1)
            values.append(value.strip())


BROKER_HOST = values[6]
BROKER_PORT = int(values[7])

BIO_TOPIC = values[10]
CHEM_TOPIC = values[11]
FCAD_TOPIC = values[12]

os.makedirs("log/log_bio_sensor", exist_ok=True)
os.makedirs("log/log_chem_sensor", exist_ok=True)
os.makedirs("log/log_fcad_sensor", exist_ok=True)
# -----------------------------------------------------------------
def save_bio(payload):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    clock = now.strftime("%H:%M:%S")

    filename = f"log/log_bio_sensor/Bio_Sensor_1_{date}.txt"

    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"{date},{clock},{payload}\n")

def save_chem(payload):
    date = payload.split(",")[0]  # already has dafe & time

    filename = f"log/log_chem_sensor/Chem_Sensor_1_{date}.txt"

    with open(filename, "a", encoding="utf-8") as file:
        file.write(payload + "\n")

def save_fcad(payload):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    clock = now.strftime("%H:%M:%S")

    filename = f"log/log_fcad_sensor/fcad_Sensor_{date}.txt"

    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"{date},{clock},{payload}\n")
# -------------------------------------------------------------------
def on_message(client, userdata,message):

    topic = message.topic
    payload = message.payload.decode("utf-8")

    print("\n" + "=" * 55)
    print(f"Message received from: {topic}")

    try:


        if topic == BIO_TOPIC:

            data = payload.split(",")

            if len(data) != 6:
                raise ValueError(
                    "Invalid biological sensor data"
                )

            sample_type = data[0]
            small_particle_count = data[1]
            large_particle_count = data[2]
            small_particle_biological_load = data[3]
            large_particle_biological_load = data[4]
            alarm = data[5]

            print(f"Sample Type                       : {sample_type}")
            print(f"Small Particle Count              : {small_particle_count}")
            print(f"Large Particle Count              : {large_particle_count}")
            print(
                f"Small Particle Biological Load   : "
                f"{small_particle_biological_load}"
            )
            print(
                f"Large Particle Biological Load   : "
                f"{large_particle_biological_load}"
            )
            print(f"Alarm                              : {alarm}")
            save_bio(payload)

        if topic == FCAD_TOPIC:

            data = payload.split(",")

            if len(data) != 9:
                raise ValueError(
                    "Invalid FCAD sensor data"
                )

            sensor_name = data[0]
            g_value = data[1]
            h_value = data[2]
            atmospheric_pressure_g = data[3]
            atmospheric_pressuer_h = data[4]
            g_pressure = data[5]
            h_pressure = data[6]
            battery = data[7]
            mode = data[8]

            print(f"Sensor Name                         : {sensor_name}")
            print(f"G Value                             : {g_value}")
            print(f"H Value                             : {h_value}")
            print(f"Atmospheric Pressure G              : {atmospheric_pressure_g}")
            print(f"Atmospheric Pressuer H              : {atmospheric_pressuer_h}")
            print(f"G Pressure                          : {g_pressure}")
            print(f"H Pressure                          : {h_pressure}")
            print(f"Battery                             : {battery}")
            print(f"Mode                                : {mode}")
            save_fcad(payload)

        elif topic == CHEM_TOPIC:

            data = payload.split(",")

            if len(data) != 5:
                raise ValueError(
                    "Invalid chemical sensor data"
                )

            date = data[0]
            sensor_time = data[1]
            g_value = data[2]
            h_value = data[3]
            mode = data[4]

            print(f"Date                               : {date}")
            print(f"Time                               : {sensor_time}")
            print(f"G Value                            : {g_value}")
            print(f"H Value                            : {h_value}")
            print(f"Mode                               : {mode}")

            save_chem(payload)
        else:

            print(f"Unknown topic: {topic}")
            print(f"Raw data: {payload}")

    except ValueError as error:

        print(f"Data parsing error: {error}")
        print(f"Raw payload: {payload}")
    finally:
        # print(log updated)
        print("=" * 55)



def main():

    print("Initializing MQTT Subscriber...")

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    client.on_message = on_message



    client.connect(
        BROKER_HOST,
        BROKER_PORT,
        keepalive=60
    )

    print(
        f"Connected to MQTT Broker at "
        f"{BROKER_HOST}:{BROKER_PORT}"
    )


    client.subscribe(BIO_TOPIC)
    client.subscribe(CHEM_TOPIC)
    client.subscribe(FCAD_TOPIC)

    print(f"Subscribed to: {BIO_TOPIC}")
    print(f"Subscribed to: {CHEM_TOPIC}")
    print(f"Subscribed to: {FCAD_TOPIC}")


    client.loop_start()            #MQTT communication is going on here in its own thread (internal working)

    try:

        while True:                # This stops Python script from ending
            time.sleep(1)

    except KeyboardInterrupt:

        print("\nStopping subscriber...")

    finally:

        client.loop_stop()
        client.disconnect()

        print("Subscriber stopped.")


if __name__ == "__main__":
    main()