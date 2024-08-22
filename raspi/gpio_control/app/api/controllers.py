import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from flask import Blueprint, jsonify, request
from app.config.config_manager import ConfigManager
from app.config.plant_manager import PlantManager

main = Blueprint('main', __name__)
config_manager = ConfigManager()

# These will be set by the main module
relay_controller = None
water_nutrient_controller = None
event_controller = None
sensor_hub_controller = None 
plant_manager = None

def set_controllers(relay, water_nutrient, event, sensor_hub, plant):
    global relay_controller, water_nutrient_controller, event_controller, sensor_hub_controller, plant_manager
    relay_controller = relay
    water_nutrient_controller = water_nutrient
    event_controller = event
    sensor_hub_controller = sensor_hub
    plant_manager = plant

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

@main.route('/water-nutrient/distribute/<plant_id>', methods=['POST'])
def distribute_to_plant(plant_id):
    logger.debug("Distributing nutrients to plant: %s", plant_id)
    ml_per_plant = request.json.get('ml_per_plant', 100)
    water_nutrient_controller.distribute_to_plant(plant_id, ml_per_plant)
    logger.info("Distributed %d ml to plant: %s", ml_per_plant, plant_id)
    return jsonify({"status": "success", "message": f"Distributed {ml_per_plant} ml to plant: {plant_id}"}), 200

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



@main.route('/sensor-hub/read', methods=['GET'])
def read_sensor():
    logger.debug("Reading sensor data")
    data = sensor_hub_controller.get_latest_sensor_data()
    return jsonify({"status": "success", "data": data}), 200

@main.route('/sensor-hub/send-command', methods=['POST'])
def request_sensor_data():
    logger.debug("Sending command to sensor hub")
    command = request.json.get('command', 'GET_DATA')
    sensor_hub_controller.send_command(command)
    logger.info("Sent command to sensor hub: %s", command)
    return jsonify({"status": "success", "message": f"Command sent to sensor hub: {command}"}), 200


@main.route('/sensor-hub/subscribe', methods=['POST'])
def subscribe_topic():
    logger.debug("Subscribing to new topic")
    topic = request.json.get('topic')
    if topic:
        sensor_hub_controller.subscribe_topic(topic)
        logger.info("Subscribed to topic: %s", topic)
        return jsonify({"status": "success", "message": f"Subscribed to topic: {topic}"}), 200
    else:
        return jsonify({"status": "error", "message": "No topic provided"}), 400

@main.route('/sensor-hub/unsubscribe', methods=['POST'])
def unsubscribe_topic():
    logger.debug("Unsubscribing from topic")
    topic = request.json.get('topic')
    if topic:
        sensor_hub_controller.unsubscribe_topic(topic)
        logger.info("Unsubscribed from topic: %s", topic)
        return jsonify({"status": "success", "message": f"Unsubscribed from topic: {topic}"}), 200
    else:
        return jsonify({"status": "error", "message": "No topic provided"}), 400

@main.route('/sensor-hub/subscriptions', methods=['GET'])
def get_subscriptions():
    logger.debug("Getting subscribed topics")
    topics = sensor_hub_controller.get_subscribed_topics()
    return jsonify({"status": "success", "topics": topics}), 200


@main.route('/sensor-hub/calibrate', methods=['POST'])
def calibrate_sensor():
    logger.debug("Starting sensor calibration")
    sensor_id = request.json.get('sensor_id')
    calibration_time = request.json.get('calibration_time', 60)
    delay = request.json.get('delay', 1)
    
    if not sensor_id:
        return jsonify({"status": "error", "message": "No sensor_id provided"}), 400
    
    sensor_hub_controller.calibrate_sensor_auto(sensor_id, int(calibration_time), int(delay))
    logger.info(f"Calibration completed for sensor {sensor_id}")
    return jsonify({"status": "success", "message": f"Calibration completed for sensor {sensor_id}"}), 200

