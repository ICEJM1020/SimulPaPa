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
        # creating : building is undergoing
        # loading: loading the agents from local machine
        # error {id}:  error in create {id} agent
        self.status = "init"

        ######################
        # finish :  finish simulating
        # working : building is undergoing
        # error {id}:  error in create {id} agent
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
            self.status = "building"
            thread.start()
        else:
            logger.info(f"info tree for agents pool of {self.info['name']}({self._uuid}) has not finished")
        return self.status
    

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
            self.status = "error create" + error
        else:
            self.status = "ready"


    def load_pool(self, ):
        logger.info(f"start load agents pool for {self.info['name']}({self._uuid})")
        thread = threading.Thread(target=self._load_pool)
        self.status = "loading"
        thread.start()
        return self.status


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
            self.status = "error load " + error
        else:
            self.status = "ready"


    def save_pool(self, ):
        if self.status=="ready":
            for idx in self.pool:
                self.pool[idx].save()
        elif self.status=="building":
            raise Exception("Agents pool is under creation")
        else:
            pass

    def fetch_all_agents(self, ):
        dir_list = os.listdir(self.folder)
        res = []
        for dir in dir_list:
            if not "." in dir:
                res.append(f"Agent-{dir}")
        return res, len(res)==self.size


    def start_simulation(self, days=1):
        logger.info(f"start simulation for {self.info['name']}({self._uuid})")
        for agent in self.pool.values():
            agent.start_planing(days)

    
    def continue_simulation(self, days=1):
        logger.info(f"continue simulation for {self.info['name']}({self._uuid})")
        for agent in self.pool.values():
            agent.continue_planing(days)


    def fetch_tree_status(self):
        return self.info_tree.get_status()
    

    def fetch_status(self):
        return self.status
    

    def fetch_simul_status(self):
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
        # ready :  finish creating and ready to simulate
        # creating : building is undergoing
        # loading: loading the agents from local machine
        # error {id}:  error in create {id} agent
        self.status = "init"

        # infomation
        self.info = {key:None for key in CONFIG["info"]}
        self.description = ""
        if info==None:
            self._load_info()
        else:
            self._fill_info(info=info)
        if self.description=="":
            self.generate_description()

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
            self.status = "error"
        else:
            missing = self._fill_info(info=info)
            logger.info(f"{self._uuid} agent({self.index}) load information file successfully, missing: {missing}")
            self.status = "ready"


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
            self.status = "error"            
            logger.info(f"{self._uuid} agent({self.index}) generate description unsuccessfully")
        else:
            self.status = "ready"
            logger.info(f"{self._uuid} agent({self.index}) generate description successfully")


    def start_planing(self, days=1):
        # self.brain.init_brain()
        self.brain.plan(days=days, simul_type="new")

    def continue_planing(self, days=1):
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
        self.brain.save_cache()


    def check_ready(self):
        return self.status=="ready"


