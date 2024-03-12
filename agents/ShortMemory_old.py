""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-01-09
""" 
import os
import json
import random
import sys
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from openai import OpenAI

sys.path.append(os.path.abspath('./'))
from config import CONFIG
from logger import logger
       

class ShortMemory:

    def __init__(self, agent_folder, info) -> None:
        self.info = info

        self.agent_act_folder = agent_folder + "/activity_hist"
        self.cache_file = os.path.join(agent_folder, "short_memory_cache.json")
        
        self.memory_tree = {
            "cur_time":"",
            "cur_halfhour":"",
            "cur_schedule":"",
            "cur_halfhour_index":0,
            "cur_activity":"",
            "activities" : {},
            "heartrate" : {},
            "chatbot" : {},
            "location" : {},
            "pred_heartrate" : {},
            "pred_chatbot" : {},
            "pred_location" : {},
        }

    def set_today(self, today):
        self.memory_tree["today"] = today


    def set_purpose(self, purpose):
        self.memory_tree["today_purpose"] = purpose


    def set_current_activity(self, activity):
        self.memory_tree["cur_activity"] = activity
        self.memory_tree["activities"][self.memory_tree["cur_time"]] = activity


    def set_current_location(self, location_dict, minutes):
        for idx, time in enumerate(location_dict.keys()):
            if idx < minutes // 2:
                self.memory_tree["location"][time] = {
                    "location":location_dict[time]["location"],
                    # "latitude":location_dict[time]["latitude"],
                    # "longitude":location_dict[time]["longitude"]
                }
            else:
                self.memory_tree["pred_location"][time] = {
                    "location":location_dict[time]["location"],
                    # "latitude":location_dict[time]["latitude"],
                    # "longitude":location_dict[time]["longitude"]
                }

    def set_current_heartrate(self, heartrate, minutes):
        for idx, time in enumerate(heartrate.keys()):
            hr = str(heartrate[time])
            if idx < minutes // 2:
                self.memory_tree["heartrate"][time] = 0 if hr.startswith("[Fill") else hr
            else:
                self.memory_tree["pred_heartrate"][time] = 0 if hr.startswith("[Fill") else hr

    def set_current_chatbot(self, conv_hist, minutes):
        for idx, time in enumerate(conv_hist.keys()):
            content = conv_hist[time]
            if content["if_chat"]=="True":
                if idx < minutes // 2:
                    self.memory_tree["chatbot"][time] = content["conversation"]
                else:
                    self.memory_tree["pred_chatbot"][time] = content["conversation"]


    def set_schedule(self, schedule):
        self.memory_tree["daily_schedule"] = schedule

    def set_task_decompose(self, decomposed):
        self.memory_tree["cur_decomposed"] = decomposed

    def fetch_task_decompose(self):
        return self.memory_tree["cur_decomposed"]

    def set_current_time(self, cur_time):
        if isinstance(cur_time, datetime):
            self.memory_tree["cur_time"] = datetime.strftime(cur_time, "%H:%M")
        else:
            self.memory_tree["cur_time"] = cur_time

        if self.memory_tree["cur_halfhour"]:
            _index = 0
            for _range in self.memory_tree["daily_schedule"].keys():
                start_time = datetime.strptime(_range.split("-")[0], "%H:%M")
                end_time = datetime.strptime(_range.split("-")[1], "%H:%M")
                if start_time > end_time:
                    end_time = datetime.strptime("23:59", "%H:%M")

                if start_time <= cur_time < end_time:
                    _schedule = self.memory_tree["daily_schedule"][_range]
                    self.memory_tree["cur_halfhour"] = _range
                    self.memory_tree["cur_halfhour_index"] = _index
                else:
                    _index += 1
        else:
            self.memory_tree["cur_halfhour"] = list(self.memory_tree["daily_schedule"].keys())[0]
            _schedule = list(self.memory_tree["daily_schedule"].values())[0]
        
        if not _schedule == self.memory_tree["cur_schedule"]:
            self.memory_tree["cur_schedule"] = _schedule
            return {'slot':self.memory_tree["cur_halfhour"],'event':_schedule}
        else:
            return None


    def get_cur_time(self):
        return self.memory_tree["cur_time"]

    def get_today(self):
        return self.memory_tree["today"]
    
    def get_today_purpose(self):
        return self.memory_tree["today_purpose"]
    
    def get_current_schedule(self):
        return self.memory_tree["cur_schedule"]

    def get_current_activity(self):
        return self.memory_tree["cur_activity"]


    def today_summary(self):
        res = f"Today is {self.memory_tree['today']}, {self.info['name']} plan for today is: {self.memory_tree['today_purpose']}. "
        return res
    

    def cur_time_summary(self):
        res = f"Now, it is {self.memory_tree['cur_time']}. "
        return res

    def cur_schedule_summary(self):
        # past_half = datetime.strptime(self.memory_tree['cur_halfhour'], "%H:%M") - timedelta(minutes=30)
        # past_half = datetime.strftime(past_half, "%H:%M")
        # next_half = datetime.strptime(self.memory_tree['cur_halfhour'], "%H:%M") + timedelta(minutes=30)
        # next_half = datetime.strftime(next_half, "%H:%M")
        # res = f"{self.info['name']} plans to {self.memory_tree['cur_schedule']} between {self.memory_tree['cur_halfhour']} and {next_half}. "
        # res += f"In the past half hour, {self.info['name']} did {self.memory_tree['daily_schedule'][past_half]}, "
        # res += f"and, in the future half hour (after {next_half}), {self.info['name']} plans to {self.memory_tree['daily_schedule'][next_half]}. "
        # return res
        past_index = self.memory_tree["cur_halfhour_index"] - 1 if self.memory_tree["cur_halfhour_index"] > 0 else 0
        past_range = list(self.memory_tree["daily_schedule"].keys())[past_index]
        past_schedule = list(self.memory_tree["daily_schedule"].values())[past_index]
        next_index = self.memory_tree["cur_halfhour_index"] + 1 if self.memory_tree["cur_halfhour_index"] < len(self.memory_tree["daily_schedule"].keys()) - 1 else len(self.memory_tree["daily_schedule"].keys()) - 1
        next_range = list(self.memory_tree["daily_schedule"].keys())[next_index]
        next_schedule = list(self.memory_tree["daily_schedule"].values())[next_index]
        res = f"{self.info['name']} plans to {self.memory_tree['cur_schedule']} between {self.memory_tree['cur_halfhour']}. "
        res += f"Before this time slot, {self.info['name']} did {past_schedule} between {past_range}. "
        res += f"And this period, {self.info['name']} plans to {next_schedule} between {next_range}. "
        return res + "\n"
    
    def cur_activity_summary(self):
        res = f"Currently, {self.info['name']} is working on {self.memory_tree['cur_activity']}, within a time slot schedule planing to {self.memory_tree['cur_schedule']} in {self.memory_tree['cur_halfhour']}. "
        return res + "\n"

    def past_activities_summary(self, min=60):
        nums = min // 5
        nums = nums if nums < len(self.memory_tree["activities"].keys()) else len(self.memory_tree["activities"].keys())
        res = f"In the the past {min}, {self.info['name']}'s activity history is:"
        for i in range(1, nums+1):
            time = list(self.memory_tree["activities"].keys())[-nums+i]
            activity = list(self.memory_tree["activities"].values())[-nums+i]
            res += f"{time} : {activity}, "
        return res + "\n"

    def past_heartrate_summary(self, min=60):
        res = f"In the the past {min} minutes, {self.info['name']}'s heart rate record history is:"
        hr_len= len(self.memory_tree["heartrate"])
        if hr_len < min:
            res += self._dumps_heartrate(hr_len)
            return res, min-hr_len
        else:
            res += self._dumps_heartrate(min)
            return res + "\n", 0

    def pred_heartrate_summary(self):
        res = f"In your last prediction, {self.info['name']}'s heart rate in next 5 min after {self.memory_tree['cur_time']}:"
        if self.memory_tree["pred_heartrate"]:
            res += json.dumps(self.memory_tree['pred_heartrate'])
            self.memory_tree['pred_heartrate'] = {}
        else:
            res += "null"
        return res + "\n"


    def past_chatbot_records(self, hour=1):
        res = f"In the the past {hour} hours, {self.info['name']}'s chatbot record is:"
        hist_len= len(self.memory_tree["chatbot"])
        if hist_len == 0:
            res += "null"
        else:
            for time in self.memory_tree["chatbot"].keys():
                time_datetime = datetime.strptime(time, "%H:%M")
                cur_time_datetime = datetime.strptime(self.memory_tree["cur_time"], "%H:%M")
                if time_datetime >= cur_time_datetime-timedelta(hours=hour):
                    res += f"[{time}]:{self.memory_tree['chatbot'][time]}"
        return res + "\n"


    def pred_chatbot_summary(self):
        res = f"In your last prediction, {self.info['name']}'s chatbot usage in next 5 min after {self.memory_tree['cur_time']}:"
        if self.memory_tree["pred_chatbot"]:
            res += json.dumps(self.memory_tree['pred_chatbot'])
            self.memory_tree['pred_chatbot'] = {}
        else:
            res += "null"
        return res + "\n"
    

    def past_location_summary(self, min=60):
        res = f"In the the past {min} miutes, {self.info['name']}'s location record is:"
        hist_len= len(self.memory_tree["location"])
        if hist_len == 0:
            res += "null"
        else:
            _start = -min if min < hist_len else -hist_len
            _activity = ""
            for time in list(self.memory_tree["location"].keys())[_start:]:
                if time in self.memory_tree["activities"].keys():
                    _activity = self.memory_tree["activities"][time]
                _temp = {
                    "activity" : _activity,
                    "location" : self.memory_tree['location'][time]
                }
                res += f"[{time}] " + json.dumps(_temp)
        return res + "\n"
    

    def pred_location_summary(self):
        res = f"In your last prediction, {self.info['name']}'s location records in next 5 min after {self.memory_tree['cur_time']}:"
        if self.memory_tree["pred_location"]:
            res += json.dumps(self.memory_tree['pred_location'])
            self.memory_tree['pred_location'] = {}
        else:
            res += "null"
        return res + "\n"

    def _dumps_heartrate(self, length):
        res = ""
        for i in range(1, length+1):
            time = list(self.memory_tree["heartrate"].keys())[-length+i]
            heartrate = list(self.memory_tree["heartrate"].values())[-length+i]
            res += f"[{time}]:{heartrate};"
        return res


    def save_cache(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.memory_tree, f)

    
    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.memory_tree = json.load(f)

    def clear_cache(self):
        self.memory_tree = {
            "cur_time":"",
            "cur_halfhour":"",
            "cur_schedule":"",
            "cur_halfhour_index":0,
            "cur_activity":"",
            "activities" : {},
            "heartrate" : {},
            "chatbot" : {},
            "location" : {},
            "pred_heartrate" : {},
            "pred_chatbot" : {},
            "pred_location" : {},
        }


    def save_pred_file(self):
        pred_dict = {}
        last_schedule = ""
        last_activity = ""

        cur_sche_index = 0
        sche_start = datetime.strptime(list(self.memory_tree["daily_schedule"].keys())[cur_sche_index].split("-")[0], "%H:%M")
        sche_end = datetime.strptime(list(self.memory_tree["daily_schedule"].keys())[cur_sche_index].split("-")[1], "%H:%M")
        for idx, time in enumerate(self.memory_tree["heartrate"]):
            time_dict = {}
            time_dict['time'] = time
            time_dict['hour'] = time.split(":")[0]
            time_dict['minute'] = time.split(":")[1]
            time_dict['heartrate'] = self.memory_tree["heartrate"][time]

            time_dict['conv_history'] = self.memory_tree["chatbot"][time] if time in self.memory_tree["chatbot"].keys() else ""

            if time in self.memory_tree["location"].keys():
                time_dict["location"] = self.memory_tree["location"][time]["location"]
                # time_dict['longitude'] = self.memory_tree["location"][time]["longitude"]
                # time_dict['latitude'] = self.memory_tree["location"][time]["latitude"]
            
            if sche_start <= datetime.strptime(time, "%H:%M") < sche_end:
                time_dict['schedule'] = list(self.memory_tree["daily_schedule"].values())[cur_sche_index]
            else:
                if cur_sche_index < len(self.memory_tree["daily_schedule"].keys()) - 1:
                    cur_sche_index += 1
                time_dict['schedule'] = list(self.memory_tree["daily_schedule"].values())[cur_sche_index]
                sche_start = datetime.strptime(list(self.memory_tree["daily_schedule"].keys())[cur_sche_index].split("-")[0], "%H:%M")
                sche_end = datetime.strptime(list(self.memory_tree["daily_schedule"].keys())[cur_sche_index].split("-")[1], "%H:%M")
            # if time in self.memory_tree["daily_schedule"].keys():
            #     time_dict['schedule'] = self.memory_tree["daily_schedule"][time]
            #     last_schedule = self.memory_tree["daily_schedule"][time]
            # else:
            #     time_dict['schedule'] = last_schedule

            if time in self.memory_tree["activities"].keys():
                time_dict['activity'] = self.memory_tree["activities"][time]
                last_activity = self.memory_tree["activities"][time]
            else:
                time_dict['activity'] = last_activity
            
            pred_dict[idx] = time_dict
            

        pred_df = pd.DataFrame(pred_dict).T
        pred_df.to_csv(self.agent_act_folder+f"/{self.memory_tree['today']}.csv")


