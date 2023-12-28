""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

from flask import Blueprint, request

from config import CONFIG
from agents import generate_description

route_group = "user"
bp = Blueprint(route_group, __name__)

@bp.route(f"/{route_group}/create", methods=["GET"])
def create_user():
    if request.method == 'GET':
        description = generate_description(**request.form)

    return_body = {
        "user" : request.form['name'],
        "description" : description
    }
    return return_body


