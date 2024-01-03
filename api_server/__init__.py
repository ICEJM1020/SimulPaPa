""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 


from flask import Flask

# from api_server import api_test, api_user, api_agents

from .api_test import tbp
from .api_user import ubp
from .api_agents import abp

from config import CONFIG

def create_app():
    app = Flask(__name__)

    app.register_blueprint(tbp)

    app.register_blueprint(ubp)

    app.register_blueprint(abp)

    return app

