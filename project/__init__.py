import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

# instantiate the app
app = Flask(__name__)

# set config
app_settings = os.getenv('APP_SETTINGS')
app.config.from_object(app_settings)

# instantiate the db
db = SQLAlchemy(app)


@app.route('/', methods=['GET'])

def ping_pong():
    return jsonify({
        'status': 'success',
        'message': 'pong!'
    })