@main.route('/sensor-hub/sensors', methods=['GET'])
def get_sensors():
    logger.debug("Getting all sensors")
    sensors = sensor_hub_controller.get_sensors()
    return jsonify({"status": "success", "sensors": sensors}), 200

@main.route('/sensor-hub/sensors', methods=['POST'])
def add_sensor():
    logger.debug("Adding new sensor")
    sensor_data = request.json
    if not sensor_data or 'pin' not in sensor_data or 'type' not in sensor_data or 'id' not in sensor_data:
        return jsonify({"status": "error", "message": "Invalid sensor data"}), 400
    
    label = f"{sensor_data['type']}_{sensor_data['id']}"
    if sensor_data['type'].startswith('dht'):
        success = sensor_hub_controller.add_dht_sensor(label, sensor_data)
    else:
        success = sensor_hub_controller.add_sensor(label, sensor_data)
    
    if success:
        logger.info(f"Added new sensor: {label}")
        return jsonify({"status": "success", "message": f"Sensor {label} added successfully"}), 201
    else:
        return jsonify({"status": "error", "message": "Failed to add sensor"}), 500

@main.route('/sensor-hub/sensors/<label>', methods=['DELETE'])
def remove_sensor(label):
    logger.debug(f"Removing sensor: {label}")
    success = sensor_hub_controller.remove_sensor(label)
    if success:
        logger.info(f"Removed sensor: {label}")
        return jsonify({"status": "success", "message": f"Sensor {label} removed successfully"}), 200
    else:
        return jsonify({"status": "error", "message": f"Sensor {label} not found"}), 404

@main.route('/sensor-hub/sensors/<label>/calibrate', methods=['POST'])
def calibrate_specific_sensor(label):
    logger.debug(f"Calibrating sensor: {label}")
    calibration_time = request.json.get('calibration_time', 60)
    delay = request.json.get('delay', 1)
    
    if not label:
        return jsonify({"status": "error", "message": "No sensor label provided"}), 400
    
    sensor_hub_controller.calibrate_sensor_auto(label, int(calibration_time), int(delay))
    logger.info(f"Calibration completed for sensor {label}")
    return jsonify({"status": "success", "message": f"Calibration completed for sensor {label}"}), 200

@main.route('/sensor-hub/sensors/<label>/calibration', methods=['GET'])
def get_sensor_calibration(label):
    logger.debug(f"Getting calibration for sensor: {label}")
    calibration = sensor_hub_controller.get_calibration(label)
    if calibration:
        return jsonify({"status": "success", "calibration": calibration}), 200
    else:
        return jsonify({"status": "error", "message": f"Calibration not found for sensor {label}"}), 404

