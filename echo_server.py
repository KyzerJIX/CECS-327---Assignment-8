import socket

port = int(input("Enter port: "))

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('', port))
server_socket.listen(1)

print("Server listening...")

client_socket, client_address = server_socket.accept()
print("Connected to", client_address)

while True:
    data = client_socket.recv(1024)

    if not data:
        break

    message = data.decode()
    print("Received:", message)

    response = message.upper()
    client_socket.send(response.encode())

client_socket.close()
server_socket.close()