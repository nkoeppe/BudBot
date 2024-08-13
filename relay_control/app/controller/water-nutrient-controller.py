from datetime import datetime
import time

class WaterNutrientController:
    """
    Controls the mixing and distribution of water and nutrients to the plants.
    Utilizes the RelayController to manage the GPIO pins connected to the pumps.
    """
    
    def __init__(self, relay_controller, config):
        """
        Initialize the WaterNutrientController with the RelayController instance and configuration.

        :param relay_controller: Instance of RelayController used to control the relays.
        :param config: Configuration dictionary containing pump settings.
        """
        self.relay_controller = relay_controller
        self.nutrient_pumps = config.get('nutrient_pumps', {
            'green': {'pin': -1, 'flow_rate': 0.5},  # flow rate in ml/sec
            'red': {'pin': -1, 'flow_rate': 0.5},
            'yellow': {'pin': -1, 'flow_rate': 0.5}
        })
        self.water_pump = config.get('water_pump', {'pin': -1, 'flow_rate': 50})  # flow rate in ml/sec
        self.distribution_pumps = config.get('distribution_pumps', [
            {'pin': -1, 'flow_rate': 10},
            {'pin': 20, 'flow_rate': 10},
            {'pin': -1, 'flow_rate': 10},
            {'pin': 5, 'flow_rate': 10},
            {'pin': -1, 'flow_rate': 10}
        ])

    def mix_nutrients(self, nutrient_amounts):
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
        print("Starting nutrient mixing...")
        for label, amount in nutrient_amounts.items():
            if label in self.nutrient_pumps:
                pump = self.nutrient_pumps[label]
                duration = amount / pump['flow_rate']
                self.relay_controller.turn_on(pump['pin'])
                time.sleep(duration)
                self.relay_controller.turn_off(pump['pin'])
                print(f"Added {amount} ml of {label} nutrient")
            else:
                print(f"Warning: Unknown nutrient label '{label}'")
        print("Nutrient mixing complete.")

    def fill_water_to_mixer(self, ml):
        """
        Activates the water pump to fill the nutrient mixer with a specified amount of water.
        The pump runs until the specified amount is added or the mixer is full.

        :param ml: Amount of water to add in milliliters
        """
        if self.is_mixer_full():
            print("Mixer is already full. No water added.")
            return

        print(f"Adding {ml} ml of water to mixer...")
        self.relay_controller.turn_on(self.water_pump['pin'])
        
        start_time = time.time()
        water_added = 0
        flow_rate = self.water_pump['flow_rate']

        while not self.is_mixer_full() and water_added < ml and (time.time() - start_time) < 60:
            time.sleep(0.1)  # Check every 100ms
            water_added += flow_rate * 0.1

        self.relay_controller.turn_off(self.water_pump['pin'])
        
        if self.is_mixer_full():
            print(f"Mixer full. Added approximately {water_added:.2f} ml of water.")
        elif water_added >= ml:
            print(f"Added {ml} ml of water to mixer.")
        else:
            print(f"Filling stopped after 60 seconds. Added approximately {water_added:.2f} ml of water.")

    def fill_mixer_with_water(self, total_ml=5000):
        """
        Activates the water pump to fill the nutrient mixer with water.
        Uses the fill_water_to_mixer function to add water until the mixer is full or the total amount is reached.

        :param total_ml: Total amount of water to add in milliliters (default: 5000 ml)
        """
        if self.is_mixer_full():
            print("Mixer is already full.")
            return

        print(f"Filling mixer with {total_ml} ml of water...")
        water_added = 0
        while not self.is_mixer_full() and water_added < total_ml:
            remaining = min(1000, total_ml - water_added)
            self.fill_water_to_mixer(remaining)
            water_added += remaining
        
        print(f"Mixer filled with {water_added} ml of water.")

    def is_mixer_full(self):
        """
        Checks the fill level sensor to determine if the mixer is full.
        """
        # TODO: Implement the actual logic to read from the fill level sensor
        # This is a placeholder and should be replaced with actual sensor reading
        return False  # Replace with actual sensor reading

    def distribute_to_plants(self, ml_per_plant):
        """
        Activates the distribution pumps to deliver the nutrient solution to the plants.
        Each pump runs sequentially to ensure equal distribution.

        :param ml_per_plant: Amount of nutrient solution to distribute to each plant in milliliters
        """
        print(f"Distributing {ml_per_plant} ml of nutrient solution to each plant...")
        for pump in self.distribution_pumps:
            duration = ml_per_plant / pump['flow_rate']
            self.relay_controller.turn_on(pump['pin'])
            time.sleep(duration)
            self.relay_controller.turn_off(pump['pin'])
        print("Distribution complete.")