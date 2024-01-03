""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

from flask import Blueprint, request, make_response
import json

from config import CONFIG
from agents import create_user_filetree, delete_user_filetree, USER_POOL

from .utils import *


route_group = "agents"
abp = Blueprint(route_group, __name__)


########
#
# info tree group
#
########
@abp.route(f"/{route_group}/<username>/infotree/status", methods=["POST"])
def info_tree_status(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "user_status" : USER_POOL.fetch_tree_status(_uuid)
            }
        else:
            return_body = {
                "status" : False,
                "message" : f"{username} has not been activated"
            }
    else:
        return_body = {
                "status" : False,
                "message" : f"{username} doesn't exist"
            }
    response = make_response(json.dumps(return_body), 200 if return_body["status"] else 500)
    response.headers["Content-Type"] = "application/json"
    return response


