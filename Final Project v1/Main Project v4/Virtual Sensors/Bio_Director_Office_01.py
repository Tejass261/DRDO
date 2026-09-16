import json
import random
import socket
from pathlib import Path

SENSOR_ID = "bio-director-office-01"
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
    small_particle_count = round(random.uniform(350.0, 370.0), 4)
    large_particle_count = round(random.uniform(1900.0, 1950.0), 4)
    small_bio_load = round(random.uniform(3250.0, 3300.0), 4)
    large_bio_load = round(random.uniform(400.0, 500.0), 4)
    alarm = random.choice(["Y", "N"])
    return f"air sample,{small_particle_count},{large_particle_count},{small_bio_load},{large_bio_load},{alarm}"


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((SENSOR["ip"], SENSOR["port"]))
    server.listen(1)
    print("Virtual Bio Sensor: Director Office")
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
        print("Bio Director Office simulator stopped.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
