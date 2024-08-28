import serial
from paho.mqtt import client as mqtt_client
import time
import threading
import logging
import random 

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

baud_rate = 115200

# Serielle Schnittstelle
try:
    ser = serial.Serial('/dev/ttyUSB0', baud_rate, timeout=5)
    logger.info(f"Serial connection established with baud rate {baud_rate}.")
except serial.SerialException as e:
    logger.error(f"Failed to connect to serial port: {e}")
    raise

# MQTT-Setup
broker="mqtt"
port = 1883
client_id = 'serial-proxy'

# Reconnect settings
FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
        else:
            logger.error("Failed to connect, return code %d\n", rc)

    def on_disconnect(client, userdata, flags, rc, properties):
        logger.info("Disconnected with result code: %s", rc)
        reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
        while reconnect_count < MAX_RECONNECT_COUNT:
            logger.info("Reconnecting in %d seconds...", reconnect_delay)
            time.sleep(reconnect_delay)

            try:
                client.reconnect()
                logger.info("Reconnected successfully!")
                return
            except Exception as err:
                logger.error("%s. Reconnect failed. Retrying...", err)

            reconnect_delay *= RECONNECT_RATE
            reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
            reconnect_count += 1
        logger.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)

    client = mqtt_client.Client(client_id=client_id, clean_session=True, userdata=None, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(broker, port)
    return client

# Globale Variablen zur Steuerung
last_sensor_data = {}
lock = threading.Lock()
def process_serial_data():
    global last_sensor_data
    while True:
        try:
            line = ser.readline()
            if line:
                try:
                    decoded_line = line.decode('utf-8').strip()
                except UnicodeDecodeError:
                    logger.warning(f"Failed to decode line using UTF-8: {line}")
                    decoded_line = line.decode('utf-8', errors='ignore').strip()
                    
                with lock:
                    logger.debug(f"Received message on serial port: `{decoded_line}`")
                    topic, message = decoded_line.split(" ", 1)
                    logger.debug(f"Received message on topic `{topic}`: `{message}`")
                    if topic == "arduino/logs":
                        logger.info(message)
                        mqtt_message = f"{topic} {message}"
                    elif topic.startswith("sensor"):
                        last_sensor_data[topic] = message
                        # Format the message for InfluxDB
                        topic_parts = topic.split('/', 1)
                        sensor_type = topic_parts[1]
                        sensor_id = message.split(' ')[0]
                        if sensor_type == "dht":
                            humidity = message.split(' ')[1]
                            temperature = message.split(' ')[2]
                            
                            mqtt_message = f"dht,humidity={humidity},temperature={temperature},sensor_id={sensor_id} value={humidity};{temperature}"
                        else:
                            value = message.split(' ')[1]
                            mqtt_message = f"{sensor_type},sensor_id={sensor_id} value={value}"
                        mqtt_message = f"{mqtt_message} {time.time_ns()}"
                        result = client.publish(topic, mqtt_message)
                        status = result[0]
                        if status == 0:
                            logger.debug(f"Send `{mqtt_message}` to topic `{topic}`")
                        else:
                            logger.error(f"Failed to send message to topic `{topic}`")
        except Exception as e:
            logger.error(f"Error processing serial data: {e}")

        time.sleep(0.1)

def on_message(client, userdata, message):
    global ser
    try:
        command = message.payload.decode('utf-8')
        if command == "REQUEST_DATA":
            ser.write(b'GET_DATA\n')
        elif command == "RESTART":
            ser.setDTR(False)
            time.sleep(1)
            ser.setDTR(True)
        else:
            ser.write(command.encode('utf-8') + b'\n')
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")

# MQTT-Callback setzen
client = connect_mqtt()
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
    logger.info("Exiting program...")
