import asyncio
import json
import re
import threading
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt
import websockets


# ============================================================
# PATHS AND CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_DIR / "Config.txt"
LOG_DIR = PROJECT_DIR / "log"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)

GLOBAL = CONFIG["global"]


# ============================================================
# WEBSOCKET CONFIGURATION
# ============================================================

WEBSOCKET_HOST = "127.0.0.1"
WEBSOCKET_PORT = 8765


# ============================================================
# CONNECTED WEBSOCKET CLIENTS
# ============================================================

connected_clients = set()

# The asyncio event loop used by the WebSocket server.
# MQTT callbacks run in Paho's thread, so we need this
# reference to safely send data from MQTT -> WebSocket.
websocket_loop = None


# ============================================================
# SENSOR INFORMATION
# ============================================================

def build_sensor_list():
    """
    Build a clean list of configured sensors.

    This information is sent to the frontend when it connects
    and every time the configuration changes.
    """

    sensors = []

    for sensor_id, sensor in CONFIG["sensors"].items():

        topic = (
            f"sensors/"
            f"{sensor['location']}/"
            f"{sensor['type']}/"
            f"{sensor_id}"
        )

        sensors.append({
            "id": sensor_id,
            "type": sensor["type"],
            "location": sensor["location"],
            "ip": sensor["ip"],
            "port": sensor["port"],
            "topic": topic
        })

    return sensors


def build_config_message():
    """
    Message sent to the frontend so it knows which sensors
    and which sensor types exist. Sent on connect, and again
    to every client whenever a sensor is added.
    """

    return {
        "event": "config",
        "sensors": build_sensor_list(),
        "sensorTypes": list(
            CONFIG["sensor_types"].keys()
        )
    }


# ============================================================
# LOGGING
# ============================================================

def save_data(location, sensor_type, sensor_id, payload):
    """
    Save the original sensor payload to a daily log file.
    """

    folder = LOG_DIR / location / sensor_type
    folder.mkdir(parents=True, exist_ok=True)

    date = datetime.now().strftime("%Y-%m-%d")

    path = folder / f"{sensor_id}_{date}.txt"

    with open(path, "a", encoding="utf-8") as file:
        file.write(
            f"{datetime.now():%Y-%m-%d,%H:%M:%S},{payload}\n"
        )


# ============================================================
# SENSOR DATA PARSING
# ============================================================

def parse_sensor_data(sensor_type, payload):
    """
    Convert the raw MQTT payload into structured data.

    IMPORTANT:
    This processing happens on the BACKEND.

    React/Electron will NOT parse the raw comma-separated
    sensor payload.
    """

    data = payload.split(",")

    if sensor_type == "bio":

        if len(data) != 6:
            raise ValueError(
                "Bio data should have 6 fields"
            )

        return {
            "sampleType": data[0],
            "smallParticleCount": data[1],
            "largeParticleCount": data[2],
            "smallBiologicalLoad": data[3],
            "largeBiologicalLoad": data[4],
            "alarm": data[5]
        }

    elif sensor_type == "chem":

        if len(data) != 5:
            raise ValueError(
                "Chem data should have 5 fields"
            )

        return {
            "date": data[0],
            "time": data[1],
            "gValue": data[2],
            "hValue": data[3],
            "mode": data[4]
        }

    elif sensor_type == "fcad":

        if len(data) != 9:
            raise ValueError(
                "FCAD data should have 9 fields"
            )

        return {
            "sensorName": data[0],
            "gValue": data[1],
            "hValue": data[2],
            "atmosphericPressureG": data[3],
            "atmosphericPressureH": data[4],
            "gPressure": data[5],
            "hPressure": data[6],
            "battery": data[7],
            "mode": data[8]
        }

    # Unknown sensor type.
    # Keep the raw data in a generic field.
    return {
        "raw": payload
    }


def detect_alarm(sensor_type, parsed_data):
    """
    Decide whether this reading represents an alarm.

    The frontend never parses payloads; it only reads this
    true/false flag.

    - bio sensors send an explicit alarm field ("Y"/"N").
    - chem and fcad payloads have no alarm field, so they
      can never raise an alarm here (always False).
    """

    if sensor_type == "bio":
        return parsed_data.get("alarm") == "Y"

    return False


# ============================================================
# WEBSOCKET BROADCAST
# ============================================================

async def broadcast(data):
    """
    Send data to every connected WebSocket frontend.
    """

    if not connected_clients:
        return

    message = json.dumps(data)

    disconnected_clients = set()

    for client in connected_clients:

        try:
            await client.send(message)

        except websockets.exceptions.ConnectionClosed:
            disconnected_clients.add(client)

    connected_clients.difference_update(
        disconnected_clients
    )


