""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-07-16
""" 

import json

from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers.string import StrOutputParser
from langchain.chains import LLMChain
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_openai import ChatOpenAI

from config import CONFIG



class Inspector:

    def __init__(self, rag_folder) -> None:
        self._rag_folder = rag_folder

        self._retry_times = 5

    # def chat(self, req:dict):
    #     for try_idx in range(self._retry_times):
    #         try:
    #             res = self._chat(req)
    #         except:
    #             if try_idx + 1 == self._retry_times:
    #                 # self.status = "error"
    #                 return None
    #             else:
    #                 continue
    #         else:
    #             return res

    def chat(self, req:dict):
        user_msg:list = req["messages"]

        prompt = ChatPromptTemplate.from_messages(
            [
                (user_msg[0]['role'], user_msg[0]['content']),
                MessagesPlaceholder("chat_history", n_messages=10),
                ("human", "{input}"),
            ]
        )
        
        chain = LLMChain(
                llm=ChatOpenAI(
                    api_key=CONFIG["openai"]["api_key"],
                    organization=CONFIG["openai"]["organization"],
                    model_name=CONFIG["openai"]["model"],
                    temperature=req['temperature'],
                    max_tokens=req['max_tokens'],
                    streaming=req['stream'],
                    model_kwargs={
                        "top_p":req['top_p'],
                        "frequency_penalty":req['frequency_penalty'],
                        "presence_penalty":req['presence_penalty'],
                    }
                ),
                prompt=prompt,
                output_parser=StrOutputParser()
            )
        
        res = chain.invoke(
                    input={
                            "chat_history":user_msg[:-1],
                            "input":user_msg[-1]
                        },
                )

        return res["text"]
            
