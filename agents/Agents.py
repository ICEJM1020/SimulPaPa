""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

import os
from shutil import rmtree
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI
import pandas as pd

from logger import logger
from agents.Info import *
from agents.Brain import *


class AgentsPool:


    def __init__(self, 
                    info: dict, 
                    user_folder: str, 
                    size:int=10,
                    start_date="03-01-2024",
                    simul_days:int=1
                 ) -> None:
        self._uuid = user_folder.split('/')[-1]
        self.info = info
        self.size = size
        self.start_date = start_date
        self.simul_days = simul_days
        self.healthy_rate = 0.5
        self.pool = {}

        self.user_folder = user_folder
        self.folder = user_folder + "/agents"
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

        # self.info_tree = InfoTree(info, folder=self.folder)
        ## For evidence-based 
        self.info_tree = InfoTreeEB(info, folder=self.folder)
        #####################

        ######################
        # ready :  finish creating and ready to simulate
        # working : working on
        # failed : all agents are error
        # error {id}:  error in create {id} agent
        self._status = "init"
        self.simul_status = "init"


    def generate_info_tree(self):
        if self.info_tree.status == "building":
            return False
        else:
            self.info_tree.start_building()
            return True

    def create_pool(self, ):
        logger.info(f"start create agents pool for {self.info['name']}({self._uuid})")
        if self.info_tree.get_status() == "ready":
            thread = threading.Thread(target=self._create_pool)
            self._status = "working"
            thread.start()
        else:
            logger.info(f"info tree for agents pool of {self.info['name']}({self._uuid}) has not finished")
        return self._status
    

    def _create_pool(self, ):
        error = ""
        if_err = False
        for i in range(1, self.size+1):
            agent_folder = self.folder + "/" + str(i)
            if os.path.exists(agent_folder):
                rmtree(agent_folder)
                os.mkdir(agent_folder)
            else:
                os.mkdir(agent_folder)
            
            if CONFIG["debug"]:
                agent_info = self.info_tree.generate_info_dict(healthy_rate=self.healthy_rate)
                self.pool[i] = Agent(index=i, user_folder=self.user_folder, info=agent_info, start_date=self.start_date)
                self.pool[i].save()
            else:
                try:
                    agent_info = self.info_tree.generate_info_dict(healthy_rate=self.healthy_rate)
                except:
                    if_err = True
                    rmtree(agent_folder)
                    logger.error(f"try to create agent {i} for {self.info['name']}({self._uuid}) failed")
                    error += f"{i}, "
                else:
                    self.pool[i] = Agent(index=i, user_folder=self.user_folder, info=agent_info, start_date=self.start_date)
                    self.pool[i].save()
        
        if if_err:
            self._status = "error create" + error
        else:
            self._status = "ready"


    def load_pool(self, ):
        logger.info(f"start load agents pool for {self.info['name']}({self._uuid})")
        thread = threading.Thread(target=self._load_pool)
        self._status = "working"
        thread.start()
        return self._status


    def _load_pool(self):
        error = ""
        if_err = 0
        exists = 0
        for i in os.listdir(self.folder):
            if "." in i : continue
            # self.pool[i] = Agent(index=i, user_folder=self.user_folder)
            try:
                self.pool[int(i)] = Agent(index=int(i), user_folder=self.user_folder)
            except:
                if_err += 1
                error += f"Agent {i}, "
                logger.error(f"try to load agent {i} pool for {self.info['name']}({self._uuid}) failed")
            else:
                exists += 1

        if if_err==self.size:
            self._status = "error load all agents"
        elif if_err==0:
            self._status = "ready"
        else:
            self.size = exists
            self._status = "ready but miss " + error


    def save_pool(self, ):
        if self._status.startswith("ready"):
            for idx in self.pool:
                self.pool[idx].save()
        elif self._status=="working":
            raise Exception("Agents pool is under creation")
        else:
            pass

    def fetch_all_agents(self, ):
        dir_list = os.listdir(self.folder)
        res = []
        for dir in dir_list:
            if not "." in dir:
                if os.path.exists(os.path.join(self.folder, dir+"/info.json")):
                    res.append(f"Agent-{dir}")
        return res, len(res)==self.size


    def start_simulation(self):
        self._monitor_agent_status()
        if self.simul_status == "working":
            return 0
        else:
            logger.info(f"start simulation for {self.info['name']}({self._uuid})")
            self.simul_status = "working"
            for agent in self.pool.values():
                agent.start_planing(self.simul_days)

    def regenerate_simulation(self, agent_list=[]):
        self._monitor_agent_status()
        if self.simul_status == "working":
            return 0
        else:
            self.simul_status = "working"

            if len(agent_list)==0:
                logger.info(f"regenerate simulation for {self.info['name']}({self._uuid})")
                for agent in self.pool.values():
                    agent.start_planing(self.simul_days)
            else:
                for _id, agent in self.pool.items():
                    if (f"Agent-{str(_id)}" in agent_list):
                        logger.info(f"regenerate simulation for {self.info['name']}({self._uuid}) Agent-{str(_id)}")
                        agent.start_planing(self.simul_days)

    
    def continue_simulation(self, days=1, agent_list=[]):
        self._monitor_agent_status()
        if self.simul_status == "working":
            return 0
        else:
            self.simul_status = "working"

            if len(agent_list)==0:
                logger.info(f"continue simulation for {self.info['name']}({self._uuid})")
                for agent in self.pool.values():
                    agent.continue_planing(days)
            else:
                for _id, agent in self.pool.items():
                    if (f"Agent-{str(_id)}" in agent_list):
                        logger.info(f"continue simulation for {self.info['name']}({self._uuid}) Agent-{str(_id)}")
                        agent.continue_planing(days)


    def set_intervention(self, plan, agent_list):
        logger.info(f"Set intervention plan for {self.info['name']}({self._uuid}): {plan}")
        for idx, agent in self.pool.items():
            if (f"Agent-{str(idx)}" in agent_list):
                logger.info(f"Set intervention for agent {idx}")
                agent.set_intervention(plan)


    def _monitor_agent_status(self):
        _status = ""
        _ready = 0
        _error = 0
        for key, agent in self.pool.items():
            if agent.status.startswith("error"):
                _status += f"Error-Agent-{key}:{agent.status}; "
                _error += 1
            if agent.status == "ready":
                _ready += 1
        if _status:
            self.simul_status = _status
        if _ready == self.size:
            self.simul_status = "ready"
        if _error == self.size:
            self.simul_status = "failed-" + _status

    def statistical_activity(self, date):

        activity_stat = {}
        heartrate_stat = {}
        for _, id in enumerate(self.pool):
            try:
                _temp_records = self.pool[id].fetch_records(date=date, col=["time", "catalogue", "heartrate"])
            except:
                logger.error(f"{self._uuid} agent({id}) fetch {date} activity data failed.")
            else:
                for time in _temp_records.keys():
                    # or (time.endswith("20")) or (time.endswith("40"))
                    if (time.endswith("0")) :
                        _time = time.split(" ")[1]

                        if _time in activity_stat.keys() or _time in heartrate_stat.keys():
                            activity_stat[_time][f"Agent {id}"] = _temp_records[time]["catalogue"]
                            heartrate_stat[_time][f"Agent {id}"] = _temp_records[time]["heartrate"]
                        else:
                            activity_stat[_time] = {f"Agent {id}" : _temp_records[time]["catalogue"]}
                            heartrate_stat[_time] = {f"Agent {id}" : _temp_records[time]["heartrate"]}
                    else:
                        continue
        return {"activity":activity_stat, "heartrate":heartrate_stat}

    def fetch_all_donedates(self):
        donedates = []

        for id in self.pool:
            _donedates = self.pool[id].fetch_done_dates()
            if donedates:
                donedates = list(set(donedates).union(_donedates))
                # donedates = list(set(donedates).intersection(_donedates))
            else:
                donedates = _donedates

        dates = [datetime.strptime(date_str, '%m-%d-%Y') for date_str in donedates]
        sorted_dates = sorted(dates)
        sorted_date_strings = [datetime.strftime(date_obj, '%m-%d-%Y') for date_obj in sorted_dates]

        return sorted_date_strings
        

    def update_agents_catalogue(self):
        for id in self.pool:
            self.pool[id].update_catalogue()

    def fetch_agent_info(self, id):
        return self.pool[id].fetch_info()
    
    def fetch_agent_portrait(self, id):
        pic_path = os.path.join(self.pool[id].folder, "portrait.png")
        if os.path.exists(pic_path):
            return os.path.join(self.pool[id].folder, "portrait.png")
        else:
            return os.path.join(CONFIG["base_dir"], "api_server/static/elderly.png")

    def fetch_agent_done_dates(self, id):
        return self.pool[id].fetch_done_dates()
    
    def fetch_agent_chatbot(self, id, date):
        return self.pool[id].fetch_chatbot(date)
    
    def fetch_agent_heartrate(self, id, date):
        return self.pool[id].fetch_heartrate(date)
    
    def fetch_agent_location_hist(self, id, date):
        return self.pool[id].fetch_location_hist(date)
    
    def fetch_agent_schedule(self, id, date):
        return self.pool[id].fetch_schedule(date)
    
    def fetch_agent_steps(self, id, date):
        return self.pool[id].fetch_steps(date)

    def fetch_tree_status(self):
        return self.info_tree.get_status()

    def fetch_status(self):
        return self._status
    
    def fetch_simul_status(self):
        self._monitor_agent_status()
        return self.simul_status


