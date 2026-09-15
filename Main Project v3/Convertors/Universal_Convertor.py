import json
import socket
import sys
import time
from pathlib import Path
import paho.mqtt.client as mqtt

if len(sys.argv) < 2:
    print("Example: python Universal_Convertor.py bio-main-gate-01")
    sys.exit(1)

SENSOR_ID = sys.argv[1]
CONFIG_PATH = Path(__file__).resolve().parent.parent / "Config.txt"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)

if SENSOR_ID not in CONFIG["sensors"]:
    print(f"Sensor '{SENSOR_ID}' was not found in Config.txt")
    sys.exit(1)

GLOBAL = CONFIG["global"]
SENSOR = CONFIG["sensors"][SENSOR_ID]
SENSOR_TYPE = CONFIG["sensor_types"][SENSOR["type"]]


def make_topic():
    return f"sensors/{SENSOR['location']}/{SENSOR['type']}/{SENSOR_ID}"


def receive_line(sock):
    # TCP messages end with a newline, so one recv cycle gets one complete message.
    data = b""
    while not data.endswith(b"\n"):
        part = sock.recv(1)
        if not part:
            return None
        data += part
    return data[:-1]


def convert_data(raw_data):
    if SENSOR_TYPE["parser"] == "fcad_bytes":
        if len(raw_data) < 78:
            print("FCAD packet is too short.")
            return None

        byte_37 = raw_data[37]
        g_value = (byte_37 & 0b11110000) >> 4
        h_value = byte_37 & 0b00001111
        atmospheric_g = raw_data[51] * 256 + raw_data[52]
        atmospheric_h = raw_data[53] * 256 + raw_data[54]
        g_pressure = raw_data[55] * 256 + raw_data[56]
        h_pressure = raw_data[57] * 256 + raw_data[58]
        battery = raw_data[67] * 10
        mode = "R" if raw_data[77] & 0b00000010 else "W"
        return f"TT2_Sensor,{g_value},{h_value},{atmospheric_g},{atmospheric_h},{g_pressure},{h_pressure},{battery},{mode}"

    return raw_data.decode("utf-8")


def run_tcp(client, topic):
    while True:
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((SENSOR["ip"], SENSOR["port"]))
            print(f"Connected to {SENSOR_ID}")

            while True:
                sock.sendall((SENSOR["request"] + "\n").encode("utf-8"))
                data = receive_line(sock)
                if data is None:
                    print("Sensor disconnected.")
                    break

                payload = convert_data(data)
                if payload:
                    result = client.publish(topic, payload)
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        print(f"Published to {topic}: {payload}")
                    else:
                        print("MQTT publish failed.")
                time.sleep(SENSOR["request_interval"])

        except (OSError, UnicodeDecodeError) as error:
            print(f"Connection error: {error}")
        finally:
            if sock:
                sock.close()

        print("Trying to reconnect...")
        time.sleep(SENSOR["request_interval"])


def run_udp(client, topic):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    try:
        while True:
            try:
                sock.sendto(SENSOR["request"].encode("utf-8"), (SENSOR["ip"], SENSOR["port"]))
                data, address = sock.recvfrom(4096)

                if address[0] == SENSOR["ip"]:
                    payload = convert_data(data)
                    if payload:
                        client.publish(topic, payload)
                        print(f"Published to {topic}: {payload}")
                else:
                    print("Ignored packet from another address.")
            except socket.timeout:
                print("No FCAD response, retrying...")

            time.sleep(SENSOR["request_interval"])
    finally:
        sock.close()


def main():
    topic = make_topic()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(GLOBAL["ip_broker"], GLOBAL["port_broker"], keepalive=GLOBAL["broker_keep_alive"])
    client.loop_start()

    print(f"Running converter for {SENSOR_ID}")
    print(f"Topic: {topic}")

    try:
        if SENSOR_TYPE["protocol"] == "tcp":
            run_tcp(client, topic)
        elif SENSOR_TYPE["protocol"] == "udp":
            run_udp(client, topic)
        else:
            print("Unknown sensor protocol.")
    except KeyboardInterrupt:
        print("Stopping converter...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
