""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-29
""" 

import uuid
import os
import json
import threading
from shutil import rmtree
from datetime import datetime, timedelta

from config import CONFIG
from logger import logger
from agents.Info import gpt_description, random_generate, extract_info
from agents.Agents import AgentsPool
from agents.utils import *

def init_pool():
    pool = UserPool()
    return pool


class UserPool:


    def __init__(self) -> None:
        self.pool:dict[User] = {}


    def append(self, _uuid):
        self.pool[_uuid] = User(_uuid)

    
    def pop(self, _uuid):
        self.pool[_uuid].save()
        self.save_agents_pool(_uuid)
        del(self.pool[_uuid])


    def exist(self, _uuid):
        return _uuid in self.pool.keys()
    

    def fetch_user_status(self, _uuid):
        return self.pool[_uuid].get_status()
    

    def modify_user_info(self, _uuid, info):
        self.pool[_uuid].modify_info(info)


    def generate_user_description(self, _uuid):
        return self.pool[_uuid].generate_description()
    

    def fetch_user_description(self, _uuid):
        return self.pool[_uuid].get_description()
    
    def fetch_user_information(self, _uuid):
        return self.pool[_uuid].get_information()
    

    ############
    # simulation
    ############
    def start_simulation(self, _uuid):
        self.pool[_uuid].start_simulation()


    def continue_simulation(self, _uuid, days):
        self.pool[_uuid].continue_simulation(days)
        
    def fetch_simulation_status(self, _uuid):
        return self.pool[_uuid].agents_pool.fetch_simul_status()
    
    def set_intervention(self, _uuid, plan, agent_list):
        self.pool[_uuid].set_intervention(plan, agent_list)


    ############
    # agents
    ############
    def fetch_tree_status(self, _uuid):
        return self.pool[_uuid].agents_pool.fetch_tree_status()
    

    def generate_tree(self, _uuid):
        return self.pool[_uuid].agents_pool.generate_info_tree()
    

    def create_agents_pool(self, _uuid):
        return self.pool[_uuid].agents_pool.create_pool()
    

    def fetch_agents_status(self, _uuid):
        return self.pool[_uuid].agents_pool.fetch_status()
    

    def save_agents_pool(self, _uuid):
        return self.pool[_uuid].agents_pool.save_pool()
    

    def load_agents_pool(self, _uuid):
        return self.pool[_uuid].agents_pool.load_pool()
    
    def fetch_all_agents(self, _uuid):
        return self.pool[_uuid].agents_pool.fetch_all_agents()
    
    def update_agents_catalog(self, _uuid):
        return self.pool[_uuid].agents_pool.update_agents_catalog()
    
    def fetch_statistical_activity(self, _uuid, date):
        return self.pool[_uuid].agents_pool.statistical_activity(date)
    
    def fetch_all_donedates(self, _uuid):
        return self.pool[_uuid].agents_pool.fetch_all_donedates()
    
    ############
    # single agent
    ############
    def load_agent_info(self, _uuid, agent_id):
        return self.pool[_uuid].agents_pool.fetch_agent_info(agent_id)
    
    def load_agent_portrait(self, _uuid, agent_id):
        return self.pool[_uuid].agents_pool.fetch_agent_portrait(agent_id)
    
    def fetch_agent_done_dates(self, _uuid, agent_id):
        return self.pool[_uuid].agents_pool.fetch_agent_done_dates(agent_id)
    
    def fetch_agent_chatbot(self, _uuid, agent_id, date):
        return self.pool[_uuid].agents_pool.fetch_agent_chatbot(agent_id, date)
    
    def fetch_agent_heartrate(self, _uuid, agent_id, date):
        return self.pool[_uuid].agents_pool.fetch_agent_heartrate(agent_id, date)
    
    def fetch_agent_steps(self, _uuid, agent_id, date):
        return self.pool[_uuid].agents_pool.fetch_agent_steps(agent_id, date)
    
    def fetch_agent_location_hist(self, _uuid, agent_id, date):
        return self.pool[_uuid].agents_pool.fetch_agent_location_hist(agent_id, date)

    def fetch_agent_schedule(self, _uuid, agent_id, date):
        return self.pool[_uuid].agents_pool.fetch_agent_schedule(agent_id, date)


class User:

    def __init__(self, _uuid) -> None:
        # machine ID
        self._uuid = _uuid
        self.user_folder = os.path.join(CONFIG["base_dir"], f".Users/{_uuid}")

        ######################
        # user status
        # ready : ready to do something
        # working : working on task
        # error:  error
        self.status = "ready"
        self.agents_size = 5
        self.simul_days = 1
        self.start_date = "03-01-2024"

        # user info
        self.info = {key:None for key in CONFIG["info"]}
        self.description = ""
        self._load_info()
        if self.description=="":
            self.generate_description()
            self.save()

        # agents pool
        self.agents_pool = AgentsPool(
            info=self.info,
            user_folder=self.user_folder,
            size=self.agents_size,
            start_date=self.start_date,
            simul_days=self.simul_days
        )

        # activity file
        # self.generate_activity_file()


    def _load_info(self):
        try:
            with open(self.user_folder + "/info.json", "r") as f:
                info = json.load(f)
        except:
            logger.error(f"UUID {self._uuid} load information file unsuccessfully")
            self.status = "error"
        else:
            missing = self._fill_info(info=info)
            logger.info(f"UUID {self._uuid} missing information: {missing}")
            self.status = "ready"
    

    def _fill_info(self, info:dict):
        missing = ""
        for key in self.info.keys():
            if key in info.keys():
                self.info[key] = info[key]
            else:
                missing += key + "/"

        if "description" in info.keys(): self.description = info["description"]
        if "agents_size" in info.keys(): self.agents_size = int(info["agents_size"])
        if "simul_days" in info.keys(): self.simul_days = int(info["simul_days"])
        if "start_date" in info.keys(): self.start_date = info["start_date"]
        
        return missing


    def generate_description(self):
        self.description = gpt_description(**self.info, _type="user")
        try:
            self.description = gpt_description(**self.info, _type="user")
            self.status = "ready"
            logger.info(f"UUID {self._uuid} generate description successfully")
        except:
            self.status = "error"
            logger.info(f"UUID {self._uuid} generate description unsuccessfully")


    def save(self):
        with open(self.user_folder + "/info.json", "w") as f:
            dumps = {
                "uuid":self._uuid,
                "description" : self.description,
                "agents_size" : self.agents_size,
                "simul_days" : self.simul_days,
                "start_date" : self.start_date,
            }
            for key in self.info.keys():
                dumps[key] = self.info[key]
            json.dump(dumps, fp=f)
        logger.info(f"UUID {self._uuid} save to local")
    

    def modify_info(self, info):
        
        res = self._fill_info(info)

        self.generate_description()
        self.save()
        logger.info(f"UUID {self._uuid} modified the information")
        return res


    def generate_activity_file(self):
        logger.info(f"decompose activity file of {self.info['name']}({self.user_folder.split('/')[-1]})")
        thread = threading.Thread(target=self._generate_activity_file)
        self.status = "working"
        thread.start()
        return self.status
    

    def _generate_activity_file(self):
        csv_files = []
        for file in os.listdir(self.user_folder):
            if file.endswith('.csv') and os.path.isfile(os.path.join(self.user_folder, file)):
                csv_files.append(self.user_folder + "/" + file)

        if csv_files:
            act_dir = self.user_folder + "/activity_hist"
            if os.path.exists(act_dir):
                rmtree(act_dir)
            os.mkdir(act_dir)
            
            decompose_activity_file(csv_files, act_dir)
        else:
            logger.info(f"There is no activity file of {self.info['name']}({self.user_folder.split('/')[-1]})")
            self.status = "error"

    
    def start_simulation(self):
        self.agents_pool.start_simulation()


    def continue_simulation(self, days):
        self.agents_pool.continue_simulation(days)

    
    def set_intervention(self, plan, agent_list):
        self.agents_pool.set_intervention(plan, agent_list)


    def get_status(self):
        return self.status

    def get_description(self):
        return self.description
    
    def get_information(self):
        _temp = {
            "description" : self.description,
            "agents_size" : self.agents_size,
            "simul_days" : self.simul_days,
            "start_date" : self.start_date,
        }
        for key in self.info.keys():
            _temp[key] = self.info[key]
        return _temp

    def check_ready(self):
        return self.status=="ready"


def create_user_filetree(name, birthday, username, **kwargs):
    uuid_base = f"{username}.{name.replace(' ', '-')}.{birthday}"
    _uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, uuid_base))
    folder = CONFIG["base_dir"] + f"/.Users/{_uuid}"
    os.mkdir(folder)
    with open(folder + "/info.json", "w") as f:
        info = {
            "uuid":_uuid,
            "name":name,
            "birthday":birthday,
            "description":""
        }
        for key in kwargs.keys():
            info[key] = kwargs[key]
        json.dump(info, fp=f)
    return _uuid


def delete_user_filetree(_uuid):
    folder = CONFIG["base_dir"] + f"/.Users/{_uuid}"
    try:
        rmtree(folder)
    except:
        return False
    else:
        return True
    

def random_user(short_description):
    return random_generate(short_description)

def vague_user(short_description):
    return extract_info(short_description)
