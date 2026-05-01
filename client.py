import socket

# Questions needed for assignment
QUERY_1 = "What is the average moisture inside our kitchen fridges in the past hours, week and month?"
QUERY_2 = "What is the average water consumption per cycle across our smart dishwashers in the past hour, week and month?"
QUERY_3 = "Which house consumed more electricity in the past 24 hours, and by how much?"

SUPPORTED_QUERIES = [QUERY_1, QUERY_2, QUERY_3]

host = input("Enter server IP (use localhost): ").strip()
port = int(input("Enter server port: "))

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((host, port))

print("\nConnected to server!")
print("\nYou must type one of the following EXACT queries:\n")

for q in SUPPORTED_QUERIES:
    print("-", q)

while True:
    message = input("\nEnter query (or type quit): ").strip()

    if message.lower() == "quit":
        break

    if message not in SUPPORTED_QUERIES:
        print("Sorry, this query cannot be processed. Please try one of the supported queries.")
        continue

    client_socket.sendall(message.encode())

    response = client_socket.recv(4096).decode()
    print("\nServer response:")
    print(response)

client_socket.close()

