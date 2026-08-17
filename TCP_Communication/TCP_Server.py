import socket
import threading

Server_Socket = socket.socket()
# print(my_socket)

Server_Socket.bind(("127.0.0.1",5050))
print("Binding Server to 127:0.0.1:5050 Successfull")

Server_Socket.listen()
print("Socket Listening...\n")

connection_Socket, client_address = Server_Socket.accept()
print("A Client Connected ", client_address)

def receive_messages():
    while True:
        data = connection_Socket.recv(1024)

        if not data:
            print("Connection closed.")
            break

        print("\nClient:", data.decode())


receive_thread = threading.Thread(
    target=receive_messages,
    daemon=True
)

receive_thread.start()


while True:
    message = input("You: ")
    if message.lower() == "exit":
        break

    connection_Socket.send(message.encode())
connection_Socket.close()