""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-01-09
""" 

import os
import json
import pandas as pd


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


def safe_load_gpt_content(content):
    try:
        json_content = json.loads(content)
    except:
        return False
    else:
        return json_content


if __name__ == "__main__":
    decompose_activity_file(
        files=["/Users/timberzhang/Documents/Documents/Long-SimulativeAgents/Code/SimulPaPa/.Users/19d7bf69-7fdc-3648-9c87-9bfca20611c2/jc-pilot001.csv"],
        target_folder="/Users/timberzhang/Documents/Documents/Long-SimulativeAgents/Code/SimulPaPa/.Users/19d7bf69-7fdc-3648-9c87-9bfca20611c2/activity_hist"
    )
