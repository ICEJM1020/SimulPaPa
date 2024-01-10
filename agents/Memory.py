""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-01-09
""" 
import os
import json
import random
from datetime import datetime, timedelta

from logger import logger


class LongMemory:

    def __init__(self, user_folder, agent_folder) -> None:
        ## folder 
        self.user_folder = user_folder
        self.agent_folder = agent_folder
        self.user_act_folder = user_folder + "/activity_hist"
        self.agent_act_folder = agent_folder + "/activity_hist"

        ## user realated、
        self._load_info()
        self.user_act_files = {}
        self.user_last_day = self._search_user_last_day()

        # print(self.user_last_day, self.user_act_files)


    def _load_info(self):
        with open(self.agent_folder + "/info.json", "r") as f:
            info = json.load(f)
            self.info = info
            self.description = info["description"]
            del(self.info["description"])
        

    def _search_user_last_day(self, ):
        newest_date = None

        for filename in os.listdir(self.user_act_folder):
            if filename.endswith('.csv'):
                # Extract date from filename
                date_str = filename.split('.')[0]  # Remove the '.csv' part
                self.user_act_files[date_str] = os.path.join(self.user_act_folder, filename)
                try:
                    file_date = datetime.strptime(date_str, "%m-%d-%Y").date()
                    if newest_date is None or file_date > newest_date:
                        newest_date = file_date
                except ValueError:
                    # Skip the file if the date is not in the correct format
                    continue

        return newest_date.strftime('%m-%d-%Y')
    

    def fetch_user_lastday(self, ):
        return self.user_last_day
    

    def past_daily_purpose(self, cur_date, past_days:int=5):
        res = {}
        for i in range(1, past_days+1):
            past_date = datetime.strptime(cur_date, '%m-%d-%Y') - timedelta(days=i)
            daily_file = past_date.strftime('%m-%d-%Y') + ".csv"

            if os.path.exists(os.path.join(self.agent_act_folder, daily_file)):
                res[past_date.strftime('%m-%d-%Y')] = self._summary_daily_purpose(os.path.join(self.agent_act_folder, daily_file))
            else:
                res[past_date.strftime('%m-%d-%Y')] = self._summary_daily_purpose(os.path.join(self.user_act_folder, daily_file))
        print(res)
        return json.dumps(res)


    def _summary_daily_purpose(self, activity_file):
        return random.choice(["at-home", "working", "travel", "outdoor"])
    
    def past_daily_schedule(self,):
        pass


class ShortMemory:

    def __init__(self, agent_folder, info) -> None:
        self.info = info

        self.cache_file = os.path.join(agent_folder, "memory_cache.json")
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.memory_tree = json.load(f)
        else:
            self.memory_tree = {}

    def set_today(self, today):
        self.memory_tree["today"] = today

    def set_purpose(self, purpose):
        self.memory_tree["today_purpose"] = purpose

    # def set_current_activity(self, activity):
    #     self.memory_tree["last_hour_activity"] = activity
    
    def today_summary(self):
        res = f"Today is {self.memory_tree['today']}, {self.info['name']} plans to {self.memory_tree['today_purpose']}."
        return res

    def save(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.memory_tree, f)


if __name__ == "__main__":
    long_mem = LongMemory(
        user_folder="/Users/timberzhang/Documents/Documents/Long-SimulativeAgents/Code/SimulPaPa/.Users/19d7bf69-7fdc-3648-9c87-9bfca20611c2",
        agent_folder="/Users/timberzhang/Documents/Documents/Long-SimulativeAgents/Code/SimulPaPa/.Users/19d7bf69-7fdc-3648-9c87-9bfca20611c2/agents/1"
    )

