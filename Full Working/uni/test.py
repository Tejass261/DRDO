import time
import socket
import threading
import paho.mqtt.client as mqtt

values = []

with open("config.txt", "r") as file:
    for line in file:
        line = line.strip()

        if line and "=" in line:
            name, value = line.split("=", 1)
            values.append(value.strip())

BROKER_HOST = values[6]
BROKER_PORT = int(values[7])
REQUEST_INTERVAL = int(values[3])


def convert_bio(data):
    """Convert Bio Sensor data. Currently pass-through."""
    return data


def convert_chem(data):
    """Convert Chem Sensor data. Currently pass-through."""
    return data


SENSORS = [
    {
        "name": "Bio Sensor 1",
        "host": values[0],
        "port": int(values[1]),
        "request": values[2],
        "topic": values[10],
        "converter": convert_bio,
    },
    {
        "name": "Chem Sensor 1",
        "host": values[3],
        "port": int(values[4]),
        "request": values[5],
        "topic": values[11],
        "converter": convert_chem,
    },
]


mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)


def process_sensor(sensor):
    name = sensor["name"]
    host = sensor["host"]
    port = sensor["port"]
    request = sensor["request"]
    topic = sensor["topic"]
    converter = sensor["converter"]

    sensor_socket = socket.socket()

    try:
        sensor_socket.connect((host, port))
        print(f"[{name}] Connected to {host}:{port}")

        while True:
            # 1. Request a fresh reading from the sensor.
            sensor_socket.sendall(request.encode("utf-8"))
            print(f"[{name}] Request sent")

            # 2. Receive the sensor response.
            data = sensor_socket.recv(4096)
            if not data:
                print(f"[{name}] Sensor disconnected.")
                break

            raw_data = data.decode("utf-8").strip()
            print(f"[{name}] Received: {raw_data}")

            # 3. Convert the data. Currently this is pass-through.
            converted_data = converter(raw_data)

            # 4. Publish the converted data to this sensor's topic.
            result = mqtt_client.publish(topic, converted_data)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[{name}] Published to {topic}: {converted_data}")
            else:
                print(f"[{name}] MQTT publish failed.")

            print("-" * 60)

            # 5. Wait three seconds before requesting the next reading.
            time.sleep(REQUEST_INTERVAL)

    except ConnectionRefusedError:
        print(f"[{name}] Could not connect to {host}:{port}")
    except (ConnectionResetError, BrokenPipeError):
        print(f"[{name}] Sensor connection was lost.")
    except Exception as error:
        print(f"[{name}] Error: {error}")
    finally:
        sensor_socket.close()
        print(f"[{name}] Socket closed.")


def main():
    print("=" * 60)
    print("             UNIVERSAL SENSOR CONVERTER")
    print("=" * 60)

    print(f"Connecting to MQTT Broker at {BROKER_HOST}:{BROKER_PORT}...")
    mqtt_client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    mqtt_client.loop_start()

    print("Connected to MQTT Broker.")
    print(f"Each sensor is requested every {REQUEST_INTERVAL} seconds.\n")

    # One worker thread per sensor means every sensor gets its own
    # independent 3-second request cycle.
    for sensor in SENSORS:
        thread = threading.Thread(
            target=process_sensor,
            args=(sensor,),
            daemon=True,
        )
        thread.start()

    print(f"Started {len(SENSORS)} sensor workers.")
    print("Universal converter is running...\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Universal Converter...")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("Disconnected from MQTT Broker.")
        print("Universal Converter stopped.")


if __name__ == "__main__":
    main()
