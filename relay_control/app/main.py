from flask import Flask, request, jsonify
from app.api.controllers import main as main_blueprint  # Import the Blueprint

app = Flask(__name__)

# Register the Blueprint
app.register_blueprint(main_blueprint, url_prefix='/api')  # You can set a prefix if needed

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)