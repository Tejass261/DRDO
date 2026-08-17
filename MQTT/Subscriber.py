import time
import paho.mqtt.client as mqtt

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
TOPIC = "sensors/environment"

def on_message(client, userdata, msg):
    payload_str = msg.payload.decode("utf-8")
    
    data_parts = payload_str.split(",")
    
    try:
        temperature = float(data_parts[0])
        humidity = float(data_parts[1])
        toxicity = float(data_parts[2])
        co2 = float(data_parts[3])
        
        print(f"\n--- Data Received on [{msg.topic}] ---")
        print(f"  Temperature : {temperature}°C")
        print(f"  Humidity    : {humidity}%")
        print(f"  Toxicity    : {toxicity} ppm")
        print(f"  CO2 Levels  : {co2} ppm")
        
        
    except (IndexError, ValueError) as e:
        print(f"Error parsing incoming payload: {payload_str}. Error: {e}")

def main():
    print("Initializing Multi-Sensor Subscriber...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.subscribe(TOPIC)
    print(f"Subscribed to topic: {TOPIC}. Listening for multi-sensor streams...")
    
    client.loop_start()
    
    try:
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping subscriber...")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()