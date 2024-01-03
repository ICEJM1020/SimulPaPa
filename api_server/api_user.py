""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

from flask import Blueprint, request, make_response
import json
import os

from config import CONFIG
from agents import create_user_filetree, delete_user_filetree, USER_POOL

from .utils import *


route_group = "user"
ubp = Blueprint(route_group, __name__)


########
#
# user manage group
#
########
@ubp.route(f"/{route_group}/create", methods=["GET"])
def create_user():
    req_form = request.form

    for key in ["name" ,"gender","race","birthday","city","disease"]:
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
        else:
            return_body = {
                "create_status" : False,
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
    

@ubp.route(f"/{route_group}/upload", methods=["GET"])
def upload_user_file():
    print()
    if "username" not in request.form.keys():
        return_body = {
                "status" : False,
                "user_status" : "Need username"
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
# activate user
#
########
@ubp.route(f"/{route_group}/activate/<username>", methods=["POST"])
def activate_user(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "user_status" : "User has activated"
            }
        else:
            USER_POOL.append(_uuid)
            return_body = {
                "status" : True,
                "message" : "User activated successfully"
            }
    else:
        return_body = {
                "status" : False,
                "message" : f"{username} doesn't exist"
            }
    response = make_response(json.dumps(return_body), 200 if return_body["status"] else 500)
    response.headers["Content-Type"] = "application/json"
    return response


@ubp.route(f"/{route_group}/deactivate/<username>", methods=["POST"])
def deactivate_user(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            USER_POOL.pop(_uuid)
            return_body = {
                "status" : True,
                "user_status" : "User has deactivated"
            }
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


@ubp.route(f"/{route_group}/status/<username>", methods=["POST"])
def fetch_user_status(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "user_status" : USER_POOL.fetch_user_status(_uuid)
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

@ubp.route(f"/{route_group}/description/<username>", methods=["POST"])
def fetch_user_description(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "user_status" : USER_POOL.fetch_user_description(_uuid)
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


@ubp.route(f"/{route_group}/description/regenerate/<username>", methods=["POST"])
def regenerate_user_description(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            USER_POOL.generate_user_description(_uuid)
            return_body = {
                "status" : True,
                "user_status" : USER_POOL.fetch_user_description(_uuid)
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


@ubp.route(f"/{route_group}/description/modify/<username>", methods=["GET"])
def modify_user_description(username):
    req_form = request.form

    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            USER_POOL.modify_user_info(_uuid, req_form)
            return_body = {
                "status" : True,
                "user_status" : USER_POOL.fetch_user_description(_uuid)
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






