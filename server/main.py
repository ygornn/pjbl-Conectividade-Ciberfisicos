
import os
import json
import time
import math

import paho.mqtt.client as mqtt

from flask import Flask, jsonify, request, render_template

from database import (
    initialize,
    save_measurement,
    get_latest_measurements
)



app = Flask(
    __name__,
    template_folder="../dashboard/templates",
    static_folder="../dashboard/static",
    static_url_path="/static"
)


MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
SENSOR_TIMEOUT_SECONDS = 60

ROOMS = ["room_A", "room_B", "room_C"]


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

initialize()


# ============================================================
# SENSOR CONNECTIVITY
# ============================================================

def is_sensor_connected(timestamp):

    if timestamp is None:
        return False

    elapsed = time.time() - timestamp

    return 0 <= elapsed <= SENSOR_TIMEOUT_SECONDS


# ============================================================
# ROOM INFORMATION
# ============================================================

def get_rooms():

    measurements = get_latest_measurements()

    measurements_by_room = {
        measurement["room"]: measurement
        for measurement in measurements
    }

    result = []

    for room_name in ROOMS:

        measurement = measurements_by_room.get(room_name)

        if measurement is None:
            result.append({
                "room": room_name,
                "connected": False,
                "status": "unknown",
                "temperature": None,
                "occupancy": None,
                "timestamp": None
            })
            continue

        connected = is_sensor_connected(
            measurement["timestamp"]
        )

        occupancy = measurement["occupancy"]

        if not connected:
            status = "unknown"
        elif occupancy == 0:
            status = "available"
        else:
            status = "occupied"

        result.append({
            **measurement,
            "connected": connected,
            "status": status
        })

    return result


# ============================================================
# MQTT CALLBACKS
# ============================================================

def on_connect(client, userdata, flags, reason_code, properties):

    print("Connected to MQTT broker!", flush=True)

    client.subscribe("pjbl/+/environment")

    print("Subscribed to pjbl/+/environment", flush=True)


def on_message(client, userdata, message):

    try:
        room = message.topic.split("/")[1]

        if room not in ROOMS:
            print(f"Unknown room: {room}", flush=True)
            return

        data = json.loads(message.payload.decode())

        required_fields = [
            "temperature",
            "occupancy"
        ]

        if not all(field in data for field in required_fields):
            print("Invalid sensor payload: missing fields", flush=True)
            return

        numeric_fields = [
            "temperature",
            "occupancy"
        ]

        if any(
            isinstance(data[field], bool)
            or not isinstance(data[field], (int, float))
            or not math.isfinite(data[field])
            for field in numeric_fields
        ):
            print("Invalid numeric sensor values", flush=True)
            return

        occupancy = data["occupancy"]

        if not isinstance(occupancy, int) or occupancy < 0:
            print("Invalid occupancy value", flush=True)
            return

       
        data["timestamp"] = time.time()

        save_measurement(room, data)

        print(
            f"Measurement saved: {room} | "
            f"Temperature: {data['temperature']} | "
            f"Occupancy: {data['occupancy']}",
            flush=True
        )

    except (ValueError, KeyError, TypeError) as error:
        print(f"Error processing MQTT message: {error}", flush=True)


# ============================================================
# API ROUTES
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "application": "SmartSpace",
        "status": "running",
        "message": "SmartSpace API is operational"
    })


@app.route("/api/rooms", methods=["GET"])
def rooms_endpoint():

    return jsonify(get_rooms())


@app.route("/api/rooms/<room_name>", methods=["GET"])
def room_endpoint(room_name):

    room = next(
        (r for r in get_rooms() if r["room"] == room_name),
        None
    )

    if room is None:
        return jsonify({"error": "Room not found"}), 404

    return jsonify(room)


@app.route("/api/metrics", methods=["GET"])
def metrics_endpoint():

    rooms = get_rooms()

    connected_rooms = [
        room for room in rooms
        if room["connected"]
    ]

    available_rooms = [
        room for room in connected_rooms
        if room["occupancy"] == 0
    ]

    occupied_rooms = [
        room for room in connected_rooms
        if room["occupancy"] > 0
    ]

    total_occupancy = sum(
        room["occupancy"]
        for room in connected_rooms
    )

    return jsonify({
        "total_occupancy": total_occupancy,
        "available_rooms": len(available_rooms),
        "occupied_rooms": len(occupied_rooms),
        "connected_rooms": len(connected_rooms),
        "rooms_without_current_data": (
            len(rooms) - len(connected_rooms)
        ),
        "total_rooms": len(rooms)
    })

@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("index.html")


# ============================================================
# START MQTT AND FLASK
# ============================================================

if __name__ == "__main__":

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="smartspace_server"
    )

    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connecting to MQTT broker: {MQTT_HOST}", flush=True)

    client.connect(MQTT_HOST, 1883, 60)

    # MQTT runs in a background thread
    client.loop_start()

    print("Starting SmartSpace API on port 8000...", flush=True)

    try:
        app.run(
            host="0.0.0.0",
            port=8000,
            debug=False
        )
    finally:
        client.loop_stop()
        client.disconnect()
