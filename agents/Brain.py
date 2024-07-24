""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-01-08
""" 
import sys
import os
import json
from datetime import datetime, timedelta
import threading
import multiprocessing as mp

sys.path.append(os.path.abspath('./'))

from openai import OpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_openai import ChatOpenAI
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter

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
        self.thoughts_folder = os.path.join(agent_folder, "thoughts_log")

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
        self.labels = CONFIG["activity_catalogue"]
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
        ## Records
        self._output_cache = ""
        self._output_cache_length = 500
        self._out_activity_file = os.path.join(agent_folder, "activity.csv")
        ## Thoughts
        self._thoughts_cache = ""
        self._thoughts_cache_length = 1000
        self._out_thoughts_file = os.path.join(agent_folder, "thoughts.txt")

        self._retry_times = retry_times
        self._verbose = verbose
        ## status
        # ready : ready to start simulation
        # working: working on simulation
        # error:  error
        self._status = "ready"
        ## 0: ready
        ## 1: working
        ## 2: error
        self.running_status = mp.Value('d', 0)

    @property
    def status(self):
        self._update_running_status()
        return self._status
    
    @status.setter
    def status(self, status):
        self._status = status

    def _update_running_status(self):
        if self.running_status.value == 0:
            self.status = "ready"
        elif self.running_status.value == 1:
            self.status = "working"
        else:
            self.status = "error"


    def plan(self, days, simul_type="new"):
        
        if simul_type=="new":
            start_date = self.base_date
            cur_time = "00:00"
            with open(self._out_activity_file, "w") as f:
                f.write("time,activity,event,location,longitude,latitude,heartrate,chatbot,steps\n")
        elif simul_type=="continue":
            start_date = self.short_memory.cur_date
            cur_time = self.short_memory.cur_time
        else:
            self.status = "error"
            raise Exception("Simulation type error!")
        self.status = "working"
        simul_process = mp.Process(
                target=self._plan, 
                kwargs={
                    '_status':self.running_status, 
                    'days':days, 
                    'start_date':start_date, 
                    'start_time':cur_time
                    }
                )
        simul_process.start()


    def _plan(
            self,
            _status,
            days:int=1,
            start_date:str="03-01-2024",
            start_time:str="08:00", 
            end_time:str="00:00"
            ):
        _status.value = 1
        try:
            start_time_dt = datetime.strptime(start_time, "%H:%M")
            del(start_time_dt)
        except:
            # self.status = "error"
            _status.value = 2
            print(f"start_time format error {start_time} (should be HH:MM). Set to 00:00")

        self.short_memory.cur_date = start_date
        self.short_memory.cur_time = start_time
        ## create end_time to end the simulation in that time
        self.end_time = self.short_memory.date_time_dt + timedelta(days=days, hours=int(end_time.split(":")[0]), minutes=int(end_time.split(":")[1]))

        if not self.long_memory.chatbot_preference:
            self.long_memory.chatbot_preference = self._generate_chatbot_preference()

        if CONFIG['debug']:
            for _ in range(days + 1):
                # if not self.long_memory.daily_purpose:
                _purpose = self._define_daily_purpose()
                self.long_memory.daily_purpose = _purpose["answer"]
                if CONFIG["save_thoughts"]:
                    self.save_thoughts("Thoughts when defining purpose of today", json.dumps(_purpose))

                # if not self.short_memory.schedule:
                _schedule = self._create_range_schedule(
                    start_date=self.short_memory.cur_date,
                    start_time=self.short_memory.cur_time
                )
                self.short_memory.schedule =_schedule.dump_dict()
                if CONFIG["save_thoughts"]:
                    self.save_thoughts("Thoughts when create schedule of today", _schedule.fetch_thoughts())
                if CONFIG["debug"]: print(self.short_memory.schedule)

                response = self._run_schedule()
                self.save_cache()

                if response:
                    # self.status = "ready"
                    _status.value = 0
                    return True
        else:
            try:
                if not self.long_memory.chatbot_preference:
                    self.long_memory.chatbot_preference = self._generate_chatbot_preference()

                for _ in range(days + 1):
                    # if not self.long_memory.daily_purpose:
                    _purpose = self._define_daily_purpose()
                    self.long_memory.daily_purpose = _purpose["answer"]
                    if CONFIG["save_thoughts"]:
                        self.save_thoughts("Thoughts when defining purpose of today", json.dumps(_purpose))

                    # if not self.short_memory.schedule:
                    _schedule = self._create_range_schedule(
                        start_date=self.short_memory.cur_date,
                        start_time=self.short_memory.cur_time
                    )
                    self.short_memory.schedule =_schedule.dump_dict()
                    if CONFIG["save_thoughts"]:
                        self.save_thoughts("Thoughts when create schedule of today", _schedule.fetch_thoughts())
                    if CONFIG["debug"]: print(self.short_memory.schedule)

                    response = self._run_schedule()
                    self.save_cache()

                    if response:
                        # self.status = "ready"
                        _status.value = 0
                        return True
            except:
                _status.value = 2
                # self.status = "error"
                self.save_cache()
                return False

    def _run_schedule(self):
        
        ## decompose the first event
        self._decompose()
        self.save_cache()
        while True:
            self.short_memory.cur_activity = self.short_memory.planning_activity

            ## save to local file
            self.save_activity()
            # print(f"[{self.short_memory.cur_date}-{self.short_memory.cur_time}] {self.short_memory.cur_event['event']}-{self.short_memory.cur_activity} ")

            ###############
            ## Update time and check end
            ###############
            self.short_memory.cur_time = self.short_memory.cur_time_dt + timedelta(minutes=1)
            if self.short_memory.cur_time_dt == datetime.strptime("00:00", "%H:%M"):
                self.save_hist()
                self.save_thoughts_log()
                self.short_memory.cur_date = self.short_memory.cur_date_dt + timedelta(days=1)

            if self.short_memory.check_new_event():
                self._decompose()
                self.save_cache()

            if self.short_memory.check_end_schedule():
                # (self.short_memory.cur_date_dt - timedelta(days=1)).strftime("%m-%d-%Y")
                self.long_memory.update_memory()
                return False
            
            if self.short_memory.date_time_dt >= self.end_time:
                return True
    

    ###############
    ## define daily purpose
    ###############
    def _define_daily_purpose(self) -> str:
        for try_idx in range(self._retry_times):
            try:
                purpose = self._define_daily_purpose_chat()
                assert "answer" in purpose.keys()
            except:
                if try_idx + 1 == self._retry_times:
                    # self.status = "error"
                    raise Exception(f"Define daily purpose failed {self._retry_times} times")
                else:
                    continue
            else:
                return purpose

    def _define_daily_purpose_chat(self):
        human_prompt = HumanMessagePromptTemplate.from_template(self._utils_prompts["define_purpose"])
        chat_prompt = ChatPromptTemplate.from_messages([human_prompt])

        records = self.long_memory.past_daily_purpose(past_days=5)
        records_str = ""
        for idx, record in enumerate(records):
            temp_date = self.short_memory.cur_date_dt - timedelta(days=(len(records)+idx))
            records_str += f"[{temp_date.strftime('%m-%d-%Y')}] {record}\n"
        if not records_str:
            records_str += "No Records."

        request = chat_prompt.format_prompt(
                description = self.long_memory.description,
                records = records_str
            ).to_messages()

        model = ChatOpenAI(
                api_key=CONFIG["openai"]["api_key"],
                organization=CONFIG["openai"]["organization"],
                model_name=CONFIG["openai"]["model"],
                temperature=1.5,
                verbose=self._verbose
            )
        results = model.invoke(request, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})
        if CONFIG["debug"]: print(results.content)
        return json.loads(results.content)


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
                    # self.status = "error"
                    raise Exception(f"Event schedule generation failed {self._retry_times} times")
                else:
                    continue
            else:
                return _schedule

    def _create_range_schedule_chat(
                self,
                start_date,
                start_time,
                llm_temperature=1.2,
            ) -> Schedule:
        
        # Generate schedule examples
        # We need to add .replace("{", "{{").replace("}", "}}") after serialising as JSON
        schedule_examples = []
        for idx, entry in enumerate(self._schedule_prompts[CONFIG['schedule_type']]):
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
            input_variables=['intervention', 'description', 'start_date', 'start_time', 'home_addr', 'work_addr', 'daily_purpose'],
            partial_variables={"format_instructions": schedule_parser.get_format_instructions()},
        )


        chain = LLMChain(
                llm=ChatOpenAI(
                        api_key=CONFIG["openai"]["api_key"],
                        organization=CONFIG["openai"]["organization"],
                        model_name=CONFIG["openai"]["model-turbo"],
                        temperature=llm_temperature,
                        verbose=self._verbose,
                    ),
                prompt=prompt,
            )
        
        results = chain.invoke(input={
            'intervention':self.long_memory.intervention,
            'description':self.long_memory.description,
            'name':self.long_memory.name,
            'home_addr':self.long_memory.home_addr,
            'work_addr':self.long_memory.work_addr,
            'daily_purpose':self.long_memory.daily_purpose,
            'start_date':start_date,
            'start_time':start_time,
            # "event_examples":label_list_to_str(self._schedule_prompts["event_examples"])
        }, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})
        response = results['text'].replace("24:00", "23:59")
        return schedule_parser.parse(response)
          
            
    ###############
    ## Decompose the schedule event
    ###############
    def _decompose(self):
        decompose = self._decompose_task()
        if isinstance(decompose, Decompose):
            if CONFIG["save_thoughts"]:
                self.save_thoughts(f"Thoughts when decompose {self.short_memory.cur_event_str}", decompose.fetch_thoughts())
            decompose = decompose.dump_list()
        self.short_memory.cur_decompose = decompose
        if CONFIG["debug"]: print(decompose)

        location = self._predict_location(decompose=decompose)
        if isinstance(location, Location):
            if CONFIG["save_thoughts"]:
                self.save_thoughts(f"Thoughts when predict the location when {self.short_memory.cur_event_str}", location.fetch_thoughts())
            location = location.dump_list()
        self.short_memory.cur_location_list = location
        if CONFIG["debug"]: print(location)

        chatbot = self._predict_botusage(decompose=decompose)
        if isinstance(chatbot, Chatbot):
            if CONFIG["save_thoughts"]:
                self.save_thoughts(f"Thoughts when predict the Chatbot usage when {self.short_memory.cur_event_str}", chatbot.fetch_thoughts())
            chatbot = chatbot.dump_dict()
        self.short_memory.cur_chatbot_dict = chatbot
        if CONFIG["debug"]: print(chatbot)

        heartrate = self._predict_heartrate(decompose=decompose)
        if isinstance(heartrate, HeartRate):
            if CONFIG["save_thoughts"]:
                self.save_thoughts(f"Thoughts when predict the heart rate when {self.short_memory.cur_event_str}", heartrate.fetch_thoughts())
            heartrate = heartrate.dump_list()
        self.short_memory.cur_heartrate_list = heartrate
        if CONFIG["debug"]: print(heartrate)

        steps = self._predict_steps(decompose=decompose)
        if isinstance(steps, Steps):
            if CONFIG["save_thoughts"]:
                self.save_thoughts(f"Thoughts when predict the steps when {self.short_memory.cur_event_str}", steps.fetch_thoughts())
            steps = steps.dump_dict()
        self.short_memory.cur_steps_dict = steps
        if CONFIG["debug"]: print(steps)


    def _decompose_task(self, re_decompose=False) -> Decompose:
        for try_idx in range(self._retry_times):
            try:
                _decompose = self._decompose_task_chat(re_decompose)
                assert len(_decompose.decompose) > 0
            except:
                if try_idx + 1 == self._retry_times:
                    print("Decompose Error")
                    # self.status = "error"
                    return [{
                        "start_time" : self.short_memory.cur_event["start_time"],
                        "end_time" : self.short_memory.cur_event["end_time"],
                        "activity" : self.short_memory.cur_event["event"],
                    }]
                    # raise Exception(f"Event decompose failed {self.short_memory.cur_event_str} {self._retry_times} times")
                else:
                    continue
            else:
                return _decompose

    def _decompose_task_chat(self, re_decompose, llm_temperature=1.0):
        # Generate decompose examples
        decompose_examples = []
        for idx, entry in enumerate(self._decompose_prompts['example']):
            decompose_examples.append({
                    "event": entry["event"], 
                    "cur_activity" : entry["cur_activity"],
                    "decompose":[]
                })
            for event_entry in entry["decompose"]:
                decompose_examples[idx]["decompose"].append(
                        DecomposeEntry.model_validate(event_entry).model_dump_json().replace("{", "{{").replace("}", "}}")
                        # json.dumps(event_entry).replace("{", "{{").replace("}", "}}")
                    )
        example_prompt = PromptTemplate(
            input_variables=["event", "cur_activity", "decompose"],
            template=self._decompose_prompts["example_prompt"]
        )

        ## event decompose few-shots examples
        decompose_parser = PydanticOutputParser(pydantic_object=Decompose)
        
        prompt = FewShotPromptTemplate(
            examples=decompose_examples,
            example_prompt=example_prompt,
            prefix=self._decompose_prompts["re_prefix"] if re_decompose else self._decompose_prompts["prefix"],
            suffix=self._decompose_prompts["suffix"],
            input_variables=['description', 'intervention', 'past_activity_summary','cur_activity', 'cur_event', 'cur_time', 'end_time'],
            partial_variables={"format_instructions": decompose_parser.get_format_instructions()},
        )

        chain = LLMChain(
            llm=ChatOpenAI(
                    api_key=CONFIG["openai"]["api_key"],
                    organization=CONFIG["openai"]["organization"],
                    model_name=CONFIG["openai"]["model-turbo"],
                    temperature=llm_temperature,
                    verbose=self._verbose,
                ),
                prompt=prompt,
            )
        
        results = chain.invoke(input={
            'description':self.long_memory.description,
            'intervention':self.long_memory.intervention,
            'name': self.long_memory.name,
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
            records_str += f"[{record['time']}] Event[{record['schedule_event']}] Activity[{record['activity']}] Location[{record['location']}]\n"
        if not records_str:
            records_str += "No Records."

        request = chat_prompt.format_prompt(records = records_str).to_messages()

        model = ChatOpenAI(
                api_key=CONFIG["openai"]["api_key"],
                organization=CONFIG["openai"]["organization"],
                model_name=CONFIG["openai"]["model"],
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
                    # self.status = "error"
                    return []
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
                    model_name=CONFIG["openai"]["model"],
                    temperature=llm_temperature,
                    verbose=self._verbose,
                ),
                prompt=prompt,
            )
        
        results = chain.invoke(input={
            'description' : self.long_memory.description,
            'home_addr' : self.long_memory.home_addr,
            'work_addr' : self.long_memory.work_addr,
            'loc_hist' : self._summarize_mmdata(self.short_memory.fetch_location_records(num_items=30)),
            'decompose' : json.dumps(decompose),
            'cur_time' : self.short_memory.cur_time,
        }, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})

        response = results['text'].replace("24:00", "23:59")
        return location_parser.parse(response)


    def _predict_heartrate(self, decompose) -> HeartRate:
        # heartrate = self._predict_heartrate_chat(decompose)
        # return heartrate
        for try_idx in range(self._retry_times):
            try:
                heartrate = self._predict_heartrate_chat(decompose)
            except:
                if try_idx + 1 == self._retry_times:
                    return {}
                else:
                    continue
            else:
                return heartrate
            
    def _predict_heartrate_chat(self, decompose, llm_temperature=1.0) -> HeartRate:
        hr_example = []
        for entry in self._mmdata_prompts['heartrate_example']:
            # print(entry)
            hr_example.append({
                    "age": entry["age"],
                    "cur_hr": entry["cur_hr"],
                    "activity": entry["activity"],
                    "mean": entry["mean"],
                    "std": entry["std"],
                })
        example_prompt = PromptTemplate(
            input_variables=["cur_hr", "activity", "mean", "std"],
            template=self._mmdata_prompts["heartrate_example_prompt"]
        )

        hr_parser = PydanticOutputParser(pydantic_object=HeartRate)
        
        prompt = FewShotPromptTemplate(
            examples=hr_example,
            example_prompt=example_prompt,
            prefix=self._mmdata_prompts["heartrate_prefix"],
            suffix=self._mmdata_prompts["heartrate_suffix"],
            input_variables=['description', 'hr_hist', 'decompose', 'cur_time', 'cur_hr', 'age', 'disease'],
            partial_variables={"format_instructions": hr_parser.get_format_instructions()},
        )

        chain = LLMChain(
            llm=ChatOpenAI(
                    api_key=CONFIG["openai"]["api_key"],
                    organization=CONFIG["openai"]["organization"],
                    model_name=CONFIG["openai"]["model"],
                    temperature=llm_temperature,
                    verbose=self._verbose,
                ),
                prompt=prompt,
            )
        
        results = chain.invoke(input={
            'description' : self.long_memory.description,
            'hr_hist' : self._summarize_mmdata(self.short_memory.fetch_heartrate_records(num_items=60)),
            'decompose' : json.dumps(decompose),
            'cur_time' : self.short_memory.cur_time,
            'cur_hr' : self.short_memory.cur_heartrate,
            'age': self.long_memory.age,
            'disease': self.long_memory.disease,

        }, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})

        response = results['text'].replace("24:00", "23:59")
        return hr_parser.parse(response)
    

    def _predict_steps(self, decompose) -> Steps:
        for try_idx in range(self._retry_times):
            try:
                steps = self._predict_steps_chat(decompose)
            except:
                if try_idx + 1 == self._retry_times:
                    return {}
                else:
                    continue
            else:
                return steps
            
    def _predict_steps_chat(self, decompose, llm_temperature=1.0) -> Steps:
        hr_example = []
        for entry in self._mmdata_prompts['steps_example']:
            # print(entry)
            hr_example.append({
                    "age": entry["age"],
                    "activity": entry["activity"],
                    "steps": entry["steps"],
                })
        example_prompt = PromptTemplate(
            input_variables=["age", "activity", "steps"],
            template=self._mmdata_prompts["steps_example_prompt"]
        )

        steps_parser = PydanticOutputParser(pydantic_object=Steps)
        
        prompt = FewShotPromptTemplate(
            examples=hr_example,
            example_prompt=example_prompt,
            prefix=self._mmdata_prompts["steps_prefix"],
            suffix=self._mmdata_prompts["steps_suffix"],
            input_variables=['description', 'steps_hist', 'decompose', 'cur_time', 'age', 'disease'],
            partial_variables={"format_instructions": steps_parser.get_format_instructions()},
        )

        chain = LLMChain(
            llm=ChatOpenAI(
                    api_key=CONFIG["openai"]["api_key"],
                    organization=CONFIG["openai"]["organization"],
                    model_name=CONFIG["openai"]["model"],
                    temperature=llm_temperature,
                    verbose=self._verbose,
                ),
                prompt=prompt,
            )
        
        results = chain.invoke(input={
            'description' : self.long_memory.description,
            'steps_hist' : self._summarize_mmdata(self.short_memory.fetch_steps_records(num_items=60)),
            'decompose' : json.dumps(decompose),
            'cur_time' : self.short_memory.cur_time,
            'age': self.long_memory.age,
            'disease': self.long_memory.disease,

        }, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})

        response = results['text'].replace("24:00", "23:59")
        return steps_parser.parse(response)


    def _predict_botusage(self, decompose) -> Chatbot:
        # usage = self._predict_botusage_chat(decompose)
        # return {}
        for try_idx in range(self._retry_times):
            try:
                usage = self._predict_botusage_chat(decompose)
            except:
                if try_idx + 1 == self._retry_times:
                    return {}
                else:
                    continue
            else:
                return usage
    
    def _predict_botusage_chat(self, decompose, llm_temperature=1.0) -> Chatbot:
        chat_example = []
        for entry in self._mmdata_prompts['chatbot_example']:
            # print(entry)
            chat_example.append({
                    "chat": entry["chat"],
                })
        example_prompt = PromptTemplate(
            input_variables=["chat",],
            template=self._mmdata_prompts["chatbot_example_prompt"]
        )

        usage_parser = PydanticOutputParser(pydantic_object=Chatbot)
        
        prompt = FewShotPromptTemplate(
            examples=chat_example,
            example_prompt=example_prompt,
            prefix=self._mmdata_prompts["chatbot_prefix"],
            suffix=self._mmdata_prompts["chatbot_suffix"],
            input_variables=['description', 'preference', 'chat_hist', 'decompose', 'cur_time'],
            partial_variables={"format_instructions": usage_parser.get_format_instructions()},
        )

        chain = LLMChain(
            llm=ChatOpenAI(
                    api_key=CONFIG["openai"]["api_key"],
                    organization=CONFIG["openai"]["organization"],
                    model_name=CONFIG["openai"]["model"],
                    temperature=llm_temperature,
                    verbose=self._verbose,
                ),
                prompt=prompt,
            )
        
        results = chain.invoke(input={
            'description' : self.long_memory.description,
            'preference' : self.long_memory.chatbot_preference,
            'chat_hist' : self._summarize_mmdata(self.short_memory.fetch_chatbot_records(num_items=60)),
            'decompose' : json.dumps(decompose),
            'cur_time' : self.short_memory.cur_time,
        }, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})

        response = results['text'].replace("24:00", "23:59")
        # print(response)
        return usage_parser.parse(response)


    def _summarize_mmdata(self, records):
        human_prompt = HumanMessagePromptTemplate.from_template(self._utils_prompts["mmdata_summary"])
        chat_prompt = ChatPromptTemplate.from_messages([human_prompt])

        request = chat_prompt.format_prompt(records = json.dumps(records)).to_messages()

        model = ChatOpenAI(
                api_key=CONFIG["openai"]["api_key"],
                organization=CONFIG["openai"]["organization"],
                model_name=CONFIG["openai"]["model"],
                temperature=0.5,
                verbose=self._verbose
            )
        results = model.invoke(request, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})
        if CONFIG["debug"]: print(results.content)
        return results.content
    
    def _generate_chatbot_preference(self):
        human_prompt = HumanMessagePromptTemplate.from_template(self._utils_prompts["chatbot_preference"])
        chat_prompt = ChatPromptTemplate.from_messages([human_prompt])

        request = chat_prompt.format_prompt(description = self.long_memory.description).to_messages()

        model = ChatOpenAI(
                api_key=CONFIG["openai"]["api_key"],
                organization=CONFIG["openai"]["organization"],
                model_name=CONFIG["openai"]["model"],
                temperature=1.5,
                verbose=self._verbose
            )
        results = model.invoke(request, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})
        if CONFIG["debug"]: print(results.content)
        return results.content


    def set_intervention(self, plan):
        self.long_memory.intervention = plan


    def save_info(self):
        info = self.long_memory.info

        info["schedule"] = self.short_memory.schedule

        with open(os.path.join(self.agent_folder, "info.json"), "w") as f:
            json.dump(info, fp=f)
    
    def save_activity(self):
        self._output_cache += self.short_memory.csv_record()

        if len(self._output_cache) >= self._output_cache_length:
            with open(self._out_activity_file, "a+") as f:
                f.write(self._output_cache)
            self._output_cache = ""

    def _categorize_activity(self, _file, retry=10):
        act_data = pd.read_csv(_file, dtype=str)
        act_list = [i[0] for i in act_data[["activity"]].value_counts().index.to_list()]

        for try_idx in range(retry):
            try:
                act_map = self._categorize_activity_chat(act_list)
            except:
                if try_idx + 1 == self._retry_times:
                    return 0
                else:
                    continue
            else:
                act_map = act_map.dump_dict()
                act_data["catalogue"] = act_data["activity"].map(act_map)
                act_data["catalogue"] = act_data["catalogue"].fillna("Other activities, not elsewhere classified")
                act_data.to_csv(_file, index=False)
                break

    def _categorize_activity_chat(self, act_list) -> catalogueMap:
        human_prompt = HumanMessagePromptTemplate.from_template(self._utils_prompts["categorize_activity"])
        chat_prompt = ChatPromptTemplate.from_messages([human_prompt])

        catalogue_parser = PydanticOutputParser(pydantic_object=catalogueMap)

        request = chat_prompt.format_prompt(
                catalogue = self.labels,
                activities = json.dumps(act_list),
                format_instructions = catalogue_parser.get_format_instructions()
            ).to_messages()

        model = ChatOpenAI(
                api_key=CONFIG["openai"]["api_key"],
                organization=CONFIG["openai"]["organization"],
                model_name=CONFIG["openai"]["model"],
                temperature=0.3,
                verbose=self._verbose
            )
        results = model.invoke(request, config={"callbacks": [CustomHandler(verbose=CONFIG["debug"])]})
        if CONFIG["debug"]: print(results.content)

        act_map = catalogue_parser.parse(results.content)

        return act_map

    def _update_catalogue(self, file_list):
        for file in file_list:
            self._categorize_activity(file)


    def update_catalogue(self, file_list):
        thread = threading.Thread(target=self._update_catalogue, args=[file_list])
        thread.start()


    def _smooth_heartrate(self, _file):
        act_data = pd.read_csv(_file, dtype=str)
        hr_list = act_data['heartrate'].to_numpy(np.float16)

        smoothed_heart_rates = savgol_filter(hr_list, window_length=10, polyorder=3)

        act_data['heartrate'] = smoothed_heart_rates.astype(int)

        act_data.to_csv(_file, index=False)


    def _avoid_nan(self, _file):
        act_data = pd.read_csv(_file, dtype=str)

        act_data["location"] = act_data["location"].fillna(self.long_memory.home_addr)
        act_data["longitude"] = act_data["longitude"].fillna(self.long_memory.info['home_longitude'])
        act_data["latitude"] = act_data["latitude"].fillna(self.long_memory.info['home_latitude'])

        act_data.to_csv(_file, index=False)


    def save_hist(self):
        with open(self._out_activity_file, "a+") as f:
            f.write(self._output_cache)
        self._output_cache = ""

        target_file = os.path.join(self.activity_folder, self.short_memory.cur_date + ".csv")
        os.replace(self._out_activity_file, target_file)

        with open(self._out_activity_file, "w") as f:
            f.write("time,activity,event,location,longitude,latitude,heartrate,chatbot,steps\n")

        self._smooth_heartrate(target_file)
        self._categorize_activity(target_file)
        self._avoid_nan(target_file)


    def save_thoughts(self, prefix, thoughts):
        self._thoughts_cache += f"\n===================================={prefix}=========================================\n"
        self._thoughts_cache += thoughts
        self._thoughts_cache += "\n=================================================================================================================\n"

        if len(self._thoughts_cache) >= self._thoughts_cache_length:
            with open(self._out_thoughts_file, "a+") as f:
                f.write(self._thoughts_cache)
            self._thoughts_cache = ""

    def save_thoughts_log(self):
        with open(self._out_thoughts_file, "a+") as f:
            f.write(self._thoughts_cache)
        self._thoughts_cache = ""

        target_file = os.path.join(self.thoughts_folder, self.short_memory.cur_date + ".txt")
        os.replace(self._out_thoughts_file, target_file)


    def save_cache(self):
        self.short_memory.save_cache()
        self.long_memory.save_cache()

    def load_cache(self):
        self.short_memory.load_cache()
        self.long_memory.load_cache()



if __name__ == "__main__":
    brain = Brain(
        user_folder="/Users/timberzhang/Documents/Documents/Long-SimulativeAgents/Code/SimulPaPa/.Users/ad458d15-76fa-3cd2-827c-2838c0e24a8b",
        agent_folder="/Users/timberzhang/Documents/Documents/Long-SimulativeAgents/Code/SimulPaPa/.Users/ad458d15-76fa-3cd2-827c-2838c0e24a8b/agents/1",
    )
    brain.init_brain()
    brain.plan()


