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


class LongMemory:

    def __init__(self, user_folder, agent_folder) -> None:
        ## folder 
        self.user_folder = user_folder
        self.agent_folder = agent_folder
        self.user_act_folder = user_folder + "/activity_hist"
        self.agent_act_folder = agent_folder + "/activity_hist"

        self.loaded = False

        ## files realated、
        self._load_info()
        # self.user_act_files = {}
        # self.user_last_day = self._search_user_last_day()
        self.agent_act_files = {}
        self._search_generated_activity()

        # print(self.user_last_day, self.user_act_files)
        ## preference_tree
        self.cache_file = os.path.join(agent_folder, "long_memory_cache.json")
        
        self.memory_tree = {}
        # self.memory_tree["user_chatbot_pref"] = ""
        self.memory_tree["agent_chatbot_pref"] = ""
        self.memory_tree["intervention"] = "No intervention plan."
        self.memory_tree["daily_purpose"] = ""
        self.memory_tree["past_daily_purpose"] = []

    @property
    def intervention(self):
        return self.memory_tree["intervention"]
    
    @intervention.setter
    def intervention(self, plan):
        self.memory_tree["intervention"] = plan

    @property
    def name(self):
        return self.info["name"]

    @property
    def description(self):
        return self.info["description"]
    
    @property
    def home_addr(self):
        return f"{self.info['building']}, {self.info['street']}, {self.info['district']}, {self.info['city']}, {self.info['state']}, {self.info['zipcode']}"

    @property
    def work_addr(self):
        return self.info["work_addr"]
    
    @property
    def disease(self):
        return self.info["disease"]
    
    @property
    def age(self):
        return self.info["age"]
    
    @property
    def name(self):
        return self.info["name"]
    
    @property
    def daily_purpose(self):
        return self.memory_tree["daily_purpose"]
    
    @daily_purpose.setter
    def daily_purpose(self, purpose):
        self.memory_tree["daily_purpose"] = purpose
        if len(self.memory_tree["past_daily_purpose"]) == 10:
            self.memory_tree["past_daily_purpose"].pop(0)
        self.memory_tree["past_daily_purpose"].append(purpose)

    @property
    def chatbot_preference(self):
        return self.memory_tree["agent_chatbot_pref"]
    
    @chatbot_preference.setter
    def chatbot_preference(self, pref):
        self.memory_tree["agent_chatbot_pref"] = pref


    def _load_info(self):
        with open(self.agent_folder + "/info.json", "r") as f:
            info = json.load(f)
            self.info = info

        with open(self.user_folder + "/info.json", "r") as f:
            info = json.load(f)
            self.user_info = info
        

    # def _search_user_last_day(self, ):
    #     newest_date = None

    #     for filename in os.listdir(self.user_act_folder):
    #         if filename.endswith('.csv'):
    #             # Extract date from filename
    #             date_str = filename.split('.')[0]  # Remove the '.csv' part
    #             self.user_act_files[date_str] = os.path.join(self.user_act_folder, filename)
    #             try:
    #                 file_date = datetime.strptime(date_str, "%m-%d-%Y").date()
    #                 if newest_date is None or file_date > newest_date:
    #                     newest_date = file_date
    #             except ValueError:
    #                 continue

    #     return newest_date.strftime('%m-%d-%Y')
    

    def update_memory(self):
        # self.record_daily_purpose()
        self._search_generated_activity()
        self.save_cache()
        
    def _search_generated_activity(self, ):
        if os.path.exists(self.agent_act_folder):
            for filename in os.listdir(self.agent_act_folder):
                if filename.endswith('.csv'):
                    # Extract date from filename
                    date_str = filename.split('.')[0]  # Remove the '.csv' part
                    self.agent_act_files[date_str] = os.path.join(self.agent_act_folder, filename)
    

    # def fetch_user_lastday(self):
    #     return self.user_last_day
    

    def past_daily_purpose(self, past_days:int=5):

        return self.memory_tree["past_daily_purpose"][-past_days:]


    # def _summary_daily_purpose(self, activity_file):
    #     date = os.path.basename(activity_file).split(".")[0]
    #     examples = {
    #         "12-05-2023":f"Today is Tuesday, {self.info['name']}'s plan of today is to work on the current project, including several meetings and chat with company CEO. ",
    #         "12-04-2023":f"Today is Monday, {self.info['name']}'s plan of today is to work on the currentproject, including talking to product manager about the detail of the product and schedule a meeting with client. ",
    #         "12-03-2023":f"Today is Sunday, {self.info['name']}'s plan of today is to travel to National park. ",
    #         "12-02-2023":f"Today is Saturday, {self.info['name']}'s plan of today is to stay at home for relex, including clean the room, watch a movie, do some cleaning, etc. ",
    #         "12-01-2023":f"Today is Friday, {self.info['name']}'s plan of today is start a new project that will create a new product, including several meetings and talk to team members. ",
    #         "11-30-2023":f"Today is Thursday, {self.info['name']}'s plan of today is to finish last project, including prepare a presentation script, go to company auditorium, and hold product launching ceremony. ",
    #         "11-29-2023":f"Today is Wednesday, {self.info['name']}'s plan of today is to work on the current project, the product need to be launched tomorrow. {self.info['name']} needs to final check the product, meet with team members. ",
    #         "11-28-2023":f"Today is Tuesday, {self.info['name']}'s plan of today is to work on the current project, including meet several clients and talk to team members. ",
    #         "11-27-2023":f"Today is Monday, {self.info['name']}'s plan of today is to go to hospital since neck sick. After that, {self.info['name']} wants to work at home. ",
    #         "11-26-2023":f"Today is Sunday, {self.info['name']}'s plan of today is to work on a recent project at home, including check the quality of the product, hold meeting with manufacture company, and hold meeting with CEO talked about product progress. ",
    #         "11-25-2023":f"Today is Saturday, {self.info['name']}'s plan of today is to stay at home for relex. In the afternoon, {self.info['name']} needs to have dinner with clients at InterContinental Boston. ",
    #         "11-24-2023":f"Today is Friday, {self.info['name']}'s plan of today is to work on a recent project, including several meetings and talk to team members. ",
    #     }

    #     return examples[date]
    

    def past_daily_schedule(self, cur_date, past_days:int=5):
        pass


    # def fetch_user_chat_hist(self, limit=10):
    #     chat_history = {}
    #     # for date, file in self.user_act_files.values():
    #     _sum = 0
    #     for date in self.user_act_files.keys():
    #         _hist = pd.read_csv(self.user_act_files[date])[['conv_history', 'hour', 'minute']]
    #         _hist = _hist.dropna(axis=0)
    #         if not _hist.empty:
    #             for _, value in _hist.iterrows():
    #                 chat_history[f"{date}-{value['hour']}:{value['minute']}"] = value['conv_history']
    #                 _sum += 1
    #                 if _sum > limit:
    #                     return chat_history
    #     return chat_history
    

    def _fetch_heart_rate(self, activity_df:pd.DataFrame, hour:int=None, minute:int | list=None):
        hr = "heartrate" if "heartrate" in activity_df.columns else "garmin_hr"

        activity_df = activity_df.dropna(axis=0)
        activity_df = activity_df[activity_df['hour']==hour]
        if (not minute==None) and (not hour==None):
            if isinstance(minute, list):
                activity_df = activity_df[activity_df['minute'].isin(minute)]
            else:
                activity_df = activity_df[activity_df['minute']==minute]

        res = ""
        if not activity_df.empty:
            for _, value in activity_df.iterrows():
                _time = datetime.strptime(f"{int(value['hour'])}:{int(value['minute'])}", "%H:%M")
                res += f"[{datetime.strftime(_time, '%H:%M')}]:{value[hr]};"
        return res


    def past_heartrate_summary(self, date, time_start, min=60):
        time_end = datetime.strptime(time_start, "%H:%M") + timedelta(minutes=min)
        if not time_end.day==datetime.strptime(time_start, "%H:%M").day:
            time_end = datetime.strptime("23:59", "%H:%M")
        time_end = datetime.strftime(time_end, "%H:%M")
        res = f"In {date}, from {time_start} to {time_end}, {self.info['name']}'s heart rate record history is:"
        
        if date in self.user_act_files:
            activity_df = pd.read_csv(self.user_act_files[date])[['garmin_hr', 'hour', 'minute']]
        else:
            activity_df = pd.read_csv(self.agent_act_files[date])[['heartrate', 'hour', 'minute']]

        for i in range(min):
            _time = datetime.strptime(time_start, "%H:%M") + timedelta(minutes=i)
            res += self._fetch_heart_rate(activity_df, _time.hour, _time.minute)
        return res
    

    def past_period_heartrate_summary(self, cur_date, time_start, days=5, mins=5):
        user_last_day_datetime = datetime.strptime(self.user_last_day, '%m-%d-%Y')
        cur_date_datetime = datetime.strptime(cur_date, '%m-%d-%Y')
        time_start_datetime = datetime.strptime(time_start, "%H:%M")
        time_end_datetime = datetime.strptime(time_start, "%H:%M") + timedelta(minutes=mins)
        time_end = datetime.strftime(time_end_datetime, "%H:%M")


        res = f"The heart rate records in {time_start}-{time_end} of past {days} day(s) before {cur_date} are:\n"

        for i in range(1, days+1):
            fetch_date = cur_date_datetime - timedelta(days=i)
            res += f"{datetime.strftime(fetch_date, '%m-%d-%Y')}: "
            if fetch_date <= user_last_day_datetime:
                activity_df = pd.read_csv(self.user_act_files[datetime.strftime(fetch_date, '%m-%d-%Y')])[['garmin_hr', 'hour', 'minute']]
            else:
                activity_df = pd.read_csv(self.agent_act_files[datetime.strftime(fetch_date, '%m-%d-%Y')])[['heartrate', 'hour', 'minute']]
            

            _mins = [time_start_datetime.minute + i for i in range(mins)]
            res += self._fetch_heart_rate(activity_df, hour=time_start_datetime.hour, minute=_mins)
            res += "\n"

        return res
    

    def _fetch_chatbot(self, activity_df:pd.DataFrame, hour:int=None, hours:int=1):
        activity_df = activity_df.dropna(axis=0)
        if hours>1:
            hours = max(hours, 3)
            activity_df = activity_df[activity_df['hour'].isin([hour+i for i in range(hours)])]
        else:
            activity_df = activity_df[activity_df['hour']==hour]
        res = ""
        if not activity_df.empty:
            for _, value in activity_df.iterrows():
                _time = datetime.strptime(f"{int(value['hour'])}:{int(value['minute'])}", "%H:%M")
                res += f"[{datetime.strftime(_time, '%H:%M')}]:{value['conv_history']};"
        return res

    def past_period_chatbot_summary(self, cur_date, time_start, days=5, hours=1):
        user_last_day_datetime = datetime.strptime(self.user_last_day, '%m-%d-%Y')
        cur_date_datetime = datetime.strptime(cur_date, '%m-%d-%Y')
        time_start_datetime = datetime.strptime(time_start, "%H:%M")
        time_end_datetime = datetime.strptime(time_start, "%H:%M") + timedelta(hours=hours)
        time_end = datetime.strftime(time_end_datetime, "%H:%M")

        res = f"The chatbot records in {time_start}-{time_end} of past {days} day(s) before {cur_date} are:\n"

        for i in range(1, days+1):
            fetch_date = cur_date_datetime - timedelta(days=i)
            res += f"{datetime.strftime(fetch_date, '%m-%d-%Y')}: "
            if fetch_date <= user_last_day_datetime:
                activity_df = pd.read_csv(self.user_act_files[datetime.strftime(fetch_date, '%m-%d-%Y')])[['conv_history', 'hour', 'minute']]
            else:
                activity_df = pd.read_csv(self.agent_act_files[datetime.strftime(fetch_date, '%m-%d-%Y')])[['conv_history', 'hour', 'minute']]
            
            res += self._fetch_chatbot(activity_df=activity_df, hour=time_start_datetime.hour, hours=hours)
            res += "\n"

        return res
            
    
    def record_daily_purpose(self):
        self.memory_tree["past_daily_purpose"] = self.daily_purpose


    def save_cache(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.memory_tree, f)


    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.memory_tree = json.load(f)