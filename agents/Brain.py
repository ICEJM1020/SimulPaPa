""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-01-08
""" 
import sys
import os
import json
from datetime import datetime, timedelta
import multiprocessing as mp

sys.path.append(os.path.abspath('./'))

from openai import OpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_openai import ChatOpenAI

from config import CONFIG
from agents.ShortMemory import ShortMemory
from agents.LongMemory import LongMemory
from agents.dantic import *
from agents.utils import *


class Brain:
    def __init__(self, 
                 user_folder, 
                 agent_folder,
                 schedule_type:str = "free",
                 activities_by_labels:bool = True,
                 labels:list[str] = [],
                 retry_times = 5,
                 verbose = False,
                 base_date = "03-01-2024"
            ) -> None:
        self.user_folder = user_folder
        self.agent_folder = agent_folder
        self.activity_folder = os.path.join(agent_folder, "activity_hist")

        ########
        # Memory
        ########
        try:
            prompts_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
            with open(os.path.join(prompts_folder, "prompt_schedule.json"), "r") as f:
                self._schedule_prompts = json.load(fp=f)
            with open(os.path.join(prompts_folder, "prompt_decompose.json"), "r") as f:
                self._decompose_prompts = json.load(fp=f)
            with open(os.path.join(prompts_folder, "prompt_utils.json"), "r") as f:
                self._utils_prompts = json.load(fp=f)
            with open(os.path.join(prompts_folder, "prompt_mmdata.json"), "r") as f:
                self._mmdata_prompts = json.load(fp=f)
        except:
            raise Exception("No prompts file")

        ########
        # free schedule or use label
        ########
        if schedule_type == "label":
            if not labels:
                raise Exception("schedule_type \"label\" need to set the parameter \"labels\", which is a list of of possible activities.")
            else:
                self.free = False
                self.labels = labels
        else:
            self.free = True
        ## if use labels to generate activities
        self.activities_by_labels = activities_by_labels
    
        ########
        # Memory
        ########
        self.base_date = base_date
        self.long_memory = LongMemory(user_folder=self.user_folder, agent_folder=self.agent_folder)
        self.short_memory = ShortMemory(agent_folder=self.agent_folder)
        
        ########
        # utils
        ########
        self._output_cache = ""
        self._output_cache_length = 500
        self._out_activity_file = os.path.join(agent_folder, "activity.csv")
        with open(self._out_activity_file, "w") as f:
            f.write("time,activity,event,location,longitude,latitude,heartrate,chatbot\n")
        self._retry_times = retry_times
        self._verbose = verbose

            

    def init_brain(self):

        # if not self.long_memory.memory_tree["user_chatbot_pref"]:
        #     self.long_memory.memory_tree["user_chatbot_pref"] = self._summary_user_chatbot_preference()
        # if not self.long_memory.memory_tree["agent_chatbot_pref"]:
        #     self.long_memory.memory_tree["agent_chatbot_pref"] = self._generate_agent_chatbot_preference()
        pass


    def plan(self, days, simul_type="new"):
        
        if simul_type=="new":
            start_date = self.base_date
            cur_time = "00:00"
        elif simul_type=="continue":
            self.short_memory.load_cache()
            self.long_memory.load_cache()
            start_date = self.short_memory.cur_date
            cur_time = self.short_memory.cur_time
        else:
            raise Exception("Simulation type error!")
        simul_process = mp.Process(target=self._plan, args=(days,start_date,cur_time))
        simul_process.start()


    def _plan(
            self, 
            days:int=1, 
            start_date:str="03-01-2024",
            start_time:str="00:00", 
            end_time:str="23:59"
            ):
        try:
            start_time_dt = datetime.strptime(start_time, "%H:%M")
            del(start_time_dt)
        except:
            print(f"start_time format error {start_time} (should be HH:MM). Set to 00:00")

        self.short_memory.cur_date = start_date
        self.short_memory.cur_time = start_time
        ## create end_time to end the simulation in that time
        self.end_time = start_date + timedelta(days=days, hours=int(end_time.split(":")[0]), minutes=int(end_time.split(":")[1]))
        for _ in range(days + 1):
            
            _schedule = self._create_range_schedule(
                start_date=self.short_memory.cur_date,
                start_time=self.short_memory.cur_time
            )
            self.short_memory.schedule =_schedule.dump_dict()
            if CONFIG["debug"]: print(self.short_memory.schedule)

            response = self._run_schedule()
            self.save_info()

            if response:
                return True
            

    def _run_schedule(self):
        self.save_info()
        
        ## decompose the first event
        self._decompose()
        self.save_cache()
        while True:
            self.short_memory.cur_activity = self.short_memory.planning_activity

            ## save to local file
            self.save_activity()
            print(f"[{self.short_memory.cur_time}] {self.short_memory.cur_event['event']}-{self.short_memory.cur_activity} ")

            ###############
            ## Update time and check end
            ###############
            self.short_memory.cur_time = self.short_memory.cur_time_dt + timedelta(minutes=1)
            if self.short_memory.cur_time_dt == datetime.strptime("00:00", "%H:%M"):
                self.save_hist()
                self.short_memory.cur_date = self.short_memory.cur_date_dt + timedelta(days=1)

            if self.short_memory.check_new_event():
                self._decompose()
                self.save_cache()

            if self.short_memory.check_end_schedule():
                return False
            
            if self.short_memory.date_time_dt >= self.end_time:
                return True
            

    ###############
    ## create the schedule
    ###############
    def _create_range_schedule(self,start_date,start_time) -> Schedule:
        for try_idx in range(self._retry_times):
            try:
                _schedule = self._create_range_schedule_chat(
                    start_date=start_date,
                    start_time=start_time,
                )
                assert len(_schedule.schedule) > 0
            except:
                if try_idx + 1 == self._retry_times:
                    raise Exception(f"Event schedule generation failed {self._retry_times} times")
                else:
                    continue
            else:
                return _schedule

    def _create_range_schedule_chat(
                self,
                start_date,
                start_time,
                llm_temperature=1.0,
            ) -> Schedule:
        
        # Generate schedule examples
        # We need to add .replace("{", "{{").replace("}", "}}") after serialising as JSON
        schedule_examples = []
        for idx, entry in enumerate(self._schedule_prompts['schedule_examples']):
            schedule_examples.append({
                    "intervention": entry["intervention"],
                    "description": entry["description"], 
                    "start_time": entry["start_time"],
                    "schedule":[]
                })
            for event_entry in entry["schedule"]:
                schedule_examples[idx]["schedule"].append(
                        ScheduleEntry.model_validate(event_entry).model_dump_json().replace("{", "{{").replace("}", "}}")
                        # json.dumps(event_entry).replace("{", "{{").replace("}", "}}")
                    )
        example_prompt = PromptTemplate(
            input_variables=["intervention", "description", "start_time", "schedule"],
            template=self._schedule_prompts["schedule_example_prompt"]
        )

        ## schedule few-shots examples
        schedule_parser = PydanticOutputParser(pydantic_object=Schedule)

        prompt = FewShotPromptTemplate(
            examples=schedule_examples,
            example_prompt=example_prompt,
            prefix=self._schedule_prompts["prefix"],
            suffix=self._schedule_prompts["suffix"],
            input_variables=['description', 'start_date', 'start_time', 'home_addr', 'work_addr'],
            partial_variables={"format_instructions": schedule_parser.get_format_instructions()},
        )

        chain = LLMChain(
            llm=ChatOpenAI(
                    api_key=CONFIG["openai"]["api_key"],
                    organization=CONFIG["openai"]["organization"],
                    model_name='gpt-3.5-turbo-16k',
                    temperature=llm_temperature,
                    verbose=self._verbose,
                ),
                prompt=prompt,
            )
        
        results = chain.invoke(input={
            'intervention':self.long_memory.intervention,
            'description':self.long_memory.description,
            'home_addr':self.long_memory.home_addr,
            'work_addr':self.long_memory.work_addr,
            'start_date':start_date,
            'start_time':start_time,
            "event_examples":label_list_to_str(self._schedule_prompts["event_examples"])
        }, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})
        response = results['text'].replace("24:00", "23:59")
        return schedule_parser.parse(response)
          
            
    ###############
    ## Decompose the schedule event
    ###############
    def _decompose(self):
        decompose = self._decompose_task().dump_list()
        self.short_memory.cur_decompose = decompose
        if CONFIG["debug"]: print(decompose)

        location = self._predict_location(decompose=decompose).dump_list()
        print(location)
        self.short_memory.cur_location_list = location
        if CONFIG["debug"]: print(location)

        # chatbot = self._predict_botusage(decompose=decompose)
        # self.short_memory.cur_chatbot_list = chatbot
        # if CONFIG["debug"]: print(chatbot)

    def _decompose_task(self, re_decompose=False) -> Decompose:
        for try_idx in range(self._retry_times):
            try:
                _decompose = self._decompose_task_chat(re_decompose)
                assert len(_decompose.decompose) > 0
            except:
                if try_idx + 1 == self._retry_times:
                    raise Exception(f"Event decompose failed {self.short_memory.cur_event_str} {self._retry_times} times")
                else:
                    continue
            else:
                return _decompose

    def _decompose_task_chat(self, re_decompose, llm_temperature=1.5):
        # Generate decompose examples
        decompose_examples = []
        for idx, entry in enumerate(self._decompose_prompts['example']):
            decompose_examples.append({
                    "event": entry["event"], 
                    "cur_activity" : entry["cur_activity"],
                    "options" : entry["options"] if self.activities_by_labels else "",
                    "decompose":[]
                })
            for event_entry in entry["decompose"]:
                decompose_examples[idx]["decompose"].append(
                        DecomposeEntry.model_validate(event_entry).model_dump_json().replace("{", "{{").replace("}", "}}")
                        # json.dumps(event_entry).replace("{", "{{").replace("}", "}}")
                    )
        example_prompt = PromptTemplate(
            input_variables=["event", "cur_activity", "options", "decompose"],
            template=self._decompose_prompts["example_prompt"]
        )

        ## event decompose few-shots examples
        decompose_parser = PydanticOutputParser(pydantic_object=Decompose)
        
        prompt = FewShotPromptTemplate(
            examples=decompose_examples,
            example_prompt=example_prompt,
            prefix=self._decompose_prompts["re_prefix"] if re_decompose else self._decompose_prompts["prefix"],
            suffix=self._decompose_prompts["suffix"],
            input_variables=['description', 'past_activity_summary','cur_activity', 'cur_event', 'cur_time', 'end_time'],
            partial_variables={"format_instructions": decompose_parser.get_format_instructions()},
        )

        chain = LLMChain(
            llm=ChatOpenAI(
                    api_key=CONFIG["openai"]["api_key"],
                    organization=CONFIG["openai"]["organization"],
                    model_name='gpt-3.5-turbo-16k',
                    temperature=llm_temperature,
                    verbose=self._verbose,
                ),
                prompt=prompt,
            )
        
        results = chain.invoke(input={
            'description':self.long_memory.description,
            'cur_time':self.short_memory.date_time if re_decompose else self.short_memory.cur_event['start_time'],
            'end_time':self.short_memory.cur_event['end_time'],
            'cur_activity':self.short_memory.cur_activity,
            'cur_event':self.short_memory.cur_event['event'],
            'past_activity_summary':self._summary_activity(),
        }, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})

        response = results['text'].replace("24:00", "23:59")
        return decompose_parser.parse(response)


    def _summary_activity(self):
        human_prompt = HumanMessagePromptTemplate.from_template(self._utils_prompts["activity_summary"])
        chat_prompt = ChatPromptTemplate.from_messages([human_prompt])

        records = self.short_memory.fetch_records(num_items=30)
        records_str = ""
        for record in records:
            records_str += f"[{record['time']}] Event[{record['schedule_event']}] Activity[{record['activity']} Location[{record['location']}]]\n"
        if not records_str:
            records_str += "No Records."

        request = chat_prompt.format_prompt(records = records_str).to_messages()

        model = ChatOpenAI(
                api_key=CONFIG["openai"]["api_key"],
                organization=CONFIG["openai"]["organization"],
                model_name='gpt-3.5-turbo',
                temperature=0.5,
                verbose=self._verbose
            )
        results = model.invoke(request, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})
        if CONFIG["debug"]: print(results.content)
        return results.content


    def _predict_location(self, decompose) -> Location:
        for try_idx in range(self._retry_times):
            try:
                location = self._predict_location_chat(decompose)
            except:
                if try_idx + 1 == self._retry_times:
                    return [self.long_memory.home_addr]
                else:
                    continue
            else:
                return location
            
    def _predict_location_chat(self, decompose, llm_temperature=1.0) -> Location:
        location_example = []
        for entry in self._mmdata_prompts['location_example']:
            # print(entry)
            location_example.append({
                    "activity": entry["activity"], 
                    "location" : entry["location"],
                    "longitude" : entry["longitude"],
                    "latitude" : entry["latitude"]
                })
        example_prompt = PromptTemplate(
            input_variables=["activity", "location", "longitude", "latitude"],
            template=self._mmdata_prompts["location_example_prompt"]
        )

        location_parser = PydanticOutputParser(pydantic_object=Location)
        
        prompt = FewShotPromptTemplate(
            examples=location_example,
            example_prompt=example_prompt,
            prefix=self._mmdata_prompts["location_prefix"],
            suffix=self._mmdata_prompts["location_suffix"],
            input_variables=['description', 'past_activity_summary','home_addr', 'work_addr', 'loc_hist', 'decompose', 'cur_time'],
            partial_variables={"format_instructions": location_parser.get_format_instructions()},
        )

        chain = LLMChain(
            llm=ChatOpenAI(
                    api_key=CONFIG["openai"]["api_key"],
                    organization=CONFIG["openai"]["organization"],
                    model_name='gpt-3.5-turbo-16k',
                    temperature=llm_temperature,
                    verbose=self._verbose,
                ),
                prompt=prompt,
            )
        
        results = chain.invoke(input={
            'description' : self.long_memory.description,
            'home_addr' : self.long_memory.home_addr,
            'work_addr' : self.long_memory.work_addr,
            'loc_hist' : json.dumps(self.short_memory.fetch_location_records(num_items=30)),
            'decompose' : json.dumps(decompose),
            'cur_time' : self.short_memory.cur_time,
        }, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})

        response = results['text'].replace("24:00", "23:59")
        return location_parser.parse(response)


    def _predict_heartrate(self):
        pass


    def _predict_botusage(self):
        for try_idx in range(self._retry_times):
            try:
                usage = self._predict_botusage_chat()
            except:
                if try_idx + 1 == self._retry_times:
                    return []
                else:
                    continue
            else:
                return usage
    
    def _predict_botusage_chat(self):
        
        pass



    def set_intervention(self, plan):
        self.long_memory.intervention = plan


    def save_info(self):
        info = self.long_memory.info

        info["schedule"] = self.short_memory.schedule

        with open(os.path.join(self.agent_folder, "info.json"), "w") as f:
            json.dump(info, fp=f)
    
    def save_activity(self):
        # "time, activity, event, feature_summary\n"
        self._output_cache += self.short_memory.csv_record()

        if len(self._output_cache) >= self._output_cache_length:
            with open(self._out_activity_file, "a+") as f:
                f.write(self._output_cache)
            self._output_cache = ""

    def save_hist(self):
        with open(self._out_activity_file, "a+") as f:
            f.write(self._output_cache)
        self._output_cache = ""

        os.replace(self._out_activity_file, os.path.join(self.activity_folder, self.short_memory.cur_date + ".csv"))

        with open(self._out_activity_file, "w") as f:
            f.write("time,activity,event,location,longitude,latitude,heartrate,chatbot\n")

    def save_cache(self):
        self.short_memory.save_cache()
        self.long_memory.update_memory()

    def load_cache(self):
        self.short_memory.load_cache()
        self.long_memory.load_cache()



if __name__ == "__main__":
    brain = Brain(
        user_folder="/Users/timberzhang/Documents/Documents/Long-SimulativeAgents/Code/SimulPaPa/.Users/19d7bf69-7fdc-3648-9c87-9bfca20611c2",
        agent_folder="/Users/timberzhang/Documents/Documents/Long-SimulativeAgents/Code/SimulPaPa/.Users/19d7bf69-7fdc-3648-9c87-9bfca20611c2/agents/9",
    )
    brain.init_brain()
    brain.plan()


