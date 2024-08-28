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
    
    def __init__(self, water_nutrient_controller, config_manager, logger, plant_manager, sensor_hub_controller):
        """
        Initialize the EventController with the WaterNutrientController instance, ConfigManager, and PlantManager.

        :param water_nutrient_controller: Instance of WaterNutrientController used to control watering and nutrient distribution.
        :param config_manager: Instance of ConfigManager for accessing and updating configuration.
        :param logger: Logger instance for logging.
        :param plant_manager: Instance of PlantManager for managing plant configurations.
        """
        try:
            self.logger = logger
            self.logger.debug("Initializing EventController")
            self.water_nutrient_controller = water_nutrient_controller
            self.config_manager = config_manager
            self.plant_manager = plant_manager
            self.sensor_hub_controller = sensor_hub_controller
            self.moisture_check_interval = 1  # Default to 1 second
            self.load_config()
            self.reapply_rules()
            self.latest_sensor_data = {}
            self.logger.debug("EventController initialized with the following configuration:")
            self.logger.debug("Moisture Thresholds: %s", self.moisture_thresholds)
            self.logger.debug("Scheduled Events: %s", self.scheduled_events)
        except Exception as e:
            self.logger.error("Error initializing EventController: %s", e)

    def load_config(self):
        try:
            config = self.config_manager.get('event', {})
            self.moisture_thresholds = config.get('moisture_thresholds', {})
            self.scheduled_events = config.get('scheduled_events', [])
            self.moisture_check_interval = config.get('moisture_check_interval', 1)
            self.logger.debug("Configuration loaded: %s", config)
        except Exception as e:
            self.logger.error("Error loading configuration: %s", e)

    def reload_config(self):
        """
        Reloads the configuration for the EventController.
        """
        try:
            self.logger.debug("Reloading configuration for EventController")
            self.load_config()
            self.reapply_rules()
            self.logger.info("Configuration reloaded for EventController")
        except Exception as e:
            self.logger.error("Error reloading configuration: %s", e)
        
        
    def reapply_rules(self):
        """
        Reapplies the saved rules from the configuration.
        """
        try:
            self.logger.debug("Reapplying saved rules")
            for event in self.scheduled_events:
                time_of_day = event.get('time_of_day', '08:00')
                self.schedule_daily_watering(time_of_day)
            self.logger.info("Reapplied saved rules")
        except Exception as e:
            self.logger.error("Error reapplying rules: %s", e)

    def schedule_daily_watering(self, time_of_day="08:00"):
        """
        Schedules the daily watering and nutrient distribution at the specified time.

        :param time_of_day: String representing the time of day to start the watering process (in 24-hour format, e.g., '08:00').
        """
        try:
            self.logger.debug("Scheduling daily watering at %s", time_of_day)
            schedule.every().day.at(time_of_day).do(self.water_nutrient_controller.run_watering_cycle)
            if {'time_of_day': time_of_day} not in self.scheduled_events:
                self.scheduled_events.append({'time_of_day': time_of_day})
                self.config_manager.set('event.scheduled_events', self.scheduled_events)
            self.logger.info("Scheduled daily watering at %s", time_of_day)
        except Exception as e:
            self.logger.error("Error scheduling daily watering: %s", e)

    def set_moisture_threshold(self, sensor_id, threshold):
        try:
            self.logger.debug("Setting moisture threshold: id=%s, threshold=%d", sensor_id, threshold)
            self.moisture_thresholds[sensor_id] = threshold
            self.config_manager.set('event.moisture_thresholds', self.moisture_thresholds)
            self.logger.info("Moisture threshold set: id=%s", sensor_id)
        except Exception as e:
            self.logger.error("Error setting moisture threshold: %s", e)

    def remove_moisture_threshold(self, sensor_id):
        try:
            self.logger.debug("Removing moisture threshold: id=%s", sensor_id)
            if sensor_id in self.moisture_thresholds:
                del self.moisture_thresholds[sensor_id]
                self.config_manager.set('event.moisture_thresholds', self.moisture_thresholds)
                self.logger.info("Moisture threshold removed: id=%s", sensor_id)
            else:
                self.logger.warning("Attempted to remove non-existent threshold: id=%s", sensor_id)
        except Exception as e:
            self.logger.error("Error removing moisture threshold: %s", e)

    def handle_sensor_message(self, sensor_id, moisture_value):
        try:
            self.logger.debug("Received sensor data: id=%s, value=%d", sensor_id, moisture_value)
            self.latest_sensor_data[sensor_id] = moisture_value
        except Exception as e:
            self.logger.error("Error handling sensor message: %s", e)


    async def monitor_events(self):
        """
        Continuously checks and runs scheduled tasks and monitors moisture sensors.
        This function should be run as an asynchronous task in the main event loop.
        """
        try:
            self.logger.debug("Starting event monitoring")
            while True:
                self.check_moisture_levels()
                self.logger.debug("sleeping for %d seconds", self.config_manager.get('event.moisture_check_interval', 60))
                await asyncio.sleep(self.config_manager.get('event.moisture_check_interval', 60))  # Check every second for pending tasks and moisture levels
        except Exception as e:
            self.logger.error("Error monitoring events: %s", e)
    
    def check_moisture_levels(self):
        if self.config_manager.get('abort_mode', False):
            self.logger.warning("ABORT mode active, skipping moisture level check")
            return

        try:
            self.logger.debug("Checking moisture levels for all plants")
            for plant_id, plant_data in self.plant_manager.get_all_plants().items():
                self.logger.debug(f"Checking moisture level for plant {plant_id}")
                sensor_id = plant_data['moisture_sensor_id']
                sensor_data = self.sensor_hub_controller.get_latest_sensor_data().get(sensor_id)
                self.logger.debug(f"Sensor data for plant {plant_id}: sensor_id={sensor_id}, sensor_data={sensor_data}")
                if sensor_data and 'percentage' in sensor_data:
                    moisture_level = sensor_data['percentage']
                    self.logger.debug(f"Checking moisture level for plant {plant_id}: {moisture_level}%")
                    if 'watering_threshold' not in plant_data or 'start_watering' not in plant_data['watering_threshold']:
                        self.logger.debug(f"No valid watering threshold config for plant {plant_id}, sensor {sensor_id}")
                        continue
                    
                    start_threshold = plant_data['watering_threshold']['start_watering']
                    self.logger.debug(f"Start threshold for plant {plant_id}: {start_threshold}%")
                    self.logger.debug(f"Moisture level {moisture_level}% is below start threshold {start_threshold}%" if moisture_level < start_threshold else f"Moisture level {moisture_level}% is above start threshold {start_threshold}%")
                    if moisture_level < start_threshold:
                        self.logger.warning(f"Moisture level below start threshold for plant {plant_id}: {moisture_level}% < {start_threshold}%")
                        self.trigger_watering(plant_id)
                else:
                    self.logger.warning(f"No valid moisture data for plant {plant_id}, sensor {sensor_id}")
        except Exception as e:
            self.logger.error("Error checking moisture levels: %s", e)

    def trigger_watering(self, plant_name):
        try:
            result = self.water_nutrient_controller.run_sensor_based_watering_cycle_for_plant(plant_name)
            if result is None:
                self.logger.warning(f"Watering cycle for {plant_name} completed, but no result was returned.")
            else:
                self.logger.info(f"Watering cycle for {plant_name} completed successfully.")
        except Exception as e:
            self.logger.error(f"Error triggering watering: {str(e)}")
            
    def get_scheduled_events(self):
        """
        Returns a list of scheduled events.
        """
        try:
            self.logger.debug("Getting scheduled events")
            return schedule.jobs
        except Exception as e:
            self.logger.error("Error getting scheduled events: %s", e)
            return []

    def get_sensor_status(self):
        """
        Returns the current status of all moisture sensors.
        """
        try:
            self.logger.debug("Getting sensor status")
            return self.latest_sensor_data
        except Exception as e:
            self.logger.error("Error getting sensor status: %s", e)
            return {}