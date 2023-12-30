""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 
from datetime import date
import json

from config import CONFIG

from openai import OpenAI

from .common_prompt import description_prompt

def gpt_description(name, birthday, **kwargs):
    age = int(date.today().year) - int(birthday.split("-")[-1])
    open_ai_client = OpenAI(
        api_key=CONFIG["openai"]["api_key"],
        organization=CONFIG["openai"]["organization"],
    )
    prompt = description_prompt(name=name, birthday=birthday, age=age, **kwargs)
    completion = open_ai_client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=[{
            # "role": "system", "content": "You are a census taker who knows everyone, and you write detailed descriptions.",
            "role": "user", "content": prompt
            }]
    )
    return json.loads(completion.choices[0].message.content)
