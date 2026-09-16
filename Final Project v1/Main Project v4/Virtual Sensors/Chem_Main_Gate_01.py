import json
import random
import socket
from datetime import datetime
from pathlib import Path

SENSOR_ID = "chem-main-gate-01"
CONFIG_PATH = Path(__file__).resolve().parent.parent / "Config.txt"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)

SENSOR = CONFIG["sensors"][SENSOR_ID]


def receive_line(connection):
    data = b""
    while not data.endswith(b"\n"):
        part = connection.recv(1)
        if not part:
            return None
        data += part
    return data[:-1].decode("utf-8")


def generate_data():
    now = datetime.now()
    g_value = random.randint(0, 8)
    h_value = random.randint(0, 8)
    mode = random.choice(["R", "W"])
    return f"{now:%Y-%m-%d},{now:%H:%M:%S},{g_value},{h_value},{mode}"


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((SENSOR["ip"], SENSOR["port"]))
    server.listen(1)
    print("Virtual Chem Sensor: Main Gate")
    print(f"Listening on {SENSOR['ip']}:{SENSOR['port']}")

    try:
        while True:
            connection, address = server.accept()
            print(f"Converter connected: {address}")
            try:
                while True:
                    request = receive_line(connection)
                    if request is None:
                        break
                    if request.lower() == SENSOR["request"].lower():
                        payload = generate_data()
                        connection.sendall((payload + "\n").encode("utf-8"))
                        print(f"Sent: {payload}")
            finally:
                connection.close()
    except KeyboardInterrupt:
        print("Chem Main Gate simulator stopped.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
