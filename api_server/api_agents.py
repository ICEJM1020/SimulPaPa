""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

from flask import Blueprint, request, make_response
import json

from config import CONFIG
from logger import logger
from agents import USER_POOL

from .utils import *


route_group = "agents"
abp = Blueprint(route_group, __name__)


########
#
# info tree group
#
########
@abp.route(f"/{route_group}/<username>/infotree/status", methods=["POST", "GET"])
def info_tree_status(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "message" : USER_POOL.fetch_tree_status(_uuid)
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


@abp.route(f"/{route_group}/<username>/infotree/generate", methods=["POST", "GET"])
def generate_tree(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            USER_POOL.generate_tree(_uuid)
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


########
#
# agents manage group
#
########
@abp.route(f"/{route_group}/<username>/create", methods=["POST", "GET"])
def create_agents_pool(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            msg = USER_POOL.create_agents_pool(_uuid)
            return_body = {
                "status" : True,
                "message" : USER_POOL.fetch_agents_status(_uuid) + " " + msg
            }
            logger.info(f"User {username}'s agents pool has created")
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


@abp.route(f"/{route_group}/<username>/status", methods=["POST", "GET"])
def fetch_agents_status(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "message" : USER_POOL.fetch_agents_status(_uuid)
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


@abp.route(f"/{route_group}/<username>/fetchall", methods=["POST", "GET"])
def fetch_all_agents(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            data, done = USER_POOL.fetch_all_agents(_uuid)
            return_body = {
                "status" : True,
                "data" : data,
                "message" : "done" if done else "aborted"
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


@abp.route(f"/{route_group}/<username>/savelocal", methods=["POST", "GET"])
def save_agents_pool(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "message" : USER_POOL.save_agents_pool(_uuid)
            }
            logger.info(f"User {username}'s agents pool has saved to local machine")
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


@abp.route(f"/{route_group}/<username>/loadlocal", methods=["POST", "GET"])
def load_agents_pool(username):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "user_status" : USER_POOL.load_agents_pool(_uuid)
            }
            logger.info(f"User {username}'s agents pool has loaded from local machine")
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


