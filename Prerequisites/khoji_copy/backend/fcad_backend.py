import asyncio
import json
import socket
import time
from datetime import datetime
from pathlib import Path

import websockets


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CONFIG_PATH = BASE_DIR / "Config.json"


with open(
    CONFIG_PATH,
    "r",
    encoding="utf-8"
) as file:

    CONFIG = json.load(file)


FCAD = CONFIG["fcad"]

WEBSOCKET = CONFIG["websocket"]

LOGGING = CONFIG.get(
    "logging",
    {}
)


SENSOR_IP = FCAD["sensor_ip"]

SENSOR_PORT = FCAD["sensor_port"]

DISCOVERY_REQUEST = FCAD["request"]

REQUEST_INTERVAL = float(
    FCAD["request_interval"]
)

SOCKET_TIMEOUT = float(
    FCAD["timeout"]
)


WEBSOCKET_HOST = WEBSOCKET["host"]

WEBSOCKET_PORT = WEBSOCKET["port"]


PRINT_PACKETS = LOGGING.get(
    "print_packets",
    True
)

PRINT_DECODED_DATA = LOGGING.get(
    "print_decoded_data",
    True
)


# ============================================================
# SENSOR CONNECTION STATUS
# ============================================================

connected_clients = set()


# This is the ACTUAL FCAD SENSOR status.
#
# It is NOT the WebSocket status.
#
# True  = valid FCAD data is coming
# False = sensor has missed enough requests
#
sensor_connected = False


# Number of consecutive requests for which
# valid FCAD data was not received.
missed_requests = 0


# Sensor becomes disconnected after four
# consecutive missed responses.
MAX_MISSED_REQUESTS = 4


# ============================================================
# FCAD PACKET DECODER
# ============================================================

