from datetime import datetime
from pathlib import Path
import time
import paho.mqtt.client as mqtt

# -----------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

CONFIG_PATH = PROJECT_DIR / "Config.txt"

# -----------------------------------------------------------
values = []

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    for line in file:
        line = line.strip()
        if line and "=" in line:
            name, value = line.split("=", 1)
            values.append(value.strip())

# ---------------------------------------------------------------
BROKER_HOST = values[6]
BROKER_PORT = int(values[7])

BIO_TOPIC = values[10]
CHEM_TOPIC = values[11]
FCAD_TOPIC = values[12]

# ---------------------------------------------------------------
LOG_DIR = PROJECT_DIR / "log"
BIO_LOG_DIR = LOG_DIR / "log_bio_sensor"
CHEM_LOG_DIR = LOG_DIR / "log_chem_sensor"
FCAD_LOG_DIR = LOG_DIR / "log_fcad_sensor"

# Create directories safely
BIO_LOG_DIR.mkdir(parents=True, exist_ok=True)
CHEM_LOG_DIR.mkdir(parents=True, exist_ok=True)
FCAD_LOG_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------
def save_bio(payload):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    clock = now.strftime("%H:%M:%S")

    # Full absolute path to file
    filepath = BIO_LOG_DIR / f"Bio_Sensor_1_{date}.txt"

    with open(filepath, "a", encoding="utf-8") as file:
        file.write(f"{date},{clock},{payload}\n")


def save_chem(payload):
    date = payload.split(",")[0]  # already has date & time

    # Full absolute path to file
    filepath = CHEM_LOG_DIR / f"Chem_Sensor_1_{date}.txt"

    with open(filepath, "a", encoding="utf-8") as file:
        file.write(payload + "\n")


def save_fcad(payload):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    clock = now.strftime("%H:%M:%S")

    # Full absolute path to file
    filepath = FCAD_LOG_DIR / f"fcad_Sensor_{date}.txt"

    with open(filepath, "a", encoding="utf-8") as file:
        file.write(f"{date},{clock},{payload}\n")


# -------------------------------------------------------------------
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

            sample_type = data[0]
            small_particle_count = data[1]
            large_particle_count = data[2]
            small_particle_biological_load = data[3]
            large_particle_biological_load = data[4]
            alarm = data[5]

            print(f"Sample Type                       : {sample_type}")
            print(f"Small Particle Count              : {small_particle_count}")
            print(f"Large Particle Count              : {large_particle_count}")
            print(f"Small Particle Biological Load    : {small_particle_biological_load}")
            print(f"Large Particle Biological Load    : {large_particle_biological_load}")
            print(f"Alarm                             : {alarm}")
            save_bio(payload)

        elif topic == FCAD_TOPIC:
            data = payload.split(",")
            # if len(data) != 28:
            #     raise ValueError("Invalid FCAD sensor data")

            sensor_name = data[0]
            g_value = data[1]
            h_value = data[2]
            atmospheric_pressure_g = data[3]
            atmospheric_pressuer_h = data[4]
            g_pressure = data[5]
            h_pressure = data[6]
            battery = data[7]
            mode = data[8]
            G_Chemical = data[9]
            H_Chemical = data[10]
            G_Ko_RIP = data[11]
            H_Ko_RIP = data[12]
            G_RIP_amp = data[13]
            H_RIP_amp = data[14]
            Hours_run_last_charge = data[15]
            G_Duty = data[16]
            H_Duty = data[17]
            G_HV_Feedback = data[18]
            H_HV_Feedback = data[19]
            Flow_Outer_loop = data[20]
            Body_Temp = data[21]
            Nozzle_Temp = data[22]
            G_HV_Temp = data[23]
            H_HV_Temp = data[24]
            Digital_board_temp = data[25]
            Sensor_board_temp = data[26]
            Display_board_temp = data[27]



            print(f"Sensor Name                         : {sensor_name}")
            print(f"G Value                             : {g_value}")
            print(f"H Value                             : {h_value}")
            print(f"G Pressure                          : {g_pressure}")
            print(f"Atmospheric Pressure G              : {atmospheric_pressure_g}")
            print(f"G_Chemical                          : {G_Chemical}")
            print(f"G_Ko_RIP                            : {G_Ko_RIP}")
            print(f"G_RIP_amp                           : {G_RIP_amp}")
            print(f"G_Duty                              : {G_Duty}")
            print(f"G_HV_Feedback                       : {G_HV_Feedback}")
            print(f"H Pressure                          : {h_pressure}")
            print(f"Atmospheric Pressuer H              : {atmospheric_pressuer_h}")
            print(f"H_Chemical                          : {H_Chemical}")
            print(f"H_Ko_RIP                            : {H_Ko_RIP}")
            print(f"H_RIP_amp                           : {H_RIP_amp}")
            print(f"H_Duty                              : {H_Duty}")
            print(f"H_HV_Feedback                       : {H_HV_Feedback}")
            print(f"Flow_Outer_loop                     : {Flow_Outer_loop}")
            print(f"Battery                             : {battery}")
            print(f"Hours_run_last_charge               : {Hours_run_last_charge}")
            print(f"Mode                                : {mode}")
            print(f"Body_Temp                           : {Body_Temp}")
            print(f"Nozzle_Temp                         : {Nozzle_Temp}")
            print(f"G_HV_Temp                           : {G_HV_Temp}")
            print(f"H_HV_Temp                           : {H_HV_Temp}")
            print(f"Digital_board_temp                  : {Digital_board_temp}")
            print(f"Sensor_board_temp                   : {Sensor_board_temp}")
            print(f"Display_board_temp                  : {Display_board_temp}")

            save_fcad(payload)

        elif topic == CHEM_TOPIC:
            data = payload.split(",")
            if len(data) != 5:
                raise ValueError("Invalid chemical sensor data")

            date = data[0]
            sensor_time = data[1]
            g_value = data[2]
            h_value = data[3]
            mode = data[4]

            print(f"Date                              : {date}")
            print(f"Time                              : {sensor_time}")
            print(f"G Value                           : {g_value}")
            print(f"H Value                           : {h_value}")
            print(f"Mode                              : {mode}")
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

    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    print(f"Connected to MQTT Broker at {BROKER_HOST}:{BROKER_PORT}")

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
