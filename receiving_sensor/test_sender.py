import socket
import secrets

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("127.0.0.2", 5010))
    print("Ready to Communicate")

    while True:
        request, address = server.recvfrom(1024)
        print("Client Sent Req")

        request = request.decode()

        payload = secrets.token_bytes(100)
        if request == "Discovery":
            server.sendto(payload,address)



if __name__ == "__main__":
        main()