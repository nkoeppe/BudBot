import pigpio
import time
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class CapacitiveMoistureSensor:
    def __init__(self, pin, min_moisture=0, max_moisture=1023):
        self.pin = pin
        self.min_moisture = min_moisture
        self.max_moisture = max_moisture
        self.pi = pigpio.pi('gpio_deamon')
        if not self.pi.connected:
            logger.error("Failed to connect to pigpio daemon")
            raise RuntimeError("Failed to connect to pigpio daemon")
        self.pi.set_mode(self.pin, pigpio.INPUT)
        logger.info(f"Capacitive Moisture Sensor initialized on pin {self.pin}")

    def read_raw(self):
        # Read the raw value from the sensor
        raw_value = self.pi.read(self.pin)
        logger.debug(f"Raw moisture reading from pin {self.pin}: {raw_value}")
        return raw_value

    def read_moisture(self):
        # Read the moisture level and convert to percentage
        raw_value = self.read_raw()
        moisture_percentage = self.convert_to_percentage(raw_value)
        logger.info(f"Moisture level on pin {self.pin}: {moisture_percentage}%")
        return moisture_percentage

    def convert_to_percentage(self, raw_value):
        # Convert the raw value to a percentage
        moisture_range = self.max_moisture - self.min_moisture
        moisture_percentage = ((raw_value - self.min_moisture) / moisture_range) * 100
        return max(0, min(100, moisture_percentage))  # Ensure the result is between 0 and 100

    def calibrate(self, samples=10, delay=1):
        logger.info(f"Starting calibration for sensor on pin {self.pin}")
        readings = []
        for _ in range(samples):
            readings.append(self.read_raw())
            time.sleep(delay)
        
        self.min_moisture = min(readings)
        self.max_moisture = max(readings)
        logger.info(f"Calibration complete. Min: {self.min_moisture}, Max: {self.max_moisture}")

    def __del__(self):
        if self.pi.connected:
            self.pi.stop()
            logger.debug(f"Pigpio connection closed for sensor on pin {self.pin}")
