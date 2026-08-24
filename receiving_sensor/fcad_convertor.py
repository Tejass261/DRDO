import time
import socket
import paho.mqtt.client as mqtt

# ------------------------------------------------------------
values = []

with open("config.txt", "r") as file:
    for line in file:
        line = line.strip()
        if line and "=" in line:
            name, value = line.split("=", 1)
            values.append(value.strip())

# ---------------------------------------------------------------
SENSOR_HOST = values[0]
SENSOR_PORT = int(values[1])

BROKER_HOST = values[2]
BROKER_PORT = int(values[3])

MQTT_TOPIC = values[4]
MQTT_KEEPALIVE = int(values[5])

REQUEST = values[6]
REQUEST_INTERVAL = int(values[7])
SOCKET_TIMEOUT = 2.0            # Seconds to wait for recv() before timing out

# -----------------------------------------------------------------
def convert_data(x):
    b37 = x[37]
    gvalue = (b37 & 0b11110000) >> 4
    hvalue = b37 & 0b00001111

    atmospheric_pressure_g = x[51] * 256 + x[52]
    atmospheric_pressure_h = x[53] * 256 + x[54]
    g_pressure = x[55] * 256 + x[56]
    h_pressure = x[57] * 256 + x[58]

    battery = x[67] * 10

    mode_masking = x[77] & 0b00000010
    if mode_masking == 2:
        mode = "R"
    else:
        mode = "W"

    payload = f"TT2_Sensor,{gvalue},{hvalue},{atmospheric_pressure_g},{atmospheric_pressure_h},{g_pressure},{h_pressure},{battery},{mode}"
    return payload

# -----------------------------------------------------------------
def main():
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    mqtt_client.connect(
        BROKER_HOST,
        BROKER_PORT,
        keepalive=MQTT_KEEPALIVE
    )

    mqtt_client.loop_start()

    print("Connected to MQTT Broker")
    print(f"Publishing to: {MQTT_TOPIC}")
    print(f"Automatic requests every {REQUEST_INTERVAL} seconds...\n")

# ---------------------------------------------------------------------
    try:
        client_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set socket timeout so recv() never hangs indefinitely
        client_receiver.settimeout(SOCKET_TIMEOUT)

        while True:
            try:
                # 1. Send request
                client_receiver.sendto(REQUEST.encode(), (SENSOR_HOST, SENSOR_PORT))
                print("Request sent to Sensor...")

                # 2. Receive response (Will raise socket.timeout if no reply within 2.0s)
                data = client_receiver.recv(4096)
                received = bytearray(data)

                if len(received) > 77:
                    converted_data = convert_data(received)

                    result = mqtt_client.publish(
                        MQTT_TOPIC,
                        converted_data
                    )

                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        print(f"Published: {converted_data}")
                    else:
                        print("MQTT publish failed.")
                else:
                    print(f"Warning: Received packet too short ({len(received)} bytes)")

                print("-" * 50)
                # Successful exchange -> wait the standard interval
                time.sleep(REQUEST_INTERVAL)

            except socket.timeout:
                print(f"Timeout: No response from sensor. Retrying in {REQUEST_INTERVAL}s...")
                print("-" * 50)
                # Timeout occurred -> wait briefly and re-enter loop to send request again
                time.sleep(REQUEST_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping FCAD Converter...")

    finally:
        client_receiver.close()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("FCAD Converter stopped.")


if __name__ == "__main__":
    main()
