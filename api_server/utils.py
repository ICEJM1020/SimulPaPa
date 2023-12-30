""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-29
"""

import json
from config import CONFIG


def check_user(username):
    try:
        with open(CONFIG["base_dir"] + "/.Users/users.json", "r") as f:
            users = json.load(f)
    except:
        return_body = (False, "Fail to open users database")
    else:
        if not username in users:
            return_body = (False, f"{username} doesn't exist")
        else:
            return_body = (True, users)
    return return_body
    
