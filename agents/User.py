""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-29
""" 

import uuid
import os
import json
from shutil import rmtree
from datetime import date

from config import CONFIG
from .description import gpt_description
from .Agents import AgentsPool


def init_pool():
    pool = UserPool()
    return pool


class UserPool:


    def __init__(self) -> None:
        self.pool = {}


    def append(self, _uuid):
        self.pool[_uuid] = User(_uuid)

    
    def pop(self, _uuid):
        self.pool[_uuid].save()
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
    

    def fetch_tree_status(self, _uuid):
        return self.pool[_uuid].agents_pool.fetch_tree_status()



class User:

    def __init__(self, _uuid) -> None:
        # machine ID
        self._uuid = _uuid
        self.user_folder = CONFIG["base_dir"] + f"/.Users/{_uuid}"

        # user status
        self._status = ""

        # user info
        self.info = {
            "name" : None,
            "gender" : None,
            "race" : None,
            "birthday" : None,
            "city" : None,
            "disease" : None,
            "description" : None,
        }
        self.add_info = {
            "street" : None,
            "district" : None,
            "state" : None,
            "zipcode" : None,
            "education" : None,
            "language" : None,
            "occupation" : None
        }
        self._load_info()
        if not self.info["description"] or self.info["description"]=="":
            self.generate_description()

        self.agents_pool = AgentsPool(
            info=self._convert_info(),
            folder=self.user_folder
        )


    def _convert_info(self):
        return {**self.info, **self.add_info}
    

    def _load_info(self):
        try:
            with open(self.user_folder + "/info.json", "r") as f:
                info = json.load(f)
        except:
            self._status = "Load information file unsuccessfully"
        else:
            missing, fake = self._fill_info(info=info)
            self._status = "Missing information: " + missing + " Following will be generated: " + fake
    

    def _fill_info(self, info):
        missing = ""
        fake = ""
        for key in self.info.keys():
            if key in info.keys():
                self.info[key] = info[key]
            else:
                missing += key + "/"
        for key in self.add_info.keys():
            if key in info.keys():
                self.add_info[key] = info[key]
            else:
                fake += key + "/"
        return missing, fake


    def generate_description(self):
        try:
            info = gpt_description(**self._convert_info())
            self._fill_info(info)
            self._status = "Generate description successfully"
        except:
            self._status = "Generate description unsuccessfully"


    def save(self):
        with open(self.user_folder + "/info.json", "w") as f:
            dumps = {"uuid":self._uuid}
            for key in self.info.keys():
                dumps[key] = self.info[key]
            for key in self.add_info.keys():
                dumps[key] = self.add_info[key]
            json.dump(dumps, fp=f)
    

    def modify_info(self, info):
        for key in info.keys():
            if key in self.info.keys():
                self.info[key] = info[key]
            elif key in self.add_info.keys():
                self.add_info[key] = info[key]
            else:
                continue
        self.generate_description()
        self.save()


    def get_status(self):
        return self._status


    def get_description(self):
        return self.info["description"]
    



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
    

if __name__ == "__main__":
    print(create_user_filetree("Timber", "20-10-1998"))


