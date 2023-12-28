""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

from flask import Blueprint
from openai import OpenAI

from config import CONFIG

route_group = "test"
bp = Blueprint(route_group, __name__)

@bp.route(f"/{route_group}/server", methods=["POST", "GET"])
def home():
    return CONFIG["test_server"] + f"\nCurrent OpenAI User: {CONFIG['openai']['key_owner']}"

@bp.route(f"/{route_group}/gpt", methods=["POST", "GET"])
def about():
    return test_gpt()


"""
Author: Joon Sung Park (joonspk@stanford.edu)
Source: https://github.com/joonspk-research/generative_agents/blob/main/reverie/backend_server/test.py
"""
def test_gpt(): 
    """
    test if GPT return words
    RETURNS: 
    a str of GPT-3's response. 
    """
    open_ai_client = OpenAI(
        api_key=CONFIG["openai"]["api_key"],
        organization=CONFIG["openai"]["organization"],
    )

    try: 
        completion = open_ai_client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[{"role": "user", "content": "Tell me what is the date Alan Turing born in the following format: Year:$year$/Month:$month$/Day:$day$"}]
        )
        return completion.choices[0].message.content
    except: 
        print ("ChatGPT ERROR")
        return "ChatGPT ERROR"


