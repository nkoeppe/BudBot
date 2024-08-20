from app.config.config_manager import ConfigManager

class PlantManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.plants = self.load_plants()

    def load_plants(self):
        return self.config_manager.get('plants', {})

    def save_plants(self):
        self.config_manager.set('plants', self.plants)

    def add_plant(self, plant_id, moisture_sensor_id, water_pump_id, start_watering_threshold, stop_watering_threshold):
        plant_data = self.config_manager.get(f'plants.{plant_id}', {})
        plant_data.update({
            'moisture_sensor_id': moisture_sensor_id,
            'water_pump_id': water_pump_id,
            'watering_threshold': plant_data.get('watering_threshold', {
                'start_watering': start_watering_threshold,
                'stop_watering': stop_watering_threshold
            })
        })
        self.config_manager.set(f'plants.{plant_id}', plant_data)

    def remove_plant(self, plant_id):
        plants = self.config_manager.get('plants', {})
        if plant_id in plants:
            del plants[plant_id]
            self.config_manager.set('plants', plants)

    def update_plant(self, plant_id, moisture_sensor_id=None, water_pump_id=None, start_watering_threshold=None, stop_watering_threshold=None):
        plant_data = self.config_manager.get(f'plants.{plant_id}', {})
        if moisture_sensor_id is not None:
            plant_data['moisture_sensor_id'] = moisture_sensor_id
        if water_pump_id is not None:
            plant_data['water_pump_id'] = water_pump_id
        if 'watering_threshold' not in plant_data:
            plant_data['watering_threshold'] = {}
        if start_watering_threshold is not None:
            plant_data['watering_threshold']['start_watering'] = start_watering_threshold
        if stop_watering_threshold is not None:
            plant_data['watering_threshold']['stop_watering'] = stop_watering_threshold
        self.config_manager.set(f'plants.{plant_id}', plant_data)

    def get_plant(self, plant_id):
        return self.config_manager.get(f'plants.{plant_id}')

    def get_all_plants(self):
        return self.config_manager.get('plants', {})

    def get_plant_by_sensor(self, sensor_id):
        plants = self.config_manager.get('plants', {})
        for plant_id, plant_data in plants.items():
            if plant_data['moisture_sensor_id'] == sensor_id:
                return plant_id, plant_data
        return None, None

    def get_plant_by_pump(self, pump_id):
        plants = self.config_manager.get('plants', {})
        for plant_id, plant_data in plants.items():
            if plant_data['water_pump_id'] == pump_id:
                return plant_id, plant_data
        return None, None