class Agent:

    def __init__(self,
                    index, 
                    user_folder,
                    info:dict=None,
                    start_date="03-01-2024",
                ) -> None:
        self._uuid = user_folder.split('/')[-1]
        self.index = index
        self.user_folder = user_folder
        self.folder = user_folder + f"/agents/{index}"
        self.activity_folder = self.folder + "/activity_hist"
        self.thoughts_folder = self.folder + "/thoughts_log"
        self.start_date = start_date
        if not os.path.exists(self.activity_folder):
            os.mkdir(self.activity_folder)
        if not os.path.exists(self.thoughts_folder):
            os.mkdir(self.thoughts_folder)

        # Agent status
        ######################
        # ready : ready to start simulation
        # working: working on simulation
        # error:  error
        self._status = "init"

        # infomation
        self.info = {key:None for key in CONFIG["info"]}
        self.description = ""
        if info==None:
            self._load_info()
        else:
            self._fill_info(info=info, start_date=self.start_date)

        if self.description=="":
            self.generate_description()
        if not os.path.exists(os.path.join(self.folder, "portrait.png")):
            self.draw_portrait()

        self.save()

        # brain
        self.brain = Brain(
                user_folder=user_folder,
                agent_folder=self.folder,
                base_date=self.start_date
            )


    def _load_info(self):
        try:
            with open(self.folder + "/info.json", "r") as f:
                info = json.load(f)
        except:
            logger.error(f"{self._uuid} agent({self.index}) load information file unsuccessfully")
            self._status = "error"
        else:
            missing = self._fill_info(info=info)
            logger.info(f"{self._uuid} agent({self.index}) load information file successfully, missing: {missing}")
            self._status = "ready"


    def _fill_info(self, info, start_date=None):
        missing = ""
        for key in self.info.keys():
            if key in info.keys():
                self.info[key] = info[key]
            else:
                missing += key + "/"
        try:
            self.description = info["description"]
        except:
            self.description = ""
        if start_date:
            self.start_date = start_date
        else:
            try:
                self.start_date = info["start_date"]
            except:
                self.start_date = "03-01-2024"

        return missing


    def generate_description(self):
        try:
            self.description = gpt_description(**self.info)
        except:
            self._status = "error"            
            logger.info(f"{self._uuid} agent({self.index}) generate description unsuccessfully")
        else:
            self._status = "ready"
            logger.info(f"{self._uuid} agent({self.index}) generate description successfully")


    def draw_portrait(self):
        # self._draw_portrait()
        thread = threading.Thread(target=self._draw_portrait)
        thread.start()
    
    def _draw_portrait(self):
        # content = dalle_portrait(self.description)   
        # with open(os.path.join(self.folder, "portrait.png"), mode="wb") as file:
        #     file.write(content)
        try:
            content = dalle_portrait(self.description)   
            with open(os.path.join(self.folder, "portrait.png"), mode="wb") as file:
                file.write(content)
        except:
            self._status = "warning-load portrait"

    def start_planing(self, days=1):
        if os.path.exists(self.activity_folder):
            rmtree(self.activity_folder)
            os.mkdir(self.activity_folder)

        if os.path.exists(self.thoughts_folder):
            rmtree(self.thoughts_folder)
            os.mkdir(self.thoughts_folder)

        ## For Ev-Base
        self.brain.long_memory.load_cache()
        ##############
        self._status = "working"
        self.brain.plan(days=days, simul_type="new")

    def continue_planing(self, days=1):
        self._status = "working"
        self.brain.load_cache()
        self.brain.plan(days=days, simul_type="continue")   

    def set_intervention(self, plan):
        self.brain.load_cache()
        self.brain.set_intervention(plan)
        self.save()

    def save(self):
        with open(self.folder + "/info.json", "w") as f:
            dumps = {
                "description":self.description,
                "start_date":self.start_date
            }
            for key in self.info.keys():
                dumps[key] = self.info[key]
            json.dump(dumps, fp=f)

        try:
            self.brain.save_cache()
        except:
            logger.info(f"{self._uuid}-{self.index}: No init brain")

    def _monitor_brain_status(self):
        self._status = self.brain.status

    @property
    def status(self):
        if self._status=="working": self._monitor_brain_status()
        return self._status
    
    @status.setter
    def status(self, status):
        self._status = status

    def check_ready(self):
        return self._status=="ready"
    
    def fetch_info(self):
        with open(self.folder + "/info.json", "r") as f:
            info = json.load(f)
            return info


    def fetch_chatbot(self, date):
        try:
            _hist = pd.read_csv(self.activity_folder + f"/{date}.csv")
        except:
            return {}
        else:
            _hist = _hist[_hist["chatbot"].notna()].loc[:, ['time', 'chatbot']]
            return _hist.T.to_dict()

    def fetch_heartrate(self, date):
        try:
            _hist = pd.read_csv(self.activity_folder + f"/{date}.csv")
        except:
            return {}
        else:
            _hist = _hist[_hist["heartrate"].notna()].loc[:, ['time', 'heartrate']]
            return _hist.T.to_dict()
        
    def fetch_steps(self, date):
        try:
            _hist = pd.read_csv(self.activity_folder + f"/{date}.csv")
        except:
            return {}
        else:
            _hist = _hist[_hist["steps"].notna()].loc[:, ['time', 'steps']]
            return _hist.T.to_dict()
    
    def fetch_location_hist(self, date):
        try:
            _hist = pd.read_csv(self.activity_folder + f"/{date}.csv")
        except:
            return {}
        else:
            _hist = _hist[_hist["location"].notna()]

            cur_loc = _hist["location"][0]
            cur_longi = _hist["longitude"][0]
            cur_lati = _hist["latitude"][0]
            loc_start_time = _hist["time"][0]
            last_time = ""
            loc_hist = []
            for idx, row in _hist.iterrows():

                if not cur_loc==row["location"]:
                    loc_hist.append({
                        "location" : cur_loc,
                        "longitude" : cur_longi,
                        "latitude" : cur_lati,
                        "start_time" : loc_start_time,
                        "end_time" : last_time,
                    })
                    cur_loc = row["location"]
                    cur_longi = row["longitude"]
                    cur_lati = row["latitude"]
                    loc_start_time = row["time"]
                last_time = row["time"]

            return loc_hist
    
    def fetch_schedule(self, date):
        try:
            data = pd.read_csv(self.activity_folder + f"/{date}.csv")
        except:
            return {}
        else:
            schedule = []
            cur_event = data["event"][0]
            event_start_time = data["time"][0]
            cur_activity = data["activity"][0]
            activity_start_time = data["time"][0]
            last_time = ""
            activities = []
            cur_location = data["location"][0]
            location_list = []
            for idx, row in data.iterrows():
                if not cur_activity==row["activity"]:
                    activities.append({
                        "activity": cur_activity,
                        "start_time" : activity_start_time,
                        "end_time" : last_time
                    })
                    cur_activity = row["activity"]
                    activity_start_time = row["time"]

                if not cur_location==row["location"]:
                    location_list.append(cur_location)
                    cur_location = row["location"]

                if not cur_event==row["event"]:
                    schedule.append({
                        "event": cur_event,
                        "start_time" : event_start_time,
                        "end_time" : last_time,
                        "activities" : activities,
                        "location_list" : location_list
                    })
                    cur_event = row["event"]
                    event_start_time = row["time"]
                    activities = []
                    location_list = []

                last_time = row["time"]

            activities.append({
                "activity": cur_activity,
                "start_time" : activity_start_time,
                "end_time" : last_time
            })
            schedule.append({
                "event": cur_event,
                "start_time" : event_start_time,
                "end_time" : last_time,
                "activities" : activities,
                "location_list" : location_list
            })
            return schedule
    
    def fetch_records(self, date, col:list=["time", "activity"]):
        if not "time" in col:
            col.append("time")
        data = pd.read_csv(self.activity_folder + f"/{date}.csv")[col]
        data.index = data["time"]
        return data.T.to_dict()


    def fetch_done_dates(self):
        date_strings = [file.split(".")[0] for file in os.listdir(self.activity_folder)]
        dates = [datetime.strptime(date_str, '%m-%d-%Y') for date_str in date_strings]
        sorted_dates = sorted(dates)
        sorted_date_strings = [datetime.strftime(date_obj, '%m-%d-%Y') for date_obj in sorted_dates]
        return sorted_date_strings
    
    def update_catalogue(self):
        done_files = [os.path.join(self.activity_folder, file) for file in os.listdir(self.activity_folder)]
        self.brain.update_catalogue(done_files)