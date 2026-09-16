import socket
import random
from datetime import datetime
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
HOST = values[3]
PORT = int(values[4])
REQUEST = values[5]


def generate_data():

    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    g_value = random.randint(0, 8)
    h_value = random.randint(0, 8)
    mode = random.choice(["R", "W"])

    return f"{date},{time},{g_value},{h_value},{mode}"


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((HOST, PORT))
    server.listen(1)

    print(f"Chem Sensor listening on {HOST}:{PORT}")

    connection, address = server.accept()
    print(f"Chem Converter connected: {address}")

    try:
        while True:
            request = connection.recv(1024)

            if not request:
                print("Chem Converter disconnected.")
                break

            request = request.decode().lower()

            if request == REQUEST:
                data = generate_data()
                connection.sendall(data.encode())

                print(f"Sensor sent: {data}")

    except ConnectionResetError:
        print("Chem Converter connection lost.")

    finally:
        connection.close()
        server.close()


if __name__ == "__main__":
    main()