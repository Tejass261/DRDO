import socket
import random
from pathlib import Path
# -----------------------------------------------------------
# Config File Path
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR.parent/"Config.txt"
# ------------------------------------------------------------
values = []

with open(CONFIG_PATH, "r") as file:
    for line in file:
        line = line.strip()
        if line and "=" in line:
            name, value = line.split("=", 1)
            values.append(value.strip())

# ---------------------------------------------------------------
HOST = values[0]
PORT = int(values[1])
REQUEST = values[2]


def generate_data():

    small_particle_count = round(random.uniform(350.0, 370.0), 4)
    large_particle_count = round(random.uniform(1900.0, 1950.0), 4)
    small_particle_biological_load = round(random.uniform(3250.0, 3300.0), 4)  #Ab it doesn't gets defined repetedly only called.
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

            while True:
                request = connection.recv(1024)

                if not request:
                    print("Bio Converter disconnected.")
                    break

                request = request.decode().lower()

                if request == REQUEST:
                    data = generate_data()
                    connection.sendall(data.encode())

                    print(f"Sensor sent: {data}")

    except ConnectionResetError:
        print("Bio Converter connection lost.")

    finally:
        # connection.close()
        server.close()


if __name__ == "__main__":
    main()