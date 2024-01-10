""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-01-08
""" 
import sys
import os
import json
from datetime import datetime, timedelta

sys.path.append(os.path.abspath('./'))

from openai import OpenAI

from config import CONFIG
from agents.Memory import LongMemory, ShortMemory



class Brain:
    def __init__(self, user_folder, agent_folder, info) -> None:
        self.user_folder = user_folder
        self.agent_folder = agent_folder

        self.long_memory = LongMemory(user_folder=user_folder, agent_folder=agent_folder)
        self.short_memory = ShortMemory(agent_folder=agent_folder, info=info)

        ######################
        # ready :  finish creating and ready to simulate
        # creating : building is undergoing
        # loading: loading the agents from local machine
        # error:  error in planing
        self.status = "init"

        self.gpt_client = OpenAI(
            api_key=CONFIG["openai"]["api_key"],
            organization=CONFIG["openai"]["organization"],
        )

        ## memory related
        self.retrieve_days = 5


    def plan(self, days:int=1, type:str="new"):
        
        planing_days = []
        if type=="new":
            user_last_day = self.long_memory.fetch_user_lastday()
            for i in range(1, days+1):
                planing_day = datetime.strptime(user_last_day, '%m-%d-%Y') + timedelta(days=1)
                planing_days.append(planing_day.strftime('%m-%d-%Y'))
        elif type=="continue":
            pass
        else:
            raise Exception("plan type error!")
        
        for i in range(days):
            self.short_memory.set_today(planing_days[i])
            self.short_memory.set_purpose(self._define_one_day_purpose())

            print(self._create_hourly_activity())




    def _define_one_day_purpose(self):
        prompt = self.long_memory.description
        prompt += f"Today is {self.short_memory.memory_tree['today']}, and this is also a new day of {self.long_memory.info['name']}. "
        prompt += f"For last {self.retrieve_days} days, the main purpose of every day is "
        prompt += f"{self.long_memory.past_daily_purpose(self.short_memory.memory_tree['today'], self.retrieve_days)}. "
        prompt += "Based on personal information and past daily purpose, combined with your knowledge about the date of today, what do you think about the main purpose of today. "
        prompt += f"Here are some options for you, {CONFIG['daily_purpose']}. Return your answer in the following JSON format without any other information: "
        prompt += "{\"choice\" : \"choice_from_options\"}"

        completion = self.gpt_client.chat.completions.create(
            model="gpt-3.5-turbo", 
            # model="gpt-4",
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        print(completion.choices[0].message.content)
        return json.loads(completion.choices[0].message.content)["choice"]
    

    def _create_hourly_activity(self):
        hourly_schedule = {f"{i}:00":"to_be_determined" for i in range(24)}
        
        prompt = self.long_memory.description
        prompt += f"Today is {self.short_memory.memory_tree['today']}, {self.long_memory.info['name']} want to {self.short_memory.memory_tree['today_purpose']}. "
        prompt += f"Now, {self.long_memory.info['name']} want to determine a schedule for today. "
        # prompt += f"For past {self.retrieve_days}, {self.long_memory.info['name']}'s daily schedules are: "
        # prompt += f"{self.long_memory.past_daily_schedule()}"
        prompt += "Based on personal information and past daily purpose, combined with your knowledge about the date of today, can fill the schedule? "
        prompt += f"Here are some options for you, {CONFIG['activity']}. If there is no resaonable choice, you can create one. "
        prompt += "Return your answer in the following JSON format without any other information: "
        prompt += json.dumps(hourly_schedule)

        completion = self.gpt_client.chat.completions.create(
            model="gpt-3.5-turbo", 
            # model="gpt-4",
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        return json.loads(completion.choices[0].message.content)




if __name__ == "__main__":
    brain = Brain(
        user_folder="/Users/timberzhang/Documents/Documents/Long-SimulativeAgents/Code/SimulPaPa/.Users/19d7bf69-7fdc-3648-9c87-9bfca20611c2",
        agent_folder="/Users/timberzhang/Documents/Documents/Long-SimulativeAgents/Code/SimulPaPa/.Users/19d7bf69-7fdc-3648-9c87-9bfca20611c2/agents/1",
        info={}
    )
    brain.plan()


