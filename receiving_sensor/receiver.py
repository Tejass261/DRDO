import socket
import time

SENSOR_HOST = "169.254.1.1"
SENSOR_PORT = 30303

REQUEST  = "Discovery"
REQ_INTERVAL = 3


def main():
    try:
        client_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        while True:
            client_receiver.sendto(REQUEST.encode(),(SENSOR_HOST,SENSOR_PORT))
            print("Request sent to Sensor")

            data = client_receiver.recv(4096)
            received = bytearray(data)
            # print(len(received))
            print("Data Received")
            # i = 0
            # while i<119:
            #     print(f"{i}   =   " , received[i])
            #     i+=1

            b37 = received[37]
            b77 = received[77]
            b67 = received[67]

            gvalue = b37 & 0b11110000
            gvalue = gvalue/(16)

            hvalue = b37 & 0b00001111

            battery = b67
            mode = "W"
            if(b77 == 2):
                mode = "R"

            print(f"Battery = {battery}")
            print(f"Hvalue = {hvalue}")
            print(f"Gvalue = {gvalue}")
            print(f"Mode = {mode}")


            time.sleep(REQ_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping Communication")


if __name__ == "__main__":
    main()
