""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-01-09
""" 

import os
import json
import sys
sys.path.append(os.path.abspath('./'))

import pandas as pd
from openai import OpenAI

from config import CONFIG


def decompose_activity_file(files:list, target_folder:str):
    for file in files:
        df = pd.read_csv(file)

        # Check if the 'date' column exists
        if 'date' not in df.columns:
            raise ValueError("The CSV file does not have a 'date' column.")

        # Group by the 'date' column
        grouped = df.groupby('date')

        # Save each group to a separate CSV file
        for date, group in grouped:
            _date = str(date)
            filename = f"{_date[:2]}-{_date[2:4]}-{_date[4:8]}.csv"
            filepath = os.path.join(target_folder, filename)
            _group = group.drop("date",axis=1)

            _group["time"] = _group["time"].apply(lambda x : str(x).zfill(6))
            _group["hour"] = _group["time"].apply(lambda x : x[:2])
            _group["minute"] = _group["time"].apply(lambda x : x[2:4])

            _group.to_csv(filepath, index=False)


def safe_chat(prompt, repeat=5):
    if CONFIG['debug']: print(prompt)
    chat_client = OpenAI(
            api_key=CONFIG["openai"]["api_key"],
            organization=CONFIG["openai"]["organization"],
        )
    for i in range(repeat):
        completion = chat_client.chat.completions.create(
            model=CONFIG["openai"]["model"], 
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        gpt_response = safe_load_gpt_content(completion.choices[0].message.content, prompt)
        if gpt_response: 
            return True, gpt_response
    return False, completion.choices[0].message.content

def safe_load_gpt_content(content:str, prompt:str):
    try:
        content = content.replace("\n", "")
        json_content = json.loads(content)
    except:
        if CONFIG['debug']:
            print("==========")
            print(prompt)
            print("==========")
            print(content)
            print("==========")
        return False
    else:
        return json_content

