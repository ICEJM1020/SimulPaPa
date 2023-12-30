""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

import os
import json

from openai import OpenAI

from api_server import create_app
from agents import init_pool
from config import CONFIG


if __name__ == '__main__':
    if not os.path.exists(CONFIG["base_dir"] + "/.Users"):
        os.mkdir(CONFIG["base_dir"] + "/.Users")

    if not os.path.exists(CONFIG["base_dir"] + "/.Users/users.json"):
        with open(CONFIG["base_dir"] + "/.Users/users.json", "w") as f:
            json.dump({}, f)
    
    app = create_app()
    app.run("0.0.0.0", port=10203)