def decode_fcad_packet(received):

    """
    Decode the FCAD TT-2 packet.

    The confirmed fields extend through byte 110,
    therefore at least 111 bytes are required.
    """

    if len(received) < 111:

        raise ValueError(
            f"FCAD packet is too short: "
            f"{len(received)} bytes. "
            f"At least 111 bytes are required."
        )


    # ========================================================
    # IDENTIFICATION
    # ========================================================

    unit_name = bytes(
        received[0:17]
    ).decode(
        "ascii",
        errors="ignore"
    ).rstrip(" \x00")


    mac_id = bytes(
        received[17:34]
    ).decode(
        "ascii",
        errors="ignore"
    ).rstrip(" \x00")


    # ========================================================
    # MAIN G / H VALUES
    # ========================================================

    g_value = (
        received[37] >> 4
    ) & 0x0F


    h_value = (
        received[37] & 0x0F
    )


    # ========================================================
    # G RIP / H RIP
    # ========================================================

    ko_rip_g = (
        received[42] * 256
        + received[43]
    ) / 100


    ko_rip_h = (
        received[44] * 256
        + received[45]
    ) / 100


    rip_amp_g = (
        received[46] * 256
        + received[47]
    ) / 100


    rip_amp_h = (
        received[48] * 256
        + received[49]
    ) / 100


    # ========================================================
    # PRESSURE
    # ========================================================

    atmospheric_pressure_g = (
        received[51] * 256
        + received[52]
    )


    atmospheric_pressure_h = (
        received[53] * 256
        + received[54]
    )


    g_pressure = (
        received[55] * 256
        + received[56]
    )


    h_pressure = (
        received[57] * 256
        + received[58]
    )


    # ========================================================
    # RECHARGE / DUTY
    # ========================================================

    hours_run_since_last_recharge = (
        received[59] * 256
        + received[60]
    )


    g_duty = (
        received[61] * 256
        + received[62]
    )


    h_duty = (
        received[63] * 256
        + received[64]
    )


    # ========================================================
    # TEMPERATURE
    #
    # Stored value = actual temperature + 128
    # ========================================================

    body_temperature = (
        received[65] - 128
    )


    nozzle_temperature = (
        received[66] - 128
    )


    # ========================================================
    # BATTERY / HV / FLOW
    # ========================================================

    battery = (
        received[67] * 10
    )


    hv_feedback_g = (
        received[68] / 100
    )


    hv_feedback_h = (
        received[69] / 100
    )


    flow_in_outer_loop = (
        received[70] / 10
    )


    # ========================================================
    # BOARD / HV TEMPERATURES
    # ========================================================

    hv_g_temperature = (
        received[71] - 128
    )


    hv_h_temperature = (
        received[72] - 128
    )


    digital_board_temperature = (
        received[73] - 128
    )


    sensor_board_temperature = (
        received[74] - 128
    )


    display_board_temperature = (
        received[75] - 128
    )


    # ========================================================
    # STATE
    #
    # Only READY / WAITING.
    #
    # Valve OPEN/CLOSED is no longer used.
    # ========================================================

    ready_state = (
        "READY"
        if (received[77] & 2) == 2
        else "WAITING"
    )


    # ========================================================
    # G KO1 / KO2 / KO3
    # ========================================================

    G_KO1 = (
        received[87] * 256
        + received[88]
    ) / 100


    G_KO2 = (
        received[89] * 256
        + received[90]
    ) / 100


    G_KO3 = (
        received[91] * 256
        + received[92]
    ) / 100


    # ========================================================
    # G KO AMPS
    # ========================================================

    Amp_G_KO1 = (
        received[93] * 2
        + received[94] / 100
    ) / 100


    Amp_G_KO2 = (
        received[95] * 2
        + received[96] / 100
    ) / 100


    Amp_G_KO3 = (
        received[97] * 2
        + received[98] / 100
    ) / 100


    # ========================================================
    # H KO1 / KO2 / KO3
    # ========================================================

    H_KO1 = (
        received[99] * 256
        + received[100]
    ) / 100


    H_KO2 = (
        received[101] * 256
        + received[102]
    ) / 100


    H_KO3 = (
        received[103] * 256
        + received[104]
    ) / 100


    # ========================================================
    # H KO AMPS
    # ========================================================

    Amp_H_KO1 = (
        received[105] * 2
        + received[106] / 100
    ) / 100


    Amp_H_KO2 = (
        received[107] * 2
        + received[108] / 100
    ) / 100


    Amp_H_KO3 = (
        received[109] * 2
        + received[110] / 100
    ) / 100


    # ========================================================
    # DATA SENT TO FRONTEND
    # ========================================================

    return {

        # ----------------------------------------------------
        # Identification
        # ----------------------------------------------------

        "sensorName":
            unit_name,

        "macId":
            mac_id,


        # ----------------------------------------------------
        # Main G / H
        # ----------------------------------------------------

        "gValue":
            g_value,

        "hValue":
            h_value,


        # ----------------------------------------------------
        # RIP
        # ----------------------------------------------------

        "koRipG":
            round(
                ko_rip_g,
                2
            ),

        "koRipH":
            round(
                ko_rip_h,
                2
            ),

        "ripAmpG":
            round(
                rip_amp_g,
                2
            ),

        "ripAmpH":
            round(
                rip_amp_h,
                2
            ),


        # ----------------------------------------------------
        # G KO
        # ----------------------------------------------------

        "ko1G":
            round(
                G_KO1,
                2
            ),

        "ko2G":
            round(
                G_KO2,
                2
            ),

        "ko3G":
            round(
                G_KO3,
                2
            ),


        # ----------------------------------------------------
        # G KO Amps
        # ----------------------------------------------------

        "ampGKo1":
            round(
                Amp_G_KO1,
                4
            ),

        "ampGKo2":
            round(
                Amp_G_KO2,
                4
            ),

        "ampGKo3":
            round(
                Amp_G_KO3,
                4
            ),


        # ----------------------------------------------------
        # H KO
        # ----------------------------------------------------

        "ko1H":
            round(
                H_KO1,
                2
            ),

        "ko2H":
            round(
                H_KO2,
                2
            ),

        "ko3H":
            round(
                H_KO3,
                2
            ),


        # ----------------------------------------------------
        # H KO Amps
        # ----------------------------------------------------

        "ampHKo1":
            round(
                Amp_H_KO1,
                4
            ),

        "ampHKo2":
            round(
                Amp_H_KO2,
                4
            ),

        "ampHKo3":
            round(
                Amp_H_KO3,
                4
            ),


        # ----------------------------------------------------
        # Pressure
        # ----------------------------------------------------

        "atmosphericPressureG":
            atmospheric_pressure_g,

        "atmosphericPressureH":
            atmospheric_pressure_h,

        "gPressure":
            g_pressure,

        "hPressure":
            h_pressure,


        # ----------------------------------------------------
        # Recharge / Duty
        # ----------------------------------------------------

        "hoursRunSinceLastRecharge":
            hours_run_since_last_recharge,

        "gDuty":
            g_duty,

        "hDuty":
            h_duty,


        # ----------------------------------------------------
        # Temperature
        # ----------------------------------------------------

        "bodyTemperature":
            body_temperature,

        "nozzleTemperature":
            nozzle_temperature,

        "hvGTemperature":
            hv_g_temperature,

        "hvHTemperature":
            hv_h_temperature,

        "digitalBoardTemperature":
            digital_board_temperature,

        "sensorBoardTemperature":
            sensor_board_temperature,

        "displayBoardTemperature":
            display_board_temperature,


        # ----------------------------------------------------
        # Battery / HV / Flow
        # ----------------------------------------------------

        "battery":
            battery,

        "hvFeedbackG":
            hv_feedback_g,

        "hvFeedbackH":
            hv_feedback_h,

        "flowInOuterLoop":
            flow_in_outer_loop,


        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        "readyState":
            ready_state,


        # ----------------------------------------------------
        # Packet
        # ----------------------------------------------------

        "packetLength":
            len(received)
    }


