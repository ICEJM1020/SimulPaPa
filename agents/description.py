""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 
from openai import OpenAI
from config import CONFIG

def generate_description(name, age, disease, city):

    open_ai_client = OpenAI(
        api_key=CONFIG["openai"]["api_key"],
        organization=CONFIG["openai"]["organization"],
    )
    
    prompt = "Generate a description from the following information within 50 words."
    prompt += f"name={name}, age={age}, disease={disease}, city={city}"
    completion = open_ai_client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=[{"role": "user", "content": prompt}]
    )

    return completion.choices[0].message.content

