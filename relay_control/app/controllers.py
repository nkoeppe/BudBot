from flask import Blueprint, jsonify, request
from relay_controller import RelayController

main = Blueprint('main', __name__)
relay_controller = RelayController()

@main.route('/')
def index():
    return jsonify({'message': 'Welcome to the Control System'})

@main.route('/control/on/<string:device>/<int:index>', methods=['POST'])
def turn_on(device, index):
    pin = relay_controller.get_pin(device, index)
    if pin and relay_controller.turn_on(pin):
        return jsonify({"status": "success", "message": f"{device.capitalize()} {index} turned on"}), 200
    else:
        return jsonify({"status": "error", "message": f"{device.capitalize()} {index} not found"}), 404

@main.route('/control/off/<string:device>/<int:index>', methods=['POST'])
def turn_off(device, index):
    pin = relay_controller.get_pin(device, index)
    if pin and relay_controller.turn_off(pin):
        return jsonify({"status": "success", "message": f"{device.capitalize()} {index} turned off"}), 200
    else:
        return jsonify({"status": "error", "message": f"{device.capitalize()} {index} not found"}), 404

@main.route('/control/on_all/<string:device>', methods=['POST'])
def turn_on_all(device):
    device_pins = relay_controller.get_device_pins(device)
    if device_pins:
        for pin in device_pins:
            relay_controller.turn_on(pin)
        return jsonify({"status": "success", "message": f"All {device} devices turned on"}), 200
    else:
        return jsonify({"status": "error", "message": f"{device.capitalize()} devices not found"}), 404

@main.route('/control/off_all', methods=['POST'])
def turn_off_all():
    relay_controller.turn_off_all()
    return jsonify({"status": "success", "message": "All devices turned off"}), 200

@main.route('/control/status', methods=['GET'])
def status():
    status = relay_controller.get_status()
    return jsonify({'status': status})

@main.route('/control/status/<int:pin>', methods=['GET'])
def pin_status(pin):
    status = relay_controller.get_pin_status(pin)
    return jsonify({'pin': pin, 'status': status})

@main.route('/control/cleanup', methods=['POST'])
def cleanup():
    relay_controller.cleanup()
    return jsonify({"status": "success", "message": "GPIO cleanup done"}), 200

@main.route('/control/test', methods=['POST'])
def test():
    relay_controller.test()
    return jsonify({"status": "success", "message": "Test completed"}), 200
