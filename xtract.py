from flask import (
        Flask,
        render_template,
)
import connexion
from connexion.resolver import  RestyResolver
from flask_cors import CORS
import os

APP_HOST = os.environ['APP_HOST']
APP_PORT = os.environ['APP_PORT']

app = connexion.App(__name__, specificatyion_dir="./")

app.add_api('xtract_api_spec.yaml', resolver=RestyResolver('api'))

@app.route('/')
def home():
    """
    Hello world @ 5000
    """

    return render_template('home.html')

if __name__ == '__main__':
    app.run(host=APP_HOST, port=APP_PORT, debug=True)
