
import os
import sqlite3

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "/data/smartrooms.db"
)


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize():
    # Create the database directory if necessary
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            temperature REAL,
            occupancy INTEGER,
            timestamp REAL NOT NULL
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_measurements_room_timestamp
        ON measurements (room, timestamp)
    """)

    connection.commit()
    connection.close()

    print(f"Database initialized: {DATABASE_PATH}", flush=True)


def save_measurement(room, data):
    connection = get_connection()

    try:
        connection.execute("""
            INSERT INTO measurements (
                room,
                temperature,
                occupancy,
                timestamp
            )
            VALUES (?, ?, ?, ?)
        """, (
            room,
            data["temperature"],
            data["occupancy"],
            data["timestamp"]
        ))

        connection.commit()

    finally:
        connection.close()

def get_latest_measurements():
    connection = get_connection()

    try:
        rows = connection.execute("""
            SELECT m.*
            FROM measurements m
            INNER JOIN (
                SELECT room, MAX(id) AS latest_id
                FROM measurements
                GROUP BY room
            ) latest ON m.id = latest.latest_id
            ORDER BY m.room
        """).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()
