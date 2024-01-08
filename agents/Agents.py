""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

import os
from shutil import rmtree

from openai import OpenAI

from .description import *

class AgentsPool:


    def __init__(self, info: dict, folder: str, size:int=10) -> None:
        self.info = info
        self.size = size
        self.pool = {}

        self.folder = folder + "/agents"
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

        self.info_tree = InfoTree(info, folder=folder+"/agents")

        ######################
        # finish :  finish creating
        # creating : building is undergoing
        # loading: loading the agents from local machine
        # error {id}:  error in create {id} agent
        # loaded : successful loaded from local machine
        self.status = "init"


    def create_pool(self, ):
        thread = threading.Thread(target=self._create_pool)
        self.status = "building"
        thread.start()
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
                agent_info = self.info_tree.generate_info_dict()
                self.pool[i] = Agent(index=i, pool_folder=agent_folder, info=agent_info)
            except:
                error += f"{i}, "
        
        if if_err:
            self.status = "error " + error
        else:
            self.status = "finish"


    def load_pool(self, ):
        thread = threading.Thread(target=self._load_pool)
        self.status = "loading"
        thread.start()
        return self.status


    def _load_pool(self, ):
        error = ""
        if_err = False
        for i in range(1, self.size+1):
            agent_folder = self.folder + "/" + str(i)
            
            try:
                self.pool[i] = Agent(index=i, pool_folder=agent_folder)
            except:
                error += f"{i}, "
        
        if if_err:
            self.status = "error " + error
        else:
            self.status = "finish"


    def save_pool(self, ):
        for idx in self.pool:
            self.pool[idx].save()


    def fetch_tree_status(self):
        return self.info_tree.get_status()
    

    def fetch_status(self):
        return self.status
    

class Agent:

    def __init__(self, index, pool_folder, info:dict=None) -> None:
        self.index = index
        self.info = info
        self.folder = pool_folder

        # Agent status
        self._status = ""

        self.description = ""

        if not info:
            self._load_info()

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