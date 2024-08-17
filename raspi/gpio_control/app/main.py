import logging
import asyncio
from logging.config import dictConfig
from flask import Flask, request, session
from app.api.controllers import main as main_blueprint, set_controllers
from app.controller.relay_controller import RelayController
from app.controller.water_nutrient_controller import WaterNutrientController
from app.controller.event_controller import EventController
from app.config.config_manager import ConfigManager
import uuid

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
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'app.log',
            'formatter': 'default',
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
    water_nutrient_controller = WaterNutrientController(relay_controller, config_manager, logger)
    event_controller = EventController(water_nutrient_controller, config_manager, logger)
    logger.info("Controllers initialized")

    # Set instances in the controllers module
    set_controllers(relay_controller, water_nutrient_controller, event_controller)
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
        run_flask(),
        monitor_events()
    )

if __name__ == '__main__':
    asyncio.run(main())