def broadcast_from_mqtt(data):
    """
    MQTT callbacks run in Paho's network thread.

    The WebSocket server runs inside asyncio.

    Therefore, we schedule the broadcast safely on the
    WebSocket event loop.
    """

    if websocket_loop is not None:

        asyncio.run_coroutine_threadsafe(
            broadcast(data),
            websocket_loop
        )


# ============================================================
# ADD SENSOR — VALIDATION AND CONFIG UPDATE
# ============================================================

def validate_sensor_data(sensor):
    """
    Check the sensor information sent by the frontend.

    Returns (clean_sensor_dict, error_message).
    If error_message is not None, the sensor is rejected.
    """

    # ---- Sensor ID ----
    sensor_id = str(sensor.get("id", "")).strip()

    if not sensor_id:
        return None, "Sensor ID is required."

    if "/" in sensor_id or " " in sensor_id:
        return None, "Sensor ID cannot contain spaces or '/' ."

    if sensor_id in CONFIG["sensors"]:
        return None, f"Sensor '{sensor_id}' already exists."

    # ---- Sensor type (must be predefined in Config.txt) ----
    sensor_type = str(sensor.get("type", "")).strip()

    if sensor_type not in CONFIG["sensor_types"]:
        return None, f"Unknown sensor type '{sensor_type}'."

    # ---- Location ----
    location = str(sensor.get("location", "")).strip()

    if not location:
        return None, "Location is required."

    if "/" in location or " " in location:
        return None, "Location cannot contain spaces or '/' ."

    # ---- IP address (simple format check) ----
    ip = str(sensor.get("ip", "")).strip()

    if not re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", ip):
        return None, "IP address must look like 127.0.0.1"

    # ---- Port ----
    try:
        port = int(sensor.get("port"))
    except (TypeError, ValueError):
        return None, "Port must be a number."

    if not 1 <= port <= 65535:
        return None, "Port must be between 1 and 65535."

    # ---- Request string ----
    request = str(sensor.get("request", "")).strip()

    if not request:
        return None, "Request string is required."

    # ---- Request interval ----
    try:
        interval = float(sensor.get("request_interval"))
    except (TypeError, ValueError):
        return None, "Request interval must be a number."

    if interval <= 0:
        return None, "Request interval must be greater than 0."

    clean_sensor = {
        "type": sensor_type,
        "location": location,
        "ip": ip,
        "port": port,
        "request": request,
        "request_interval": interval
    }

    return clean_sensor, None


def save_config():
    """
    Write the in-memory CONFIG back to Config.txt so the
    change survives a restart.
    """

    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump(CONFIG, file, indent=2)


async def handle_add_sensor(websocket, message):
    """
    Handle the "add_sensor" command sent by the frontend.

    1. Validate the data.
    2. Add the sensor to CONFIG and save Config.txt.
    3. Reply to the frontend that sent the command.
    4. Broadcast the new configuration to ALL connected
       frontends so every open window updates automatically.
    """

    sensor = message.get("sensor", {})

    clean_sensor, error = validate_sensor_data(sensor)

    if error is not None:
        await websocket.send(json.dumps({
            "event": "add_sensor_result",
            "success": False,
            "message": error
        }))
        print(f"[Backend] Add sensor rejected: {error}")
        return

    sensor_id = str(sensor.get("id", "")).strip()

    CONFIG["sensors"][sensor_id] = clean_sensor
    save_config()

    print(f"[Backend] Sensor added: {sensor_id}")

    # ---- Reply to the client that sent the command ----
    await websocket.send(json.dumps({
        "event": "add_sensor_result",
        "success": True,
        "message": f"Sensor '{sensor_id}' added successfully.",
        "sensor": {
            "id": sensor_id,
            **clean_sensor
        }
    }))

    # ---- Tell every connected frontend the config changed ----
    await broadcast(build_config_message())


# ============================================================
# WEBSOCKET CLIENT HANDLER
# ============================================================

