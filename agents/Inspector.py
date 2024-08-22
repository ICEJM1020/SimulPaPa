""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-07-16
""" 

import json
import os
from datetime import datetime, timedelta

import pandas as pd

from langchain_core.tools import tool
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent

from config import CONFIG


class Inspector:

    def __init__(self, rag_folder) -> None:
        # self._rag_folder = rag_folder
        CONFIG["RAG_FOLDER"] = rag_folder

        self._retry_times = 5

    @tool("search-thoughts-tool")
    def search_thoughts(agent_id: int, date: str, keywords: str) -> str:
        """
        Search the thoughts log for any agents on specific date. The thoughts may include why this agent make a decision to define a purpose of one day, to decompose a schedule event, or to simulate personal activity data.
        PARAMETERS:
        agent_id: (int) Agent ID
        date: (string) The date you want to check, format as MM-DD-YYYY.
        keywords: (string) A set of key words, that you may interest, such as 'heartrate', 'location', 'purpose', and so on. Use ';' to seperate each keyword. Max number of the keywords is three
        """
        try:
            with open(os.path.join(CONFIG["RAG_FOLDER"], f"agents/{agent_id}/thoughts_log/{date}.txt"), "r") as f:
                _txt = f.read()
            thoughts = _txt[2:].split("\n\n")
        except:
            return "No thoughts records available for this agent."
        else:
            res = {}
            for _t in thoughts:
                _temp = _t.replace("=", "")
                _temp = _temp.split("\n")
                if len(_temp)<=1: continue
                _t_key = _temp[0]
                for _kw in keywords.split(";"):
                    if _kw in _t_key:
                        res[_t_key] = json.dumps(_temp[1:-1])[1:-1]
                        break
            if res:
                return json.dumps(res)
            else:
                return "No thoughts records available, try to change or reduce your keywords."
        
    @tool("search-activity-tool")
    def search_activity(agent_id: int, date: str, start_time: str, end_time: str, data_type: str) -> str:
        """
        Search the activity records of one of the given data type for any agents on specific date and time range (max 2 hours).
        PARAMETERS:
        agent_id: (int) Agent ID
        date: (string) The date you want to check, format as MM-DD-YYYY.
        start_time: The start time of the records, format as HH:MM.
        end_time: The end time of the records, format as HH:MM.
        data_type: A specific data type you want, or use 'all' to fetch all kinds of data. We offer 'activity', 'event', 'heartrate', 'location', 'chatbot', 'steps', or 'all'. 
        """
        try:
            data = pd.read_csv(os.path.join(CONFIG["RAG_FOLDER"], f"agents/{agent_id}/activity_hist/{date}.csv"))
        except:
            return "No activity records available for this agent."
        else:
            if data_type=="all":
                res = data.loc[f"{date} {start_time}":f"{date} {end_time}", :]
            else:
                res = data.loc[f"{date} {start_time}":f"{date} {end_time}", data_type]
            if res.shape[0]>120:
                res = res.iloc[-120:, :]

            if res:
                return json.dumps(res.to_dict())
            else:
                return "No activity records available, try to provide a correct time or data_type."
            
    @tool("search-schedule-tool")
    def search_schedule(agent_id: int, date: str) -> str:
        """
        Search a daily schedule for any specific agent on specific date.
        PARAMETERS:
        agent_id: (int) Agent ID
        date: (string) The date you want to check, format as MM-DD-YYYY.
        """
        try:
            data = pd.read_csv(os.path.join(CONFIG["RAG_FOLDER"], f"agents/{agent_id}/activity_hist/{date}.csv"))
        except:
            return "No activity records available for this agent."
        else:
            schedule = {}
            cur_event = data["event"][0]
            event_start_time = data["time"][0]
            last_time = ""
            for _, row in data.iterrows():
                if not cur_event==row["event"]:
                    schedule[f"{event_start_time}-{last_time}"] = cur_event
                    cur_event = row["event"]
                    event_start_time = row["time"]
                last_time = row["time"]
            schedule[f"{event_start_time}-{last_time}"] = cur_event

            return json.dumps(schedule)
        
    @tool("search-experiment-all-dates")
    def fetch_all_donedates():
        """
        Search how many days in this experiemnt. Return full experiment date list.
        """
        donedates = []

        for id in os.listdir(os.path.join(CONFIG["RAG_FOLDER"], "agents")):
            if "." in id: continue
            _donedates = [i.split(".")[0] for i in os.listdir(os.path.join(CONFIG["RAG_FOLDER"], f"agents/{id}/activity_hist"))]
            if donedates:
                donedates = list(set(donedates).union(_donedates))
            else:
                donedates = _donedates

        dates = [datetime.strptime(date_str, '%m-%d-%Y') for date_str in donedates]
        sorted_dates = sorted(dates)
        sorted_date_strings = [datetime.strftime(date_obj, '%m-%d-%Y') for date_obj in sorted_dates]
        return sorted_date_strings
    
    @tool("search-agent-dates")
    def fetch_agent_donedates(agent_id: int):
        """
        Search how many days an agent has done in this experiemnt. Return full experiment date list.
        PARAMETERS:
        agent_id: (int) Agent ID
        """
        try:
            donedates = [i.split(".")[0] for i in os.listdir(os.path.join(CONFIG["RAG_FOLDER"], f"agents/{agent_id}/activity_hist"))]
        except:
            return f"No records for agent {agent_id}"

        dates = [datetime.strptime(date_str, '%m-%d-%Y') for date_str in donedates]
        sorted_dates = sorted(dates)
        sorted_date_strings = [datetime.strftime(date_obj, '%m-%d-%Y') for date_obj in sorted_dates]
        return sorted_date_strings
        
    @tool("search-agent-infor-tool")
    def search_agent_info(agent_id: int) -> str:
        """
        Search the personal profile for any agents.
        PARAMETERS:
        agent_id: (int) Agent ID
        """
        try:
            with open(os.path.join(CONFIG["RAG_FOLDER"], f"agents/{agent_id}/info.json"), "r") as f:
                profile = json.load(f)
        except:
            return "No profile records available for this agent."
        else:
            return profile["description"]
    
    @tool("search-agent-list")
    def fetch_agent_list() -> str:
        """Return the agents list."""
        agent_list = os.listdir(os.path.join(CONFIG["RAG_FOLDER"], "agents"))
        agent_list = list(filter(lambda x: "." not in x, agent_list))
        return json.dumps(agent_list)


    def chat(self, req:dict):
        user_msg:list = req["messages"]

        prompt = ChatPromptTemplate.from_messages(
            [
                (user_msg[0]['role'], user_msg[0]['content']),
                MessagesPlaceholder("chat_history", n_messages=10),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )
        llm=ChatOpenAI(
                    api_key=CONFIG["openai"]["api_key"],
                    organization=CONFIG["openai"]["organization"],
                    model_name=CONFIG["openai"]["model-turbo"],
                    temperature=req['temperature'],
                    max_tokens=req['max_tokens'],
                    streaming=req['stream'],
                    model_kwargs={
                        "top_p":req['top_p'],
                        "frequency_penalty":req['frequency_penalty'],
                        "presence_penalty":req['presence_penalty'],
                    }
                )
        tools = [
                self.search_thoughts,
                self.fetch_agent_list,
                self.search_activity,
                self.search_schedule,
                self.search_agent_info,
                self.fetch_all_donedates,
                self.fetch_agent_donedates,
            ]

        agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools
            )

        res = agent_executor.invoke(
                            input={
                                    "chat_history":user_msg[:-1],
                                    "input":user_msg[-1]
                                },
                        )

        return res["output"]
            
