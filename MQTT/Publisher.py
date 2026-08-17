import time
import random
import paho.mqtt.client as mqtt

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
TOPIC = "sensors/environment" 

def main():
    print("Initializing Multi-Sensor Publisher...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    print("Publisher running... sending multi-sensor data.")
    
    try:
        while True:
            temperature = round(random.uniform(20.0, 30.0), 2)
            humidity = round(random.uniform(40.0, 70.0), 2)
            toxicity = round(random.uniform(0.0, 1.5), 2)
            co2 = round(random.uniform(400.0, 1000.0), 1)
            
            payload = f"{temperature},{humidity},{toxicity},{co2}"
            
            result = client.publish(TOPIC, payload)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Published multi-sensor data: [{payload}]")
            else:
                print("Failed to queue message.")
                
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\nStopping publisher...")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()