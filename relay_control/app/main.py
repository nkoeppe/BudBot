import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from flask import Flask
from app.api.controllers import main as main_blueprint, set_controllers
from app.controller.relay_controller import RelayController
from app.controller.water_nutrient_controller import WaterNutrientController
from app.controller.event_controller import EventController

app = Flask(__name__)

# Initialize instances
logger.debug("Initializing controllers")
relay_controller_instance = RelayController()
water_nutrient_controller_instance = WaterNutrientController(relay_controller_instance, {})
event_controller_instance = EventController(water_nutrient_controller_instance)
logger.info("Controllers initialized")

# Set instances in the controllers module
set_controllers(relay_controller_instance, water_nutrient_controller_instance, event_controller_instance)

# Register the Blueprint
app.register_blueprint(main_blueprint, url_prefix='/api')

if __name__ == '__main__':
    logger.debug("Starting Flask app")
    app.run(host='0.0.0.0', port=5000)
    logger.info("Flask app started on port 5000")