# ============================================================
# MESSAGE CREATION
# ============================================================

def create_reading(data):

    return {

        "event":
            "reading",

        "sensor":
            "FCAD",

        "id":
            "fcad-main-gate-01",

        "type":
            "fcad",

        "location":
            "main-gate",

        "timestamp":
            datetime.now().isoformat(),

        "data":
            data
    }


def create_sensor_status(
    connected
):

    return {

        "event":
            "sensor_status",

        "connected":
            connected,

        "timestamp":
            datetime.now().isoformat()
    }


# ============================================================
# BROADCAST
# ============================================================

async def broadcast(
    message
):

    if not connected_clients:
        return


    payload = json.dumps(
        message
    )


    disconnected = set()


    for websocket in connected_clients:

        try:

            await websocket.send(
                payload
            )

        except websockets.exceptions.ConnectionClosed:

            disconnected.add(
                websocket
            )


    connected_clients.difference_update(
        disconnected
    )


# ============================================================
# CHANGE SENSOR STATUS
# ============================================================

async def set_sensor_status(
    connected
):

    global sensor_connected


    # Nothing changed.
    if sensor_connected == connected:
        return


    sensor_connected = connected


    if connected:

        print(
            "[FCAD] SENSOR STATUS: "
            "CONNECTED"
        )

    else:

        print(
            "[FCAD] SENSOR STATUS: "
            "DISCONNECTED"
        )


    await broadcast(
        create_sensor_status(
            connected
        )
    )


# ============================================================
# WEBSOCKET HANDLER
# ============================================================

async def websocket_handler(
    websocket
):

    connected_clients.add(
        websocket
    )


    print(
        "[WebSocket] Frontend connected."
    )


    # Send the CURRENT SENSOR status.
    #
    # This does NOT automatically mean connected.
    # The sensor must actually be sending data.

    try:

        await websocket.send(
            json.dumps(
                create_sensor_status(
                    sensor_connected
                )
            )
        )


    except websockets.exceptions.ConnectionClosed:

        connected_clients.discard(
            websocket
        )

        return


    try:

        async for _ in websocket:
            pass


    except websockets.exceptions.ConnectionClosed:

        pass


    finally:

        connected_clients.discard(
            websocket
        )


        print(
            "[WebSocket] Frontend disconnected."
        )


# ============================================================
# FCAD SENSOR LOOP
# ============================================================

