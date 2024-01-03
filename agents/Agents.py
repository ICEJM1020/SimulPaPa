""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 

from openai import OpenAI

from .description import *

class AgentsPool:


    def __init__(self, info: dict, folder: str, size:int=100) -> None:
        self.info = info
        self.size = size
        self.pool = {}

        self.folder = folder + "/agents"

        self.info_tree = InfoTree(info)


    def create_pool(self, ):
        pass
    

    def fetch_tree_status(self):
        return self.info_tree.get_status()
    

class Agent:

    def __init__(self) -> None:
        
        pass

