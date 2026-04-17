import socket
import sys

def start_client():
    server_ip = input("Enter the server IP address: ").strip()

    try:
        server_port = int(input("Enter the server port number: ").strip())
    except ValueError:
        print("[ERROR] Invalid port number. Please enter a numeric value.")
        sys.exit(1)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((server_ip, server_port))
        print(f"\n[CLIENT] Connected to server at {server_ip}:{server_port}\n")
    except socket.gaierror:
        print("[ERROR] Invalid IP address. Please check and try again.")
        sys.exit(1)
    except ConnectionRefusedError:
        print("[ERROR] Connection refused. Make sure the server is running and the port is correct.")
        sys.exit(1)
    except OSError as e:
        print(f"[ERROR] Could not connect: {e}")
        sys.exit(1)

    while True:
        message = input("Enter a message to send (or type 'quit' to exit): ").strip()

        if message.lower() == 'quit':
            print("[CLIENT] Closing connection. Goodbye!")
            break

        if not message:
            print("[CLIENT] Message cannot be empty. Please try again.")
            continue

        client_socket.send(message.encode('utf-8'))

        try:
            response = client_socket.recv(1024).decode('utf-8')
            if not response:
                print("[CLIENT] Server closed the connection unexpectedly.")
                break
            print(f"[CLIENT] Server responded: {response}\n")
        except OSError:
            print("[ERROR] Lost connection to the server.")
            break

    client_socket.close()

if __name__ == "__main__":
    start_client()