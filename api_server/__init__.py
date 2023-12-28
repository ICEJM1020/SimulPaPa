""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 


from flask import Flask

from api_server import api_test, api_user
from config import CONFIG

def create_app():
    app = Flask(__name__)

    app.register_blueprint(api_test.bp)

    app.register_blueprint(api_user.bp)

    return app

