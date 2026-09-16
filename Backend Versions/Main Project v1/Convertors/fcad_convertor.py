import time
import socket
import paho.mqtt.client as mqtt
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
SENSOR_HOST = values[13]
SENSOR_PORT = int(values[14])

BROKER_HOST = values[6]
BROKER_PORT = int(values[7])

MQTT_TOPIC = values[15]
MQTT_KEEPALIVE = int(values[9])

REQUEST = values[16]
REQUEST_INTERVAL = int(values[8])
SOCKET_TIMEOUT = 2.0            # Seconds to wait for recv() before timing out

# -----------------------------------------------------------------
def convert_data(x):
    b37 = x[37]
    gvalue = (b37 & 0b11110000) >> 4
    hvalue = b37 & 0b00001111

    G_Chemical = x[38]*256+x[39]
    H_Chemical = x[40]*256+x[41]

    ko_rip_G = (x[42]*256+x[43])/100
    ko_rip_H = (x[44]*256+x[45])/100

    rip_amp_g = (x[46]*256+x[47])/100
    rip_amp_h = (x[48]*256+x[49])/100

    atmospheric_pressure_g = x[51] * 256 + x[52]
    atmospheric_pressure_h = x[53] * 256 + x[54]

    g_pressure = x[55] * 256 + x[56]
    h_pressure = x[57] * 256 + x[58]

    hours_run_last_recharge = x[59]*256+x[60]

    G_Duty = x[61] * 256 + x[62]
    H_Duty = x[63] * 256 + x[64]

    Body_Temp = x[65] - 128
    Nozzle_Temp = x[66] - 128

    battery = x[67] * 10

    HV_Feedback_G = x[68]/100
    HV_Feedback_H = x[69]/100

    Flow_Outer_loop = x[70]/10

    HV_Temperature_G = x[71] - 128
    HV_Temperature_H = x[72] - 128
    Digital_Board_temp = x[73] - 128
    Sensor_Board_temp = x[74] - 128
    Display_Board_temp = x[75] - 128

    if(x[76] == 1):
        valve_status = "OPEN"
    else:
        valve_status = "CLOSE"

    mode_masking = x[77] & 0b00000010
    if mode_masking == 2:
        mode = "R"
    else:
        mode = "W"

    payload = (f"TT2_Sensor,{gvalue},{hvalue},{atmospheric_pressure_g},{atmospheric_pressure_h},{g_pressure},{h_pressure},{battery},{mode},{G_Chemical},{H_Chemical},{ko_rip_G},{ko_rip_H},{rip_amp_g},{rip_amp_h},{hours_run_last_recharge},{G_Duty},{H_Duty},{HV_Feedback_G},{HV_Feedback_H},{Flow_Outer_loop},{Body_Temp}{Nozzle_Temp},{HV_Temperature_G},{HV_Temperature_H},{Digital_Board_temp},{Sensor_Board_temp},{Display_Board_temp}")
    return payload

# -----------------------------------------------------------------
def main():
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    mqtt_client.connect(
        BROKER_HOST,
        BROKER_PORT,
        keepalive=MQTT_KEEPALIVE
    )

    mqtt_client.loop_start()

    print("Connected to MQTT Broker")
    print(f"Publishing to: {MQTT_TOPIC}")
    print(f"Automatic requests every {REQUEST_INTERVAL} seconds...\n")

# ---------------------------------------------------------------------
    try:
        client_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set socket timeout so recv() doesn't stuck the code
        client_receiver.settimeout(SOCKET_TIMEOUT)

        while True:
            try:
                client_receiver.sendto(REQUEST.encode(), (SENSOR_HOST, SENSOR_PORT))
                print("Request sent to Sensor...")

                # 2. Receive response (socket.timeout if no reply within 2.0s)
                data = client_receiver.recv(4096)
                received = bytearray(data)

                if len(received) > 77:
                    converted_data = convert_data(received)

                    result = mqtt_client.publish(
                        MQTT_TOPIC,
                        converted_data
                    )

                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        print(f"Published: {converted_data}")
                    else:
                        print("MQTT publish failed.")
                else:
                    print(f"Warning: Received packet too short ({len(received)} bytes)")

                print("-" * 50)
                # Successful exchange
                time.sleep(REQUEST_INTERVAL)

            except socket.timeout:
                print(f"Timeout: No response from sensor. Retrying in {REQUEST_INTERVAL}s...")
                print("-" * 50)
                # Timeout occurred -> wait briefly and re-enter loop to send request again
                time.sleep(REQUEST_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping FCAD Converter...")

    finally:
        client_receiver.close()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("FCAD Converter stopped.")


if __name__ == "__main__":
    main()
