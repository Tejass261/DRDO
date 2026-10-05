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
    # TCP messages end with a newline.
    data = b""

    while not data.endswith(b"\n"):
        part = sock.recv(1)

        if not part:
            return None

        data += part

    return data[:-1]


# ============================================================
# FCAD DECODER
# ============================================================

def u16_be(data, index):
    """Read an unsigned 16-bit big-endian integer."""
    return (data[index] << 8) | data[index + 1]


def signed_temp(byte_value):
    """FCAD temperature encoding: stored value - 128."""
    return byte_value - 128


def ascii_field(data, start, end):
    """
    Decode a fixed-width ASCII field.

    Non-printable bytes are preserved as '?' rather than being
    silently discarded. This is useful for diagnosing a bad
    packet without changing the byte positions.
    """
    raw = data[start:end]

    chars = []
    for value in raw:
        if 32 <= value <= 126:
            chars.append(chr(value))
        else:
            chars.append("?")

    return "".join(chars).rstrip(" ?\x00")


def decode_fcad_packet(raw_data):
    """
    Decode the FCAD TT-2 packet.

    The supplied data sheet documents bytes 0-78. Bytes 79+
    are retained as raw bytes because their exact encoding is
    not established by the supplied documentation.
    """

    if len(raw_data) < 79:
        raise ValueError(
            f"FCAD packet is too short: {len(raw_data)} bytes; "
            "at least 79 bytes are required."
        )

    # --------------------------------------------------------
    # Header / identification
    # --------------------------------------------------------

    unit_name = ascii_field(raw_data, 0, 17)
    mac_id = ascii_field(raw_data, 17, 34)

    # --------------------------------------------------------
    # SystemStat[3]
    #
    # Byte 37:
    #   high nibble = G value
    #   low nibble  = H value
    # --------------------------------------------------------

    packed_values = raw_data[37]

    g_value = (packed_values >> 4) & 0x0F
    h_value = packed_values & 0x0F

    # --------------------------------------------------------
    # SystemStat[4] / [6]
    # Two-byte values, big-endian.
    # --------------------------------------------------------

    g_ko_chemical_raw = u16_be(raw_data, 38)
    h_ko_chemical_raw = u16_be(raw_data, 40)

    # --------------------------------------------------------
    # SystemStat[8] / [10]
    # RIP coefficients are stored as integer / 100.
    # --------------------------------------------------------

    ko_rip_g_raw = u16_be(raw_data, 42)
    ko_rip_h_raw = u16_be(raw_data, 44)

    ko_rip_g = ko_rip_g_raw / 100.0
    ko_rip_h = ko_rip_h_raw / 100.0

    # --------------------------------------------------------
    # SystemStat[12] / [14]
    # RIP amplifier values are stored as integer / 100.
    # --------------------------------------------------------

    rip_amp_g_raw = u16_be(raw_data, 46)
    rip_amp_h_raw = u16_be(raw_data, 48)

    rip_amp_g = rip_amp_g_raw / 100.0
    rip_amp_h = rip_amp_h_raw / 100.0

    # --------------------------------------------------------
    # SystemStat[17] / [19]
    # Atmospheric pressure.
    # --------------------------------------------------------

    atmospheric_pressure_g = u16_be(raw_data, 51)
    atmospheric_pressure_h = u16_be(raw_data, 53)

    # --------------------------------------------------------
    # SystemStat[21] / [23]
    # Pressure in Torr.
    # --------------------------------------------------------

    g_pressure = u16_be(raw_data, 55)
    h_pressure = u16_be(raw_data, 57)

    # --------------------------------------------------------
    # SystemStat[25]
    # --------------------------------------------------------

    hours_run_since_last_recharge = u16_be(raw_data, 59)

    # --------------------------------------------------------
    # SystemStat[27] / [29]
    # --------------------------------------------------------

    g_duty = u16_be(raw_data, 61)
    h_duty = u16_be(raw_data, 63)

    # --------------------------------------------------------
    # Temperatures / battery / feedback / flow
    # --------------------------------------------------------

    body_temperature = signed_temp(raw_data[65])
    nozzle_temperature = signed_temp(raw_data[66])

    battery = raw_data[67] * 10

    hv_feedback_g = raw_data[68] / 100.0
    hv_feedback_h = raw_data[69] / 100.0
    flow_in_outer_loop = raw_data[70] / 10.0

    hv_g_temperature = signed_temp(raw_data[71])
    hv_h_temperature = signed_temp(raw_data[72])
    digital_board_temperature = signed_temp(raw_data[73])
    sensor_board_temperature = signed_temp(raw_data[74])
    display_board_temperature = signed_temp(raw_data[75])

    valve_status_raw = raw_data[76]
    valve_status = "OPEN" if valve_status_raw == 1 else "CLOSED"

    ready_state_raw = raw_data[77]
    ready_state = "READY" if ready_state_raw == 2 else "WAIT"

    end_packet = raw_data[78]

    # --------------------------------------------------------
    # Bytes 79+ are present in the supplied Excel capture but
    # their exact field boundaries/scaling are not documented.
    # Keep them untouched for later reverse engineering.
    # --------------------------------------------------------

    unknown_tail = list(raw_data[79:])

    return {
        "sensorName": unit_name,
        "macId": mac_id,

        "gValue": g_value,
        "hValue": h_value,

        "gKoChemical": g_ko_chemical_raw,
        "hKoChemical": h_ko_chemical_raw,

        "koRipG": round(ko_rip_g, 2),
        "koRipH": round(ko_rip_h, 2),

        "ripAmpG": round(rip_amp_g, 2),
        "ripAmpH": round(rip_amp_h, 2),

        "atmosphericPressureG": atmospheric_pressure_g,
        "atmosphericPressureH": atmospheric_pressure_h,

        "gPressure": g_pressure,
        "hPressure": h_pressure,

        "hoursRunSinceLastRecharge": hours_run_since_last_recharge,

        "gDuty": g_duty,
        "hDuty": h_duty,

        "bodyTemperature": body_temperature,
        "nozzleTemperature": nozzle_temperature,

        "battery": battery,

        "hvFeedbackG": round(hv_feedback_g, 2),
        "hvFeedbackH": round(hv_feedback_h, 2),

        "hvGTemperature": hv_g_temperature,
        "hvHTemperature": hv_h_temperature,
        "digitalBoardTemperature": digital_board_temperature,
        "sensorBoardTemperature": sensor_board_temperature,
        "displayBoardTemperature": display_board_temperature,

        "valveStatus": valve_status,
        "valveStatusRaw": valve_status_raw,

        "readyState": ready_state,
        "readyStateRaw": ready_state_raw,

        "endPacket": end_packet,

        "packetLength": len(raw_data),
        "flowInOuterLoop": round(flow_in_outer_loop, 2),

        # The supplied sheet explicitly labels byte 88 as Ko-1 G
        # and byte 104 as Ko-3 H. Their /100 scaling is consistent
        # with the screenshot. Other bytes in this tail are not yet
        # sufficiently documented to decode safely.
        "ko1G": round(raw_data[88] / 100.0, 2) if len(raw_data) > 88 else None,
        "ko3H": round(raw_data[104] / 100.0, 2) if len(raw_data) > 104 else None,

        "unknownTail": unknown_tail,
    }


