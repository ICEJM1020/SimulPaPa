""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

import os

from openai import OpenAI

from api_server import create_app
from config import CONFIG

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':

    app = create_app()
    app.run("0.0.0.0", port=10203)
