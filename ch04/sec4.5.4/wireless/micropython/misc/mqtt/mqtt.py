import network
import time
from umqtt.simple import MQTTClient
from machine import Pin
import json

class PicoMQTTClient:
    def __init__(self, client_id="pico_w_001", broker="test.mosquitto.org", port=1883):
        self.client_id = client_id
        self.broker = broker
        self.port = port
        self.led = Pin(25, Pin.OUT)
        
        # MQTT topics
        self.status_topic = f"devices/{client_id}/status"
        self.command_topic = f"devices/{client_id}/commands"
        self.telemetry_topic = f"devices/{client_id}/telemetry"
        
        self.mqtt_client = None
        self.setup_mqtt()
    
    def setup_mqtt(self):
        try:
            self.mqtt_client = MQTTClient(
                client_id=self.client_id,
                server=self.broker,
                port=self.port,
                keepalive=60
            )
            
            # Set callback for incoming messages
            self.mqtt_client.set_callback(self.message_callback)
            
            # Connect to broker
            self.mqtt_client.connect()
            
            # Subscribe to command topic
            self.mqtt_client.subscribe(self.command_topic)
            
            print(f"MQTT connected to {self.broker}:{self.port}")
            print(f"Subscribed to: {self.command_topic}")
            
            # Publish online status
            self.publish_status("online")
            
        except Exception as e:
            print(f"MQTT setup error: {e}")
            raise
    
    def message_callback(self, topic, msg):
        try:
            topic_str = topic.decode('utf-8')
            message = msg.decode('utf-8')
            
            print(f"MQTT message: {topic_str} -> {message}")
            
            if topic_str == self.command_topic:
                self.process_command(message)
                
        except Exception as e:
            print(f"Message callback error: {e}")
    
    def process_command(self, command):
        try:
            # Try to parse as JSON first
            try:
                cmd_data = json.loads(command)
                command_type = cmd_data.get('command', '').lower()
                
                if command_type == 'led_on':
                    self.led.value(1)
                    self.publish_status(f"LED turned on by command")
                elif command_type == 'led_off':
                    self.led.value(0)
                    self.publish_status(f"LED turned off by command")
                elif command_type == 'status':
                    self.publish_telemetry()
                else:
                    self.publish_status(f"Unknown command: {command_type}")
                    
            except json.JSONDecodeError:
                # Handle simple text commands
                command = command.lower().strip()
                
                if command == "led_on":
                    self.led.value(1)
                    self.publish_status("LED turned on")
                elif command == "led_off":
                    self.led.value(0)
                    self.publish_status("LED turned off")
                elif command == "status":
                    self.publish_telemetry()
                else:
                    self.publish_status(f"Unknown command: {command}")
                    
        except Exception as e:
            print(f"Command processing error: {e}")
            self.publish_status(f"Command error: {e}")
    
    def publish_status(self, message):
        try:
            payload = {
                "timestamp": time.time(),
                "device": self.client_id,
                "message": message
            }
            
            self.mqtt_client.publish(
                self.status_topic, 
                json.dumps(payload)
            )
            print(f"Status published: {message}")
            
        except Exception as e:
            print(f"Status publish error: {e}")
    
    def publish_telemetry(self):
        try:
            telemetry_data = {
                "timestamp": time.time(),
                "device": self.client_id,
                "uptime": time.ticks_ms(),
                "led_status": bool(self.led.value()),
                "free_memory": gc.mem_free(),
                "temperature": 25.0,  # Placeholder
                "signal_strength": -45  # Placeholder
            }
            
            self.mqtt_client.publish(
                self.telemetry_topic,
                json.dumps(telemetry_data)
            )
            print("Telemetry data published")
            
        except Exception as e:
            print(f"Telemetry publish error: {e}")
    
    def run(self):
        print(f"MQTT Client running - Device ID: {self.client_id}")
        print(f"Command topic: {self.command_topic}")
        print(f"Status topic: {self.status_topic}")
        print(f"Telemetry topic: {self.telemetry_topic}")
        
        last_telemetry = time.time()
        telemetry_interval = 30.0  # 30 seconds
        
        try:
            while True:
                # Check for incoming messages
                self.mqtt_client.check_msg()
                
                # Publish periodic telemetry
                current_time = time.time()
                if current_time - last_telemetry >= telemetry_interval:
                    self.publish_telemetry()
                    last_telemetry = current_time
                
                time.sleep(1)

        except KeyboardInterrupt:
            print("MQTT client shutting down..")
            self.publish_status("offline")
            self.mqtt_client.disconnect()
        except Exception as e:
            print(f"MQTT client error: {e}")
            self.mqtt_client.disconnect()

# MQTT client usage
import gc
mqtt_client = PicoMQTTClient()
mqtt_client.run()

