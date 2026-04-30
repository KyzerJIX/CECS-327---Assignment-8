import socket
import psycopg


DATABASE_URL = "postgresql://neondb_owner:npg_iOw5uCRl1JGm@ep-winter-cake-a4vqxkkh-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require" #Change for your own code

QUERY_1 = "What is the average moisture inside our kitchen fridges in the past hours, week and month?"
QUERY_2 = "What is the average water consumption per cycle across our smart dishwashers in the past hour, week and month?"
QUERY_3 = "Which house consumed more electricity in the past 24 hours, and by how much?"

# Your JSON keys
MOISTURE_KEY = "Moisture Meter for Fridge2" #Change for your own code
WATER_KEY = "Water consumption sensor 2" #Change for your own code
ELECTRICITY_KEY = "Ammeter for Fridge2"  #Change for your own code

def get_avg(cur, key, interval):
    cur.execute(f"""
        SELECT AVG((payload->>%s)::float)
        FROM "Project_virtual"
        WHERE payload::jsonb ? %s
        AND "createdAt" >= NOW() - %s::interval;
    """, (key, key, interval))
    return cur.fetchone()[0]

def handle_query(message):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            # Moisture
            if message == QUERY_1:
                hour = get_avg(cur, MOISTURE_KEY, "1 hour")
                week = get_avg(cur, MOISTURE_KEY, "7 days")
                month = get_avg(cur, MOISTURE_KEY, "30 days")

                return f"""Moisture Levels:
Past hour: {hour}
Past week: {week}
Past month: {month}"""

            # Dishwasher water
            elif message == QUERY_2:
                hour = get_avg(cur, WATER_KEY, "1 hour")
                week = get_avg(cur, WATER_KEY, "7 days")
                month = get_avg(cur, WATER_KEY, "30 days")

                return f"""Dishwasher Water Usage:
Past hour: {hour}
Past week: {week}
Past month: {month}"""

            # Electricity 
            elif message == QUERY_3: 
                cur.execute("""
                    SELECT SUM((payload->>'Ammeter for Fridge2')::float)
                    FROM "Project_virtual" 
                    WHERE payload::jsonb ? 'Ammeter for Fridge2'
                    AND "createdAt" >= NOW() - INTERVAL '24 hours';
                """)
                total = cur.fetchone()[0]
                 #Change for your own code                                   
                if total is None: 
                    return "No electricity data found."

                return f"Total electricity in last 24 hours: {total:.2f}"

            else:
                return "Invalid query."

# ---- SERVER START ----

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
        data = client_socket.recv(4096)

        if not data:
            print("Client disconnected:", client_address)
            break

        message = data.decode().strip()
        print("Received:", message)

        try:
            response = handle_query(message)
        except Exception as e:
            response = f"Database error: {e}"

        client_socket.sendall(response.encode())

    client_socket.close()
