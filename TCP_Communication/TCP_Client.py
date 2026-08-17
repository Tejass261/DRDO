import socket
import threading

Client_socket = socket.socket()

Client_socket.connect(("127.0.0.1",5050))
print("Connection to Server at 127.0.0.1:5050 successful")

def receive_messages():
    while True:
        data = Client_socket.recv(1024)

        if not data:
            print("Connection closed.")
            break

        print("\nServer:", data.decode())


receive_thread = threading.Thread(
    target=receive_messages,
    daemon=True
)

receive_thread.start()


while True:
    message = input("You: ")

    if message.lower() == "exit":
        break

    Client_socket.send(message.encode())
Client_socket.close()
