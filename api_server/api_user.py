""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

from flask import Blueprint, request, make_response
import json
import os

from config import CONFIG
from agents import create_user_filetree, delete_user_filetree, random_user, USER_POOL
from logger import logger

from .utils import *


route_group = "user"
ubp = Blueprint(route_group, __name__)


########
#
# user manage group
#
########
@ubp.route(f"/{route_group}/create", methods=["GET", "POST"])
def create_user():
    req_form = request.form

    for key in ["birthday"]:
        if not (key in req_form):
            return_body = {
                "status" : False,
                "message" : "Missing key information"
            }
            response = make_response(json.dumps(return_body), 500)
            response.headers["Content-Type"] = "application/json"
            return response
        
    try:
        with open(CONFIG["base_dir"] + "/.Users/users.json", "r") as f:
            users = json.load(f)
    except:
        return_body = {
            "status" : False,
            "message" : "Fail to open users database"
        }
    else:
        if req_form['username'] in users:
            return_body = {
                "status" : False,
                "message" : req_form['username'] + " has cretated by " + req_form['name']
            }
        else:
            try:
                uuid = create_user_filetree(**req_form)

                users[req_form['username']] = uuid
                return_body = {
                    "status" : True,
                    "user" : req_form['username'],
                    "name" : req_form['name'],
                    "message" : "Creation successful"
                }
                logger.info(f"User {req_form['username']} created")
            except:
                return_body = {
                    "status" : False,
                    "message" : "Creation Error"
                }
        with open(CONFIG["base_dir"] + "/.Users/users.json", "w") as f:
            json.dump(users, f)

    response = make_response(json.dumps(return_body), 200 if return_body["status"] else 500)
    response.headers["Content-Type"] = "application/json"
    return response


@ubp.route(f"/{route_group}/random", methods=["GET", "POST"])
def radnom_user():
    req_form = request.form
    return_body = {"status" : False}
    if not ("short_description" in req_form):
        return_body = {
            "status" : False,
            "message" : "Missing key information"
        }
        response = make_response(json.dumps(return_body), 500)
        response.headers["Content-Type"] = "application/json"
        return response
    else:
        short_description = req_form["short_description"]
    
    return_body = {}
    try:
        infos = random_user(short_description)
    except:
        return_body = {
            "status" : False,
            "message" : "Random creation failed"
        }
    else:
        return_body = {
            "status" : True,
            "infos" : infos
        }

    response = make_response(json.dumps(return_body), 200 if return_body["status"] else 500)
    response.headers["Content-Type"] = "application/json"
    return response


@ubp.route(f"/{route_group}/delete/<username>", methods=["POST"])
def delete_user(username):
    status, user_list = check_user(username=username)
    if status:
        if delete_user_filetree(user_list[username]):
            user_list.pop(username)
            return_body = {
                "status" : True,
                "message" : f"Successfully delete user: {username}"
            }
            logger.info(f"User {username} deleted")
        else:
            return_body = {
                "status" : False,
                "message" : "Delete error"
            }
    else:
        return_body = {
            "status" : False,
            "message" : f"{username} doesn't exist"
        }
    with open(CONFIG["base_dir"] + "/.Users/users.json", "w") as f:
        json.dump(user_list, f)

    response = make_response(json.dumps(return_body), 200 if return_body["status"] else 500)
    response.headers["Content-Type"] = "application/json"
    return response
    

@ubp.route(f"/{route_group}/upload", methods=["POST"])
def upload_user_file():
    if "username" not in request.form.keys():
        return_body = {
                "status" : False,
                "message" : "Need username"
            }
    else:
        username = request.form["username"]
        status, user_list = check_user(username=username)
        if status:
            _uuid = user_list[username]
            file = request.files['activity']
            file.save(CONFIG['base_dir']+f"/.Users/{_uuid}/{file.filename}")
            return_body = {
                "status" : True,
                "message" : "Upload successfully"
            }
            logger.info(f"User {username} uploaded {file.filename}")
        else:
            return_body = {
                "status" : False,
                "message" : f"{username} doesn't exist"
            }
    response = make_response(json.dumps(return_body), 200 if return_body["status"] else 500)
    response.headers["Content-Type"] = "application/json"
    return response

