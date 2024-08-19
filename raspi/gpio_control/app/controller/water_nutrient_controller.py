import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from datetime import datetime
import time

class WaterNutrientController:
    """
    Controls the mixing and distribution of water and nutrients to the plants.
    Utilizes the RelayController to manage the GPIO pins connected to the pumps.
    """
    
    def __init__(self, relay_controller, config_manager, logger):
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
        self.load_config()
        self.logger.info("WaterNutrientController initialized with the following configuration:")
        self.logger.info("Nutrient Pumps: %s", self.nutrient_pumps)
        self.logger.info("Water Pump: %s", self.water_pump)
        self.logger.info("Distribution Pumps: %s", self.distribution_pumps)
        self.logger.info("Fill Level Sensor: %s", self.fill_level_sensor)
        self.logger.info("Nutrient Amounts: %s", self.nutrient_amounts)
        self.logger.info("Total Water (ml): %d", self.total_water_ml)
        self.logger.info("ML per Plant: %d", self.ml_per_plant)

    def load_config(self):
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
        
        self.fill_level_sensor = config.get('fill_level_sensor', {'pin': 26})
        self.nutrient_amounts = config.get('nutrient_amounts', {'green': 50, 'red': 30, 'yellow': 20})
        self.total_water_ml = config.get('total_water_ml', 8000)
        self.ml_per_plant = config.get('ml_per_plant', 1000)
        self.logger.debug("Configuration loaded: %s", config)
        
        gpio_output_pins = [pump['pin'] for pump in self.nutrient_pumps.values()]
        gpio_output_pins.append(self.water_pump['pin'])
        gpio_output_pins.extend([pump['pin'] for pump in self.distribution_pumps.values()])
        gpio_output_pins = [pin for pin in gpio_output_pins if pin != -1]
        
        self.relay_controller.init_gpio_output(gpio_output_pins)
        
        gpio_input_pins = [self.fill_level_sensor['pin']]
        gpio_input_pins = [pin for pin in gpio_input_pins if pin != -1]
        self.relay_controller.init_gpio_input(gpio_input_pins)
        
        

    def save_config(self):
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
        if nutrient_amounts is None:
            nutrient_amounts = self.nutrient_amounts

        self.logger.debug("Mixing nutrients: %s", nutrient_amounts)
        for label, amount in nutrient_amounts.items():
            if label in self.nutrient_pumps and self.nutrient_pumps[label]['pin'] != -1:
                pump = self.nutrient_pumps[label]
                duration = amount / pump['flow_rate']
                self.relay_controller.turn_on(pump['pin'])
                time.sleep(duration)
                self.relay_controller.turn_off(pump['pin'])
                self.logger.info("Added %d ml of %s nutrient", amount, label)
            else:
                self.logger.warning("Unknown nutrient label '%s'", label)
        self.logger.info("Nutrient mixing complete.")

    def fill_water_to_mixer(self, ml):
        """
        Activates the water pump to fill the nutrient mixer with a specified amount of water.
        The pump runs until the specified amount is added or the mixer is full.

        :param ml: Amount of water to add in milliliters
        """
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
            time.sleep(0.1)  # Check every 100ms
            water_added += flow_rate * 0.1

        self.relay_controller.turn_off(self.water_pump['pin'])
        
        if self.is_mixer_full():
            self.logger.info("Mixer full. Added approximately %.2f ml of water.", water_added)
        elif water_added >= ml:
            self.logger.info("Added %d ml of water to mixer.", ml)
        else:
            self.logger.warning("Filling stopped after 60 seconds. Added approximately %.2f ml of water.", water_added)

    def fill_mixer_with_water(self, total_ml=None):
        """
        Activates the water pump to fill the nutrient mixer with water.
        Uses the fill_water_to_mixer function to add water until the mixer is full or the total amount is reached.

        :param total_ml: Total amount of water to add in milliliters (default: 5000 ml)
        """
        if total_ml is None:
            total_ml = self.total_water_ml

        self.logger.debug("Filling mixer with water: %d ml", total_ml)
        if self.is_mixer_full():
            self.logger.info("Mixer is already full.")
            return

        self.logger.debug("Filling mixer with %d ml of water...", total_ml)
        water_added = 0
        while not self.is_mixer_full() and water_added < total_ml:
            remaining = min(1000, total_ml - water_added)
            self.fill_water_to_mixer(remaining)
            water_added += remaining
        
        self.logger.info("Mixer filled with %d ml of water.", water_added)
        
    def is_mixer_full(self):
        """
        Checks the fill level sensor to determine if the mixer is full.
        """
        self.logger.debug("Checking if mixer is full")
        fill_level_pin = self.fill_level_sensor['pin']  # Assuming this is defined in the class
        
        # Read the GPIO input
        is_full = self.relay_controller.get_pin_state(fill_level_pin)
        
        self.logger.debug("Mixer full status: %s", is_full)
        return is_full

    def distribute_to_plants(self, ml_per_plant=None):
        """
        Activates the distribution pumps to deliver the nutrient solution to the plants.
        Each pump runs sequentially to ensure equal distribution.

        :param ml_per_plant: Amount of nutrient solution to distribute to each plant in milliliters
        """
        if ml_per_plant is None:
            ml_per_plant = self.ml_per_plant

        self.logger.debug("Distributing %d ml of nutrient solution to each plant", ml_per_plant)
        for plant_id, pump in self.distribution_pumps.items():
            duration = ml_per_plant / pump['flow_rate']
            self.relay_controller.turn_on(pump['pin'])
            time.sleep(duration)
            self.relay_controller.turn_off(pump['pin'])
            self.logger.info("Distribution complete for plant: %s", plant_id)
        self.logger.info("Distribution complete for all plants.")
        
    def distribute_to_plant(self, plant_id, ml=None):
        """
        Activates the distribution pump for a specific plant to deliver the nutrient solution.
        
        :param plant_id: The ID of the plant to distribute the nutrient solution to
        :param ml: Amount of nutrient solution to distribute to the plant in milliliters
        """
        if ml is None:
            ml = self.ml_per_plant

        self.logger.debug("Distributing %d ml of nutrient solution to plant: %s", ml, plant_id)
        if plant_id in self.distribution_pumps:
            pump = self.distribution_pumps[plant_id]
            duration = ml / pump['flow_rate']
            self.relay_controller.turn_on(pump['pin'])
            time.sleep(duration)
            self.relay_controller.turn_off(pump['pin'])
            self.logger.info("Distribution complete for plant: %s", plant_id)
        else:
            self.logger.warning("No distribution pump found for plant: %s", plant_id)

    def run_watering_cycle(self):
        """
        Runs the full watering and nutrient distribution cycle.
        This includes mixing nutrients, filling the mixer with water, and distributing the solution to the plants.
        """
        self.logger.debug("Running watering cycle")
        self.mix_nutrients()
        self.fill_mixer_with_water()
        self.distribute_to_plants()
        self.logger.info("Watering cycle complete.")

    def run_watering_cycle_for_plant(self, plant_id):
        """
        Runs the full watering and nutrient distribution cycle for a specific plant.
        This includes mixing nutrients, filling the mixer with water, and distributing the solution to the plants.
        """
        self.logger.debug("Running watering cycle for plant: %s", plant_id)
        self.mix_nutrients()
        self.fill_mixer_with_water()
        self.distribute_to_plant(plant_id)
        self.logger.info("Watering cycle complete for plant: %s", plant_id)

    def reload_config(self):
        self.logger.debug("Reloading configuration for WaterNutrientController")
        self.load_config()
        self.logger.info("Configuration reloaded for WaterNutrientController")