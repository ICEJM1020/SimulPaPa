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


    def create_pool(self, ):
        for i in range(1, self.size+1):
            agent_folder = self.folder + "/" + str(i)
            if os.path.exists(agent_folder):
                rmtree(agent_folder)
                os.mkdir(agent_folder)
            else:
                os.mkdir(agent_folder)
            agent_info = self.info_tree.generate_info_dict()
            print(agent_info)
            self.pool[i] = Agent()
    

    def load_pool(self, ):
        pass

    def fetch_tree_status(self):
        return self.info_tree.get_status()
    

class Agent:

    def __init__(self) -> None:
        
        pass