async def websocket_handler(websocket):
    """
    Handle a frontend WebSocket connection.

    - On connect: send the current configuration.
    - Then: listen for commands coming FROM the frontend
      (for example "add_sensor").
    """

    connected_clients.add(websocket)

    print("[WebSocket] Frontend connected.")

    try:

        # ----------------------------------------------------
        # Send sensor configuration to the frontend.
        # ----------------------------------------------------

        await websocket.send(
            json.dumps(build_config_message())
        )

        # ----------------------------------------------------
        # Listen for messages (commands) from the frontend.
        # The loop ends when the client disconnects.
        # ----------------------------------------------------

        async for raw_message in websocket:

            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                continue

            event = message.get("event")

            if event == "add_sensor":
                await handle_add_sensor(
                    websocket,
                    message
                )

    except websockets.exceptions.ConnectionClosed:
        pass

    finally:

        connected_clients.discard(websocket)

        print(
            "[WebSocket] Frontend disconnected."
        )


# ============================================================
# MQTT MESSAGE CALLBACK
# ============================================================

def on_message(client, userdata, message):

    try:

        # ----------------------------------------------------
        # Expected topic:
        #
        # sensors/location/type/sensor-id
        # ----------------------------------------------------

        topic_parts = message.topic.split("/")

        if (
            len(topic_parts) != 4
            or topic_parts[0] != "sensors"
        ):

            print(
                f"[MQTT] Ignored topic: {message.topic}"
            )

            return

        location = topic_parts[1]
        sensor_type = topic_parts[2]
        sensor_id = topic_parts[3]

        # ----------------------------------------------------
        # Decode MQTT payload.
        # ----------------------------------------------------

        payload = message.payload.decode(
            "utf-8"
        )

        print("\n" + "=" * 60)

        print(
            f"[MQTT] Received from: {sensor_id}"
        )

        print(
            f"[MQTT] Topic: {message.topic}"
        )

        print(
            f"[MQTT] Raw payload: {payload}"
        )

        # ----------------------------------------------------
        # Backend parses the sensor-specific payload.
        # ----------------------------------------------------

        parsed_data = parse_sensor_data(
            sensor_type,
            payload
        )

        # ----------------------------------------------------
        # Backend decides if this reading is an alarm.
        # ----------------------------------------------------

        alarm = detect_alarm(
            sensor_type,
            parsed_data
        )

        # ----------------------------------------------------
        # Save original data to log.
        # ----------------------------------------------------

        save_data(
            location,
            sensor_type,
            sensor_id,
            payload
        )

        # ----------------------------------------------------
        # Create normalized message for frontend.
        # ----------------------------------------------------

        reading = {
            "event": "reading",

            "id": sensor_id,

            "type": sensor_type,

            "location": location,

            "topic": message.topic,

            "receivedAt": datetime.now().isoformat(),

            # Simple true/false flag for the UI LEDs.
            "alarm": alarm,

            "data": parsed_data
        }

        # ----------------------------------------------------
        # Send processed data to WebSocket clients.
        # ----------------------------------------------------

        broadcast_from_mqtt(
            reading
        )

        print(
            "[WebSocket] Reading forwarded to frontend."
        )

        print("=" * 60)

    except (
        UnicodeDecodeError,
        ValueError,
        OSError
    ) as error:

        print(
            f"[Backend] Data error: {error}"
        )


# ============================================================
# MQTT CONNECTION
# ============================================================

def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties=None
):

    if reason_code == 0:

        client.subscribe(
            "sensors/#"
        )

        print(
            "[MQTT] Subscribed to sensors/#"
        )

    else:

        print(
            f"[MQTT] Connection failed: {reason_code}"
        )


# ============================================================
# MQTT THREAD
# ============================================================

def mqtt_thread():

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    client.on_connect = on_connect

    client.on_message = on_message

    client.connect(
        GLOBAL["ip_broker"],
        GLOBAL["port_broker"],
        keepalive=GLOBAL["broker_keep_alive"]
    )

    print(
        "[MQTT] Backend MQTT subscriber started."
    )

    client.loop_forever()


# ============================================================
# WEBSOCKET SERVER
# ============================================================

async def websocket_server():

    global websocket_loop

    websocket_loop = asyncio.get_running_loop()

    print(
        f"[WebSocket] Server starting on "
        f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}"
    )

    async with websockets.serve(
        websocket_handler,
        WEBSOCKET_HOST,
        WEBSOCKET_PORT
    ):

        print(
            "[WebSocket] Server started."
        )

        # Keep the server running forever.
        await asyncio.Future()


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Start MQTT in a background thread.
    # --------------------------------------------------------

    mqtt_worker = threading.Thread(
        target=mqtt_thread,
        daemon=True
    )

    mqtt_worker.start()

    # --------------------------------------------------------
    # Start WebSocket server.
    # --------------------------------------------------------

    try:

        asyncio.run(
            websocket_server()
        )

    except KeyboardInterrupt:

        print(
            "\n[Backend] Backend stopped."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
