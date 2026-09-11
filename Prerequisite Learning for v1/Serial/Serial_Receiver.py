import serial
import threading

PORT = "COM2"
BAUDRATE = 9600

ser = serial.Serial(
    port=PORT,
    baudrate=BAUDRATE,
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=0.5
)

running = True


def receive_messages():
    global running

    while running:
        try:
            data = ser.readline()

            if data:
                message = data.decode("utf-8").rstrip("\r\n")
                print(f"Them: {message}")
                print("You: ", end="", flush=True)

        except serial.SerialException:
            print("\nSerial connection error.")
            running = False


receiver_thread = threading.Thread(
    target=receive_messages,
    daemon=True
)

receiver_thread.start()

print(f"Connected to {PORT}")
print("Type messages. Type 'exit' to quit.")

while running:
    try:
        message = input("You: ")

        if message.lower() == "exit":
            running = False
            break

        ser.write((message + "\n").encode("utf-8"))

    except KeyboardInterrupt:
        running = False
        break

ser.close()
print("Serial port closed.")