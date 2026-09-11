import sys
import time
import socket
import paho.mqtt.client as mqtt


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
# GET SENSOR TYPE
# ============================================================

if len(sys.argv) != 2:

    print("Usage:")
    print("python Universal_Converter.py bio")
    print("python Universal_Converter.py chem")
    print("python Universal_Converter.py fcad")

    sys.exit()


sensor_type = sys.argv[1].lower()


# ============================================================
# SENSOR SETTINGS
# ============================================================

if sensor_type == "bio":

    SENSOR_HOST = config["bio_host"]
    SENSOR_PORT = int(config["bio_port"])
    REQUEST = config["bio_request"]
    MQTT_TOPIC = config["bio_topic"]
    REQUEST_INTERVAL = int(config["bio_interval"])
    PROTOCOL = config["bio_protocol"]
    CONVERSION = config["bio_conversion"]


elif sensor_type == "chem":

    SENSOR_HOST = config["chem_host"]
    SENSOR_PORT = int(config["chem_port"])
    REQUEST = config["chem_request"]
    MQTT_TOPIC = config["chem_topic"]
    REQUEST_INTERVAL = int(config["chem_interval"])
    PROTOCOL = config["chem_protocol"]
    CONVERSION = config["chem_conversion"]


elif sensor_type == "fcad":

    SENSOR_HOST = config["fcad_host"]
    SENSOR_PORT = int(config["fcad_port"])
    REQUEST = config["fcad_request"]
    MQTT_TOPIC = config["fcad_topic"]
    REQUEST_INTERVAL = int(config["fcad_interval"])
    PROTOCOL = config["fcad_protocol"]
    CONVERSION = config["fcad_conversion"]


else:

    print("Unknown sensor type.")
    print("Use: bio, chem or fcad")
    sys.exit()


# ============================================================
# MQTT SETTINGS
# ============================================================

BROKER_HOST = config["broker_host"]
BROKER_PORT = int(config["broker_port"])
MQTT_KEEPALIVE = int(config["broker_keepalive"])


# ============================================================
# FCAD CONVERSION
# ============================================================

def convert_fcad(data):

    b37 = data[37]

    gvalue = (b37 & 0b11110000) >> 4
    hvalue = b37 & 0b00001111

    atmospheric_pressure_g = (
        data[51] * 256 + data[52]
    )

    atmospheric_pressure_h = (
        data[53] * 256 + data[54]
    )

    g_pressure = (
        data[55] * 256 + data[56]
    )

    h_pressure = (
        data[57] * 256 + data[58]
    )

    battery = data[67] * 10

    mode_masking = data[77] & 0b00000010

    if mode_masking == 2:
        mode = "R"
    else:
        mode = "W"

    payload = (
        f"TT2_Sensor,"
        f"{gvalue},"
        f"{hvalue},"
        f"{atmospheric_pressure_g},"
        f"{atmospheric_pressure_h},"
        f"{g_pressure},"
        f"{h_pressure},"
        f"{battery},"
        f"{mode}"
    )

    return payload


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(f"Universal Converter: {sensor_type}")
    print("=" * 60)


    # --------------------------------------------------------
    # MQTT
    # --------------------------------------------------------

    mqtt_client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    mqtt_client.connect(
        BROKER_HOST,
        BROKER_PORT,
        keepalive=MQTT_KEEPALIVE
    )

    mqtt_client.loop_start()

    print("Connected to MQTT Broker.")
    print(f"Publishing to: {MQTT_TOPIC}")


    # ========================================================
    # TCP SENSOR
    # ========================================================

    if PROTOCOL == "tcp":

        sensor_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sensor_socket.connect(
            (SENSOR_HOST, SENSOR_PORT)
        )

        print(
            f"Connected to {sensor_type} sensor at "
            f"{SENSOR_HOST}:{SENSOR_PORT}"
        )

        try:

            while True:

                # Send request
                sensor_socket.sendall(
                    REQUEST.encode()
                )

                print("Request sent to sensor.")

                # Receive data
                data = sensor_socket.recv(4096)

                if not data:

                    print("Sensor disconnected.")
                    break

                raw_data = data.decode().strip()

                print(
                    f"Received: {raw_data}"
                )


                # ------------------------------------------------
                # Conversion
                # ------------------------------------------------

                if CONVERSION == "raw":

                    converted_data = raw_data


                # ------------------------------------------------
                # MQTT
                # ------------------------------------------------

                result = mqtt_client.publish(
                    MQTT_TOPIC,
                    converted_data
                )

                if result.rc == mqtt.MQTT_ERR_SUCCESS:

                    print(
                        f"Published: {converted_data}"
                    )

                else:

                    print(
                        "MQTT publish failed."
                    )

                print("-" * 60)

                time.sleep(REQUEST_INTERVAL)


        except KeyboardInterrupt:

            print(
                "\nStopping converter..."
            )

        finally:

            sensor_socket.close()


    # ========================================================
    # UDP SENSOR
    # ========================================================

    elif PROTOCOL == "udp":

        sensor_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        sensor_socket.settimeout(2)

        print(
            f"Ready for UDP sensor at "
            f"{SENSOR_HOST}:{SENSOR_PORT}"
        )

        try:

            while True:

                try:

                    # Send request
                    sensor_socket.sendto(
                        REQUEST.encode(),
                        (SENSOR_HOST, SENSOR_PORT)
                    )

                    print(
                        "Request sent to sensor."
                    )


                    # Receive data
                    data, address = sensor_socket.recvfrom(
                        4096
                    )

                    received = bytearray(data)

                    print(
                        f"Received {len(received)} bytes."
                    )


                    # ------------------------------------------------
                    # Conversion
                    # ------------------------------------------------

                    if CONVERSION == "fcad":

                        if len(received) > 77:

                            converted_data = convert_fcad(
                                received
                            )

                        else:

                            print(
                                "Received packet is too short."
                            )

                            time.sleep(
                                REQUEST_INTERVAL
                            )

                            continue

                    else:

                        converted_data = received.decode()


                    # ------------------------------------------------
                    # MQTT
                    # ------------------------------------------------

                    result = mqtt_client.publish(
                        MQTT_TOPIC,
                        converted_data
                    )

                    if result.rc == mqtt.MQTT_ERR_SUCCESS:

                        print(
                            f"Published: {converted_data}"
                        )

                    else:

                        print(
                            "MQTT publish failed."
                        )

                    print("-" * 60)

                    time.sleep(
                        REQUEST_INTERVAL
                    )


                except socket.timeout:

                    print(
                        "No response from sensor."
                    )

                    print(
                        "Retrying..."
                    )

                    time.sleep(
                        REQUEST_INTERVAL
                    )


        except KeyboardInterrupt:

            print(
                "\nStopping converter..."
            )

        finally:

            sensor_socket.close()


    # ========================================================
    # STOP MQTT
    # ========================================================

    mqtt_client.loop_stop()
    mqtt_client.disconnect()

    print(
        "Universal Converter stopped."
    )


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":
    main()