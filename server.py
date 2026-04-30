import socket
import psycopg
from datetime import datetime, timezone, timedelta

# Configuration 

DATABASE_URL = "postgresql://neondb_owner:npg_DHWhPtFO5Gj3@ep-royal-smoke-a4yxy7nt-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

PST = timezone(timedelta(hours=-8))
LITERS_TO_GALLONS = 0.264172

# DataNiz device metadata — sensor keys distinguish House A vs House B
# electricity_keys is a list covering all ammeter devices per house
METADATA = {
    "House A": {
        "moisture_key":    "Moisture Meter1",
        "water_key":       "Flame Sensor Module1",
        "electricity_keys": ["Ammeter 1", "Ammeter2", "Ammeter"],
    },
    "House B": {
        "moisture_key":    "Moisture Meter for Fridge2",
        "water_key":       "Water consumption sensor",
        "electricity_keys": ["Ammeter for Fridge2", "Ammeter for DishWasher", "Ammeter for Fridge"],
    },
}

QUERY_1 = "What is the average moisture inside our kitchen fridges in the past hours, week and month?"
QUERY_2 = "What is the average water consumption per cycle across our smart dishwashers in the past hour, week and month?"
QUERY_3 = "Which house consumed more electricity in the past 24 hours, and by how much?"


# ── Sorted Time-Series Data Structure 
# Keeps (timestamp, value, house) records sorted by timestamp via binary search.
# Used to correctly merge and order readings from both houses.

class SortedTimeSeries:
    def __init__(self):
        self._timestamps = []
        self._records = []  # (timestamp, value, house)

    def insert(self, timestamp, value, house):
        lo, hi = 0, len(self._timestamps)
        while lo < hi:
            mid = (lo + hi) // 2
            if self._timestamps[mid] <= timestamp:
                lo = mid + 1
            else:
                hi = mid
        self._timestamps.insert(lo, timestamp)
        self._records.insert(lo, (timestamp, value, house))

    def values_by_house(self, house):
        return [r[1] for r in self._records if r[2] == house]


#  Database Fetch Helpers 

def fetch_rows(cur, key, interval):
    """Fetch (createdAt, value) for a single sensor key within a time interval."""
    cur.execute("""
        SELECT "createdAt", (payload->>%s)::float
        FROM "MyIoTData_virtual"
        WHERE payload->>%s IS NOT NULL
          AND "createdAt" >= NOW() - %s::interval
    """, (key, key, interval))
    return cur.fetchall()


# Build Series — Single Key 

def build_series(cur, key_type, interval):
    """
    Build a SortedTimeSeries for a single-key sensor type (moisture, water).
    House A and House B are distinguished by their unique sensor key names.
    """
    series = SortedTimeSeries()
    for house, meta in METADATA.items():
        for ts, val in fetch_rows(cur, meta[key_type], interval):
            if val is not None:
                series.insert(ts, val, house)
    return series


# Build Series — Multiple Electricity Keys 

def build_electricity_series(cur, interval):
    """
    Build a SortedTimeSeries summing all ammeter devices per house.
    Each house has 3 ammeter keys; all are fetched and tagged by house,
    so values_by_house() returns combined readings across all 3 devices.
    """
    series = SortedTimeSeries()
    for house, meta in METADATA.items():
        for key in meta["electricity_keys"]:
            for ts, val in fetch_rows(cur, key, interval):
                if val is not None:
                    series.insert(ts, val, house)
    return series


def avg_of(values):
    return sum(values) / len(values) if values else None

def fmt(val, unit=""):
    return f"{val:.4f} {unit}".strip() if val is not None else "No data"


#  Query Handlers 

def handle_query(message):
    now_pst = datetime.now(PST).strftime("%Y-%m-%d %I:%M %p PST")

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            if message == QUERY_1:
                # Moisture: reported per house as % relative humidity
                # % RH requires no imperial conversion
                windows = [
                    ("Past hour",  "1 hour"),
                    ("Past week",  "7 days"),
                    ("Past month", "30 days"),
                ]
                lines = ["Average Moisture (% RH) - Kitchen Fridges:"]
                for label, interval in windows:
                    series = build_series(cur, "moisture_key", interval)
                    avg_a = avg_of(series.values_by_house("House A"))
                    avg_b = avg_of(series.values_by_house("House B"))
                    lines.append(f"\n  {label}:")
                    lines.append(f"    House A: {fmt(avg_a, '%')}")
                    lines.append(f"    House B: {fmt(avg_b, '%')}")
                lines.append(f"\nQueried at {now_pst}")
                return "\n".join(lines)

            elif message == QUERY_2:
                # Water: reported per house, converted from liters to gallons (imperial)
                # Conversion: 1 liter = 0.264172 gallons
                windows = [
                    ("Past hour",  "1 hour"),
                    ("Past week",  "7 days"),
                    ("Past month", "30 days"),
                ]
                lines = ["Average Water Consumption per Cycle (gallons) - Smart Dishwashers:"]
                for label, interval in windows:
                    series = build_series(cur, "water_key", interval)
                    avg_a = avg_of(series.values_by_house("House A"))
                    avg_b = avg_of(series.values_by_house("House B"))
                    gal_a = avg_a * LITERS_TO_GALLONS if avg_a is not None else None
                    gal_b = avg_b * LITERS_TO_GALLONS if avg_b is not None else None
                    lines.append(f"\n  {label}:")
                    lines.append(f"    House A: {fmt(gal_a, 'gal')}")
                    lines.append(f"    House B: {fmt(gal_b, 'gal')}")
                lines.append(f"\nQueried at {now_pst}")
                return "\n".join(lines)

            elif message == QUERY_3:
                # Electricity: sum all 3 ammeter devices per house, then compare
                # House A devices: Ammeter 1, Ammeter2, Ammeter
                # House B devices: Ammeter for Fridge2, Ammeter for DishWasher, Ammeter for Fridge
                # Assumption: Ammeter values in Amps at 120V US residential
                series = build_electricity_series(cur, "24 hours")

                total_a = sum(series.values_by_house("House A")) or 0.0
                total_b = sum(series.values_by_house("House B")) or 0.0
                diff = abs(total_a - total_b)

                if total_a > total_b:
                    winner, loser = "House A", "House B"
                elif total_b > total_a:
                    winner, loser = "House B", "House A"
                else:
                    winner = None

                lines = [
                    "Electricity Usage - Past 24 Hours (All Devices Combined):",
                    f"  House A: {total_a:.4f} A  (Ammeter 1 + Ammeter2 + Ammeter)",
                    f"  House B: {total_b:.4f} A  (Ammeter for Fridge2 + Ammeter for DishWasher + Ammeter for Fridge)",
                ]
                if winner:
                    lines.append(f"\n{winner} consumed more electricity than {loser} by {diff:.4f} A")
                else:
                    lines.append("\nBoth houses consumed equal electricity.")
                lines.append(f"\nQueried at {now_pst}")
                return "\n".join(lines)

            else:
                return "Invalid query."


#  TCP Server 

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