@ubp.route(f"/{route_group}/all", methods=["POST", "GET"])
def fetch_all_user():
    return_body = {}
    try:
        with open(CONFIG["base_dir"] + "/.Users/users.json", "r") as f:
            users = json.load(f)
    except:
        return_body['message'] = "Fail to open users database"
    else:
        return_body['message'] = "success"
        return_body['users'] = users

    response = make_response(json.dumps(return_body), 200 if return_body else 500)
    response.headers["Content-Type"] = "application/json"
    return response

########
#
# activate user
#
########
@ubp.route(f"/{route_group}/activate/<username>", methods=["POST", "GET"])
def activate_user(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "message" : "User has activated"
            }
        else:
            USER_POOL.append(_uuid)
            return_body = {
                "status" : True,
                "message" : "User activated successfully"
            }
            logger.info(f"User {username} activated")
    else:
        return_body = {
                "status" : False,
                "message" : f"{username} doesn't exist"
            }
    response = make_response(json.dumps(return_body), 200 if return_body["status"] else 500)
    response.headers["Content-Type"] = "application/json"
    return response


@ubp.route(f"/{route_group}/deactivate/<username>", methods=["POST", "POST"])
def deactivate_user(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            try:
                USER_POOL.pop(_uuid)
            except:
                return_body = {
                    "status" : False,
                    "message" : "User failed to deactivate"
                }
            else:
                return_body = {
                    "status" : True,
                    "message" : "User has deactivated"
                }
                logger.info(f"User {username} deactivated")
        else:
            return_body = {
                "status" : False,
                "message" : "User has not activated"
            }
    else:
        return_body = {
                "status" : False,
                "message" : f"{username} doesn't exist"
            }
    response = make_response(json.dumps(return_body), 200 if return_body["status"] else 500)
    response.headers["Content-Type"] = "application/json"
    return response


@ubp.route(f"/{route_group}/status/<username>", methods=["POST", "GET"])
def fetch_user_status(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "message" : USER_POOL.fetch_user_status(_uuid)
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


########
#
# description group
#
########

@ubp.route(f"/{route_group}/description/<username>", methods=["POST", "GET"])
def fetch_user_description(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "description" : USER_POOL.fetch_user_description(_uuid)
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


@ubp.route(f"/{route_group}/description/regenerate/<username>", methods=["POST", "GET"])
def regenerate_user_description(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            USER_POOL.generate_user_description(_uuid)
            return_body = {
                "status" : True,
                "description" : USER_POOL.fetch_user_description(_uuid)
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


@ubp.route(f"/{route_group}/description/modify/<username>", methods=["GET", "POST"])
def modify_user_description(username):
    req_form = request.form

    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            USER_POOL.modify_user_info(_uuid, req_form)
            return_body = {
                "status" : True,
                "description" : USER_POOL.fetch_user_description(_uuid)
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


########
#
# simulation group
#
########
@ubp.route(f"/simulation/start/<username>", methods=["GET", "POST"])
def start_simulation(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            USER_POOL.start_simulation(_uuid)
            return_body = {
                "status" : True,
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


@ubp.route(f"/simulation/continue/<username>", methods=["GET", "POST"])
def continue_simulation(username):
    if "days" in request.form.keys(): 
        days = int(request.form['days'])
    else:
        days=1
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            USER_POOL.continue_simulation(_uuid, days)
            return_body = {
                "status" : True,
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


@ubp.route(f"/simulation/status/<username>", methods=["GET", "POST"])
def simulation_status(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "message" : USER_POOL.fetch_simulation_status(_uuid)
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


@ubp.route(f"/simulation/interplan/<username>", methods=["GET", "POST"])
def set_intervention(username):
    status, user_list = check_user(username=username)
    if "plan" in request.form.keys(): 
        plan = request.form['plan']
        if status:
            _uuid = user_list[username]
            if USER_POOL.exist(_uuid):
                return_body = {
                    "status" : True,
                    "message" : USER_POOL.set_intervention(_uuid, plan)
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
    else:
        return_body = {
                    "status" : False,
                    "message" : f"No intervention plan, missing \"plan\" key in form data."
                }
    response = make_response(json.dumps(return_body), 200 if return_body["status"] else 500)
    response.headers["Content-Type"] = "application/json"
    return response