async def fcad_loop():

    global missed_requests


    print()
    print("=" * 60)
    print("FCAD BACKEND")
    print("=" * 60)

    print(
        f"Sensor              : "
        f"{SENSOR_IP}"
    )

    print(
        f"Port                : "
        f"{SENSOR_PORT}"
    )

    print(
        f"Request             : "
        f"{DISCOVERY_REQUEST}"
    )

    print(
        f"Request interval    : "
        f"{REQUEST_INTERVAL}s"
    )

    print(
        f"Socket timeout      : "
        f"{SOCKET_TIMEOUT}s"
    )

    print(
        f"Disconnect threshold: "
        f"{MAX_MISSED_REQUESTS} missed requests"
    )

    print(
        f"WebSocket           : "
        f"ws://{WEBSOCKET_HOST}:"
        f"{WEBSOCKET_PORT}"
    )

    print("=" * 60)
    print()


    # ========================================================
    # UDP SOCKET
    # ========================================================

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )


    sock.settimeout(
        SOCKET_TIMEOUT
    )


    try:

        while True:

            # Record the beginning of this request cycle.
            cycle_start = time.monotonic()


            received_valid_data = False


            try:

                # =================================================
                # SEND REQUEST
                # =================================================

                sock.sendto(
                    DISCOVERY_REQUEST.encode(
                        "utf-8"
                    ),
                    (
                        SENSOR_IP,
                        SENSOR_PORT
                    )
                )


                if PRINT_PACKETS:

                    print(
                        "[FCAD] Discovery sent "
                        f"to {SENSOR_IP}:"
                        f"{SENSOR_PORT}"
                    )


                # =================================================
                # RECEIVE RESPONSE
                # =================================================

                received, address = (
                    sock.recvfrom(
                        4096
                    )
                )


                # Only accept packets from the configured sensor.
                if address[0] != SENSOR_IP:

                    print(
                        "[FCAD] Ignored packet "
                        f"from {address[0]}"
                    )


                else:

                    if PRINT_PACKETS:

                        print(
                            "[FCAD] Packet received "
                            f"from {address}"
                        )

                        print(
                            "[FCAD] Packet length: "
                            f"{len(received)} bytes"
                        )


                    # =================================================
                    # DECODE
                    # =================================================

                    decoded_data = (
                        decode_fcad_packet(
                            received
                        )
                    )


                    # If decoding succeeded, this is valid data.
                    received_valid_data = True


                    # =================================================
                    # RESET MISSED REQUEST COUNT
                    # =================================================

                    missed_requests = 0


                    # =================================================
                    # SENSOR IS CONNECTED
                    # =================================================

                    await set_sensor_status(
                        True
                    )


                    # =================================================
                    # PRINT DECODED DATA
                    # =================================================

                    if PRINT_DECODED_DATA:

                        print(
                            "[FCAD] Decoded data:"
                        )

                        print(
                            json.dumps(
                                decoded_data,
                                indent=2
                            )
                        )


                    # =================================================
                    # SEND DATA TO FRONTEND
                    # =================================================

                    await broadcast(
                        create_reading(
                            decoded_data
                        )
                    )


            except socket.timeout:

                print(
                    "[FCAD] No response received."
                )


            except ValueError as error:

                print(
                    "[FCAD] Packet decoding error: "
                    f"{error}"
                )


            except OSError as error:

                print(
                    "[FCAD] Socket error: "
                    f"{error}"
                )


            # ========================================================
            # MISSED REQUEST HANDLING
            # ========================================================

            if not received_valid_data:

                missed_requests += 1


                print(
                    "[FCAD] Missed requests: "
                    f"{missed_requests}/"
                    f"{MAX_MISSED_REQUESTS}"
                )


                if (
                    missed_requests
                    >= MAX_MISSED_REQUESTS
                ):

                    await set_sensor_status(
                        False
                    )


            # ========================================================
            # KEEP REQUEST INTERVAL CONSISTENT
            # ========================================================
            #
            # Instead of always sleeping the full interval after
            # the timeout, compensate for time already spent on
            # the request.
            #
            # This makes the request cycle approximately equal to
            # request_interval.
            # ========================================================

            elapsed = (
                time.monotonic()
                - cycle_start
            )


            remaining = (
                REQUEST_INTERVAL
                - elapsed
            )


            if remaining > 0:

                await asyncio.sleep(
                    remaining
                )


    finally:

        sock.close()


        print(
            "[FCAD] UDP socket closed."
        )


# ============================================================
# WEBSOCKET SERVER
# ============================================================

async def websocket_server():

    print(
        "[WebSocket] Starting server "
        f"on ws://{WEBSOCKET_HOST}:"
        f"{WEBSOCKET_PORT}"
    )


    async with websockets.serve(
        websocket_handler,
        WEBSOCKET_HOST,
        WEBSOCKET_PORT
    ):

        print(
            "[WebSocket] Server started."
        )


        await fcad_loop()


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        asyncio.run(
            websocket_server()
        )


    except KeyboardInterrupt:

        print(
            "\n[Backend] Stopped by user."
        )


if __name__ == "__main__":

    main()