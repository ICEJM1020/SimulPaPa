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
from agents.ShortMemory import ShortMemory
from agents.LongMemory import LongMemory
from agents.utils import *


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

            _schedule = self._create_halfhour_activity()
            if CONFIG['debug']: print(_schedule)
            self.short_memory.set_schedule(_schedule)

            self._shift_window_pred()

            self.short_memory.save_pred_file()


    def _define_one_day_purpose(self):
        prompt = self.long_memory.description
        prompt += f"Today is {self.short_memory.memory_tree['today']}, and this is also a new day of {self.long_memory.info['name']}. "
        prompt += f"For last {self.retrieve_days} days, the main purpose of every day is "
        prompt += f"{self.long_memory.past_daily_purpose(self.short_memory.memory_tree['today'], self.retrieve_days)}. "
        prompt += "Based on personal information and past daily purpose, combined with your knowledge about the date of today, what do you think about the main purpose of today. "
        prompt += f"Here are some options for you, {CONFIG['daily_purpose']}. Return your answer in the following JSON format without any other information: "
        prompt += "{\"choice\" : \"choice_from_options\"}"

        if CONFIG['debug']: print(prompt)
        completion = self.gpt_client.chat.completions.create(
            model="gpt-3.5-turbo", 
            # model="gpt-4",
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG['debug']:  print(completion.choices[0].message.content)
        return json.loads(completion.choices[0].message.content)["choice"]
    

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
        prompt += "Please make your plan as detailed as possible, using a phrase about 3-5 words, except sleep you can just use \"Sleep\". "
        prompt += "Here are some examples of the activities: "
        prompt += "wake up, complete the morning routine, eat breakfast, read a book, take a nap, relax and watch TV, prepare for bed, and so on. "
        prompt += "You need to be creative to imagine what else could do besides these examples. "
        prompt += "Return your answer in the following JSON format without any other information: "
        prompt += json.dumps(schedule)

        if CONFIG['debug']: print(prompt)
        completion = self.gpt_client.chat.completions.create(
            model="gpt-3.5-turbo", 
            # model="gpt-4",
            messages=[{
                "role": "system", "content": "You are a helpful assistant to design daily schedules for the olderly.",
                "role": "user", "content": prompt
                }]
        )
        if CONFIG['debug']:  print(completion.choices[0].message.content)
        return json.loads(completion.choices[0].message.content)

    
    def _shift_window_pred(self):
        # Start at midnight
        current_time = datetime.strptime("00:00", "%H:%M") 
        # Circulate through 24 hours in 10-minute increments
        while current_time < datetime.strptime("23:59", "%H:%M"):
            print(self.short_memory.memory_tree["cur_time"])
            if current_time.minute==0:
                self.long_memory.save_cache()
                self.short_memory.save_cache()
                self.short_memory.save_pred_file()


            self.short_memory.set_current_time(current_time)

            self._decide_cur_activity()
            
            # Multi-modality prdiction
            self._predict_heartrate()
            self._predict_chatbot()

            current_time += timedelta(minutes=5)


    def _decide_cur_activity(self):
        if self.short_memory.get_current_schedule().lower()=="sleep":
            self.short_memory.set_current_activity(activity="sleep")
        else:
            prompt = self.long_memory.description
            prompt += self.short_memory.today_summary()
            prompt += self.short_memory.cur_time_summary()
            prompt += self.short_memory.cur_schedule_summary()
            prompt += self.short_memory.past_activities_summary(min=15)
            # prompt += self.long_memory.past_activities_summary(cur_time=, halfhour=, items=)
            prompt += f"Now, {self.long_memory.info['name']} need to decide an activity for next 5 minutes. "
            prompt += f"Do you think what is the best activity based on {self.long_memory.info['name']}'s plan and past activities. "
            prompt += "Your choice of activity should be specific using a short phrase. "
            prompt += f"You need to be careful about the occupation, education and physical status of {self.long_memory.info['name']}. "
            prompt += "You may need to think about the half hour plan, for example during the work hour you may text to manager, join a meeting, write a e-mail, and so on. "
            prompt += "And the coherence between activities are also important, for example if you eat food in last 5 miutes, you cannot do sports right now. "
            # prompt += "There may also be possible that you will continue last activity, since not all work can be finished in 5 minutes, for example hold a meeting. "
            # prompt += "But there may also be impossible to do the same activity too long. "
            prompt += "Return your answer in the following JSON format without any other information: "
            prompt += "{\"activity\":\"[Fill in]\"}"

            if CONFIG['debug']: print(prompt)
            completion = self.gpt_client.chat.completions.create(
                model="gpt-3.5-turbo", 
                # model="gpt-4",
                messages=[{
                    "role": "user", "content": prompt
                    }]
            )
            if CONFIG['debug']:  print(completion.choices[0].message.content)
            activity = json.loads(completion.choices[0].message.content)["activity"]
            self.short_memory.set_current_activity(activity=activity)


    def _predict_heartrate(self):
        prompt = self.long_memory.description
        prompt += self.short_memory.cur_time_summary()
        prompt += self.short_memory.cur_activity_summary()
        if not self.short_memory.get_current_activity() == "sleep":
            prompt += self.short_memory.past_activities_summary(min=15)

        # summary past X miutes heartrate
        hr_summary, lack = self.short_memory.past_heartrate_summary(min=30)
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
                days=5,
                time_start=self.short_memory.memory_tree['cur_time'],
                mins=5
            )

        #
        #
        # TODO relevent activities
        #
        #

        prompt += f"Now, you need to predict {self.long_memory.info['name']}'s heart rate for next 10 minutes, with 1 minute increment, "
        prompt += f"starting from {self.short_memory.memory_tree['cur_time']}. "
        prompt += "There may be some useful information about the heart rate in the past records or same time in past days. "
        # prompt += "There may be some useful information during relevent  or similar activities. "
        prompt += "There may also be first 5 minutes of predcition in your last prediction, which may provide some useful information for you. "
        prompt += f"You need to be careful about the age and physical status of {self.long_memory.info['name']}. "
        prompt += "And the prediction should also be reasonable in realistic scenario. "
        prompt += "Return your answer in the following JSON format without any other information: "

        pred_dict = {}
        for i in range(10):
            _time = datetime.strptime(self.short_memory.memory_tree['cur_time'], "%H:%M") + timedelta(minutes=i)
            pred_dict[datetime.strftime(_time, "%H:%M")] = "[Fill in]"
        prompt += json.dumps(pred_dict)

        if CONFIG['debug']: print(prompt)
        completion = self.gpt_client.chat.completions.create(
            model="gpt-3.5-turbo", 
            # model="gpt-4",
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG['debug']:  print(completion.choices[0].message.content)

        pred = safe_load_gpt_content(completion.choices[0].message.content)
        if pred:
            self.short_memory.set_current_heartrate(pred)
        else:
            self.short_memory.set_current_heartrate(pred_dict)


    def _predict_chatbot(self):
        if self.short_memory.get_current_activity() == "sleep":
            return 0
        else:
            prompt = self.long_memory.description
            prompt += f"{self.long_memory.info['name']}'s usage preference of using Alexa chatbot is: "
            prompt += self.long_memory.pref_tree["agent_chatbot_pref"]
            prompt += "==========\n"
            prompt += self.short_memory.cur_time_summary()
            prompt += self.short_memory.cur_activity_summary()

            prompt += self.short_memory.past_chatbot_summary()
            prompt += self.short_memory.pred_chatbot_summary()

            prompt += self.long_memory.past_period_chatbot_summary(
                    cur_date=self.short_memory.memory_tree['today'], 
                    days=5,
                    time_start=self.short_memory.memory_tree['cur_time'],
                    hours=2
                )

            prompt += f"Now, you need to predict {self.long_memory.info['name']}'s chatbot interaction (chat content) in the next 10 minutes, with 1 minute increment, "
            prompt += f"starting from {self.short_memory.memory_tree['cur_time']}. "
            prompt += f"You need to think carefully about {self.long_memory.info['name']}'s usage preference, and the occupation, education, and age or maybe living area may also affect the usage. "
            prompt += "There may also be first 5 minutes of predcition in your last prediction, which may provide some useful information for you. "
            prompt += "If you think there will be a interaction, you must to think about the following question: \n"
            prompt += "1. What is the topic of this conversation?\n"
            prompt += "2. Based on this topic, what should you ask?\n"
            prompt += "3. How could you generate a gentle utterance that may get positive response?\n"
            prompt += "4. How long will the conversation last? Some conversation may happen in 1 min, others may not.\n"
            prompt += "Here are some examples of the conversation that may help you:\n"
            prompt += """user:Hello?,alexa:Hello! I'm Coco, your friendly chatbot. How's your day going so far?;
            user:How/what/why/when/Is/Can/who/Do going good but it's pretty tired,alexa:I see, what made your day tiring?;
            user:Other question: are just too many soft to do today so I went to school to have a course in the morning and
            then I have a meeting in the afternoon afterwards my boyfriend went to the airport so I was him and then 
            I come back home there are even more readings,alexa:That does sound like a packed day. How did the meeting in the 
            afternoon go?;user:Other question: meeting was OK so we are trying to revise our paper it was it was OK,alexa:Sounds 
            productive. Can you tell me more about your visit to the airport?;user:Yes(positive response) so my boyfriend visited 
            me in Boston and then it's time for him to come back to Elena so he drove actually V drove to the airport so my boyfriend 
            come came back to Elena,alexa:Must have been tough to say goodbye. Can you tell me about any other activities of your day?;
            user:Yes(positive response) I don't think I have a lot of other activities today so I picked up a package 
            also I nothing else actually,alexa:Got it. How did you feel about your day overall?;user:I/My have pretty 
            complex feeling of the day cause you know my boyfriend went to the airport and laughed to atlander but it was 
            also a really productive day,alexa:I understand. It sounds like a bittersweet day. Thanks for sharing your 
            day with me.;user:No(negative response) worries bye-bye,alexa:Goodbye! Take care. Let's chat again tomorrow.
            ;user:How/what/why/when/Is/Can/who/Do,alexa:Hello! I'm Coco. How was your day today? Did you do any outdoor exercises?"""
            prompt += "Return your answer in the following JSON format without any other information: "

            pred_dict = {}
            for i in range(10):
                _time = datetime.strptime(self.short_memory.memory_tree['cur_time'], "%H:%M") + timedelta(minutes=i)
                pred_dict[datetime.strftime(_time, "%H:%M")] = "[Fill in or 'null']"
            prompt += json.dumps(pred_dict)

            if CONFIG['debug']: print(prompt)
            completion = self.gpt_client.chat.completions.create(
                model="gpt-3.5-turbo", 
                # model="gpt-4",
                messages=[{
                    "role": "user", "content": prompt
                    }]
            )
            if CONFIG['debug']: print(completion.choices[0].message.content)

            pred = safe_load_gpt_content(completion.choices[0].message.content)
            if pred:
                self.short_memory.set_current_chatbot(pred)
            else:
                self.short_memory.set_current_chatbot(pred_dict)



if __name__ == "__main__":
    brain = Brain(
        user_folder="/Users/timberzhang/Documents/Documents/Long-SimulativeAgents/Code/SimulPaPa/.Users/19d7bf69-7fdc-3648-9c87-9bfca20611c2",
        agent_folder="/Users/timberzhang/Documents/Documents/Long-SimulativeAgents/Code/SimulPaPa/.Users/19d7bf69-7fdc-3648-9c87-9bfca20611c2/agents/1",
        info={'name':'Siphiwe Ndlovu'}
    )
    brain.plan()


