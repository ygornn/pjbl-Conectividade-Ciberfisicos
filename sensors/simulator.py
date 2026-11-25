import os
import json
import time
import random
import paho.mqtt.client as mqtt

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="smartspace_sensors"
)

host = os.getenv("MQTT_HOST", "localhost")
username = os.getenv("MQTT_USER")
password = os.getenv("MQTT_PASSWORD")

client.username_pw_set(username, password)

client.connect(host, 1883, 60)
client.loop_start()

rooms = ["room_A", "room_B", "room_C"]

while True:
    for room in rooms:
        data = {
            "temperature": round(random.uniform(20, 30), 1),
            "occupancy": random.randint(0, 1),
            "timestamp": time.time()
        }

        topic = f"pjbl/{room}/environment"

        client.publish(topic, json.dumps(data))

        print(room, data)

    time.sleep(3)
