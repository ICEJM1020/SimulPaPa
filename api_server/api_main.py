""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

from datetime import date

from flask import Blueprint, make_response, render_template
from openai import OpenAI

from config import CONFIG


mbp = Blueprint("main", __name__)

@mbp.route('/index')
@mbp.route('/')
def index(name=None):
    return render_template('index.html', name=name)

@mbp.route('/dashboard')
def dashboard(name=None):
    return render_template('dashboard.html', name=name)

@mbp.route('/create_user')
def create_user(name=None):
    return render_template('create_user.html', name=name)

@mbp.route('/random_create_user')
def random_create_user(name=None):
    return render_template('random_create_user.html', name=name)

@mbp.route('/user')
def user_page(name=None):
    return render_template('user.html', name=name)

@mbp.route('/<username>/<agentID>')
def agent_page(username, agentID, name=None):
    print(username, agentID)
    ############################
    # !!!!!!! Agent Page !!!!!!!
    ############################
    return render_template('agent.html', name=name)


"""
Test route
"""
@mbp.route(f"/test/server", methods=["POST", "GET"])
def test_server():
    return CONFIG["welcome"] + f"\nCurrent OpenAI User: {CONFIG['openai']['key_owner']}"

@mbp.route(f"/test/gpt", methods=["POST", "GET"])
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


