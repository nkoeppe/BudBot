from app.config.config_manager import ConfigManager

class PlantManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.plants = self.load_plants()

    def load_plants(self):
        return self.config_manager.get('plants', {})

    def save_plants(self):
        self.config_manager.set('plants', self.plants)

    def add_plant(self, plant_id, moisture_sensor_id, water_pump_id):
        self.plants[plant_id] = {
            'moisture_sensor_id': moisture_sensor_id,
            'water_pump_id': water_pump_id
        }
        self.save_plants()

    def remove_plant(self, plant_id):
        if plant_id in self.plants:
            del self.plants[plant_id]
            self.save_plants()

    def update_plant(self, plant_id, moisture_sensor_id=None, water_pump_id=None):
        if plant_id in self.plants:
            if moisture_sensor_id is not None:
                self.plants[plant_id]['moisture_sensor_id'] = moisture_sensor_id
            if water_pump_id is not None:
                self.plants[plant_id]['water_pump_id'] = water_pump_id
            self.save_plants()

    def get_plant(self, plant_id):
        return self.plants.get(plant_id)

    def get_all_plants(self):
        return self.plants

    def get_plant_by_sensor(self, sensor_id):
        for plant_id, plant_data in self.plants.items():
            if plant_data['moisture_sensor_id'] == sensor_id:
                return plant_id, plant_data
        return None, None

    def get_plant_by_pump(self, pump_id):
        for plant_id, plant_data in self.plants.items():
            if plant_data['water_pump_id'] == pump_id:
                return plant_id, plant_data
        return None, None
