import logging
from math import ceil

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from datetime import datetime
import time

class WaterNutrientController:
    """
    Controls the mixing and distribution of water and nutrients to the plants.
    Utilizes the RelayController to manage the GPIO pins connected to the pumps.
    """
    
    def __init__(self, relay_controller, config_manager, logger, plant_controller, sensor_controller):
        """
        Initialize the WaterNutrientController with the RelayController instance and configuration.

        :param relay_controller: Instance of RelayController used to control the relays.
        :param config_manager: Instance of ConfigManager for accessing and updating configuration.
        :param logger: Logger instance for logging.
        """
        self.logger = logger
        self.logger.debug("Initializing WaterNutrientController")
        self.relay_controller = relay_controller
        self.config_manager = config_manager
        self.plant_controller = plant_controller
        self.sensor_controller = sensor_controller
        self.load_config()
        self.logger.info("WaterNutrientController initialized with the following configuration:")
        self.logger.info("Nutrient Pumps: %s", self.nutrient_pumps)
        self.logger.info("Water Pump: %s", self.water_pump)
        self.logger.info("Distribution Pumps: %s", self.distribution_pumps)
        self.logger.info("Fill Level Sensor: %s", self.fill_level_sensor)
        self.logger.info("Nutrient Amounts: %s", self.nutrient_amounts)
        self.logger.info("Total Water (ml): %d", self.total_water_ml)
        self.logger.info("ML per Plant: %d", self.ml_per_plant)        
        self.logger.info("Mixer Status: %s", "Full" if self.is_mixer_full() else "Not Full")

    def load_config(self):
        try:
            config = self.config_manager.get('water_nutrient', {})
            self.nutrient_pumps = config.get('nutrient_pumps', {
                'green': {'pin': -1, 'flow_rate': 0.5},  # flow rate in ml/sec
                'red': {'pin': -1, 'flow_rate': 0.5},
                'yellow': {'pin': -1, 'flow_rate': 0.5}
            })
            
            self.water_pump = config.get('water_pump', {'pin': 16, 'flow_rate': 20})  # flow rate in ml/sec
            
            self.distribution_pumps = config.get('distribution_pumps', {
                'pump_1': {'pin': 5, 'flow_rate': 30},
                'pump_2': {'pin': 20, 'flow_rate': 30},
                'pump_3': {'pin': 13, 'flow_rate': 30},
                'pump_4': {'pin': 6, 'flow_rate': 30},
                'pump_5': {'pin': 19, 'flow_rate': 30}
            })
            
            self.fill_level_sensor = config.get('fill_level_sensor', {
                'mixer_full': {'pin': 26},
                'nutrient_tank_low': {'pin': -1},
                'water_tank_low': {'pin': -1}
            })
            self.nutrient_amounts = config.get('nutrient_amounts', {'green': 50, 'red': 30, 'yellow': 20})
            self.total_water_ml = config.get('total_water_ml', 8000)
            self.ml_per_plant = config.get('ml_per_plant', 1000)
            self.logger.debug("Configuration loaded: %s", config)
            
            gpio_output_pins = [pump['pin'] for pump in self.nutrient_pumps.values()]
            gpio_output_pins.append(self.water_pump['pin'])
            gpio_output_pins.extend([pump['pin'] for pump in self.distribution_pumps.values()])
            gpio_output_pins = [pin for pin in gpio_output_pins if pin != -1]
            
            self.relay_controller.init_gpio_output(gpio_output_pins)
            
            gpio_input_pins = [sensor['pin'] for sensor in self.fill_level_sensor.values() if sensor['pin'] != -1]
            self.relay_controller.init_gpio_input(gpio_input_pins)
        except Exception as e:
            self.logger.error("Error loading configuration: %s", e)
        

    def save_config(self):
        try:
            config = {
                'nutrient_pumps': self.nutrient_pumps,
                'water_pump': self.water_pump,
                'distribution_pumps': self.distribution_pumps,
                'fill_level_sensor': self.fill_level_sensor,
                'nutrient_amounts': self.nutrient_amounts,
                'total_water_ml': self.total_water_ml,
                'ml_per_plant': self.ml_per_plant
            }
            self.config_manager.set('water_nutrient', config)
        except Exception as e:
            self.logger.error("Error saving configuration: %s", e)

    def mix_nutrients(self, nutrient_amounts=None):
        """
        Activates the nutrient pumps sequentially to mix the nutrients into the water.
        Each pump runs for a duration based on the specified amount in milliliters.

        :param nutrient_amounts: Dictionary of nutrient amounts in milliliters, keyed by nutrient label.

        Example:
            controller = WaterNutrientController(relay_controller, config)
            nutrient_amounts = {
                'green': 50,  # 50 ml of green nutrient
                'red': 30,    # 30 ml of red nutrient
                'yellow': 20  # 20 ml of yellow nutrient
            }
            controller.mix_nutrients(nutrient_amounts)
        """
        try:
            if nutrient_amounts is None:
                nutrient_amounts = self.nutrient_amounts

            self.logger.debug("Mixing nutrients: %s", nutrient_amounts)
            for label, amount in nutrient_amounts.items():
                if self.config_manager.get('abort_mode', False):
                    self.logger.warning("ABORT mode activated. Stopping nutrient mixing.")
                    break
                if label in self.nutrient_pumps and self.nutrient_pumps[label]['pin'] != -1:
                    pump = self.nutrient_pumps[label]
                    duration = amount / pump['flow_rate']
                    self.relay_controller.turn_on(pump['pin'])
                    start_time = time.time()
                    while time.time() - start_time < duration:
                        if self.config_manager.get('abort_mode', False):
                            self.logger.warning("ABORT mode activated. Stopping nutrient mixing for %s.", label)
                            break
                        time.sleep(0.1)
                    self.relay_controller.turn_off(pump['pin'])
                    if not self.config_manager.get('abort_mode', False):
                        self.logger.info("Added %d ml of %s nutrient", amount, label)
                    else:
                        actual_duration = time.time() - start_time
                        actual_amount = actual_duration * pump['flow_rate']
                        self.logger.info("Aborted. Added approximately %.2f ml of %s nutrient", actual_amount, label)
                        break
                else:
                    self.logger.warning("Unknown nutrient label '%s'", label)
            if not self.config_manager.get('abort_mode', False):
                self.logger.info("Nutrient mixing complete.")
            else:
                self.logger.warning("Nutrient mixing aborted.")
        except Exception as e:
            self.logger.error("Error mixing nutrients: %s", e)

    def fill_water_to_mixer(self, ml):
        """
        Activates the water pump to fill the nutrient mixer with a specified amount of water.
        The pump runs until the specified amount is added or the mixer is full.

        :param ml: Amount of water to add in milliliters
        """
        try:
            self.logger.debug("Filling water to mixer: %d ml", ml)
            if self.is_mixer_full():
                self.logger.info("Mixer is already full. No water added.")
                return

            self.logger.debug("Adding %d ml of water to mixer...", ml)
            self.relay_controller.turn_on(self.water_pump['pin'])
            
            start_time = time.time()
            water_added = 0
            flow_rate = self.water_pump['flow_rate']

            while not self.is_mixer_full() and water_added < ml and (time.time() - start_time) < 60:
                if self.config_manager.get('abort_mode', False):
                    self.logger.warning("ABORT mode activated. Stopping water filling.")
                    break
                time.sleep(0.1)  # Check every 100ms
                water_added += flow_rate * 0.1

            self.relay_controller.turn_off(self.water_pump['pin'])
            
            if self.config_manager.get('abort_mode', False):
                self.logger.warning("Water filling aborted. Added approximately %.2f ml of water.", water_added)
            elif self.is_mixer_full():
                self.logger.info("Mixer full. Added approximately %.2f ml of water.", water_added)
            elif water_added >= ml:
                self.logger.info("Added %d ml of water to mixer.", ml)
            else:
                self.logger.warning("Filling stopped after 60 seconds. Added approximately %.2f ml of water.", water_added)
        except Exception as e:
            self.logger.error("Error filling water to mixer: %s", e)

    def fill_mixer_with_water(self, total_ml=None):
        """
        Activates the water pump to fill the nutrient mixer with water.
        Uses the fill_water_to_mixer function to add water until the mixer is full or the total amount is reached.

        :param total_ml: Total amount of water to add in milliliters (default: 5000 ml)
        """
        try:
            if total_ml is None:
                total_ml = self.total_water_ml

            self.logger.debug("Filling mixer with water: %d ml", total_ml)
            if self.is_mixer_full():
                self.logger.info("Mixer is already full.")
                return

            self.logger.debug("Filling mixer with %d ml of water...", total_ml)
            water_added = 0
            while not self.is_mixer_full() and water_added < total_ml:
                if self.config_manager.get('abort_mode', False):
                    self.logger.warning("ABORT mode activated. Stopping mixer filling.")
                    break
                remaining = min(1000, total_ml - water_added)
                self.fill_water_to_mixer(remaining)
                water_added += remaining
            
            if self.config_manager.get('abort_mode', False):
                self.logger.warning("Mixer filling aborted. Added approximately %d ml of water.", water_added)
            else:
                self.logger.info("Mixer filled with %d ml of water.", water_added)
        except Exception as e:
            self.logger.error("Error filling mixer with water: %s", e)
            
    def is_mixer_full(self):
        """
        Checks the fill level sensor to determine if the mixer is full.
        """
        try:
            mixer_full_sensor = self.fill_level_sensor.get('mixer_full', {'pin': -1})
            # Read the GPIO input
            is_full = self.relay_controller.get_pin_state(mixer_full_sensor['pin'])
            return is_full
        except Exception as e:
            self.logger.error("Error checking if mixer is full: %s", e)
            return False
    
    def is_nutrient_tank_low(self):
        """
        Checks if the nutrient tank is low.
        """
        try:
            self.logger.debug("Checking if nutrient tank is low")
            nutrient_tank_sensor = self.fill_level_sensor.get('nutrient_tank_low', {'pin': -1})
            
            is_low = self.relay_controller.get_pin_state(nutrient_tank_sensor['pin'])
            
            self.logger.debug("Nutrient tank low status: %s", is_low)
            return is_low
        except Exception as e:
            self.logger.error("Error checking if nutrient tank is low: %s", e)
            return False

    def is_water_tank_low(self):
        """
        Checks if the water tank is low.
        """
        try:
            self.logger.debug("Checking if water tank is low")
            water_tank_sensor = self.fill_level_sensor.get('water_tank_low', {'pin': -1})
            
            is_low = self.relay_controller.get_pin_state(water_tank_sensor['pin'])
            
            self.logger.debug("Water tank low status: %s", is_low)
            return is_low
        except Exception as e:
            self.logger.error("Error checking if water tank is low: %s", e)
            return False
    def distribute_to_plants(self, ml_per_plant=None):
        """
        Activates the distribution pumps to deliver the nutrient solution to the plants.
        Each pump runs sequentially to ensure equal distribution.

        :param ml_per_plant: Amount of nutrient solution to distribute to each plant in milliliters
        """
        try:
            if ml_per_plant is None:
                ml_per_plant = self.ml_per_plant

            self.logger.debug("Distributing %d ml of nutrient solution to each plant", ml_per_plant)
            for plant_id, pump in self.distribution_pumps.items():
                if self.config_manager.get('abort_mode', False):
                    self.logger.warning("ABORT mode activated. Stopping distribution.")
                    break
                
                duration = ml_per_plant / pump['flow_rate']
                start_time = time.time()
                self.relay_controller.turn_on(pump['pin'])
                
                while time.time() - start_time < duration:
                    if self.config_manager.get('abort_mode', False):
                        self.logger.warning("ABORT mode activated. Stopping distribution for plant: %s", plant_id)
                        break
                    time.sleep(0.1)  # Check abort mode every 100ms
                
                self.relay_controller.turn_off(pump['pin'])
                
                if not self.config_manager.get('abort_mode', False):
                    self.logger.info("Distribution complete for plant: %s", plant_id)
                else:
                    actual_duration = time.time() - start_time
                    actual_ml = actual_duration * pump['flow_rate']
                    self.logger.info("Distribution aborted for plant: %s. Approximate amount distributed: %.2f ml", plant_id, actual_ml)
                    break
            
            if not self.config_manager.get('abort_mode', False):
                self.logger.info("Distribution complete for all plants.")
            else:
                self.logger.warning("Distribution aborted due to ABORT mode.")
        except Exception as e:
            self.logger.error("Error distributing to plants: %s", e)
            for pump in self.distribution_pumps.values():
                self.relay_controller.turn_off(pump['pin']) 
                
    def distribute_to_plant(self, plant_id, ml=None):
        """
        Activates the distribution pump for a specific plant to deliver the nutrient solution.
        
        :param plant_id: The ID of the plant to distribute the nutrient solution to
        :param ml: Amount of nutrient solution to distribute to the plant in milliliters
        """
        try:
            if ml is None:
                ml = self.ml_per_plant

            self.logger.debug("Distributing %d ml of nutrient solution to plant: %s", ml, plant_id)
            plant = self.plant_controller.get_plant(plant_id)
            if not plant:
                self.logger.warning("No plant found with id: %s", plant_id)
                return
            
            pump = self.distribution_pumps.get(plant['water_pump_id'])
            if not pump:
                self.logger.warning("No distribution pump with label %s found for plant: %s", plant['water_pump_id'], plant_id)
                return
            
            duration = ml / pump['flow_rate']
            start_time = time.time()
            self.relay_controller.turn_on(pump['pin'])
            
            while time.time() - start_time < duration:
                if self.config_manager.get('abort_mode', False):
                    self.logger.warning("ABORT mode activated. Stopping distribution for plant: %s", plant_id)
                    break
                time.sleep(0.1)  # Check abort mode every 100ms
            
            self.relay_controller.turn_off(pump['pin'])
            
            if not self.config_manager.get('abort_mode', False):
                self.logger.info("Distribution complete for plant: %s", plant_id)
            else:
                actual_duration = time.time() - start_time
                actual_ml = actual_duration * pump['flow_rate']
                self.logger.info("Distribution aborted for plant: %s. Approximate amount distributed: %.2f ml", plant_id, actual_ml)
        except Exception as e:
            self.logger.error("Error distributing to plant %s: %s", plant_id, e)
            self.relay_controller.turn_off(pump['pin'])  # Ensure pump is turned off in case of error
            
    def sensor_based_distribute_to_plant(self, plant_id):
        """
        Activates the distribution pump for a specific plant to deliver the nutrient solution.
        Uses the sensor data to determine the amount of water to distribute.
        :param plant_id: The ID of the plant to distribute the nutrient solution to
        """
        try:
            self.logger.debug("Distributing nutrient solution to plant: %s", plant_id)
            plant = self.plant_controller.get_plant(plant_id)
            if not plant:
                self.logger.warning("No plant found with id: %s", plant_id)
                return
            
            pump = self.distribution_pumps.get(plant['water_pump_id'])
            if not pump:
                self.logger.warning("No distribution pump with label %s found for plant: %s", plant['water_pump_id'], plant_id)
                return
            
            if not plant['moisture_sensor_id'] in self.sensor_controller.get_sensors():
                self.logger.warning("No soil moisture sensor found for plant: %s", plant_id)
                return
            
            threshold = plant['watering_threshold']['stop_watering']
            max_watering_time = self.config_manager.get('max_watering_time', 60)
            
            self.sensor_controller.set_interval(100)
            max_readings = self.config_manager.get('sensor_hub.max_readings', 5)
            self.sensor_controller.set_max_readings(5)

            if self.config_manager.get('abort_mode', False):
                self.logger.info("ABORT mode active, stopping watering for plant: %s", plant_id)
                return

            self.relay_controller.turn_on(pump['pin'])
            start_time = time.time()
            while (time.time() - start_time < max_watering_time and 
                   self.sensor_controller.get_latest_sensor_data_by_sensor_id(plant['moisture_sensor_id'])['percentage'] < threshold):
                if self.config_manager.get('abort_mode', False):
                    self.logger.info("ABORT mode activated, stopping watering for plant: %s", plant_id)
                    break
                time.sleep(0.1)
            
            self.relay_controller.turn_off(pump['pin'])
            end_time = time.time()
            
            duration = end_time - start_time
            estimated_water_added = duration * pump['flow_rate']
            
            if duration >= max_watering_time:
                self.logger.warning("Max watering time reached for plant: %s. Stopping watering.", plant_id)
            
            self.logger.info("Distribution complete for plant: %s. Estimated water added: %.2f ml", plant_id, estimated_water_added)
            self.sensor_controller.set_max_readings(max_readings)
            self.sensor_controller.set_interval(ceil(self.config_manager.get('sensor_hub.interval', 5000)/self.sensor_controller.max_readings))

        except Exception as e:
            self.logger.error("Error in sensor-based distribution to plant %s: %s", plant_id, e)

    def run_watering_cycle(self):
        """
        Runs the full watering and nutrient distribution cycle.
        This includes mixing nutrients, filling the mixer with water, and distributing the solution to the plants.
        """
        try:
            self.logger.debug("Running watering cycle")
            self.mix_nutrients()
            self.fill_mixer_with_water()
            self.distribute_to_plants()
            self.logger.info("Watering cycle complete.")
        except Exception as e:
            self.logger.error("Error running watering cycle: %s", e)

    def run_watering_cycle_for_plant(self, plant_id):
        """
        Runs the full watering and nutrient distribution cycle for a specific plant.
        This includes mixing nutrients, filling the mixer with water, and distributing the solution to the plants.
        """
        try:
            self.logger.debug("Running watering cycle for plant: %s", plant_id)
            self.mix_nutrients()
            self.fill_mixer_with_water()
            self.distribute_to_plant(plant_id)
            self.logger.info("Watering cycle complete for plant: %s", plant_id)
        except Exception as e:
            self.logger.error("Error running watering cycle for plant %s: %s", plant_id, e)

    def run_sensor_based_watering_cycle_for_plant(self, plant_id):
        try:
            self.logger.debug("Running sensor based watering cycle for plant: %s", plant_id)
            self.mix_nutrients()    
            self.fill_mixer_with_water()
            self.sensor_based_distribute_to_plant(plant_id)
            self.logger.info("Watering cycle complete for plant: %s", plant_id)
            return True
        except Exception as e:
            self.logger.error("Error running sensor-based watering cycle for plant %s: %s", plant_id, e)
        return False

    def reload_config(self):
        try:
            self.logger.debug("Reloading configuration for WaterNutrientController")
            self.load_config()
            self.logger.info("Configuration reloaded for WaterNutrientController")
        except Exception as e:
            self.logger.error("Error reloading configuration: %s", e)

    def abort(self):
        self.logger.debug("Executing ABORT command in WaterNutrientController")
        # Stop any ongoing operations
        # This might involve setting flags to stop loops in other methods
        self.config_manager.set('abort_mode', True)
        # Turn off all pumps
        for pump in self.nutrient_pumps.values():
            self.relay_controller.turn_off(pump['pin'])
        self.relay_controller.turn_off(self.water_pump['pin'])
        for pump in self.distribution_pumps.values():
            self.relay_controller.turn_off(pump['pin'])
        self.logger.info("ABORT command executed in WaterNutrientController")
        self.logger.info("ABORT command executed in WaterNutrientController")