@main.route('/sensor-hub/max-readings', methods=['GET', 'POST'])
def max_readings():
    if request.method == 'POST':
        max_readings = request.json.get('max_readings')
        if max_readings is not None and isinstance(max_readings, int) and max_readings > 0:
            sensor_hub_controller.set_max_readings(max_readings)
            logger.info(f"Max readings updated to {max_readings}")
            return jsonify({"status": "success", "message": f"Max readings updated to {max_readings}"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid max_readings value"}), 400
    else:
        max_readings = sensor_hub_controller.max_readings
        return jsonify({"status": "success", "max_readings": max_readings}), 200
    
@main.route('/sensor-hub/readings', methods=['GET'])
def get_readings():
    data = {label: list(readings) for label, readings in sensor_hub_controller.sensor_readings.items()}
    logger.info(f"Readings retrieved: {data}")
    return jsonify({"status": "success", "data": data}), 200
    
@main.route('/sensor-hub/clear-all', methods=['POST'])
def clear_all():
    logger.debug(f"Clearing all sensors and settings")
    sensor_hub_controller.clear_all()
    return jsonify({"status": "success", "message": "Cleared all sensors and settings"}), 200

@main.route('/sensor-hub/restart-arduino', methods=['POST'])
def restart_arduino():
    logger.debug(f"Restarting Arduino")
    sensor_hub_controller.restart_arduino()
    return jsonify({"status": "success", "message": "Arduino restarted"}), 200

@main.route('/plants', methods=['GET'])
def get_all_plants():
    logger.debug("Getting all plants")
    plants = plant_manager.get_all_plants()
    return jsonify({"status": "success", "plants": plants}), 200

@main.route('/plants', methods=['POST'])
def add_plant():
    logger.debug("Adding new plant")
    data = request.json
    if not data or 'plant_id' not in data or 'moisture_sensor_id' not in data or 'water_pump_id' not in data or 'start_watering_threshold' not in data or 'stop_watering_threshold' not in data:
        return jsonify({"status": "error", "message": "Invalid plant data"}), 400
    
    plant_manager.add_plant(
        data['plant_id'],
        data['moisture_sensor_id'],
        data['water_pump_id'],
        data['start_watering_threshold'],
        data['stop_watering_threshold']
    )
    logger.info(f"Added new plant: {data['plant_id']}")
    return jsonify({"status": "success", "message": f"Plant {data['plant_id']} added successfully"}), 201

@main.route('/plants/<plant_id>', methods=['GET'])
def get_plant(plant_id):
    logger.debug(f"Getting plant: {plant_id}")
    plant = plant_manager.get_plant(plant_id)
    if plant:
        return jsonify({"status": "success", "plant": plant}), 200
    else:
        return jsonify({"status": "error", "message": f"Plant {plant_id} not found"}), 404


@main.route('/plants/<plant_id>', methods=['PUT'])
def update_plant(plant_id):
    logger.debug(f"Updating plant: {plant_id}")
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No update data provided"}), 400
    
    plant_manager.update_plant(
        plant_id,
        data.get('moisture_sensor_id'),
        data.get('water_pump_id'),
        data.get('start_watering_threshold'),
        data.get('stop_watering_threshold')
    )
    logger.info(f"Updated plant: {plant_id}")
    return jsonify({"status": "success", "message": f"Plant {plant_id} updated successfully"}), 200

@main.route('/plants/<plant_id>', methods=['DELETE'])
def remove_plant(plant_id):
    logger.debug(f"Removing plant: {plant_id}")
    plant_manager.remove_plant(plant_id)
    logger.info(f"Removed plant: {plant_id}")
    return jsonify({"status": "success", "message": f"Plant {plant_id} removed successfully"}), 200

@main.route('/plants/by-sensor/<sensor_id>', methods=['GET'])
def get_plant_by_sensor(sensor_id):
    logger.debug(f"Getting plant by sensor: {sensor_id}")
    plant_id, plant_data = plant_manager.get_plant_by_sensor(sensor_id)
    if plant_id:
        return jsonify({"status": "success", "plant_id": plant_id, "plant_data": plant_data}), 200
    else:
        return jsonify({"status": "error", "message": f"No plant found for sensor {sensor_id}"}), 404

@main.route('/plants/by-pump/<pump_id>', methods=['GET'])
def get_plant_by_pump(pump_id):
    logger.debug(f"Getting plant by pump: {pump_id}")
    plant_id, plant_data = plant_manager.get_plant_by_pump(pump_id)
    if plant_id:
        return jsonify({"status": "success", "plant_id": plant_id, "plant_data": plant_data}), 200
    else:
        return jsonify({"status": "error", "message": f"No plant found for pump {pump_id}"}), 404

@main.route('/event/moisture-check-interval', methods=['GET', 'POST'])
def moisture_check_interval():
    if request.method == 'POST':
        interval = request.json.get('interval')
        if interval is not None and isinstance(interval, (int, float)) and interval > 0:
            event_controller.moisture_check_interval = interval
            config_manager.set('event.moisture_check_interval', interval)
            logger.info(f"Moisture check interval updated to {interval} seconds")
            return jsonify({"status": "success", "message": f"Moisture check interval updated to {interval} seconds"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid interval value"}), 400
    else:
        interval = event_controller.moisture_check_interval
        return jsonify({"status": "success", "interval": interval}), 200