def convert_data(raw_data):
    """
    Convert raw sensor data into the MQTT payload.

    Bio/Chem behavior is intentionally unchanged.

    FCAD uses JSON because the FCAD packet contains substantially
    more fields than the original 9-field FCAD payload.
    """

    if SENSOR_TYPE["parser"] == "fcad_bytes":
        decoded = decode_fcad_packet(raw_data)
        return json.dumps(decoded, separators=(",", ":"))

    return raw_data.decode("utf-8")


# ============================================================
# TCP
# ============================================================

def run_tcp(client, topic):
    while True:
        sock = None

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((SENSOR["ip"], SENSOR["port"]))

            print(f"Connected to {SENSOR_ID}")

            while True:
                sock.sendall(
                    (SENSOR["request"] + "\n").encode("utf-8")
                )

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

        except (OSError, UnicodeDecodeError, ValueError) as error:
            print(f"Connection error: {error}")

        finally:
            if sock:
                sock.close()

        print("Trying to reconnect...")
        time.sleep(SENSOR["request_interval"])


# ============================================================
# UDP
# ============================================================

def run_udp(client, topic):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)

    try:
        while True:
            try:
                sock.sendto(
                    SENSOR["request"].encode("utf-8"),
                    (SENSOR["ip"], SENSOR["port"])
                )

                data, address = sock.recvfrom(4096)

                if address[0] == SENSOR["ip"]:
                    payload = convert_data(data)

                    if payload:
                        result = client.publish(topic, payload)

                        if result.rc == mqtt.MQTT_ERR_SUCCESS:
                            print(f"Published to {topic}: {payload}")
                        else:
                            print("MQTT publish failed.")
                else:
                    print("Ignored packet from another address.")

            except socket.timeout:
                print("No FCAD response, retrying...")

            except ValueError as error:
                print(f"FCAD packet error: {error}")

            time.sleep(SENSOR["request_interval"])

    finally:
        sock.close()


# ============================================================
# MAIN
# ============================================================

def main():
    topic = make_topic()

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    client.connect(
        GLOBAL["ip_broker"],
        GLOBAL["port_broker"],
        keepalive=GLOBAL["broker_keep_alive"]
    )

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
