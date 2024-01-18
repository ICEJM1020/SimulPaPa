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

        ## user realated、
        self._load_info()
        self.user_act_files = {}
        self.user_last_day = self._search_user_last_day()

        ## chatgpt
        self.gpt_client = OpenAI(
            api_key=CONFIG["openai"]["api_key"],
            organization=CONFIG["openai"]["organization"],
        )

        # print(self.user_last_day, self.user_act_files)
        ## preference_tree
        self.cache_file = os.path.join(agent_folder, "long_memory_cache.json")
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.pref_tree = json.load(f)
        else:
            self.pref_tree = {}

            self.pref_tree["user_chatbot_pref"] = self._summary_user_chatbot_preference()

            self.pref_tree["agent_chatbot_pref"] = self._generate_agent_chatbot_preference()


    def _load_info(self):
        with open(self.agent_folder + "/info.json", "r") as f:
            info = json.load(f)
            self.info = info
            self.description = info["description"]
            del(self.info["description"])

        with open(self.user_folder + "/info.json", "r") as f:
            info = json.load(f)
            self.user_info = info
            self.user_description = info["description"]
            del(self.user_info["description"])
        

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
        return json.dumps(res)


    def _summary_daily_purpose(self, activity_file):
        return random.choice(["at-home", "working", "travel", "outdoor"])
    

    def past_daily_schedule(self, cur_date, past_days:int=5):
        pass


    def _summary_user_chatbot_preference(self):
        chat_history = {}
        # for date, file in self.user_act_files.values():
        for date in self.user_act_files.keys():
            _hist = pd.read_csv(self.user_act_files[date])[['conv_history', 'hour', 'minute']]
            _hist = _hist.dropna(axis=0)
            if not _hist.empty:
                for _, value in _hist.iterrows():
                    chat_history[f"{date}-{value['hour']}:{value['minute']}"] = value['conv_history']

        prompt = self.user_description
        prompt += f"In the past several days, {self.user_info['name']} had several interactions with Alexa chatbot. "
        prompt += f"Here is a json format chat history, the key is the chat time(format as MM-DD-YYYY-hh:mm), the value is the content of the conversation. "
        prompt += json.dumps(chat_history)
        prompt += f"Based on personal information and past chat history, can you summarize the chatbot usage preference of {self.user_info['name']}. "
        prompt += "In order to better describe the preferences, here are some example question may describe a user's preference. "
        prompt += "1. How often do users use chatbot(times/week or times/day)? 2. During what period of time do users use chatbot? "
        prompt += "3. What topics do users talk about when using the chatbot (there may be several options)? "
        prompt += "4. What conversation topics will get positive responses from users (there may be several options)? "
        # prompt += "5. If available, you can choose some typical Question-Answer pairs to include in your answer."
        prompt += "Despite these points, there may also be other descriptions that illustrates the user preference. "
        prompt += "You need to figure out more aspects that may help understanding the user's usage prefernce. "
        prompt += "To make the estimation more detailed, you can imagine that you are a product manager who want to build up a user profile for a chatbot. "
        prompt += "Limit your answer in 50 words and format as: 1 : desciprtion, ..., n : description. You could ignore the name in your answer so that you could provide more useful words."

        if CONFIG['debug']:   print(prompt)

        completion = self.gpt_client.chat.completions.create(
            model="gpt-3.5-turbo", 
            # model="gpt-4",
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG['debug']:   print(completion.choices[0].message.content)
        return completion.choices[0].message.content
    

    def _generate_agent_chatbot_preference(self):
        prompt = "---\n"
        prompt += self.user_description
        prompt += "\n"
        prompt += f"Here are some points describing {self.user_info['name']}'s usage preference of using Alexa chatbot: \n"
        prompt += self.pref_tree["user_chatbot_pref"]
        prompt = "\n---\n"
        prompt += "There are some potential connections here between chatbot usage preferences and personal information. "
        prompt += f"Now, Alexa want to depict a new usage prefernce for {self.info['name']}. {self.description} \n"
        prompt += "In order to better describe the preferences, here are some example question may describe a user's preference. "
        prompt += "1. How often do users use chatbot(times/week or times/day)? 2. During what period of time do users use chatbot? "
        prompt += "3. What topics do users talk about when using the chatbot (there may be several options)? "
        prompt += "4. What conversation topics will get positive responses from users (there may be several options)? "
        # prompt += "5. If available, you can choose some typical Question-Answer pairs to include in your answer."
        prompt += "Despite these points, there may also be other descriptions that illustrates the user preference. "
        prompt += "You need to figure out more aspects that may help understanding the user's usage prefernce. "
        prompt += "To make the estimation more detailed, you can imagine that you are a product manager who want to build up a user profile for a chatbot. "
        prompt += "Limit your answer in 50 words and format as: 1 : desciprtion, ..., n : description. You could ignore the name in your answer so that you could provide more useful words."

        if CONFIG['debug']:   print(prompt)

        completion = self.gpt_client.chat.completions.create(
            model="gpt-3.5-turbo", 
            # model="gpt-4",
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG['debug']:  print(completion.choices[0].message.content)
        return completion.choices[0].message.content
    

    def _fetch_heart_rate(self, activity_df:pd.DataFrame, hour:int=None, minute:int or list=None):
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
                res += f"[{datetime.strftime(_time, '%H:%M')}]:{value['garmin_hr']};"
        return res


    def past_heartrate_summary(self, date, time_start, min=60):
        time_end = datetime.strptime(time_start, "%H:%M") + timedelta(minutes=min)
        if not time_end.day==datetime.strptime(time_start, "%H:%M").day:
            time_end = datetime.strptime("23:59", "%H:%M")
        time_end = datetime.strftime(time_end, "%H:%M")
        res = f"In {date}, from {time_start} to {time_end}, {self.info['name']}'s heart rate record history is:"
        
        activity_df = pd.read_csv(self.user_act_files[date])[['garmin_hr', 'hour', 'minute']]
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
            res += f"{datetime.strftime(fetch_date, '%m-%d-%Y')}:\n"
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
            res += f"{datetime.strftime(fetch_date, '%m-%d-%Y')}:\n"
            if fetch_date <= user_last_day_datetime:
                activity_df = pd.read_csv(self.user_act_files[datetime.strftime(fetch_date, '%m-%d-%Y')])[['conv_history', 'hour', 'minute']]
            else:
                activity_df = pd.read_csv(self.agent_act_files[datetime.strftime(fetch_date, '%m-%d-%Y')])[['conv_history', 'hour', 'minute']]
            
            res += self._fetch_chatbot(activity_df=activity_df, hour=time_start_datetime.hour, hours=hours)
            res += "\n"

        return res
            
    

    def save_cache(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.pref_tree, f)
