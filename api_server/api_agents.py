""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

from flask import Blueprint, request, make_response, send_file
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
            USER_POOL.create_agents_pool(_uuid)
            return_body = {
                "status" : True,
                "message" : USER_POOL.fetch_agents_status(_uuid)
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
                "message" : USER_POOL.load_agents_pool(_uuid)
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


########
#
# single agent group
#
########
@abp.route(f"/agent/<username>/<agent_id>/info", methods=["POST", "GET"])
def load_agent_info(username, agent_id):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "info" : USER_POOL.load_agent_info(_uuid, int(agent_id)),
                "message" : "",
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


@abp.route(f"/agent/<username>/<agent_id>/portrait", methods=["POST", "GET"])
def load_agent_portrait(username, agent_id):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "file" : USER_POOL.load_agent_portrait(_uuid, int(agent_id)),
                "message" : "",
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
    
    if return_body["status"]:
        return send_file(return_body["file"])
    else:
        response = make_response(json.dumps(return_body), 200 if return_body["status"] else 500)
        response.headers["Content-Type"] = "application/json"
        return response
    

@abp.route(f"/agent/<username>/<agent_id>/donedate", methods=["POST", "GET"])
def fetch_done_dates(username, agent_id):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "data" : USER_POOL.fetch_agent_done_dates(_uuid, int(agent_id)),
                "message" : "",
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


@abp.route(f"/agent/<username>/<agent_id>/chathis/<date>", methods=["POST", "GET"])
def fetch_chat_history(username, agent_id, date):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "data" : USER_POOL.fetch_agent_chatbot(_uuid, int(agent_id), date),
                "message" : "",
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

@abp.route(f"/agent/<username>/<agent_id>/heartrate/<date>", methods=["POST", "GET"])
def fetch_heartrate(username, agent_id, date):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "data" : USER_POOL.fetch_agent_heartrate(_uuid, int(agent_id), date),
                "message" : "",
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

@abp.route(f"/agent/<username>/<agent_id>/lochis/<date>", methods=["POST", "GET"])
def fetch_location_hist(username, agent_id, date):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "data" : USER_POOL.fetch_agent_location_hist(_uuid, int(agent_id), date),
                "message" : "",
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


@abp.route(f"/agent/<username>/<agent_id>/schedule/<date>", methods=["POST", "GET"])
def fetch_schedule(username, agent_id, date):
    status, user_list = check_user(username=username)
    if status:
        _uuid = user_list[username]
        if USER_POOL.exist(_uuid):
            return_body = {
                "status" : True,
                "data" : USER_POOL.fetch_agent_schedule(_uuid, int(agent_id), date),
                "message" : "",
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
