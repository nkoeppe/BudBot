from math import ceil
from paho.mqtt import client as mqtt_client
import threading
import time
import json
from collections import deque

class SensorHubController:
    def __init__(self, logger, config_manager, mqtt_broker="mqtt", mqtt_port=1883):
        threading.Thread.__init__(self)
        self.logger = logger
        self.config_manager = config_manager
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.running = False
        self.last_sensor_data = {}
        self.sensor_readings = {}  # Dictionary to store the last n readings for each sensor
        self.max_readings = self.config_manager.get('sensor_hub.max_readings', 10)  # Get max_readings from config
        self.subscribed_topics = []  # Keep track of subscribed topics

        self.logger.debug("Initializing SensorHubController with MQTT broker: %s, port: %d", mqtt_broker, mqtt_port)
        
        self.client = mqtt_client.Client(client_id="sensor_hub_controller", clean_session=True, userdata=None, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
        self.client.connect(mqtt_broker, mqtt_port)
        self.load_subscriptions()
        
        self.load_sensors()
    
        self.client.loop_start()
        self.logger.info("SensorHubController initialized and connected to MQTT broker: %s, port: %d", mqtt_broker, mqtt_port)

        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        
    def load_subscriptions(self):
        topics = self.config_manager.get('sensor_hub.subscribed_topics', [])
        self.logger.debug(f"Loading subscriptions for topics: {topics}")
        for topic in topics:
            self.subscribe_topic(topic)

    def load_sensors(self):
        self.clear_all()
        sensors = self.config_manager.get('sensor_hub.sensors', {})
        for label, sensor in sensors.items():
            if sensor['type'].startswith('dht'):
                self.add_dht_sensor(label, sensor)
            else:
                self.add_sensor(label, sensor)
        self.set_interval(ceil(self.config_manager.get('sensor_hub.interval', 5000)/self.max_readings))

    def set_interval(self, interval):
        self.send_command(f"SET_INTERVAL {interval}")

    def add_sensor(self, label, sensor):
        self.logger.debug(f"Adding sensor: {label}")
        self.send_command(f"ADD_SENSOR {sensor['pin']} {sensor['type']} {sensor['id']}")
        self.subscribe_topic(f"sensor/{sensor['type']}")
        self.logger.info(f"Added sensor: {label} on pin: {sensor['pin']}")
        sensors = self.config_manager.get('sensor_hub.sensors', {})
        if label not in sensors:
            sensors[label] = sensor
            self.config_manager.set('sensor_hub.sensors', sensors)
            self.logger.debug(f"Added sensor to config: {label}")
        return True

    def add_dht_sensor(self, label, sensor):
        self.logger.debug(f"Adding DHT sensor: {label}")
        self.send_command(f"ADD_SENSOR {sensor['pin']} {sensor['type']} {sensor['id']}")
        self.subscribe_topic(f"sensor/{sensor['type']}")
        self.logger.info(f"Added DHT sensor: {label} on pin: {sensor['pin']}")
        sensors = self.config_manager.get('sensor_hub.sensors', {})
        if label not in sensors:
            sensors[label] = sensor
            self.config_manager.set('sensor_hub.sensors', sensors)
            self.logger.debug(f"Added DHT sensor to config: {label}")
        return True

    def remove_sensor(self, label):
        sensors = self.config_manager.get('sensor_hub.sensors', {})
        if label in sensors:
            sensor = sensors[label]
            self.logger.debug(f"Removing sensor: {label}")
            self.send_command(f"REMOVE_SENSOR {sensor['pin']}")
            self.logger.info(f"Removed sensor: {label} on pin: {sensor['pin']}")
            del sensors[label]
            self.config_manager.set('sensor_hub.sensors', sensors)
            self.logger.debug(f"Removed sensor from config: {label}")
            return True
        else:
            self.logger.warning(f"Attempted to remove non-existent sensor: {label}")
        return False
        
    def subscribe_topic(self, topic):
        self.logger.debug(f"Subscribing to topic: {topic}")
        if topic not in self.subscribed_topics:
            result, mid = self.client.subscribe(topic)
            if result == 0:
                self.subscribed_topics.append(topic)
                self.logger.info(f"Subscribed to topic: {topic}")
            else:
                self.logger.error(f"Failed to subscribe to topic: {topic}")
        if topic not in self.config_manager.get('sensor_hub.subscribed_topics', []):
            self.config_manager.add_to_array('sensor_hub.subscribed_topics', topic)
            self.logger.debug(f"Added topic to config: {topic}")

    def unsubscribe_topic(self, topic):
        self.logger.debug(f"Unsubscribing from topic: {topic}")
        self.client.unsubscribe(topic)
        self.logger.info(f"Unsubscribed from topic: {topic}")
        if topic in self.subscribed_topics:
            self.subscribed_topics.remove(topic)
        if topic in self.config_manager.get('sensor_hub.subscribed_topics', []):
            self.config_manager.remove_from_array('sensor_hub.subscribed_topics', topic)
            self.logger.info(f"Removed topic from config: {topic}")

    def run(self):
        self.running = True
        self.client.loop_start()
        while self.running:
            time.sleep(1)  # Add a small delay to prevent high CPU usage

    def stop(self):
        self.running = False
        self.close()

    def read_sensor_data(self, topic):
        self.logger.debug("Subscribing to topic: %s", topic)
        self.client.subscribe(topic)
        self.client.on_message = self.on_message
        self.client.loop_forever()

    def calibrate_sensor(self, label, dry_value, wet_value):
        """
        Calibrate a sensor with dry and wet values.

        :param label: Label of the sensor
        :param dry_value: Value read when sensor is completely dry
        :param wet_value: Value read when sensor is completely wet
        """
        sensors = self.config_manager.get('sensor_hub.sensors', {})
        if label in sensors:
            sensors[label]['configuration'] = {
                "dry_value": dry_value,
                "wet_value": wet_value
            }
            self.config_manager.set('sensor_hub.sensors', sensors)
            self.logger.info(f"Sensor {label} calibrated with dry_value={dry_value}, wet_value={wet_value}")
        else:
            self.logger.warning(f"Attempted to calibrate non-existent sensor: {label}")

    def get_calibration(self, label):
        """
        Get calibration data for a sensor.

        :param label: Label of the sensor
        :return: Calibration data dictionary or None if not calibrated
        """
        sensors = self.config_manager.get('sensor_hub.sensors', {})
        if label in sensors and 'configuration' in sensors[label]:
            return sensors[label]['configuration']
        return None

    def convert_to_percentage(self, label, raw_value):
        """
        Convert a raw sensor value to a percentage based on calibration.

        :param label: Label of the sensor
        :param raw_value: Raw value from the sensor
        :return: Moisture percentage or None if sensor is not calibrated
        """
        calibration = self.get_calibration(label)
        if not calibration:
            self.logger.debug(f"Sensor {label} is not calibrated")
            return None

        dry_value = calibration['dry_value']
        wet_value = calibration['wet_value']
        
        # Ensure the raw_value is within the calibrated range
        raw_value = max(min(raw_value, dry_value), wet_value)
        
        # Calculate percentage (0% is dry, 100% is wet)
        percentage = (dry_value - raw_value) / (dry_value - wet_value) * 100
        return round(percentage, 2)

    def calibrate_sensor_auto(self, label, calibration_time=15, delay=1):
        """
        Automatically calibrate a sensor by taking measurements over a specified time period.

        :param label: Label of the sensor
        :param calibration_time: Duration of calibration in seconds (default: 15)
        :param delay: Delay between samples in seconds (default: 1)
        """
        self.logger.info(f"Starting auto-calibration for sensor {label}")
        
        sensors = self.config_manager.get('sensor_hub.sensors', {})
        if label not in sensors:
            self.logger.error(f"Sensor {label} not found")
            return

        sensor = sensors[label]
        # topic = f"{measurement}/{sensor_id}]"
        topic = f"{sensor['type']}_{sensor['id']}"

        # Set the sampling interval on the Arduino
        self.set_interval(ceil((delay * 500)/self.max_readings))  # Convert seconds to milliseconds
        
        readings = set()
        start_time = time.time()
        
        while time.time() - start_time < calibration_time:
            last_sensor_data = self.get_latest_sensor_data_by_sensor_id(topic)
            self.logger.info(f"Last sensor data: {last_sensor_data}")
            if last_sensor_data and 'value' in last_sensor_data:
                try:
                    self.logger.info(f"Raw data: {last_sensor_data['value']}")
                    readings.add(float(last_sensor_data['value']))
                except ValueError:
                    self.logger.error(f"Invalid sensor data for {label}: {last_sensor_data['value']}")
            time.sleep(delay/10)

        if readings:
            dry_value = max(readings)  # Highest value is considered dry
            wet_value = min(readings)  # Lowest value is considered wet
            self.calibrate_sensor(label, dry_value, wet_value)
            self.logger.info(f"Auto-calibration complete for sensor {label}. Dry: {dry_value}, Wet: {wet_value}")
        else:
            self.logger.error(f"No valid readings obtained for sensor {label} during auto-calibration")

        # Reset the sampling interval on the Arduino to default (if needed)
        self.set_interval(ceil(self.config_manager.get('sensor_hub.interval', 5000)/self.max_readings))  # Reset to 5 seconds, adjust as needed
        
    def on_message(self, client, userdata, message):
        raw_data = message.payload.decode('utf-8')
        self.logger.debug("Received data on topic: %s, payload: %s", message.topic, raw_data)
        try:
            
# dht,humidity={humidity},temperature={temperature},sensor_id={sensor_id} value={humidity};{temperature} {timestamp}"
# soil_moisture,sensor_id=0 value=277 1724263913.2976274
            measurement, rest = raw_data.split(',', 1)
            self.logger.debug(f"Measurement: {measurement}, Rest: {rest}")
            values, timestamp = rest.rsplit(' ', 1)  # Extract and remove the timestamp
            self.logger.debug(f"Values: {values}, Timestamp: {timestamp}")
            fields, value = values.rsplit(' ', 1)  # Extract and remove the timestamp
            self.logger.debug(f"Fields: {fields}, Value: {value}")
            data = {}
            for field in fields.split(','):
                self.logger.debug(f"Field: {field}")
                key, field = field.split('=')
                data[key] = field
            sensor_id = data['sensor_id']
                
            data['value'] = value.split('=')[1]
            
            sensor_data_label = f"{measurement}_{sensor_id}"
            
            if message.topic.startswith('sensor/dht'):
                self.update_dht_sensor_readings(sensor_data_label, data)
            else:
                percentage = self.convert_to_percentage(sensor_data_label, float(data['value']))
                self.update_sensor_readings(sensor_data_label, percentage, **data)
            if sensor_data_label in self.last_sensor_data:
                self.logger.debug(f"Sensor {sensor_id} data: {self.last_sensor_data[sensor_data_label]}")
                self.publish_sensor_data(f"processed_{message.topic}", measurement, self.last_sensor_data[sensor_data_label])
        except ValueError as err:
            self.logger.error(err)
            self.logger.error(f"Invalid sensor data received for measurement {measurement}: {raw_data}")
            self.last_sensor_data[sensor_data_label] = {"raw_value": raw_data, "percentage": None, "last_updated_at": time.time()}
    
    def update_sensor_readings(self, label, percentage, **data):
        """
        Update the sensor readings with the new value and calculate the average.

        :param label: Label of the sensor
        :param value: New sensor value
        :param percentage: New sensor percentage
        """
        try:
            value = float(data.get('value'))
            if label not in self.sensor_readings:
                self.sensor_readings[label] = deque(maxlen=self.max_readings)
            
            self.sensor_readings[label].append({"value": value, "percentage": percentage})
            values = [reading["value"] for reading in self.sensor_readings[label]]
            percentages = [reading["percentage"] for reading in self.sensor_readings[label]]
            
            if len(values) == 0 or len(percentages) == 0:
                average_value = -1
                average_percentage = -1
            else:
                average_value = sum(values) / len(values)
                average_percentage = sum(percentages) / len(percentages)
            
            self.last_sensor_data[label] = {
                "value": round(average_value, 2),
                "percentage": round(average_percentage, 2),
                "last_updated_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                **data
            }
        except Exception as err:
            self.logger.error(f"Error updating sensor readings: {err}")

    def update_dht_sensor_readings(self, label, data):
        try:
            if label not in self.sensor_readings:
                self.sensor_readings[label] = deque(maxlen=self.max_readings)
            
            data['temperature'] = float(data['temperature'])
            data['humidity'] = float(data['humidity'])
            self.sensor_readings[label].append(data)
            
            temperature_values = [float(reading['temperature']) for reading in self.sensor_readings[label]]
            humidity_values = [float(reading['humidity']) for reading in self.sensor_readings[label]]
            
            if len(temperature_values) == 0 or len(humidity_values) == 0:
                average_temperature = -1
                average_humidity = -1
            else:
                average_temperature = sum(temperature_values) / len(temperature_values)
                average_humidity = sum(humidity_values) / len(humidity_values)
            
            self.last_sensor_data[label] = {
                "temperature": round(average_temperature, 2),
                "humidity": round(average_humidity, 2),
                "last_updated_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                **data
            }
        except Exception as err:
            self.logger.error(f"Error updating DHT sensor readings: {err}")

    def publish_sensor_data(self, topic, sensor_type, data):
        # msg = {
        #     "measurement": sensor_type,
        #     "tags": {
        #         "sensor_id": data['sensor_id']
        #     },
        #     "fields": data,
        #     "timestamp": time.time_ns()
        # }
        data['measurement'] = sensor_type
        data['timestamp'] = time.time_ns()
        
        self.logger.debug(f"Publishing sensor data to topic: {topic}, data: {data}")
        self.client.publish(f"{topic}", json.dumps(data))
        
    def on_disconnect(self, client, userdata, flags, rc, properties):
        self.logger.info("Disconnected with result code: %s", rc)
        self.reconnect()

    def reconnect(self):
        self.logger.info("Attempting to reconnect to MQTT broker...")
        while not self.client.is_connected():
            try:
                self.client.reconnect()
                self.logger.info("Reconnected successfully!")
                return
            except Exception as e:
                self.logger.error("Reconnect failed: %s. Retrying...", e)
                time.sleep(5)  # Wait before retrying

    def close(self):
        self.client.loop_stop()  # Stop the MQTT client loop
        self.client.disconnect()  # Disconnect from the MQTT broker
        self.logger.info("MQTT client stopped and disconnected from broker")
    
    def send_command(self, command):
        """
        Sends a command to the Arduino via MQTT.

        :param command: The command to be sent to the Arduino.
        """
        self.logger.debug("Sending command to Arduino: %s", command)
        self.client.publish("arduino/commands", command)
        self.logger.info("Command sent successfully: %s", command)
    
    def get_latest_sensor_data(self):
        """
        Returns the last received sensor data.

        :return: The last received sensor data.
        """
        return self.last_sensor_data

    def get_latest_sensor_data_by_sensor_id(self, sensor_id):
        """
        Returns the last received sensor data.

        :return: The last received sensor data.
        """
        return self.last_sensor_data.get(sensor_id)

    def get_sensors(self):
        """
        Get all sensors from the configuration.

        :return: Dictionary of all sensors
        """
        return self.config_manager.get('sensor_hub.sensors', {})

    def get_subscribed_topics(self):
        """
        Get all subscribed topics.

        :return: List of subscribed topics
        """
        return self.config_manager.get('sensor_hub.subscribed_topics', [])

    def clear_all(self):
        """
        Hard reset arduino to the initial defaults

        """
        self.send_command("CLEAR_ALL")

    def set_max_readings(self, value):
        self.max_readings = value
        self.config_manager.set('sensor_hub.max_readings', value)
        # Update existing deques
        for sensor in self.sensor_readings:
            self.sensor_readings[sensor] = deque(self.sensor_readings[sensor], maxlen=value)
        self.set_interval(ceil(self.config_manager.get('sensor_hub.interval', 5000)/self.max_readings))
        
    def restart_arduino(self):
        self.send_command("RESTART")
        