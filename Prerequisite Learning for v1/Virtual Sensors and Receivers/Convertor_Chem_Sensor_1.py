import time
import socket
import paho.mqtt.client as mqtt

values = []

with open("config.txt", "r") as file:
    for line in file:
        line = line.strip()

        if line and "=" in line:
            name, value = line.split("=", 1)
            values.append(value.strip())


SENSOR_HOST = values[3]
SENSOR_PORT = int(values[4])

BROKER_HOST = values[6]
BROKER_PORT = int(values[7])

MQTT_TOPIC = values[11]
MQTT_KEEPALIVE = int(values[9])

REQUEST = values[5]
REQUEST_INTERVAL = int(values[8])



def main():


    sensor_socket = socket.socket()

    sensor_socket.connect((SENSOR_HOST, SENSOR_PORT))

    print(
        f"Connected to Chem Sensor at "
        f"{SENSOR_HOST}:{SENSOR_PORT}"
    )


    mqtt_client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    mqtt_client.connect(
        BROKER_HOST,
        BROKER_PORT,
        keepalive= MQTT_KEEPALIVE
    )

    mqtt_client.loop_start()

    print("Connected to MQTT Broker")
    print(f"Publishing to: {MQTT_TOPIC}")
    print(f"Automatic requests every {REQUEST_INTERVAL} seconds...\n")

    try:

        while True:


            sensor_socket.sendall(
                REQUEST.encode()
            )

            print("Request sent to Chem Sensor")


            data = sensor_socket.recv(4096)

            if not data:
                print("Chem Sensor disconnected.")
                break

            raw_data = data.decode()

            print(f"Received: {raw_data}")


            result = mqtt_client.publish(
                MQTT_TOPIC,
                raw_data
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(
                    f"Published: {raw_data}"
                )
            else:
                print("MQTT publish failed.")

            print("-" * 50)


            time.sleep(REQUEST_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping Chem Converter...")

    finally:
        sensor_socket.close()

        mqtt_client.loop_stop()
        mqtt_client.disconnect()

        print("Chem Converter stopped.")


if __name__ == "__main__":
    main()