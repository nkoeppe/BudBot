import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from flask import Blueprint, jsonify, request
from app.config.config_manager import ConfigManager

main = Blueprint('main', __name__)
config_manager = ConfigManager()

# These will be set by the main module
relay_controller = None
water_nutrient_controller = None
event_controller = None

def set_controllers(relay, water_nutrient, event):
    global relay_controller, water_nutrient_controller, event_controller
    relay_controller = relay
    water_nutrient_controller = water_nutrient
    event_controller = event

@main.route('/')
def index():
    logger.debug("Index route accessed")
    return jsonify({'message': 'Welcome to the Control System'})

@main.route('/control/status', methods=['GET'])
def status():
    logger.debug("Getting control status")
    status = relay_controller.get_status()
    logger.info("Control status retrieved")
    return jsonify({'status': status})

@main.route('/control/status/<int:pin>', methods=['GET'])
def pin_status(pin):
    logger.debug("Getting status for pin %d", pin)
    status = relay_controller.get_pin_state(pin)
    logger.info("Status for pin %d: %d", pin, status)
    return jsonify({'pin': pin, 'status': status})

@main.route('/control/test', methods=['POST'])
def test():
    logger.debug("Testing all relay pins")
    relay_controller.test()
    logger.info("Test completed")
    return jsonify({"status": "success", "message": "Test completed"}), 200

@main.route('/control/test/<int:pin>', methods=['POST'])
def test_pin(pin):
    logger.debug("Testing pin %d", pin)
    relay_controller.test_pin(pin)
    logger.info("Test completed for pin %d", pin)
    return jsonify({"status": "success", "message": f"Test completed for pin {pin}"}), 200

@main.route('/water-nutrient/mix', methods=['POST'])
def mix_nutrients():
    logger.debug("Mixing nutrients")
    nutrient_amounts = request.json.get('nutrient_amounts', {})
    water_nutrient_controller.mix_nutrients(nutrient_amounts)
    logger.info("Nutrients mixed successfully")
    return jsonify({"status": "success", "message": "Nutrients mixed successfully"}), 200

@main.route('/water-nutrient/fill-water', methods=['POST'])
def fill_water():
    logger.debug("Filling water")
    ml = request.json.get('ml', 5000)
    water_nutrient_controller.fill_mixer_with_water(ml)
    logger.info("Mixer filled with %d ml of water", ml)
    return jsonify({"status": "success", "message": f"Mixer filled with {ml} ml of water"}), 200

@main.route('/water-nutrient/distribute', methods=['POST'])
def distribute_to_plants():
    logger.debug("Distributing nutrients to plants")
    ml_per_plant = request.json.get('ml_per_plant', 100)
    water_nutrient_controller.distribute_to_plants(ml_per_plant)
    logger.info("Distributed %d ml to each plant", ml_per_plant)
    return jsonify({"status": "success", "message": f"Distributed {ml_per_plant} ml to each plant"}), 200

@main.route('/water-nutrient/mixer-status', methods=['GET'])
def mixer_status():
    logger.debug("Getting mixer status")
    is_full = water_nutrient_controller.is_mixer_full()
    logger.info("Mixer status retrieved: is_full=%s", is_full)
    return jsonify({"status": "success", "is_full": is_full}), 200

@main.route('/event/schedule', methods=['POST'])
def schedule_event():
    logger.debug("Scheduling event")
    time_of_day = request.json.get('time_of_day', '08:00')
    event_controller.schedule_daily_watering(time_of_day)
    logger.info("Scheduled daily watering at %s", time_of_day)
    return jsonify({"status": "success", "message": f"Scheduled daily watering at {time_of_day}"}), 200

@main.route('/event/status', methods=['GET'])
def event_status():
    logger.debug("Getting event status")
    events = event_controller.get_scheduled_events()
    event_list = [{"time": job.next_run.strftime("%Y-%m-%d %H:%M:%S"), "job": str(job.job_func)} for job in events]
    logger.info("Event status retrieved")
    return jsonify({"status": "success", "events": event_list}), 200

@main.route('/event/run', methods=['POST'])
def run_event():
    logger.debug("Running event")
    event_controller.run_watering_cycle()
    logger.info("Watering cycle started")
    return jsonify({"status": "success", "message": "Watering cycle started"}), 200

@main.route('/config', methods=['GET'])
def get_config():
    return jsonify(config_manager.config)

@main.route('/config', methods=['POST'])
def update_config():
    data = request.json
    for key, value in data.items():
        config_manager.set(key, value)
    return jsonify({"status": "success", "message": "Configuration updated"}), 200

@main.route('/config/reload', methods=['POST'])
def reload_config():
    logger.debug("Reloading configuration for all controllers")
    water_nutrient_controller.reload_config()
    event_controller.reload_config()
    logger.info("Configuration reloaded for all controllers")
    return jsonify({"status": "success", "message": "Configuration reloaded for all controllers"}), 200