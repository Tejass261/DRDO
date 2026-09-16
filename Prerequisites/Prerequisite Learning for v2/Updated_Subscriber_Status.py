import json
import socket
import sys
import time
from pathlib import Path
import paho.mqtt.client as mqtt

# -----------------------------------------------------------
# 1. READ SENSOR NAME FROM COMMAND-LINE
# -----------------------------------------------------------
if len(sys.argv) < 2:
    print("Error: Missing sensor name!")
    print("Usage Example: python universal_converter.py bio_sensor")
    sys.exit(1)

SENSOR_TO_RUN = sys.argv[1]

# -----------------------------------------------------------
# 2. LOAD CONFIG.TXT (JSON / DICTIONARY)
# -----------------------------------------------------------
CONFIG_PATH = Path(__file__).resolve().parent.parent / "Config.txt"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)

if SENSOR_TO_RUN not in CONFIG["sensors"]:
    print(f"Error: Sensor '{SENSOR_TO_RUN}' not found in Config.txt")
    sys.exit(1)

# Extract Global Settings
BROKER_HOST = CONFIG["global"]["ip_broker"]
BROKER_PORT = CONFIG["global"]["port_broker"]
KEEPALIVE = CONFIG["global"]["broker_keep_alive"]

# Extract Selected Sensor Settings
sensor_cfg = CONFIG["sensors"][SENSOR_TO_RUN]

SENSOR_HOST = sensor_cfg["ip"]
SENSOR_PORT = sensor_cfg["port"]
PROTOCOL = sensor_cfg["protocol"]
REQUEST = sensor_cfg["request"]
INTERVAL = sensor_cfg["request_interval"]
TOPIC = sensor_cfg["topic"]
PARSER_NAME = sensor_cfg["parser"]

# Topic to publish converter status (for UI)
STATUS_TOPIC = f"{TOPIC}/status"


# -----------------------------------------------------------
# 3. CONVERT DATA
# -----------------------------------------------------------
def convert_data(raw_data):
    if PARSER_NAME == "fcad_bytes":
        if len(raw_data) <= 77:
            return None
        b37 = raw_data[37]
        gvalue = (b37 & 0b11110000) >> 4
        hvalue = b37 & 0b00001111
        atm_g = raw_data[51] * 256 + raw_data[52]
        atm_h = raw_data[53] * 256 + raw_data[54]
        g_press = raw_data[55] * 256 + raw_data[56]
        h_press = raw_data[57] * 256 + raw_data[58]
        battery = raw_data[67] * 10
        mode = "R" if (raw_data[77] & 0b00000010) == 2 else "W"
        return f"TT2_Sensor,{gvalue},{hvalue},{atm_g},{atm_h},{g_press},{h_press},{battery},{mode}"
    else:
        return raw_data.decode("utf-8")


# -----------------------------------------------------------
# 4. MAIN WORKFLOW (WITH RESILIENT RECONNECT & UI STATES)
# -----------------------------------------------------------
def main():
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.connect(BROKER_HOST, BROKER_PORT, keepalive=KEEPALIVE)
    mqtt_client.loop_start()

    print(f"Starting Universal Converter for: [{SENSOR_TO_RUN}]")
    print(f"Data Topic: {TOPIC} | Status Topic: {STATUS_TOPIC}\n")

    # -----------------------------------------------------------
    # TCP Handling (Bio / Chem)
    # -----------------------------------------------------------
    if PROTOCOL == "tcp":
        while True:
            sock = None
            try:
                # 1. Attempt connection
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)  # Don't freeze forever on connect
                sock.connect((SENSOR_HOST, SENSOR_PORT))
                sock.settimeout(None) # Reset timeout for normal stream operation

                print(f"Successfully connected to {SENSOR_TO_RUN}!")
                mqtt_client.publish(STATUS_TOPIC, "ACTIVE")

                # 2. Data Transfer Loop
                while True:
                    sock.sendall(REQUEST.encode())
                    data = sock.recv(4096)

                    # Empty data means remote socket closed connection
                    if not data:
                        raise ConnectionResetError("Sensor closed connection.")

                    payload = convert_data(data)
                    if payload:
                        mqtt_client.publish(TOPIC, payload)
                        mqtt_client.publish(STATUS_TOPIC, "ACTIVE")
                        print(f"Published: {payload}")

                    time.sleep(INTERVAL)

            except (socket.error, ConnectionResetError, OSError) as e:
                # 3. Handle Disconnect / Unreachable Sensor
                print(f"Sensor unreachable or disconnected ({e}). Retrying in {INTERVAL}s...")
                mqtt_client.publish(STATUS_TOPIC, "OFFLINE")

            finally:
                if sock:
                    sock.close()

            time.sleep(INTERVAL)

    # -----------------------------------------------------------
    # UDP Handling (FCAD)
    # -----------------------------------------------------------
    elif PROTOCOL == "udp":
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)

        try:
            while True:
                try:
                    sock.sendto(REQUEST.encode(), (SENSOR_HOST, SENSOR_PORT))
                    data, _ = sock.recvfrom(4096)

                    payload = convert_data(data)
                    if payload:
                        mqtt_client.publish(TOPIC, payload)
                        mqtt_client.publish(STATUS_TOPIC, "ACTIVE")
                        print(f"Published: {payload}")

                except socket.timeout:
                    print("No response from sensor, retrying...")
                    mqtt_client.publish(STATUS_TOPIC, "OFFLINE")

                time.sleep(INTERVAL)
        finally:
            sock.close()


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
