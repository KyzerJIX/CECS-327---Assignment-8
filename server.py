import socket
import psycopg


DATABASE_URL = "postgresql://neondb_owner:npg_iOw5uCRl1JGm@ep-winter-cake-a4vqxkkh-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

port = int(input("Enter port: "))

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind(("", port))
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

        message = data.decode().strip().lower()
        print("Received:", message)

        try:
            with psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:

                    if message == "test":
                        cur.execute("SELECT NOW();")
                        result = cur.fetchone()[0]
                        response = f"Database connected. Time: {result}"

                    elif message == "avg moisture":
                        cur.execute("""
                            SELECT AVG((payload->>'Moisture Meter for Fridge2')::float)
                            FROM "Project_virtual"
                            WHERE payload ? 'Moisture Meter for Fridge2';
                        """)
                        result = cur.fetchone()[0]

                        if result is not None:
                            response = f"Average moisture for Fridge2: {result:.2f}"
                        else:
                            response = "No moisture data found."

                    elif message == "avg temp":
                        cur.execute("""
                            SELECT AVG((payload->>'Thermistor for Fridge2')::float)
                            FROM "Project_virtual"
                            WHERE payload ? 'Thermistor for Fridge2';
                        """)
                        result = cur.fetchone()[0]

                        if result is not None:
                            response = f"Average temperature for Fridge2: {result:.2f}"
                        else:
                            response = "No temperature data found."

                    else:
                        response = "Invalid query. Try: test, avg moisture, or avg temp."

        except Exception as e:
            response = f"Database error: {e}"

        client_socket.sendall(response.encode())

    client_socket.close()
