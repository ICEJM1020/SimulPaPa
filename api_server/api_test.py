""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

from datetime import date

from flask import Blueprint, make_response
from openai import OpenAI

from config import CONFIG

route_group = "test"
tbp = Blueprint(route_group, __name__)

@tbp.route(f"/{route_group}/server", methods=["POST", "GET"])
def test_server():
    return CONFIG["welcome"] + f"\nCurrent OpenAI User: {CONFIG['openai']['key_owner']}"

@tbp.route(f"/{route_group}/gpt", methods=["POST", "GET"])
def test_gpt():
    gpt_response = _test_gpt()
    if gpt_response[0]:
        return  gpt_response[1], 200
    else:
        return  gpt_response[1], 502


"""
Author: Joon Sung Park (joonspk@stanford.edu)
Source: https://github.com/joonspk-research/generative_agents/blob/main/reverie/backend_server/test.py
"""
def _test_gpt(): 
    """
    test if GPT return words
    RETURNS: 
    a str of GPT-3's response. 
    """
    
    try: 
        open_ai_client = OpenAI(
            api_key=CONFIG["openai"]["api_key"],
            organization=CONFIG["openai"]["organization"],
        )
        completion = open_ai_client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[{
                "role": "user", "content": f"Today is {date.today()}. Tell me how old is Alan Turing born in the following format: Alan Turing was born in Year:$year$/Month:$month$/Day:$day$, and hs is $Age$ if he is alive!"
                }]
        )
        return True, completion.choices[0].message.content
    except: 
        return False, "OpenAI Error"


