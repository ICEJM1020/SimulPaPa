""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-01-09
""" 

import os
import json
import sys
import re
from typing import Dict, List, Any
sys.path.append(os.path.abspath('./'))

import pandas as pd
from openai import OpenAI
from langchain_core.callbacks import BaseCallbackHandler

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


"""
copyright: https://github.com/langchain-ai/langchain/issues/6628#issuecomment-1906776820
print full prompts in langchain
"""
class CustomHandler(BaseCallbackHandler):
    def __init__(self, verbose, **kwargs) -> None:
        self._verbose = verbose
        super().__init__(**kwargs)

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        formatted_prompts = "\n".join(prompts)
        if self._verbose: print(f"Prompt:\n{formatted_prompts}")
        # output = chain.invoke({"info": input_text}, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})


def label_list_to_str(labels:list):
    res = ""
    for label in labels:
        res += label
        res += "; "
    return res

def parse_reg_activity(content):
    try:
        match = re.search(
                r"\{.*\}", content.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL
            )
        json_str = ""
        if match:
            json_str = match.group()
        json_object = json.loads(json_str, strict=False)
        
        answer = json_object["answer"] 
        if re.search(r'\b(Yes)\b', answer):
            return True, json_object["activity"], json_object["sensor_summary"]
        elif re.search(r'\b(No)\b', answer):
            return False, json_object["activity"], json_object["sensor_summary"]
        else:
            raise Exception(f"Parse recognition answer error\n{content}")
    except:
        raise Exception(f"Parse recognition answer error\n{content}")


