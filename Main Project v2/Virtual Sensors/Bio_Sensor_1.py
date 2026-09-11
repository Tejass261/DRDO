import json
import random
import socket
from pathlib import Path

# Load Config
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR.parent / "Config.txt"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)

HOST = CONFIG["sensors"]["bio_sensor"]["ip"]
PORT = CONFIG["sensors"]["bio_sensor"]["port"]
REQUEST = CONFIG["sensors"]["bio_sensor"]["request"]


def generate_data():
    small_particle_count = round(random.uniform(350.0, 370.0), 4)
    large_particle_count = round(random.uniform(1900.0, 1950.0), 4)
    small_particle_biological_load = round(random.uniform(3250.0, 3300.0), 4)
    large_particle_biological_load = round(random.uniform(400.0, 500.0), 4)
    alarm = random.choice(["Y", "N"])

    return (
        f"air sample,"
        f"{small_particle_count},"
        f"{large_particle_count},"
        f"{small_particle_biological_load},"
        f"{large_particle_biological_load},"
        f"{alarm}"
    )


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)

    print(f"Bio Sensor listening on {HOST}:{PORT}")

    try:
        while True:
            connection, address = server.accept()
            print(f"Bio Converter connected: {address}")

            try:
                while True:
                    request = connection.recv(1024)

                    if not request:
                        print("Bio Converter disconnected.")
                        break

                    request = request.decode().lower()

                    if request == REQUEST.lower():
                        data = generate_data()
                        connection.sendall(data.encode())
                        print(f"Sensor sent: {data}")
            finally:
                connection.close()

    except ConnectionResetError:
        print("Bio Converter connection lost.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
