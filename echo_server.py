import socket

port = int(input("Enter port: "))

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind(('', port))
server_socket.listen(5)

print("Server listening...")

while True:
    client_socket, client_address = server_socket.accept()
    print("Connected to", client_address)

    while True:
        data = client_socket.recv(1024)

        if not data:
            print("Client disconnected:", client_address)
            break

        message = data.decode()
        print("Received:", message)

        response = message.upper()
        client_socket.sendall(response.encode())

    client_socket.close()
