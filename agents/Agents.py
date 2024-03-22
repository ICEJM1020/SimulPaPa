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
                    start_date=datetime.strptime("02-01-2024", '%m-%d-%Y')
                 ) -> None:
        self._uuid = user_folder.split('/')[-1]
        self.info = info
        self.size = size
        self.start_date = start_date
        self.healthy_rate = 0.5
        self.pool = {}

        self.user_folder = user_folder
        self.folder = user_folder + "/agents"
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

        self.info_tree = InfoTree(info, folder=self.folder)

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
        if_err = False
        for i in range(1, self.size+1):
            if CONFIG["debug"]:
                self.pool[i] = Agent(index=i, user_folder=self.user_folder)
            else:
                try:
                    self.pool[i] = Agent(index=i, user_folder=self.user_folder)
                except:
                    if_err = True
                    error += f"{i}, "
                    logger.error(f"try to load agent {i} pool for {self.info['name']}({self._uuid}) failed")

        if if_err:
            self._status = "error load " + error
        else:
            self._status = "ready"


    def save_pool(self, ):
        if self._status=="ready":
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


    def start_simulation(self, days=1):
        logger.info(f"start simulation for {self.info['name']}({self._uuid})")
        self.simul_status = "working"
        for agent in self.pool.values():
            agent.start_planing(days)

    
    def continue_simulation(self, days=1):
        logger.info(f"continue simulation for {self.info['name']}({self._uuid})")
        self.simul_status = "working"
        for agent in self.pool.values():
            agent.continue_planing(days)


    def _monitor_agent_status(self):
        _status = ""
        _ready = 0
        _error = 0
        for key, agent in self.pool.items():
            if agent.status == "error":
                _status += f"Error-Agent-{key}; "
                _error += 1
            if agent.status == "ready":
                _ready += 1
        if _status:
            self.simul_status = _status
        if _ready == self.size:
            self.simul_status = "ready"
        if _error == self.size:
            self.simul_status = "failed"

    def fetch_agent_info(self, id):
        return self.pool[id].fetch_info()
    
    def fetch_agent_portrait(self, id):
        return os.path.join(self.pool[id].folder, "portrait.png")

    def fetch_agent_done_dates(self, id):
        return self.pool[id].fetch_done_dates()
    
    def fetch_agent_chatbot(self, id, date):
        return self.pool[id].fetch_chatbot(date)
    
    def fetch_agent_heartrate(self, id, date):
        return self.pool[id].fetch_heartrate(date)


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
                    start_date=datetime.strptime("02-01-2024", '%m-%d-%Y'),
                ) -> None:
        self._uuid = user_folder.split('/')[-1]
        self.index = index
        self.user_folder = user_folder
        self.folder = user_folder + f"/agents/{index}"
        self.activity_folder = self.folder + "/activity_hist"
        if not os.path.exists(self.activity_folder):
            os.mkdir(self.activity_folder)

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
            self._fill_info(info=info)
        if self.description=="":
            self.generate_description()
        if not os.path.exists(os.path.join(self.folder, "portrait.png")):
            self.draw_portrait()
        self.save()

        # brain
        self.brain = Brain(
                user_folder=user_folder,
                agent_folder=self.folder,
                base_date=start_date
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


    def _fill_info(self, info):
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
        
        return missing


    def generate_description(self):
        try:
            info = gpt_description(**self.info)
            self._fill_info(info)
        except:
            self._status = "error"            
            logger.info(f"{self._uuid} agent({self.index}) generate description unsuccessfully")
        else:
            self._status = "ready"
            logger.info(f"{self._uuid} agent({self.index}) generate description successfully")


    def draw_portrait(self):
        content = dalle_portrait(self.description)   
        with open(os.path.join(self.folder, "portrait.png"), mode="wb") as file:
            file.write(content)
        # try:
        #     content = dalle_portrait(self.description)   
        #     with open(os.path.join(self.folder, "portrait.png"), mode="wb") as file:
        #         file.write(content)
        # except:
        #     self._status = "error"


    def start_planing(self, days=1):
        # self.brain.init_brain()
        self._status = "working"
        self.brain.plan(days=days, simul_type="new")

    def continue_planing(self, days=1):
        self._status = "working"
        self.brain.load_cache()
        self.brain.plan(days=days, simul_type="continue")   

    def save(self):
        with open(self.folder + "/info.json", "w") as f:
            dumps = {
                "description":self.description
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
        self._monitor_brain_status()
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
        _hist = pd.read_csv(self.activity_folder + f"/{date}.csv")
        _hist = _hist[_hist["chatbot"].notna()].loc[:, ['time', 'chatbot']]
        return _hist.T.to_dict()

    def fetch_heartrate(self, date):
        _hist = pd.read_csv(self.activity_folder + f"/{date}.csv")
        _hist = _hist[_hist["heartrate"].notna()].loc[:, ['time', 'heartrate']]
        return _hist.T.to_dict()

    def fetch_done_dates(self):
        date_strings = [file.split(".")[0] for file in os.listdir(self.activity_folder)]
        dates = [datetime.strptime(date_str, '%m-%d-%Y') for date_str in date_strings]
        sorted_dates = sorted(dates)
        sorted_date_strings = [datetime.strftime(date_obj, '%m-%d-%Y') for date_obj in sorted_dates]
        return sorted_date_strings