""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 
import os

from flask import Flask

# from api_server import api_test, api_user, api_agents

from .api_main import mbp
from .api_user import ubp
from .api_agents import abp

from config import CONFIG


def create_app():
    
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

    app = Flask(__name__, static_folder=static_dir, template_folder=templates_dir)

    app.register_blueprint(mbp)

    app.register_blueprint(ubp)

    app.register_blueprint(abp)

    return app


