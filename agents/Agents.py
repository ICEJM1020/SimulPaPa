""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

import os
from shutil import rmtree

from openai import OpenAI

from logger import logger
from agents.Info import *



class AgentsPool:


    def __init__(self, info: dict, user_folder: str, size:int=10) -> None:
        self.info = info
        self.size = size
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


    def create_pool(self, ):
        logger.info(f"start create agents pool for {self.info['name']}({self.user_folder.split('/')[-1]})")
        if self.info_tree.get_status() == "ready":
            thread = threading.Thread(target=self._create_pool)
            self.status = "building"
            thread.start()
        else:
            logger.info(f"info tree for agents pool of {self.info['name']}({self.user_folder.split('/')[-1]}) has not finished")
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
            
            if CONFIG["debug"]:
                agent_info = self.info_tree.generate_info_dict()
                self.pool[i] = Agent(index=i, user_folder=self.user_folder, info=agent_info)
            else:
                try:
                    agent_info = self.info_tree.generate_info_dict()
                    self.pool[i] = Agent(index=i, user_folder=self.user_folder, info=agent_info)
                except:
                    if_err = True
                    logger.error(f"try to create agent {i} for {self.info['name']}({self.user_folder.split('/')[-1]}) failed")
                    error += f"{i}, "
        
        if if_err:
            self.status = "error create" + error
        else:
            self.status = "ready"


    def load_pool(self, ):
        logger.info(f"start load agents pool for {self.info['name']}({self.user_folder.split('/')[-1]})")
        thread = threading.Thread(target=self._load_pool)
        self.status = "loading"
        thread.start()
        return self.status


    def _load_pool(self):
        error = ""
        if_err = False
        for i in range(1, self.size+1):
            
            try:
                self.pool[i] = Agent(index=i, user_folder=self.user_folder)
            except:
                if_err = True
                error += f"{i}, "
                logger.error(f"try to load agent {i} pool for {self.info['name']}({self.user_folder.split('/')[-1]}) failed")

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


    def start_simulation(self, day=1):
        logger.info(f"start simulation for {self.info['name']}({self.user_folder.split('/')[-1]})")
        thread = threading.Thread(target=self._start_simulation, name=f"{self.user_folder.split('/')[-1]}-simulation", kwargs={"day":day})
        self.simul_status = "working"
        thread.start()
        return self.status


    def _start_simulation(self, day=1):
        pass


    def fetch_tree_status(self):
        return self.info_tree.get_status()
    

    def fetch_status(self):
        return self.status
    

    def fetch_simul_status(self):
        return self.simul_status


class Agent:

    def __init__(self, index, user_folder, info:dict=None) -> None:
        self.index = index
        self.info = {key:None for key in CONFIG["info"]}
        self.user_folder = user_folder
        self.folder = user_folder + f"/agents/{index}"

        # Agent status
        self._status = ""

        self.description = ""

        if not info:
            self._load_info()
        else:
            self._fill_info(info=info)

        if self.description=="":
            self.generate_description()


    def _load_info(self):
        try:
            with open(self.folder + "/info.json", "r") as f:
                info = json.load(f)
        except:
            self._status = "Load information file unsuccessfully"
        else:
            missing = self._fill_info(info=info)
            self._status = "Missing information: " + missing


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
            self._status = "Generate description successfully"
        except:
            self._status = "Generate description unsuccessfully"


    def save(self):
        with open(self.folder + "/info.json", "w") as f:
            dumps = {
                "description":self.description
            }
            for key in self.info.keys():
                dumps[key] = self.info[key]
            json.dump(dumps, fp=f)




