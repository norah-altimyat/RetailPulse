import json
import random
import time
from datetime import datetime
from kafka import KafkaProducer

BOOTSTRAP_SERVER = "localhost:9092"
TOPIC = "retail-events"

PRODUCTS = ["Laptop", "Smartphone", "Headphones", "Webcam", "Desk Lamp"]
COUNTRIES = ["USA", "UK", "Germany", "Japan", "Australia"]

def make_event(i):
    return {
        "order_id": f"ORD-{100000 + i}",
        "product_id": random.choice(PRODUCTS),
        "country": random.choice(COUNTRIES),
        "price": round(random.uniform(5, 120), 2),
        "quantity": random.randint(1, 4),
        "event_time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    }

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

print("Starting Producer...")

i = 0

try:
    while True:
        event = make_event(i)
        producer.send(TOPIC, event)
        print("Sent:", event)
        i += 1
        time.sleep(1)

except KeyboardInterrupt:
    print("Producer stopped.")

finally:
    producer.flush()
    producer.close()
