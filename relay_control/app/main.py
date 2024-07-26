from flask import Flask, request, jsonify
from relay_controller import RelayController
from controllers import main as main_blueprint  # Import the Blueprint

app = Flask(__name__)

# Register the Blueprint
app.register_blueprint(main_blueprint, url_prefix='/api')  # You can set a prefix if needed


relay_controller = RelayController()

@app.route('/relay/on/<int:pin>', methods=['POST'])
def turn_on_relay(pin):
    if relay_controller.turn_on(pin):
        return jsonify({"status": "success", "message": f"Relay {pin} turned on"}), 200
    else:
        return jsonify({"status": "error", "message": f"Relay {pin} not found"}), 404

@app.route('/relay/off/<int:pin>', methods=['POST'])
def turn_off_relay(pin):
    if relay_controller.turn_off(pin):
        return jsonify({"status": "success", "message": f"Relay {pin} turned off"}), 200
    else:
        return jsonify({"status": "error", "message": f"Relay {pin} not found"}), 404

@app.route('/relay/cleanup', methods=['POST'])
def cleanup():
    relay_controller.cleanup()
    return jsonify({"status": "success", "message": "GPIO cleanup done"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)