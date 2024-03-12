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
    def __init__(self, user_folder, agent_folder, info) -> None:
        self.user_folder = user_folder
        self.agent_folder = agent_folder
        self.info = info

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

        ## examples
        self.have_examples = False
        if os.path.exists(os.path.dirname(os.path.abspath(__file__))+"/examples.json"):
            self.have_examples = True
            with open(os.path.dirname(os.path.abspath(__file__))+"/examples.json") as f:
                self.examples = json.load(f)

            

    def init_brain(self):
        self.long_memory = LongMemory(user_folder=self.user_folder, agent_folder=self.agent_folder)
        self.short_memory = ShortMemory(agent_folder=self.agent_folder, info=self.info)

        if not self.long_memory.memory_tree["user_chatbot_pref"]:
            self.long_memory.memory_tree["user_chatbot_pref"] = self._summary_user_chatbot_preference()
        if not self.long_memory.memory_tree["agent_chatbot_pref"]:
            self.long_memory.memory_tree["agent_chatbot_pref"] = self._generate_agent_chatbot_preference()


    def plan(self, days:int=1, type:str="new"):
        
        planing_days = []
        if type=="new":
            user_last_day = self.long_memory.fetch_user_lastday()
            for i in range(1, days+1):
                planing_day = datetime.strptime(user_last_day, '%m-%d-%Y') + timedelta(days=i)
                planing_days.append(planing_day.strftime('%m-%d-%Y'))
            cur_time = "00:00"
        elif type=="continue":
            self.short_memory.load_cache()
            self.long_memory.load_cache()
            agent_last_day = self.short_memory.get_today()
            cur_time = self.short_memory.get_cur_time()
            for i in range(0, days):
                planing_day = datetime.strptime(agent_last_day, '%m-%d-%Y') + timedelta(days=i)
                planing_days.append(planing_day.strftime('%m-%d-%Y'))
        else:
            raise Exception("plan type error!")
        

        for i in range(days):
            if cur_time=="00:00":
                self.short_memory.set_today(planing_days[i])
                self.short_memory.set_purpose(self._define_one_day_purpose())
                self.long_memory.record_daily_purpose(self.short_memory.get_today(), self.short_memory.get_today_purpose())

                # _schedule = self._create_halfhour_activity()
                _schedule = self._create_halfhour_range_activity()
                if CONFIG['debug']: print(_schedule)
                self.short_memory.set_schedule(_schedule)

            self._shift_window_pred(cur_time)

            self.long_memory.update_memory()
            self.short_memory.save_pred_file()
            self.short_memory.clear_cache()
            cur_time = "00:00"


    def _summary_user_chatbot_preference(self):

        chat_history = self.long_memory.fetch_user_chat_hist()

        prompt = self.long_memory.user_description
        prompt += f"In the past several days, {self.long_memory.user_info['name']} had several interactions with Alexa chatbot. "
        prompt += f"Here is a json format chat history, the key is the chat time(format as MM-DD-YYYY-hh:mm), the value is the content of the conversation. "
        prompt += json.dumps(chat_history)
        prompt += f"Based on personal information and past chat history, can you summarize the chatbot usage preference of {self.long_memory.user_info['name']}. "
        prompt += "In order to better describe the preferences, here are some example question may describe a user's preference. "
        prompt += "1. How often do users use chatbot(times/week or times/day)? 2. During what period of time do users use chatbot? "
        prompt += "3. What topics do users talk about when using the chatbot (there may be several options)? "
        prompt += "4. What conversation topics will get positive responses from users (there may be several options)? "
        # prompt += "5. If available, you can choose some typical Question-Answer pairs to include in your answer."
        prompt += "Despite these points, there may also be other descriptions that illustrates the user preference. "
        prompt += "You need to figure out more aspects that may help understanding the user's usage prefernce. "
        prompt += "To make the estimation more detailed, you can imagine that you are a product manager who want to build up a user profile for a chatbot. "
        prompt += "Limit your answer in 50 words and format as: 1 : desciprtion, ..., n : description. You could ignore the name in your answer so that you could provide more useful words."

        if CONFIG['debug']:   print(prompt)

        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"],
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG['debug']:   print(completion.choices[0].message.content)
        return completion.choices[0].message.content


    def _generate_agent_chatbot_preference(self):
        prompt = "---\n"
        prompt += self.long_memory.user_description
        prompt += "\n"
        prompt += f"Here are some points describing {self.long_memory.user_info['name']}'s usage preference of using Alexa chatbot: \n"
        prompt += self.long_memory.memory_tree["user_chatbot_pref"]
        prompt = "\n---\n"
        prompt += "There are some potential connections here between chatbot usage preferences and personal information. "
        prompt += f"Now, Alexa want to depict a new usage prefernce for {self.long_memory.user_info['name']}. {self.long_memory.user_description} \n"
        prompt += "In order to better describe the preferences, here are some example question may describe a user's preference. "
        prompt += "1. How often do users use chatbot(times/week or times/day)? 2. During what period of time do users use chatbot? "
        prompt += "3. What topics do users talk about when using the chatbot (there may be several options)? "
        prompt += "4. What conversation topics will get positive responses from users (there may be several options)? "
        # prompt += "5. If available, you can choose some typical Question-Answer pairs to include in your answer."
        prompt += "Despite these points, there may also be other descriptions that illustrates the user preference. "
        prompt += "You need to figure out more aspects that may help understanding the user's usage prefernce. "
        prompt += "To make the estimation more detailed, you can imagine that you are a product manager who want to build up a user profile for a chatbot. "
        prompt += "Limit your answer in 50 words and format as: 1 : desciprtion, ..., n : description. You could ignore the name in your answer so that you could provide more useful words."

        if CONFIG['debug']:   print(prompt)

        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG['debug']:  print(completion.choices[0].message.content)
        return completion.choices[0].message.content


    ########################
    ####
    #### Daily level planing
    ####
    ########################
    def _define_one_day_purpose(self):
        prompt = self.long_memory.description
        prompt += f"Today is {self.short_memory.memory_tree['today']}. "
        prompt += f"For last {self.retrieve_days} days, {self.long_memory.info['name']}'s main purpose of every day is "
        prompt += f"{self.long_memory.past_daily_purpose(self.short_memory.memory_tree['today'], self.retrieve_days)}. "
        prompt += "Fisrtly, based on the daily purpose of past days and personal information, plus your knowledge about the date of today, what will be the new new purpose of today? "
        prompt += "To think about the new purpose, let's think step bu step:\n"
        prompt += f"step 1: in the past days, {self.long_memory.info['name']} mostly did what? Like, design a new product, travel to the national park. \n"
        prompt += f"step 2: Today is a weekday or weekend?\n"
        prompt += f"step 3: since {self.long_memory.info['name']} has done such things, what could be the next step? "
        prompt += "Like, correspondingly, talk about the new product to teammates, stay at home and Photoshop the pictures, or if he/she is illed so that plan a trip to hospital.\n"
        prompt += f"step 4: Summarize the new daily purpose. \n"
        # prompt += "On the other hand,  including occupation and physical status, may also influence the decision of the daily purpose. "
        # prompt += "For example, product manager will design product, but software engineer will program; Someone is illed, he/she may go to hospital. "
        # prompt += "Combined with your knowledge about the date of today, what do you think about the main purpose of today. "
        prompt += f"Return your answer without any other information: "

        if CONFIG['debug']: print(prompt)
        completion = self.gpt_client.chat.completions.create(
            model=CONFIG["openai"]["model"], 
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG['debug']:  print(completion.choices[0].message.content)
        return completion.choices[0].message.content
    

    def _create_halfhour_activity(self):
        # hourly_schedule = {f"{i}:00":"to_be_determined" for i in range(24)}
        schedule = { }
        for h in range(24):
            for m in ["00", "30"]:
            # for m in ["00", "10", "20", "30", "40", "50"]:
                _time = datetime.strptime(f"{h}:{m}", "%H:%M")
                schedule[datetime.strftime(_time, "%H:%M")] = "[Fill in]"

        prompt = self.long_memory.description
        prompt += f"{self.short_memory.today_summary()}. "
        prompt += f"Now, {self.long_memory.info['name']} want to determine a schedule for today. "
        # prompt += f"For past {self.retrieve_days}, {self.long_memory.info['name']}'s daily schedules are: "
        # prompt += f"{self.long_memory.past_daily_schedule()}"
        prompt += "Based on personal information and past daily purpose, combined with your knowledge about the date of today, can you fill the schedule? "
        prompt += "Please make your plan as detailed as possible, using a phrase about 3-5 words, except sleep you can just use \"Sleep\", "
        prompt += "here are some examples of the activities: "
        prompt += "wake up, complete the morning routine, eat breakfast, read a book, take a nap, relax, prepare for bed, and so on. "
        prompt += "You need to be creative to imagine what else could do besides these examples. "
        prompt += "Return your answer in the following JSON format without any other information: "
        prompt += json.dumps(schedule)

        # if CONFIG['debug']: print(prompt)
        # completion = self.gpt_client.chat.completions.create(
        #     model=CONFIG["openai"]["model"], 
        #     messages=[{
        #         "role": "system", "content": "You are a helpful assistant to design daily schedules for the olderly.",
        #         "role": "user", "content": prompt
        #         }]
        # )
        # if CONFIG['debug']:  print(completion.choices[0].message.content)
        # return json.loads(completion.choices[0].message.content)

        success, response = safe_chat(prompt=prompt)
        if success:
            return response
        else:
            raise Exception("GPT Chat response error. \n" + prompt + "\n" + response)
    

    def _create_halfhour_range_activity(self):
        prompt = self.long_memory.description
        prompt += f"{self.short_memory.today_summary()}. "
        prompt += f"Now, {self.long_memory.info['name']} want to determine a schedule for today. "
        # prompt += f"For past {self.retrieve_days}, {self.long_memory.info['name']}'s daily schedules are: "
        # prompt += f"{self.long_memory.past_daily_schedule()}"
        prompt += "Based on personal information and past daily purpose, combined with your knowledge about the date of today, can you fill the schedule? "
        prompt += "The schedule should start from 00:00, and end at 23:59, with each time period has a duration of 15 minutes or multiples thereof. "
        prompt += "for example \"00:00-07:30\":\"sleep\", \"07:30-08:00\":\"shower\", \"10:00-12:00\":\"work\", \"15:45-16:00\":\"coffee break\""
        prompt += "And of course, everyday will start with sleep and end with sleep. "
        prompt += "You need to consider the relationship between each adjacent activities, and make sure that the time is reasonable and enough to finish that activity. "
        prompt += "Like, if you want to commute for somewhere, you need to think about the transportation tool (bus, car, subway) and distance to decide the time for commute. "
        prompt += "Or, if you plan to have a break for afternoon tea, maybe you need just 15 minutes. "
        prompt += "Please make your plan as detailed as possible, using a phrase about 5 words. Except sleep or sleep-related activities you can just use \"Sleep\" or \"sleep\". "
        if self.have_examples:
            if "schedule" in self.examples.keys():
                if "event" in self.examples["schedule"]:
                    prompt += "\nHere are some examples of the activities: "
                    prompt += self.examples["schedule"]["event"]
                    prompt += " You need to be creative to imagine what else could do besides these examples. \n"
                if ("purpose" in self.examples["schedule"]) and ("schedule" in self.examples["schedule"]):
                    prompt += "\nHere is pair of daily purpose and schdule example: \n"
                    prompt += f"Daily purpose:\n{self.examples['schedule']['purpose']}\n"
                    prompt += f"Schedule:\n{self.examples['schedule']['schedule']}\n"
        prompt += "Return your answer in the following JSON format without any other information: "
        prompt += "{\"[00:00]-[end_time_HH:MM]\":\"activity\", \"[start_time_HH:MM]-[end_time_HH:MM]\":\"activity\", ..., \"[start_time_HH:MM]-[23:59]\":\"activity\"}"

        # if CONFIG['debug']: print(prompt)
        # completion = self.gpt_client.chat.completions.create(
        #     model=CONFIG["openai"]["model"], 
        #     messages=[{
        #         "role": "system", "content": "You are a helpful assistant to design daily schedules for the olderly.",
        #         "role": "user", "content": prompt
        #         }]
        # )
        # if CONFIG['debug']:  print(completion.choices[0].message.content)
        # return json.loads(completion.choices[0].message.content)
        success, response = safe_chat(prompt=prompt)
        if success:
            return response
        else:
            raise Exception("GPT Chat response error. \n" + prompt + "\n" + response)


    ########################
    ####
    #### minutes level planing & data estimation
    ####
    ########################
    def _shift_window_pred(self, cur_time=None):
        #### Start at midnight
        if cur_time:
            current_time = datetime.strptime(cur_time, "%H:%M")
        else:
            current_time = datetime.strptime("00:00", "%H:%M")

        #### Circulate through 24 hours in 5-minute increments
        while current_time < datetime.strptime("23:59", "%H:%M"):

            new_slot = self.short_memory.set_current_time(current_time)
            #### activity in prediction
            # self._decide_cur_activity()
            #### activity by decomposing
            if new_slot:
                self._decompose_task(new_slot["slot"], new_slot["event"])
            self._decide_decomposed_task()

            print(self.short_memory.memory_tree["cur_time"], self.short_memory.memory_tree["cur_activity"])
            # print(self.short_memory.memory_tree["cur_schedule"], self.short_memory.memory_tree["cur_halfhour"])
            
            ### Multi-modality prdiction
            self._predict_heartrate()
            if current_time.minute // 30 == 0:
                self._predict_chatbot(pred_minutes=30)
            self._predict_location()
            current_time += timedelta(minutes=5)


            ### regular save
            if current_time.minute==0:
                self.long_memory.save_cache()
                self.short_memory.save_cache()
                self.short_memory.save_pred_file()


    def _decide_decomposed_task(self):
        cur_decomposed = self.short_memory.fetch_task_decompose()

        _activity = list(cur_decomposed.keys())[0]
        _duration = int(cur_decomposed[_activity])

        if _duration > 0:
            cur_decomposed[_activity] = str(_duration - 5)
        elif len(cur_decomposed.keys()) < 2:
            _activity = _activity
        else:
            _activity = list(cur_decomposed.keys())[1]
            cur_decomposed[_activity] = str(int(cur_decomposed[_activity]) - 5)
            del cur_decomposed[list(cur_decomposed.keys())[0]]
            self.short_memory.set_task_decompose(cur_decomposed)
        activity = _activity

        self.short_memory.set_current_activity(activity=activity)


    def _decide_cur_activity(self):
        if "sleep" in self.short_memory.get_current_schedule().lower():
            self.short_memory.set_current_activity(activity="sleep")
        else:
            prompt = self.long_memory.description
            prompt += self.short_memory.today_summary()
            prompt += self.short_memory.cur_time_summary()
            prompt += self.short_memory.cur_schedule_summary()
            prompt += self.short_memory.past_activities_summary(min=30)
            # prompt += self.long_memory.past_activities_summary(cur_time=, halfhour=, items=)
            prompt += f"Now, {self.long_memory.info['name']} need to decide an activity for next 5 minutes. "
            prompt += f"Do you think what is the best activity based on {self.long_memory.info['name']}'s plan of today and past activities. "
            prompt += "Firstly, the plan of current time period is most important for decision, you need choose an activity that can be done within this time period. "
            prompt += "For example during the work hour you may text to manager, join a meeting, write a e-mail; during morning routine, you may dress up, brush teeth, take a shower. "
            prompt += "And the coherence between activities are also important, for example if you eat food in last 5 miutes, you cannot do sports in the next 5 minutes. "
            prompt += "Secondly, you need to carefully think about the last activity, since not some activities may take a longer time, for example hold a meeting for 60 minutes. "
            prompt += "But there may also be some could be done in a short time, for example take a coffee break for 10 minutes, check e-mails for 5 minutes. "
            prompt += "Your choice of activity should be specific using a short phrase about 5 words to better describe the work you are doing. "
            if self.have_examples:
                prompt += "\nHere are some examples of the activity: \n"
                prompt += self.examples["activity"]["activity"]
                prompt += "\n"
            prompt += "Return your answer in the following JSON format without any other information: "
            prompt += "{\"activity\":\"[Fill in]\"}"

            # if CONFIG['debug']: print(prompt)
            # completion = self.gpt_client.chat.completions.create(
            #     model=CONFIG["openai"]["model"], 
            #     messages=[{
            #         "role": "user", "content": prompt
            #         }]
            # )
            # if CONFIG['debug']:  print(completion.choices[0].message.content)
            # activity = json.loads(completion.choices[0].message.content)["activity"]
            success, response = safe_chat(prompt=prompt)
            if success:
                self.short_memory.set_current_activity(activity=response["activity"])
            else:
                self.short_memory.set_current_activity(activity=self.short_memory.get_current_schedule())
            


    def _predict_heartrate(self, pred_minutes=10):
        prompt = self.long_memory.description
        prompt += self.short_memory.cur_time_summary()
        prompt += self.short_memory.cur_activity_summary()
        prompt += self.short_memory.past_activities_summary()

        # summary past X miutes heartrate
        hr_summary, lack = self.short_memory.past_heartrate_summary(min=60)
        if lack>0:
            time_start = datetime.strptime(self.short_memory.memory_tree['cur_time'], "%H:%M") - timedelta(minutes=lack)
            last_day = datetime.strptime(self.short_memory.memory_tree['today'], "%m-%d-%Y") - timedelta(days=1)
            hr_summary += self.long_memory.past_heartrate_summary(
                    date=datetime.strftime(last_day, "%m-%d-%Y"), 
                    time_start=datetime.strftime(time_start, "%H:%M"),
                    min=lack
                )
        prompt += hr_summary

        # heart rate in this period in last prediction
        prompt += self.short_memory.pred_heartrate_summary()
        
        # summary period heart rate in past X days in XX:XX-XX:XX
        prompt += self.long_memory.past_period_heartrate_summary(
                cur_date=self.short_memory.memory_tree['today'], 
                days=7,
                time_start=self.short_memory.memory_tree['cur_time'],
                mins=10
            )

        #
        #
        # TODO relevent activities
        #
        #

        prompt += f"Now, you need to predict {self.long_memory.info['name']}'s heart rate for next {pred_minutes} minutes, with 1 minute increment. "
        prompt += "There may be some useful information about the heart rate in the past records or same time in past days. "
        prompt += f"There may be some useful information during relevent or similar activities, these records may indicate that {self.long_memory.info['name']}'s heart rate value in similar conditions. "
        prompt += f"You need to be careful about the age and physical status of {self.long_memory.info['name']}. "
        prompt += f"And also, you need to consider what {self.long_memory.info['name']} is doing or just did, the heart rate may be influenced by the activities. "
        prompt += "The heart rate also needs to be consistent with physiological facts. "
        prompt += "It is unlikely to remain the same in a short period of time, but fluctuates up and down within a reasonable range. "
        prompt += "And the prediction should also be reasonable in realistic scenario, like the heart rate may not skyrocket in a short time. "
        prompt += f"There may also be first {pred_minutes//2} minutes of predcition in your last prediction, which may provide some useful information for you. "
        prompt += f"This prediction may be based on past activities and time in past {pred_minutes//2} minutes. Based on current status of time and activity, you may make some changes. "
        prompt += "Return your answer in the following JSON format without any other information: "

        pred_dict = {}
        for i in range(pred_minutes):
            _time = datetime.strptime(self.short_memory.memory_tree['cur_time'], "%H:%M") + timedelta(minutes=i)
            pred_dict[datetime.strftime(_time, "%H:%M")] = "integer_heartrate"
        prompt += json.dumps(pred_dict)

        # if CONFIG['debug']: print(prompt)
        # completion = self.gpt_client.chat.completions.create(
        #     model=CONFIG["openai"]["model"], 
        #     messages=[{
        #         "role": "system", "content": "You are a wearable watch recoding heart rate.",
        #         "role": "user", "content": prompt
        #         }]
        # )
        # if CONFIG['debug']:  print(completion.choices[0].message.content)

        success, pred = safe_chat(prompt=prompt)
        if success:
            self.short_memory.set_current_heartrate(pred, pred_minutes)
        else:
            for key in pred_dict:
                pred_dict[key] = 0
            self.short_memory.set_current_heartrate(pred_dict, pred_minutes)


    def _predict_chatbot(self, pred_minutes=10, past_hours=2, last_days=5, last_hours=2):
        if "sleep" in self.short_memory.get_current_activity().lower():
            return 0
        else:
            prompt = self.long_memory.description
            prompt += f"{self.long_memory.info['name']}'s usage preference of using Alexa chatbot is: "
            prompt += self.long_memory.memory_tree["agent_chatbot_pref"]
            prompt += "\n"
            prompt += self.short_memory.cur_time_summary()
            prompt += self.short_memory.cur_activity_summary()
            prompt += self.short_memory.past_activities_summary()

            prompt += f"Here is a summary of Chatbot records in the past {past_hours} hours: "
            prompt += self._summary_chatbot_history(self.short_memory.past_chatbot_records(hour=past_hours))
            prompt += "\n"
            prompt += self.short_memory.pred_chatbot_summary()
            prompt += "\n"

            prompt += f"Here is a summary of Chatbot records in the last {last_days} days during recent {last_hours} hours: "
            prompt += self._summary_chatbot_history(self.long_memory.past_period_chatbot_summary(
                    cur_date=self.short_memory.memory_tree['today'], 
                    days=last_days,
                    time_start=self.short_memory.memory_tree['cur_time'],
                    hours=last_hours
                ))

            prompt += f"Now, imagine you are the Chatbot, you need to predict that if {self.long_memory.info['name']} will use Chatbot in the next {pred_minutes} minutes. "
            prompt += "If he/she will use Chatbot, what question would be asked, and based on the question what would you respond. "
            prompt += f"{self.long_memory.info['name']}'s Chatbot usage preference is imporatant. The frequency and topics are the most import factors that may impact the usage. "
            prompt += f"The useage frequency should match the user's usage preference. The records in past {past_hours} hours could restrict your prediction to match the prefernece frequency. "
            prompt += "For example, if someone only uses chatbot several times per week, he/she may only use one or two times in one day. This means that if he/she used Chatbot in the past few hours, he/she probably won't use it again."
            prompt += "Correspondingly, if someone use chatbot a lot of times per week, even per day, he/she may use it every hour if he/she wish to. "
            prompt += "Another important point is the current activity and time, the usage of the ChatBot (or the chat topic) must accord with the someone's current status. "
            prompt += "For example, during a meeting, someone cannot use ChatBot; during the morning routine, someone may ask the weather of today; during the commute to work, someone may ask about the trafic. "
            prompt += "And the usage records of last few days in the same time period may indicate if the user want to use the chatbot or what is the topic that may be talked currently. "
            prompt += f"There may also be first {past_hours//2} minutes of predcition in your last prediction, which may provide some useful information for you. "
            prompt += f"If you have predict the usage, you need to think why you made that decision based on past activities and time in past {pred_minutes//2} minutes. "
            prompt += "Based on current status of time and activity, you may make some changes. "
            # prompt += "If you think there will be a interaction, you must to think about the following question: \n"
            # prompt += "1. What is the topic of this conversation?\n"
            # prompt += "2. Based on this topic, what should you ask?\n"
            # prompt += "3. How could you generate a gentle utterance that may get positive response?\n"
            # prompt += "4. How long will the conversation last? Some conversation may happen in 1 min, others may not.\n"
            if self.have_examples:
                if "chat_conv" in self.examples.keys():
                    prompt += "Here are some examples of the conversation that may help you:\n"
                    for conv in self.examples["chat_conv"]:
                        prompt += conv
                        prompt += "\n"
            prompt += "Return your answer in the following JSON format without any other information: "

            pred_dict = {}
            for i in range(pred_minutes):
                _time = datetime.strptime(self.short_memory.memory_tree['cur_time'], "%H:%M") + timedelta(minutes=i)
                pred_dict[datetime.strftime(_time, "%H:%M")] = {
                    "if_chat":"[Fill True_or_False]", 
                    "conversation":"[Fill conversation if need chat]"}
            prompt += json.dumps(pred_dict)

            # if CONFIG['debug']: print(prompt)
            # completion = self.gpt_client.chat.completions.create(
            #     model=CONFIG["openai"]["model"], 
            #     messages=[{
            #         "role": "user", "content": prompt
            #         }]
            # )
            # if CONFIG['debug']: print(completion.choices[0].message.content)
            # pred = safe_load_gpt_content(completion.choices[0].message.content, prompt)
            success, pred = safe_chat(prompt=prompt)
            if success:
                self.short_memory.set_current_chatbot(pred, pred_minutes)
            else:
                for key in pred_dict:
                    pred_dict[key]["if_chat"] = "False"
                self.short_memory.set_current_chatbot(pred_dict, pred_minutes)


    def _predict_location(self, pred_minutes=10):
        prompt = self.long_memory.description
        # prompt += f"The longitude and latitude of the home of {self.long_memory.info['name']} is {self.long_memory.info['home_longitude']} and {self.long_memory.info['home_latitude']}. "
        # prompt += f"The longitude and latitude of the company building of {self.long_memory.info['name']} is {self.long_memory.info['work_longitude']} and {self.long_memory.info['work_latitude']}. "
        prompt += self.short_memory.cur_time_summary()
        prompt += self.short_memory.cur_activity_summary()

        prompt += self._summary_location_history(self.short_memory.past_location_summary())

        prompt += self.short_memory.pred_location_summary()


        # prompt += self.long_memory.past_period_location_summary(
        #         cur_date=self.short_memory.memory_tree['today'], 
        #         days=5,
        #         time_start=self.short_memory.memory_tree['cur_time'],
        #         mins=5
        #     )
        # prompt += self.long_memory.past_activity_location_summary(
        #         cur_date=self.short_memory.memory_tree['today'], 
        #         days=5,
        #         activity=self.short_memory.memory_tree["cur_activity"]
        #     )

        prompt += f"Now, you need to predict {self.long_memory.info['name']}'s location in the next {pred_minutes} minutes, starting from {self.short_memory.memory_tree['cur_time']}."
        # prompt += f"Now, you need to predict {self.long_memory.info['name']}'s location (both the longitude and latitude) in the next 10 minutes, starting from {self.short_memory.memory_tree['cur_time']}. "
        prompt += f"You need to think carefully about {self.long_memory.info['name']}'s usual location in this time period and when doing similar activities. "
        # prompt += f"The home location and company location maybe the most frequent location that {self.long_memory.info['name']} may stay. "
        prompt += f"The home location and company address of {self.long_memory.info['name']} has provided. "
        prompt += "When predict the future location, you need to conside the current activity, for example, when commute to work the location should be on the route between home and company. "
        prompt += "Or, when doing exercise or travelling, the location may be at a gym near the company or a national park. "
        # prompt += "Worth to be noticed is that even staying in the same place, the longitude and latitude will slightly change based on current activity. "
        # prompt += "Like you are staying at home, but locations are different when you are sleeping or eating. "
        prompt += "On the other side, you need to think about if the usage is logical and reasonable, for example, you won't move too far from past location. "
        prompt += f"There may also be first {pred_minutes//2} minutes of predcition in your last prediction, which may provide some useful information for you. "
        prompt += f"This prediction may be based on past activities and time in past {pred_minutes//2} minutes. Based on current status of time and activity, you may make some changes. "
        if self.have_examples:
            if "location" in self.examples.keys():
                # prompt += "\nHere are some examples of the activity and corresponding location with their longitude and latitude: \n"
                prompt += "\nHere are some examples of the activity and corresponding location address: \n"
                for _item in self.examples["location"]:
                    prompt += _item + "\n"
        prompt += "Return your answer in the following JSON format without any other information: "

        pred_dict = {}
        for i in range(pred_minutes):
            _time = datetime.strptime(self.short_memory.memory_tree['cur_time'], "%H:%M") + timedelta(minutes=i)
            pred_dict[datetime.strftime(_time, "%H:%M")] = {
                "location" : "[real_address]", 
                # "longitude" : "[longitude_format_as_xx.xxxxxx]",
                # "latitude" : "[latitude_format_as_xx.xxxxxx]"
                }
        prompt += json.dumps(pred_dict)

        # if CONFIG['debug']: print(prompt)
        # completion = self.gpt_client.chat.completions.create(
        #     model=CONFIG["openai"]["model"], 
        #     messages=[{
        #         # "role": "system", "content": "Imagine that you are a wearable GPS that recodrs user's location changes.",
        #         "role": "user", "content": prompt
        #         }]
        # )
        # if CONFIG['debug']: print(completion.choices[0].message.content)
        # pred = safe_load_gpt_content(completion.choices[0].message.content, prompt)
        success, pred = safe_chat(prompt=prompt)
        if success:
            self.short_memory.set_current_location(pred, pred_minutes)
        else: 
            for key in pred_dict:
                pred_dict[key]["location"] = "Home"
                # pred_dict[key]["longitude"] = self.long_memory.info["home_longitude"]
                # pred_dict[key]["latitude"] = self.long_memory.info["home_latitude"]
            self.short_memory.set_current_location(pred_dict, pred_minutes)


    ########################
    ####
    #### tool functions
    ####
    ########################
    def _decompose_task(self, time_slot, event):
        time1 = datetime.strptime(time_slot.split("-")[0], "%H:%M")
        time2 = datetime.strptime(time_slot.split("-")[1], "%H:%M")
        duration = (time2 - time1).total_seconds() / 60

        prompt = self.long_memory.description
        prompt += self.short_memory.today_summary()
        prompt += self.short_memory.cur_time_summary()
        prompt += self.short_memory.cur_schedule_summary()
        prompt += f"In 5 min increments, list the subtasks {self.long_memory.info['name']} does when {self.long_memory.info['name']} is working on "
        prompt += f"{event} during {time_slot}. The duration of all subtask should fullfill current time slot, which is {duration} minutes. "
        if self.have_examples:
                if "task_decompose" in self.examples.keys():
                    prompt += "\nHere are some examples of how to decompose the work: \n"
                    prompt += self.examples["task_decompose"][0]
                    prompt += "\n"
        prompt += "Return your answer in the following JSON format, the key represents the subtask (description about 5 words), the value represents the duration time (minutes integer)."
        prompt += "Your answer should be without any other information. "
        prompt += "{\"subtask\":\"duration_minutes_in_integer\", ...}"

        # if CONFIG['debug']: print(prompt)
        # completion = self.gpt_client.chat.completions.create(
        #     model=CONFIG["openai"]["model"], 
        #     messages=[{
        #         "role": "user", "content": prompt
        #         }]
        # )
        # if CONFIG['debug']:  print(completion.choices[0].message.content)
        # decomposed = safe_load_gpt_content(completion.choices[0].message.content, prompt)

        success, decomposed = safe_chat(prompt=prompt)
        if success:
            self.short_memory.set_task_decompose(decomposed=decomposed)
        else:
            self.short_memory.set_task_decompose(decomposed = {f"{event}" : f"{duration}"})


    def _summary_chatbot_history(self, chat_history):
        prompt = chat_history
        prompt += "You need to summarize the Chatbot history in the past. "
        prompt += "To obtain the answer, you need to figure out "
        prompt += "what are the topcis that mostly talked, and how about the frequency (exact times per hour)? "
        prompt += "Limit your answer in 100 words. Please return your summary only."

        if CONFIG['debug']: print(prompt)
        completion = self.gpt_client.chat.completions.create(
            model=CONFIG["openai"]["model"], 
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG['debug']:  print(completion.choices[0].message.content)

        return completion.choices[0].message.content
    

    def _summary_location_history(self, location_history):
        prompt = location_history
        prompt += "You need to summarize the location records in the past. "
        prompt += "To obtain the answer, you need to figure out summarize the path of the location changes, "
        # prompt += "which should include the name, longitude, and latitude of the key location, time of when the location changes. "
        prompt += "which should include the address of the key location, time of when the location changes. "
        if self.have_examples:
            if "location_summary" in self.examples.keys():
                prompt += "\nHere is an examples of how to summarize the changes of location: \n"
                prompt += "Records:\n"
                prompt += self.examples["location_summary"]["record"]
                prompt += "\nSummary:\n"
                prompt += self.examples["location_summary"]["summary"]
                prompt += "\n"

        prompt += "The max length of your answer is 200 words. Please return your summary only."

        if CONFIG['debug']: print(prompt)
        completion = self.gpt_client.chat.completions.create(
            model=CONFIG["openai"]["model"], 
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG['debug']:  print(completion.choices[0].message.content)

        return completion.choices[0].message.content



if __name__ == "__main__":
    brain = Brain(
        user_folder="/home/ubuntu/SimulPaPa/.Users/19d7bf69-7fdc-3648-9c87-9bfca20611c2",
        agent_folder="/home/ubuntu/SimulPaPa/.Users/19d7bf69-7fdc-3648-9c87-9bfca20611c2/agents/2",
        # info={'name':'David Lee'}
        # info={'name':'Emily Johnson'}
        info={'name':'Jason Nguyen'}
    )
    brain.init_brain()
    brain.plan(days=5, type="new")


