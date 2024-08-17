import logging
import schedule
import asyncio
from datetime import datetime
from app.sensors.capacitive_moisture_sensor import CapacitiveMoistureSensor

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class EventController:
    """
    Manages the scheduling and triggering of events for the grow system.
    Supports both time-based events and sensor-based triggers.
    """
    
    def __init__(self, water_nutrient_controller, config_manager, logger):
        """
        Initialize the EventController with the WaterNutrientController instance and ConfigManager.

        :param water_nutrient_controller: Instance of WaterNutrientController used to control watering and nutrient distribution.
        :param config_manager: Instance of ConfigManager for accessing and updating configuration.
        :param logger: Logger instance for logging.
        """
        self.logger = logger
        self.logger.debug("Initializing EventController")
        self.water_nutrient_controller = water_nutrient_controller
        self.config_manager = config_manager
        self.load_config()
        self.reapply_rules()
        self.logger.debug("EventController initialized with the following configuration:")
        self.logger.debug("Moisture Sensors: %s", self.moisture_sensors)
        self.logger.debug("Moisture Thresholds: %s", self.moisture_thresholds)
        self.logger.debug("Scheduled Events: %s", self.scheduled_events)

    def load_config(self):
        config = self.config_manager.get('event', {})
        self.moisture_sensors = config.get('moisture_sensors', {})
        self.moisture_thresholds = config.get('moisture_thresholds', {})
        self.scheduled_events = config.get('scheduled_events', [])
        self.logger.debug("Configuration loaded: %s", config)

    def reload_config(self):
        """
        Reloads the configuration for the EventController.
        """
        self.logger.debug("Reloading configuration for EventController")
        self.load_config()
        self.reapply_rules()
        self.logger.info("Configuration reloaded for EventController")
        
    def reapply_rules(self):
        """
        Reapplies the saved rules from the configuration.
        """
        self.logger.debug("Reapplying saved rules")
        for event in self.scheduled_events:
            time_of_day = event.get('time_of_day', '08:00')
            self.schedule_daily_watering(time_of_day)
        self.logger.info("Reapplied saved rules")

    def schedule_daily_watering(self, time_of_day="08:00"):
        """
        Schedules the daily watering and nutrient distribution at the specified time.

        :param time_of_day: String representing the time of day to start the watering process (in 24-hour format, e.g., '08:00').
        """
        
        self.logger.debug("Scheduling daily watering at %s", time_of_day)
        schedule.every().day.at(time_of_day).do(self.water_nutrient_controller.run_watering_cycle)
        if {'time_of_day': time_of_day} not in self.scheduled_events:
            self.scheduled_events.append({'time_of_day': time_of_day})
            self.config_manager.set('event', {'scheduled_events': self.scheduled_events})
        self.logger.info("Scheduled daily watering at %s", time_of_day)

    def add_moisture_sensor(self, sensor_id, pin, threshold):
        """
        Adds a new moisture sensor to be monitored.

        :param sensor_id: Unique identifier for the sensor
        :param pin: GPIO pin number the sensor is connected to
        :param threshold: Moisture threshold to trigger watering
        """
        self.logger.debug("Adding moisture sensor: id=%s, pin=%d, threshold=%d", sensor_id, pin, threshold)
        self.moisture_sensors[sensor_id] = CapacitiveMoistureSensor(pin)
        self.moisture_thresholds[sensor_id] = threshold
        self.config_manager.set('moisture_sensors', self.moisture_sensors)
        self.config_manager.set('moisture_thresholds', self.moisture_thresholds)
        self.logger.info("Moisture sensor added: id=%s", sensor_id)

    def remove_moisture_sensor(self, sensor_id):
        """
        Removes a moisture sensor from monitoring.

        :param sensor_id: Unique identifier for the sensor to remove
        """
        self.logger.debug("Removing moisture sensor: id=%s", sensor_id)
        if sensor_id in self.moisture_sensors:
            del self.moisture_sensors[sensor_id]
            del self.moisture_thresholds[sensor_id]
            self.config_manager.set('moisture_sensors', self.moisture_sensors)
            self.config_manager.set('moisture_thresholds', self.moisture_thresholds)
            self.logger.info("Moisture sensor removed: id=%s", sensor_id)
        else:
            self.logger.warning("Attempted to remove non-existent sensor: id=%s", sensor_id)

    async def monitor_events(self):
        """
        Continuously checks and runs scheduled tasks and monitors moisture sensors.
        This function should be run as an asynchronous task in the main event loop.
        """
        self.logger.debug("Starting event monitoring")
        while True:
            schedule.run_pending()
            await self.check_moisture_levels()
            await asyncio.sleep(1)  # Check every second for pending tasks and moisture levels

    async def check_moisture_levels(self):
        """
        Checks all moisture sensors and triggers watering if below threshold.
        """
        # self.logger.("Checking moisture levels")
        for sensor_id, sensor in self.moisture_sensors.items():
            moisture_level = sensor.read_moisture()
            self.logger.debug("Moisture level for sensor %s: %d", sensor_id, moisture_level)
            if moisture_level < self.moisture_thresholds[sensor_id]:
                self.logger.info("Moisture level below threshold for sensor %s", sensor_id)
                await self.trigger_watering(sensor_id)

    async def trigger_watering(self, sensor_id):
        """
        Triggers a watering cycle for a specific sensor.

        :param sensor_id: Identifier of the sensor that triggered the watering
        """
        self.logger.info("Triggering watering for sensor %s", sensor_id)
        await self.water_nutrient_controller.run_watering_cycle()

    def get_scheduled_events(self):
        """
        Returns a list of scheduled events.
        """
        self.logger.debug("Getting scheduled events")
        return schedule.jobs

    def get_sensor_status(self):
        """
        Returns the current status of all moisture sensors.
        """
        self.logger.debug("Getting sensor status")
        return {sensor_id: sensor.read_moisture() for sensor_id, sensor in self.moisture_sensors.items()}
