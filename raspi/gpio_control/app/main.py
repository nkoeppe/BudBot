import logging
import asyncio
from logging.config import dictConfig
from flask import Flask, request, session
from app.api.controllers import main as main_blueprint, set_controllers
from app.controller.relay_controller import RelayController
from app.controller.water_nutrient_controller import WaterNutrientController
from app.controller.sensor_hub_controller import SensorHubController
from app.controller.event_controller import EventController
from app.config.config_manager import ConfigManager
import uuid
from app.config.plant_manager import PlantManager

# Configure logger
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] [%(levelname)s | %(module)s] %(message)s',
            'datefmt': '%B %d, %Y %H:%M:%S %Z',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'app.log',
            'formatter': 'default',
            'level': 'DEBUG',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,  # 5 files max
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file'],
    },
})

app = Flask(__name__)
app.secret_key = "supersecretkey"
config_manager = ConfigManager()

@app.before_request
def before_request():
    session["ctx"] = {"request_id": str(uuid.uuid4())}
    app.logger.info("Request started: %s", session["ctx"])

@app.after_request
def after_request(response):
    app.logger.info(
        "Request completed: path=%s, method=%s, status=%s, size=%s, request_id=%s",
        request.path,
        request.method,
        response.status,
        response.content_length,
        session["ctx"]["request_id"],
    )
    return response

async def main():
    logger = logging.getLogger(__name__)
    logger.debug("Starting main function")
    logger.debug("Initializing controllers")
    relay_controller = RelayController(logger)
    sensor_hub_controller = SensorHubController(logger, config_manager, mqtt_broker="mqtt", mqtt_port=1883)
    plant_manager = PlantManager(config_manager, sensor_hub_controller)
    water_nutrient_controller = WaterNutrientController(relay_controller, config_manager, logger, plant_manager, sensor_hub_controller)   
    event_controller = EventController(water_nutrient_controller, config_manager, logger, plant_manager, sensor_hub_controller)
    logger.info("Controllers initialized")

    # Set instances in the controllers module
    set_controllers(relay_controller, water_nutrient_controller, event_controller, sensor_hub_controller, plant_manager)
    # Register the Blueprint
    app.register_blueprint(main_blueprint, url_prefix='/api')

    # Define async functions for Flask and event monitoring
    async def run_flask():
        logger.debug("Starting Flask app")
        await asyncio.to_thread(app.run, host='0.0.0.0', port=5000)
        logger.info("Flask app started on port 5000")

    async def monitor_events():
        await event_controller.monitor_events()

    # Run Flask and event monitoring concurrently
    await asyncio.gather(
        monitor_events(),
        run_flask()
    )

if __name__ == '__main__':
    asyncio.run(main())