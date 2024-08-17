import serial
import paho.mqtt.client as mqtt
import time
import threading

# Serielle Schnittstelle
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

# MQTT-Setup
mqtt_broker = "mqtt"  # Docker-Netzwerkname des Brokers
client = mqtt.Client()
client.connect(mqtt_broker)

# Globale Variablen zur Steuerung
last_sensor_data = {}
lock = threading.Lock()

def process_serial_data():
    global last_sensor_data
    while True:
        line = ser.readline().decode('utf-8').strip()
        if line:
            # Daten verarbeiten und veröffentlichen
            with lock:
                topic, message = line.split(" ", 1)
                last_sensor_data[topic] = message
                client.publish(topic, message)
        time.sleep(0.1)

def on_message(client, userdata, message):
    global ser
    command = message.payload.decode('utf-8')
    if command == "REQUEST_DATA":
        ser.write(b'GET_DATA\n')
    else:
        ser.write(command.encode('utf-8') + b'\n')

# MQTT-Callback setzen
client.on_message = on_message
client.subscribe("arduino/commands")
client.loop_start()

# Starten des Threads zum Lesen der seriellen Daten
serial_thread = threading.Thread(target=process_serial_data)
serial_thread.start()

# Haupt-Thread wartet auf serielle Befehle
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ser.close()
    client.loop_stop()
