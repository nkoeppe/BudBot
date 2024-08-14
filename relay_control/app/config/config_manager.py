import json
import os

CONFIG_FILE_PATH = '/app/app/config/settings.json'

class ConfigManager:
    def __init__(self, config_file=CONFIG_FILE_PATH):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                return json.load(file)
        else:
            default_config = {
                "water_nutrient": {
                    "nutrient_pumps": {
                        "green": {"pin": -1, "flow_rate": 0.5},
                        "red": {"pin": -1, "flow_rate": 0.5},
                        "yellow": {"pin": -1, "flow_rate": 0.5}
                    },
                    "water_pump": {"pin": 16, "flow_rate": 20},
                    "distribution_pumps": [
                        {"pin": 5, "flow_rate": 30},
                        {"pin": 20, "flow_rate": 30},
                        {"pin": 13, "flow_rate": 30},
                        {"pin": 6, "flow_rate": 30},
                        {"pin": 19, "flow_rate": 30}
                    ],
                    "fill_level_sensor": {"pin": 26},
                    "nutrient_amounts": {"green": 50, "red": 30, "yellow": 20},
                    "total_water_ml": 8000,
                    "ml_per_plant": 1000
                },
                "event": {
                    "moisture_sensors": {},
                    "moisture_thresholds": {},
                    "scheduled_events": []
                }
            }
            with open(self.config_file, 'w') as file:
                json.dump(default_config, file, indent=4)
            return default_config

    def save_config(self):
        with open(self.config_file, 'w') as file:
            json.dump(self.config, file, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()