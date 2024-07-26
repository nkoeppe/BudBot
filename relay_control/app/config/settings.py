import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
    SENSOR_CONFIG = os.environ.get('SENSOR_CONFIG', '/config/sensor_config.json')
    CONTROL_CONFIG = os.environ.get('CONTROL_CONFIG', '/config/control_config.json')