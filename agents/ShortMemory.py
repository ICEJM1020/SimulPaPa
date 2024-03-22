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
from agents.dantic import Schedule
from config import CONFIG
from logger import logger




class RecordsQueue:
    def __init__(self, max_size):
        self.max_size = max_size
        self.queue = []

    def push(self, item):
        if len(self.queue) == self.max_size:
            self.queue.pop(0)
        self.queue.append(item)

    def pop(self):
        if self.queue:
            return self.queue.pop(0)
        else:
            return None
    
    def get_current(self):
        return self.queue[-1]
        
    def length(self):
        return len(self.queue)
        
    def fetch(self, size):
        return self.queue[-size:]

    def fetch_all(self):
        return self.queue


class ShortMemory:

    def __init__(self, agent_folder, cache_length:int=60) -> None:

        self.agent_act_folder = agent_folder + "/activity_hist"
        self.cache_file = os.path.join(agent_folder, "short_memory_cache.json")

        self._cur_date = ""
        self._cur_time = ""
        self._schedule = {}

        self._cur_event = {}
        self._cur_event_index = 0
        self._max_event = 25

        self._cur_decompose = []
        self._cur_decompose_index = 0
        self._cur_location_list = []
        self._cur_location_list_index = 0
        self._cur_chatbot_dict = {}

        self._cur_activity = "Sleeping"

        self.memory_cache = RecordsQueue(cache_length)


    @property
    def cur_date(self):
        return self._cur_date
    
    @property
    def cur_date_dt(self):
        return datetime.strptime(self._cur_date, "%m-%d-%Y")
    
    @cur_date.setter
    def cur_date(self, cur_date):
        if isinstance(cur_date, str):
            self._cur_date = cur_date
        elif isinstance(cur_date, datetime):
            self._cur_date = datetime.strftime(cur_date, "%m-%d-%Y")
        else:
            raise Exception("Current date type error, need to be \"str\" or \"datetime\"")
        
    @property
    def cur_time(self):
        return self._cur_time
    
    @property
    def cur_time_dt(self):
        return datetime.strptime(self._cur_time, "%H:%M")
    
    @cur_time.setter
    def cur_time(self, cur_time):
        if isinstance(cur_time, str):
            self._cur_time = cur_time
        elif isinstance(cur_time, datetime):
            self._cur_time = datetime.strftime(cur_time, "%H:%M")
        else:
            raise Exception("Current time type error, need to be \"str\" or \"datetime\"")
        
    @property
    def date_time_dt(self):
        return datetime.strptime(self.date_time, "%m-%d-%Y %H:%M")

    @property
    def date_time(self):
        return f"{self._cur_date} {self._cur_time}"
    
    @property
    def schedule(self):
        return self._schedule

    @schedule.setter
    def schedule(self, schedule:Schedule):
        self._schedule = schedule
        self._cur_event = schedule[0]
        self._cur_event_index = 0
        self._max_event = len(schedule.keys())

    @property
    def cur_event(self):
        return self._cur_event
    
    @property
    def cur_event_str(self):
        try:
            res = f"To do {self._cur_event['event']}, from {self._cur_event['start_time']} to {self._cur_event['end_time']}"
        except:
            res="Null"
        return res

    @property
    def cur_decompose(self):
        return self._cur_decompose
    
    @cur_decompose.setter
    def cur_decompose(self, decompose):
        self._cur_decompose = decompose
        self._cur_decompose_index = 0

    @property
    def cur_location_list(self):
        return self._cur_location_list
    
    @cur_location_list.setter
    def cur_location_list(self, location):
        if location:
            self._cur_location_list = location
        else:
            self._cur_location_list = {
                "start_time" : "01-01-1900 00:00",
                "end_time" : "12-31-2100 23:59",
                "location" : "unknown",
                "longitude" : "unknown",
                "latitude" : "unknown",
            }
        self._cur_location_list_index = 0

    @property
    def cur_chatbot_dict(self):
        return self._cur_chatbot_dict
    
    @cur_chatbot_dict.setter
    def cur_chatbot_dict(self, uasge):
        self._cur_chatbot_dict = uasge

    @property
    def cur_activity(self):
        return self._cur_activity
    
    @cur_activity.setter
    def cur_activity(self, activity):
        self._cur_activity = activity
        self.memory_cache.push({
            "time" : self.date_time,
            "schedule_event" : self._cur_event["event"],
            "activity" : activity,
            "location" : self.cur_location['location'],
            "longitude" : self.cur_location['longitude'],
            "latitude" : self.cur_location['latitude'],
            "chatbot":  self.cur_chatbot,
            "heartrate" : 60,
        })

    @property
    def last_event(self):
        if self._cur_event_index == 0:
            return "sleep until now"
        else:
            return json.dumps(self._schedule[self._cur_event_index - 1])
        
    @property
    def next_event(self):
        if self._cur_event_index == self._max_event - 1:
            return "Undecided"
        else:
            return json.dumps(self._schedule[self._cur_event_index + 1])
        
    @property
    def planning_activity(self):
        try:
            _decompose_entry = self._cur_decompose[self._cur_decompose_index]
            start_time = datetime.strptime(_decompose_entry["start_time"], "%m-%d-%Y %H:%M")
            end_time = datetime.strptime(_decompose_entry["end_time"], "%m-%d-%Y %H:%M")
        except:
            _temp = self.fetch_records(1)[0]
            return _temp['activity']
        else:
            if start_time <= self.date_time_dt < end_time:
                return _decompose_entry['activity']
            else:
                if self._cur_decompose_index < len(self._cur_decompose) - 1:
                    self._cur_decompose_index += 1
                
                return self._cur_decompose[self._cur_decompose_index]['activity']

    @property
    def cur_location(self):
        try:
            _location_entry = self._cur_location_list[self._cur_location_list_index]
            start_time = datetime.strptime(_location_entry["start_time"], "%m-%d-%Y %H:%M")
            end_time = datetime.strptime(_location_entry["end_time"], "%m-%d-%Y %H:%M")
        except:
            _temp = self.fetch_records(1)[0]
            if _temp:
                return {
                            'location' : _temp['location'],
                            'longitude' : _temp['longitude'],
                            'latitude' : _temp['latitude'],
                        }
            else:
                return {'location' : "null",'longitude' : "",'latitude' : "",}
        else:
            if start_time <= self.date_time_dt < end_time:
                return {
                        'location' : _location_entry['location'],
                        'longitude' : _location_entry['longitude'],
                        'latitude' : _location_entry['latitude'],
                    }
            else:
                if self._cur_location_list_index < len(self._cur_location_list) - 1:
                    self._cur_location_list_index += 1
                
                return {
                    'location' : self._cur_location_list[self._cur_location_list_index]['location'],
                    'longitude': self._cur_location_list[self._cur_location_list_index]['longitude'],
                    'latitude' : self._cur_location_list[self._cur_location_list_index]['latitude'],
                }
            
    @property
    def cur_chatbot(self):
        if self.date_time in self._cur_chatbot_dict.keys():
            return self._cur_chatbot_dict[self.date_time].replace("\n", ";")
        else:
            return "null"


    def csv_record(self):
        entry = self.memory_cache.get_current()
        return f"{entry['time']},\"{entry['activity']}\",\"{entry['schedule_event']}\",\"{entry['location']}\",\"{entry['longitude']}\",\"{entry['latitude']}\",\"{entry['heartrate']}\",\"{entry['chatbot']}\"\n"


    def check_new_event(self):
        if self.date_time_dt == datetime.strptime(self._cur_event["end_time"], "%m-%d-%Y %H:%M"):
            self._cur_event_index += 1
            try:
                self._cur_event = self._schedule[self._cur_event_index]
            except:
                return False
            return True
        return False
    

    def check_end_schedule(self):
        return self._cur_event_index == self._max_event
    

    def fetch_records(self, num_items):
        return self.memory_cache.fetch(num_items)
    

    def fetch_location_records(self, num_items):
        records = []
        for entry in self.memory_cache.fetch(num_items):
            records.append({
                "time" : entry["time"],
                "activity" : entry['activity'],
                "location" : entry['location'],
                "longitude" : entry['longitude'],
                "latitude" : entry['latitude']
            })
        return records

    def fetch_chatbot_records(self, num_items):
        records = []
        for entry in self.memory_cache.fetch(num_items):
            records.append({
                "time" : entry["time"],
                "chatbot" : entry['chatbot']
            })
        return records

    def save_cache(self):

        save_dict = {
            "cur_date" : self._cur_date,
            "cur_time" : self._cur_time,
            "schedule" : self._schedule,

            "cur_event" : self._cur_event,
            "cur_event_index" : self._cur_event_index,

            "cur_decompose" : self._cur_decompose,
            "cur_decompose_index" : self._cur_decompose_index,
            "cur_location_list" : self._cur_location_list,
            "cur_location_list_index" : self._cur_location_list_index,

            "cur_activity" : self._cur_activity,

            "cache" : self.memory_cache.fetch_all(),
        }

        with open(self.cache_file, "w") as f:
            json.dump(save_dict, f)

    
    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                local_cache = json.load(f)
            self._cur_date = local_cache["cur_date"]
            self._cur_time = local_cache["cur_time"]
            self._schedule = local_cache["schedule"]

            self._cur_event = local_cache["cur_event"]
            self._cur_event_index = local_cache["cur_event_index"]

            self._cur_decompose = local_cache["cur_decompose"]
            self._cur_decompose_index = local_cache["cur_decompose_index"]
            self._cur_location_list = local_cache["cur_location_list"]
            self._cur_location_list_index = local_cache["cur_location_list_index"]

            self._cur_activity = local_cache["cur_activity"]

            for entry in local_cache["cache"]:
                self.memory_cache.push(entry)


