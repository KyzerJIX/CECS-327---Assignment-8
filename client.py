import socket

host = input("Enter server IP (use localhost): ").strip()
port = int(input("Enter server port: "))

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((host, port))

print("\nConnected to server!\n")

while True:
    message = input("Enter message (avg fridge / test / quit): ").strip()

    if message.lower() == "quit":
        break

    client_socket.sendall(message.encode())

    response = client_socket.recv(4096).decode()
    print("Server:", response, "\n")

client_socket.close()
