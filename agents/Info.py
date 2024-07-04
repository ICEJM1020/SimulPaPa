""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2023-12-28
""" 
from datetime import date
import json
import os
import threading
import random
import re
from datetime import datetime

from openai import OpenAI
import requests
import numpy as np

from config import CONFIG


def description_prompt(**kwargs):
    infos = {key:"" for key in CONFIG["info"]}
    infos["description"] = ""
    has_info = ""
    missing_info = ""
    for key in infos.keys():
        if key == "description":
            continue
        if key in kwargs.keys():
            has_info += f"{key}={kwargs[key]}, "
        else:
            missing_info += f"{key},"

    prompt = "Generate a description from the following information: "
    prompt += has_info
    prompt += "The following information is missing and you could jump them: "
    prompt += missing_info
    prompt += "Today is June-15-2024 (compute age based on today's date). "
    prompt += "The generated profile should match the following guidance:\n<"
    prompt += "{Name} is a {age} {race} {gender} living in {street}, {city}, {district}, {state}, {zipcode}. "
    prompt += "The weight of {Pronoun} is {weight} and the BMI is {BMI}."
    prompt += "The physical status of {Pronoun} is {diesease}, {descirbe the effect of the disease}."
    prompt += "{Pronoun} is a {occupation} with annual income {income} at {company} ({company_address}), {infer_retirement_status}. "
    prompt += "{Pronoun} speaks {language}. Pronoun's education background is {education}. "
    prompt += "{Pronoun}'s date of birth is {birthday}. {possible_life_activity_preference}>\n"
    prompt += "\nLimit the description within 100 words, return your answer in JSON format: "
    prompt += "{\"description\":\"profile_description\"}"

    return prompt


def gpt_description(name, birthday, _type="agent", retry=5, **kwargs):
    # description = _gpt_description(name, birthday, **kwargs)
    # return description["description"]
    for try_idx in range(retry):
        try:
            description = _gpt_description(name, birthday, _type=_type, **kwargs)
            assert "description" in description.keys()
        except:
            if try_idx + 1 == retry:
                return {"error":"Error generating description."}
            else:
                continue
        else:
            return description["description"]


def _gpt_description(name, birthday, _type="agent", **kwargs) -> dict:
    open_ai_client = OpenAI( 
        api_key=CONFIG["openai"]["api_key"],
        organization=CONFIG["openai"]["organization"],
    )
    if _type=="user":
        # print(int(date.today().year))
        # print(int(birthday.split("-")[-1]))
        age = int(date.today().year) - int(birthday.split("-")[-1])
        # prompt = description_prompt(name=name, birthday=birthday, age=age, **kwargs)
        print(age)
    else:
        prompt = description_prompt(name=name, birthday=birthday, **kwargs)

    completion = open_ai_client.chat.completions.create(
        model = CONFIG["openai"]["model"], 
        
        messages=[{
            # "role": "system", "content": "You are a census taker who knows everyone, and you write detailed descriptions.",
            "role": "user", "content": prompt
            }]
    )
    return json.loads(completion.choices[0].message.content)


def random_generate(short_description, retry=5):
    for try_idx in range(retry):
        try:
            infos = _random_generate(short_description)
        except:
            if try_idx + 1 == retry:
                return {"error":"Error generating information."}
            else:
                continue
        else:
            return infos


def _random_generate(short_description) -> dict:
    infos = {key:"" for key in CONFIG["info"]}
    infos["description"] = "profile_description"
    infos["gender"] = "male_or_female"
    infos["retirement"] = "yes_or_no"

    prompt = "Generate a realistic profile corresponding to the following short description:\n"
    prompt += short_description
    prompt += "\n\n"
    prompt += "Today is 01-01-2024 (compute age based on today's date). "
    prompt += "The income should be in dollars. "
    prompt += "The birthday should be in the MM-DD-YYYY format. "
    prompt += "Every information should be specific and realistic. "
    prompt += "Here is the template of the profile description:\n"
    prompt += "{Name} is a {age} {race} {gender} living in {street}, {city}, {district}, {state}, {zipcode}. "
    prompt += "The physical status of {Pronoun} is {diesease}. "
    prompt += "{Pronoun} is a {occupation} with annual income {income}, working at {company} ({company_address}), {retirement}. "
    prompt += "{Pronoun} speaks {language}. Pronoun's education background is {education}. "
    prompt += "{Pronoun}'s date of birth is {birthday}.> "
    prompt += "\nSummarize the information and return your answer in JSON format:\n"
    prompt += json.dumps(infos)

    open_ai_client = OpenAI( 
        api_key=CONFIG["openai"]["api_key"],
        organization=CONFIG["openai"]["organization"],
    )

    completion = open_ai_client.chat.completions.create(
        model = CONFIG["openai"]["model"],
        messages=[{
            "role": "user", "content": prompt
            }]
    )
    return json.loads(completion.choices[0].message.content)


def extract_info(short_description, retry=5):
    for try_idx in range(retry):
        try:
            infos = _extract_info(short_description)
        except:
            if try_idx + 1 == retry:
                return {"error":"Error extracting information."}
            else:
                continue
        else:
            return infos

def _extract_info(short_description):
    infos = {key:"" for key in CONFIG["info"]}
    infos["gender"] = "male_or_female"
    infos["retirement"] = "yes_or_no"

    prompt = "Extract Key information from this short description:\n"
    prompt += short_description
    prompt += "\n\n"
    prompt += "Here are some options for some key information, which if mentioned in short description, you need to chooose from them:\n"
    prompt += "Working Industry: "
    prompt += json.dumps(CONFIG["industry"])
    prompt += "Education Level: "
    prompt += json.dumps(CONFIG["education"])
    prompt += "Annual Income: "
    prompt += json.dumps(CONFIG["income"])
    prompt += "Race: "
    prompt += json.dumps(CONFIG["race"])
    prompt += "\nBirthday is required, which you can generate an estimated birthday based on the description, format as \"MM-DD-YYYY\". Summarize the information and return your answer in JSON format, keep missing information empty:\n"
    prompt += json.dumps(infos)

    open_ai_client = OpenAI( 
        api_key=CONFIG["openai"]["api_key"],
        organization=CONFIG["openai"]["organization"],
    )

    completion = open_ai_client.chat.completions.create(
        model = CONFIG["openai"]["model"],
        temperature = 0.5,
        messages=[{
            "role": "user", "content": prompt
            }]
    )
    return json.loads(completion.choices[0].message.content)

def dalle_portrait(description):
    prompts_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
    with open(os.path.join(prompts_folder, "prompt_utils.json"), "r") as f:
        prompt = json.load(fp=f)["portrait"]

    client = OpenAI(
        api_key=CONFIG["openai"]["api_key"],
        organization=CONFIG["openai"]["organization"]
        )

    response = client.images.generate(
        model = "dall-e-2",
        prompt = prompt + description,
        size = "512x512",
        quality = "standard",
        n=1,
    )
    image_url = response.data[0].url
    response = requests.get(image_url)
    return response.content


class InfoTree():

    def __init__(self, info, folder) -> None:
        self.user_info = info
        self.folder = folder
        self.tree_file = folder + "/tree.json"
        self.tree = {}

        self.gpt_client = OpenAI(
            api_key=CONFIG["openai"]["api_key"],
            organization=CONFIG["openai"]["organization"],
        )
        
        ######################
        # init : finish init
        # ready :  finish building the tree
        # building : building is undergoing
        # error :  error in building
        self.status = "init"

        if os.path.exists(self.tree_file):
            with open(self.tree_file, "r") as f:
                self.tree = json.load(f)
            self.status = "ready"
        else:
            self.start_building()


    def start_building(self):
        thread = threading.Thread(target=self._build_tree)
        self.status = "building"
        thread.start()
        return True
    

    def _build_tree(self):
        
        self._search_city_state(city=self.user_info["city"], state=self.user_info["state"])

        for idx in self.tree["option"].keys():
            res = self._search_district(
                u_city=self.user_info["city"],
                u_state=self.user_info["state"],
                city=self.tree["option"][idx]["city"],
                state=self.tree["option"][idx]["state"],
                district=self.user_info["district"]
            )
            self.tree["option"][idx]["district"] = res
        
        self._search_disease(self.user_info["disease"])

        self.status = "ready"

        with open(self.tree_file, "w") as f:
            json.dump(self.tree, f)


    def _search_city_state(self, city, state, size=5, retry=5):
        for try_idx in range(retry):
            try:
                cities = self._search_city_state_chat(city, state, size)
                _p = 0.0
                self.tree["option"] = {}
                self.tree["prob"] = []
                for idx, city in enumerate(cities):
                    self.tree["option"][str(idx)] = {
                            "city" : city["city"],
                            "state" : city["state"],
                            # "education" : {"option":[k for k in city["education"]], "prob":[float(city["education"][k]) for k in city["education"]]},
                            # "race" : {"option":[k for k in city["race"]], "prob":[float(city["race"][k]) for k in city["race"]]},
                            # "income" : {"option":[k for k in city["income"]], "prob":[float(city["income"][k]) for k in city["income"]]},
                            # "industry" : {"option":[k for k in city["industry"]], "prob":[float(city["industry"][k]) for k in city["industry"]]},
                            # "gender" : {"option":["male", "female"], "prob":[float(city["gender"]["male"]), float(city["gender"]["female"])]},
                            "education" : self._compute_prob("education", city),
                            "race" : self._compute_prob("race", city),
                            "income" : self._compute_prob("income", city),
                            "industry" : self._compute_prob("industry", city),
                            "gender" : self._compute_prob("gender", city),
                            "district" : {},
                        }
                    if city["city"]==self.user_info["city"]:
                        self.tree["prob"].append(float(city["similarity"]) + CONFIG["user_info_rate"])
                        _p += float(city["similarity"]) + CONFIG["user_info_rate"]
                    else:
                        self.tree["prob"].append(float(city["similarity"]))
                        _p += float(city["similarity"])
                self.tree["prob"] = [x / _p for x in self.tree["prob"]]
            except:
                if try_idx + 1 == retry:
                    self.status = "error"
                    raise Exception(f"Search cities failed {retry} times")
                else:
                    continue
            else:
                return True
            
    def _compute_prob(self, aim_key:str, ans_dic:list) -> dict:
        if self.user_info[aim_key]:
            options = []
            probs = []
            for k in ans_dic[aim_key]:
                options.append(k)
                if k==self.user_info[aim_key]:
                    probs.append(float(ans_dic[aim_key][k]) + CONFIG["user_info_rate"])
                else:
                    probs.append(float(ans_dic[aim_key][k]))
            probs = [p / sum(probs) for p in probs]
            return {"option":options, "prob":probs}
        else:
            return {"option":[k for k in ans_dic[aim_key]], "prob":[float(ans_dic[aim_key][k]) for k in ans_dic[aim_key]]}


    def _search_city_state_chat(self, city, state, size=5):
        industries = {key : "population_percentage_in_decimal" for key in CONFIG["industry"]}
        educations = {key : "population_percentage_in_decimal" for key in CONFIG["education"]}
        races = {key : "population_percentage_in_decimal" for key in CONFIG["race"]}
        incomes = {key : "population_percentage_in_decimal" for key in CONFIG["income"]}
        if "city":
            prompt = f"{city} is a city in {state} state. Based on your understanding, make an evaluation from the dimensions of climate, geographical conditions, and economic development. " 
            # prompt = f"Please find me {size} cities in the US (including {city}), rating them use the similarity to the {city}. " 
        else:
            prompt = f"Please find me {size} most representive cities in the US, rating them use the similarity. " 
        prompt += "Furthermore, tell me about the population statistic in each state. These data need to be based on real data, from resources like census bureau or government report. "
        prompt += "The data should based on real information during 2010 to 2020. Decimal precision needs to reach 4 decimal places. "
        prompt += "Return your answer in the following JSON format without any other information: "
        prompt += "{\"response\" : [{\"city\" : \"city_name\", \"state\" : \"state/province\", \"similarity\" : \"similarity_to_given_city_in_decimal\", "
        prompt += f"\"education\": {json.dumps(educations)}, "
        prompt += f"\"income\": {json.dumps(incomes)}, "
        prompt += f"\"industry\": {json.dumps(industries)}, "
        prompt += f"\"race\": {json.dumps(races)}, "
        prompt += "\"gender\": {\"male\":\"gender_percentage_in_decimal\", \"female\":gender_percentage_in_decimal}}, ...], "
        prompt += "\"information\" : \"put_other_information_you_want_to_tell_here\"}"

        if CONFIG["debug"]: print(prompt)
        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
            
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG["debug"]: print(completion.choices[0].message.content)
        cities = json.loads(completion.choices[0].message.content)["response"]
        if CONFIG["debug"]: print(cities)

        return cities
    

    def _search_district(self, u_city, u_state, city, state, district, size=5, retry=5):
        for try_idx in range(retry):
            try:
                res = self._search_district_chat(u_city, u_state, city, state, district, size)
            except:
                if try_idx + 1 == retry:
                    self.status = "error"
                    raise Exception(f"Search districts failed {retry} times")
                else:
                    continue
            else:
                return res

    def _search_district_chat(self, u_city, u_state, city, state, district, size=5):
        prompt = f"{district} is a zone in {u_city}, {u_state}. "
        prompt += "Based on your knowledge, to evaluate the convenience of this district, including the population, the infrastructure, and the medical and educational resources. "
        prompt += f"Please find me {size} districts with similar conditions in {city}, {state}. Besides, give me {size} streets in these districts that suitable for living. "
        prompt += "Return your answer in the following JSON format: "
        prompt += "{\"response\" : [{\"district\" : \"district_1\", \"similarity\" : \"similarity_to_given_district_in_decimal\", \"streets\":[\"street_1\", ..., \"street_N\"], ...], "
        prompt += "\"information\" : \"put_other_information_you_want_to_tell_here\"}"
        
        if CONFIG["debug"]: print(prompt)
        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
                        messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG["debug"]: print(completion.choices[0].message.content)

        districts = json.loads(completion.choices[0].message.content)["response"]
        res = {"option":{}, "prob":[]}
        _p = 0.0
        for idx, district in enumerate(districts):
            res["option"][str(idx)] = {
                    "district" : district["district"],
                    "street" : district["streets"],
                }
            res["prob"].append(float(district["similarity"]))
            _p += float(district["similarity"])
        res["prob"] = [x / _p for x in res["prob"]]

        return res
    

    def _search_disease(self, disease, size=10, retry=5):
        # res = self._search_disease_chat(disease, size)
        # self.tree["disease"] = res
        if self.user_info["disease"]:
            self.tree["disease"] = {"option": [self.user_info["disease"]], "prob": [1.0]}
        else:
            for try_idx in range(retry):
                try:
                    res = self._search_disease_chat(disease, size)
                except:
                    if try_idx + 1 == retry:
                        self.status = "error"
                        raise Exception(f"Search disease failed {retry} times")
                    else:
                        continue
                else:
                    self.tree["disease"] = res
                    return True

    def _search_disease_chat(self, disease, size=10):
        age = int(date.today().year) - int(self.user_info["birthday"].split("-")[-1])
        prompt = f"There is a {age} {self.user_info['gender']} who has {disease}. "
        prompt += f"Now you need to provide {size} other diseases, with a detailed analysis, that share similar symptoms, impacts on health, methods of transmission (if applicable), and treatment approaches. "
        prompt += "For each related disease you identify, explain why it is relevant to the disease in question, focusing on the similarities in their clinical presentations, epidemiology, and management strategies. "
        prompt += "T0 figure out this question, let's think step by step. Do it in the following format, and keep the JSON format of the final Answer:\n"
        prompt += "Thought 1: your thought about this question\n...\nThought n: your thought about this question\nFinal Answer:\n"
        ans = {f"disease_{i}":{"name":"disease_name","stage":"disease_progression","similarity":"similarity_to_the_given_disease_in_float"} for i in range(1, size+1)}
        prompt += json.dumps(ans)

        if CONFIG["debug"]: print(prompt)
        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
            messages=[{
                "role": "user", "content": prompt
            }]
        )
        if CONFIG["debug"]: print(completion.choices[0].message.content)

        json_strs = re.findall(r"\{(?:[^{}])*\}", completion.choices[0].message.content.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL)
        if json_strs: 
            res = {"option":[], "prob":[]}
            _p = 0.0
            for _, json_str in enumerate(json_strs):
                disease = json.loads(json_str)
                res["option"].append(f"{disease['name']} ({disease['stage']})")
                res["prob"].append(float(disease["similarity"]))
                _p += float(disease["similarity"])
            res["prob"] = [x / _p for x in res["prob"]]
            return res
        else:
            raise Exception("GPT response error.")
        

    def _infer_addtional(self, gender, race, location, education, income_range, age_range=5):
        age = int(date.today().year) - int(self.user_info["birthday"].split("-")[-1])
        prompt = f"There is a {race} {gender} living in {location} who has a {education} degree, ages between {age-age_range}-{age+age_range}. "
        prompt += f"First, generate a birthday based on their age range. (It's {date.today().year} now.) "
        prompt += "Based on their gender and race, generate a name and their spoken languages. "
        prompt += f"Based on their income range {income_range}, generate a home address for them."
        prompt += f"Find a residential building in {location} that is affordable and reasonable based on their age and income level. "
        prompt += "Be mindful that a place could be rented, financed, or owned. "
        prompt += "Return your answer in the following JSON format: "
        prompt += "{\"response\" : {\"name\" : \"firstname familyname\", \"birthday\" : \"MM-DD-YYYYY\", "
        prompt += "\"language\" : \"language\", \"zipcode\" : \"zipcode\", \"building\":\"building_name\","
        prompt += "\"home_longitude\":\"home_longitude_format_as_xx.xxxxxx\", \"home_latitude\":\"home_latitude_format_as_xx.xxxxxx\"}, "
        prompt += "\"information\" : \"put_other_information_you_want_to_tell_here\"}"
        

        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        return json.loads(completion.choices[0].message.content)["response"]
    

    def _infer_occupation(self, name, income_range, location, education, industry):
        age = int(date.today().year) - int(self.user_info["birthday"].split("-")[-1])
        prompt = f"{name}, {age} years old, lives in {location} who has {education} degree. Their income range is {income_range}."
        # #evidence-based
        # prompt = f"Currently, the person's weight is {weight}. "
        prompt += f"Based on all of the provided information, provide a job for them in industry: '{industry}', and determine if they have retired now. "
        #prompt += "This job needs to be specific and consistent with the career plan of this industry. "
        prompt += f"This job needs to be reasonable, specific, and aligned with the industry and their income range. "
        prompt += "You also have to consider their educational background and age to determine if the job fits a reasonable career path. "
        prompt += "After assigning a job for them, infer their retirement status based on their age. "
            #"and their health status. "
        prompt += "People normally retire after a specific age (based on policy). "
        prompt += "Even if they have retired, they might be participating in some volunteering and part-time works, based on their expertise and interests. "
        prompt += f"After determining their job, grant {name} an annual salary. "
        prompt += f"Their annual salary should be a reasonable number in US dollar, within their income range '{income_range}', and aligned with their retirement status and location. "
        prompt += f"Afterwards, based on {name}'s current job, find a specific company for them."
        prompt += "First, generate a company name that aligned with their occupation and location. "
        prompt += "Then, determine the address of that company."
        prompt += f"No matter if the company was made up or not, the address needs to be REAL, located in {location}, aligned with where {name} live. " 
        prompt += "The format of that address should be standard USPS address: \"{building}, {street}, {city}, {state}, {zipcode}\""
        prompt += "At last, based on all the information you have generated, add 2-3 sentences about some other information that could be helpful. Could be related to their hobbies, social networks, personality, or anything you can think of."
        prompt += "Return your answer in the following JSON format: "
        prompt += "{\"response\" : {\"job\" : \"job\", \"company\" : \"company_name\", \"work_addr\":\"company_address\", \"income\":\"annual_salary\""
        prompt += "\"work_longitude\" : \"work_longitude_format_as_xx.xxxxxx\", \"work_latitude\" : \"work_latitude_format_as_xx.xxxxxx\", \"retirement\":\"retired_or_working\"}, "
        prompt += "\"information\" : \"put_other_information_you_want_to_tell_here\"}"
        

        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
            
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        print(json.loads(completion.choices[0].message.content)["response"])
        return json.loads(completion.choices[0].message.content)["response"]


    def generate_info_dict(self, healthy_rate=0.7):
        res = {key:None for key in self.user_info}
        city_choice = random.choices([str(i) for i in range(len(self.tree["prob"]))], weights=self.tree["prob"])[0]
        city = self.tree["option"][city_choice]
        res["city"] = city["city"]
        res["state"] = city["state"]

        res["gender"] = random.choices(["male", "female"], weights=city["gender"]["prob"])[0]
        res["race"] = random.choices(city["race"]["option"][:-1], weights=city["race"]["prob"][:-1])[0]
        res["education"] = random.choices(city["education"]["option"], weights=city["education"]["prob"])[0]

        income_range =  random.choices(city["income"]["option"], weights=city["income"]["prob"])[0]
        res["industry"] = random.choices(city["industry"]["option"], weights=city["industry"]["prob"])[0]

        district_choice = random.choices([str(i) for i in range(len(city["district"]["prob"]))], weights=city["district"]["prob"])[0]
        district = city["district"]["option"][district_choice]
        res["district"] = district["district"]
        res["street"] = random.choices(district["street"])[0]
        
        add_info = self._infer_addtional(
            gender=res["gender"],
            race=res["race"],
            education=res["education"],
            income_range=income_range,
            location=f"{res['street']}, {res['district']}, {res['city']}, {res['state']}"
        )
        res["name"] = add_info["name"]
        res["birthday"] = add_info["birthday"]
        res["age"] = int((datetime.strptime("01-01-2024", "%m-%d-%Y") - datetime.strptime(add_info["birthday"], "%m-%d-%Y")).days // 365.2425)
        res["zipcode"] = add_info["zipcode"]
        res["language"] = add_info["language"]
        res["building"] = add_info["building"]
        res["home_longitude"] = add_info["home_longitude"]
        res["home_latitude"] = add_info["home_latitude"]

        job_info = self._infer_occupation(
            name=res["name"],
            income_range=income_range,
            education=res["education"],
            location=f"{res['street']}, {res['district']}, {res['city']}, {res['state']}",
            industry=res["industry"]
        )
        res["income"] = job_info["income"]
        res["occupation"] = job_info["job"]
        res["retirement"] = job_info["retirement"]
        res["company"] = job_info["company"]
        res["work_addr"] = job_info["work_addr"]
        res["work_longitude"] = job_info["work_longitude"]
        res["work_latitude"] = job_info["work_latitude"]

        if self.user_info['disease']:
            res["disease"] = self.user_info['disease']
        else:
            if random.random() > healthy_rate:
                res["disease"] = "Healthy"
            else:
                if len(self.tree["disease"]["option"]) == 1:
                    res["disease"] = self.tree["disease"]["option"][0]
                else:
                    res["disease"] = random.choices(self.tree["disease"]["option"], weights=self.tree["disease"]["prob"])[0]
        
        return res


    def get_status(self):
        return self.status
    



class InfoTreeEB():

    def __init__(self, info, folder) -> None:
        self.user_info = info
        self.folder = folder
        self.tree_file = folder + "/tree.json"
        self.tree = {}

        self.gpt_client = OpenAI(
            api_key=CONFIG["openai"]["api_key"],
            organization=CONFIG["openai"]["organization"],
        )
        
        ######################
        # init : finish init
        # ready :  finish building the tree
        # building : building is undergoing
        # error :  error in building
        self.status = "init"

        if os.path.exists(self.tree_file):
            with open(self.tree_file, "r") as f:
                self.tree = json.load(f)
            self.status = "ready"
        else:
            self.start_building()


    def start_building(self):
        thread = threading.Thread(target=self._build_tree)
        self.status = "building"
        thread.start()
        return True
    

    def _build_tree(self):

        self._search_city_state(city=self.user_info["city"], state=self.user_info["state"])

        for idx in self.tree["option"].keys():
            res = self._search_district(
                u_city=self.user_info["city"],
                u_state=self.user_info["state"],
                city=self.tree["option"][idx]["city"],
                state=self.tree["option"][idx]["state"],
                district=self.user_info["district"]
            )
            self.tree["option"][idx]["district"] = res
        
        self._search_disease(self.user_info["disease"])

        self.status = "ready"

        with open(self.tree_file, "w") as f:
            json.dump(self.tree, f)


    def _search_city_state(self, city, state, size=5, retry=5):
        for try_idx in range(retry):
            try:
                cities = self._search_city_state_chat(city, state, size)
                _p = 0.0
                self.tree["option"] = {}
                self.tree["prob"] = []
                for idx, city in enumerate(cities):
                    self.tree["option"][str(idx)] = {
                            "city" : city["city"],
                            "state" : city["state"],
                            # "education" : {"option":[k for k in city["education"]], "prob":[float(city["education"][k]) for k in city["education"]]},
                            # "race" : {"option":[k for k in city["race"]], "prob":[float(city["race"][k]) for k in city["race"]]},
                            # "income" : {"option":[k for k in city["income"]], "prob":[float(city["income"][k]) for k in city["income"]]},
                            # "industry" : {"option":[k for k in city["industry"]], "prob":[float(city["industry"][k]) for k in city["industry"]]},
                            # "gender" : {"option":["male", "female"], "prob":[float(city["gender"]["male"]), float(city["gender"]["female"])]},
                            "education" : self._compute_prob("education", city),
                            "race" : self._compute_prob("race", city),
                            "income" : self._compute_prob("income", city),
                            "industry" : self._compute_prob("industry", city),
                            "gender" : self._compute_prob("gender", city),
                            "district" : {},
                        }
                    if city["city"]==self.user_info["city"]:
                        self.tree["prob"].append(float(city["similarity"]) + CONFIG["user_info_rate"])
                        _p += float(city["similarity"]) + CONFIG["user_info_rate"]
                    else:
                        self.tree["prob"].append(float(city["similarity"]))
                        _p += float(city["similarity"])
                self.tree["prob"] = [x / _p for x in self.tree["prob"]]
            except:
                if try_idx + 1 == retry:
                    self.status = "error"
                    raise Exception(f"Search cities failed {retry} times")
                else:
                    continue
            else:
                return True
            
    def _compute_prob(self, aim_key:str, ans_dic:list) -> dict:
        if self.user_info[aim_key]:
            options = []
            probs = []
            for k in ans_dic[aim_key]:
                options.append(k)
                if k==self.user_info[aim_key]:
                    probs.append(float(ans_dic[aim_key][k]) + CONFIG["user_info_rate"])
                else:
                    probs.append(float(ans_dic[aim_key][k]))
            probs = [p / sum(probs) for p in probs]
            return {"option":options, "prob":probs}
        else:
            return {"option":[k for k in ans_dic[aim_key]], "prob":[float(ans_dic[aim_key][k]) for k in ans_dic[aim_key]]}


    def _search_city_state_chat(self, city, state, size=5):
        industries = {key : "population_percentage_in_decimal" for key in CONFIG["industry"]}
        educations = {key : "population_percentage_in_decimal" for key in CONFIG["education"]}
        races = {key : "population_percentage_in_decimal" for key in CONFIG["race"]}
        incomes = {key : "population_percentage_in_decimal" for key in CONFIG["income"]}
        if "city":
            prompt = f"{city} is a city in {state} state. Based on your understanding, make an evaluation from the dimensions of climate, geographical conditions, and economic development. " 
            # prompt = f"Please find me {size} cities in the US (including {city}), rating them use the similarity to the {city}. " 
        else:
            prompt = f"Please find me {size} most representive cities in the US, rating them use the similarity. " 
        prompt += "Furthermore, tell me about the population statistic in each state. These data need to be based on real data, from resources like census bureau or government report. "
        prompt += "The data should based on real information during 2010 to 2020. Decimal precision needs to reach 4 decimal places. "
        prompt += "Return your answer in the following JSON format without any other information: "
        prompt += "{\"response\" : [{\"city\" : \"city_name\", \"state\" : \"state/province\", \"similarity\" : \"similarity_to_given_city_in_decimal\", "
        prompt += f"\"education\": {json.dumps(educations)}, "
        prompt += f"\"income\": {json.dumps(incomes)}, "
        prompt += f"\"industry\": {json.dumps(industries)}, "
        prompt += f"\"race\": {json.dumps(races)}, "
        prompt += "\"gender\": {\"male\":\"gender_percentage_in_decimal\", \"female\":gender_percentage_in_decimal}}, ...], "
        prompt += "\"information\" : \"put_other_information_you_want_to_tell_here\"}"

        if CONFIG["debug"]: print(prompt)
        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
            
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG["debug"]: print(completion.choices[0].message.content)
        cities = json.loads(completion.choices[0].message.content)["response"]
        if CONFIG["debug"]: print(cities)

        return cities
    

    def _search_district(self, u_city, u_state, city, state, district, size=5, retry=5):
        for try_idx in range(retry):
            try:
                res = self._search_district_chat(u_city, u_state, city, state, district, size)
            except:
                if try_idx + 1 == retry:
                    self.status = "error"
                    raise Exception(f"Search districts failed {retry} times")
                else:
                    continue
            else:
                return res

    def _search_district_chat(self, u_city, u_state, city, state, district, size=5):
        prompt = f"{district} is a zone in {u_city}, {u_state}. "
        prompt += "Based on your knowledge, to evaluate the convenience of this district, including the population, the infrastructure, and the medical and educational resources. "
        prompt += f"Please find me {size} districts with similar conditions in {city}, {state}. Besides, give me {size} streets in these districts that suitable for living. "
        prompt += "Return your answer in the following JSON format: "
        prompt += "{\"response\" : [{\"district\" : \"district_1\", \"similarity\" : \"similarity_to_given_district_in_decimal\", \"streets\":[\"street_1\", ..., \"street_N\"], ...], "
        prompt += "\"information\" : \"put_other_information_you_want_to_tell_here\"}"
        
        if CONFIG["debug"]: print(prompt)
        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
                        messages=[{
                "role": "user", "content": prompt
                }]
        )
        if CONFIG["debug"]: print(completion.choices[0].message.content)

        districts = json.loads(completion.choices[0].message.content)["response"]
        res = {"option":{}, "prob":[]}
        _p = 0.0
        for idx, district in enumerate(districts):
            res["option"][str(idx)] = {
                    "district" : district["district"],
                    "street" : district["streets"],
                }
            res["prob"].append(float(district["similarity"]))
            _p += float(district["similarity"])
        res["prob"] = [x / _p for x in res["prob"]]

        return res
    

    def _search_disease(self, disease, size=10, retry=5):
        # res = self._search_disease_chat(disease, size)
        # self.tree["disease"] = res
        if self.user_info["disease"]:
            self.tree["disease"] = {"option": [self.user_info["disease"]], "prob": [1.0]}
        else:
            for try_idx in range(retry):
                try:
                    res = self._search_disease_chat(disease, size)
                except:
                    if try_idx + 1 == retry:
                        self.status = "error"
                        raise Exception(f"Search disease failed {retry} times")
                    else:
                        continue
                else:
                    self.tree["disease"] = res
                    return True

    def _search_disease_chat(self, disease, size=10):
        age = int(date.today().year) - int(self.user_info["birthday"].split("-")[-1])
        prompt = f"There is a {age} {self.user_info['gender']} who has {disease}. "
        prompt += f"Now you need to provide {size} other diseases, with a detailed analysis, that share similar symptoms, impacts on health, methods of transmission (if applicable), and treatment approaches. "
        prompt += "For each related disease you identify, explain why it is relevant to the disease in question, focusing on the similarities in their clinical presentations, epidemiology, and management strategies. "
        prompt += "T0 figure out this question, let's think step by step. Do it in the following format, and keep the JSON format of the final Answer:\n"
        prompt += "Thought 1: your thought about this question\n...\nThought n: your thought about this question\nFinal Answer:\n"
        ans = {f"disease_{i}":{"name":"disease_name","stage":"disease_progression","similarity":"similarity_to_the_given_disease_in_float"} for i in range(1, size+1)}
        prompt += json.dumps(ans)

        if CONFIG["debug"]: print(prompt)
        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
            messages=[{
                "role": "user", "content": prompt
            }]
        )
        if CONFIG["debug"]: print(completion.choices[0].message.content)

        json_strs = re.findall(r"\{(?:[^{}])*\}", completion.choices[0].message.content.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL)
        if json_strs: 
            res = {"option":[], "prob":[]}
            _p = 0.0
            for _, json_str in enumerate(json_strs):
                disease = json.loads(json_str)
                res["option"].append(f"{disease['name']} ({disease['stage']})")
                res["prob"].append(float(disease["similarity"]))
                _p += float(disease["similarity"])
            res["prob"] = [x / _p for x in res["prob"]]
            return res
        else:
            raise Exception("GPT response error.")
        

<<<<<<< Updated upstream
    def _infer_addtional(self, gender, race, location, education, income_range, age_range=5):
        age = int(date.today().year) - int(self.user_info["birthday"].split("-")[-1])
        prompt = f"There is a {race} {gender} living in {location} who has {education} degree. "
        prompt += "Based on the gender and race information, firstly figure out a name. Tell me the exact zip code of where he/she lives, and possible spoken language. "
        prompt += f"Secondly, based on income range {income_range}, you need to find a building in the location that is suitable to live as home in {location}. "
        prompt += "The building should be affordable and consistent with income levels, whether rented, financed, or already owned. "
        prompt += f"Next, the range of the age is {age-age_range}-{age+age_range}, please generate a birthday in this range. "
=======
    def _infer_addtional(self, gender, race, location, education, income_range, age):
        age = int(date.today().year) - int(self.user_info["birthday"].split("-")[-1])
        prompt = f"There is a {race} {gender} living in {location} who has a {education} degree, age {age}. "
        prompt += f"First, generate a birthday based on their age range. (It's {date.today().year} now.) "
        prompt += "Based on their gender and race, generate a name and their spoken languages. "
        prompt += f"Based on their income range {income_range}, generate a home address for them."
        prompt += f"Find a residential building in {location} that is affordable and reasonable based on their age and income level. "
        prompt += "Be mindful that a place could be rented, financed, or owned. "
>>>>>>> Stashed changes
        prompt += "Return your answer in the following JSON format: "
        prompt += "{\"response\" : {\"name\" : \"firstname familyname\", \"birthday\" : \"MM-DD-YYYYY\", "
        prompt += "\"language\" : \"language\", \"zipcode\" : \"zipcode\", \"building\":\"building_name\","
        prompt += "\"home_longitude\":\"home_longitude_format_as_xx.xxxxxx\", \"home_latitude\":\"home_latitude_format_as_xx.xxxxxx\""
        prompt += "\"information\" : \"put_other_information_you_want_to_tell_here\"}"
        

        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        print("evidence-bases")
        print(json.loads(completion.choices[0].message.content)["response"])
        return json.loads(completion.choices[0].message.content)["response"]
    

<<<<<<< Updated upstream
    def _infer_occupation(self, name, income_range, location, education, industry, disease):
        age = int(date.today().year) - int(self.user_info["birthday"].split("-")[-1])
        prompt = f"{name}, {age} years old, lives in {location} who has {education} degree. "
        prompt += f"Based on collected information, we know that {name} working in {industry}, with income range {income_range}. "
        prompt += "Based on all of the provided information and your inference, provide a reasonable job for him/her and if he/she is retired. "
        prompt += f"And grant {name} a reasonable and annual salary, a exact number in US dollar in the given income range. "
        prompt += "This job needs to be specific and consistent with the career plan of this industry. "
        prompt += "You also have to consider his educational background and age to determine if the job fits your reasoning. "
        prompt += f"Normmaly people usaully get retired after a specific age, you need consider the {name}'s age ({age}) amd body status ({disease}). "
        prompt += "There are some jobs that allow people to work no matter how old they are, like professors, CEO, etc."
        prompt += f"And based on your inference, you need to find a working place in where {name} lives. You need provide a company name and address of this company. "
        prompt += "The company address need to be exact and format as \"{building}, {strteet}, {district}, {city}, {state}\""
=======
    def _infer_occupation(self, name, age, income_range, location, education, industry, disease):
        age = int(date.today().year) - int(self.user_info["birthday"].split("-")[-1])
        prompt = f"{name}, {age} years old, lives in {location} who has {education} degree. Their income range is {income_range}. They have these diseases: {disease}"
        # #evidence-based
        # prompt = f"Currently, the person's weight is {weight}. "
        prompt += f"Based on all of the provided information, provide a job for them in industry: '{industry}', and determine if they have retired now. "
        #prompt += "This job needs to be specific and consistent with the career plan of this industry. "
        prompt += f"This job needs to be reasonable, specific, and aligned with the industry and their income range. "
        prompt += "You also have to consider their educational background and age to determine if the job fits a reasonable career path. "
        prompt += "After assigning a job for them, infer their retirement status based on their age and health status. "
            #"and their health status. "
        prompt += "People normally retire after a specific age (based on policy). "
        prompt += "Even if they have retired, they might be participating in some volunteering and part-time works, based on their expertise and interests. "
        prompt += f"After determining their job, grant {name} an annual salary. "
        prompt += f"Their annual salary should be a reasonable number in US dollar, within their income range '{income_range}', and aligned with their retirement status and location. "
        prompt += f"Afterwards, based on {name}'s current job, find a specific company for them."
        prompt += "First, generate a company name that aligned with their occupation and location. "
        prompt += "Then, determine the address of that company."
        prompt += f"No matter if the company was made up or not, the address needs to be REAL, located in {location}, aligned with where {name} live. " 
        prompt += "The format of that address should be standard USPS address: \"{building}, {street}, {city}, {state}, {zipcode}\""
        prompt += "At last, based on all the information you have generated, add 2-3 sentences about some other information that could be helpful. Could be related to their hobbies, social networks, personality, or anything you can think of."
>>>>>>> Stashed changes
        prompt += "Return your answer in the following JSON format: "
        prompt += "{\"response\" : {\"job\" : \"job\", \"company\" : \"company_name\", \"work_addr\":\"company_address\", \"income\":\"annual_salary\""
        prompt += "\"work_longitude\" : \"work_longitude_format_as_xx.xxxxxx\", \"work_latitude\" : \"work_latitude_format_as_xx.xxxxxx\", \"retirement\":\"retired_or_working\""
        prompt += "\"information\" : \"put_other_information_you_want_to_tell_here\"}"
        

        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
            
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        print("evidence-based")
        print(json.loads(completion.choices[0].message.content)["response"])
        return json.loads(completion.choices[0].message.content)["response"]


    def generate_info_dict(self, healthy_rate=0.7):
        res = {key:None for key in self.user_info}
        city_choice = random.choices([str(i) for i in range(len(self.tree["prob"]))], weights=self.tree["prob"])[0]
        city = self.tree["option"][city_choice]
        res["city"] = city["city"]
        res["state"] = city["state"]

        ## For Evidence-Based
        res["gender"] = random.choices(["male", "female"], weights=[0.2, 0.8])[0]
        ##################### 
        res["race"] = random.choices(city["race"]["option"][:-1], weights=city["race"]["prob"][:-1])[0]
        res["education"] = random.choices(city["education"]["option"], weights=city["education"]["prob"])[0]

        income_range =  random.choices(city["income"]["option"], weights=city["income"]["prob"])[0]
        res["industry"] = random.choices(city["industry"]["option"], weights=city["industry"]["prob"])[0]

        district_choice = random.choices([str(i) for i in range(len(city["district"]["prob"]))], weights=city["district"]["prob"])[0]
        district = city["district"]["option"][district_choice]
        res["district"] = district["district"]
        res["street"] = random.choices(district["street"])[0]
        
        add_info = self._infer_addtional(
            gender=res["gender"],
            race=res["race"],
            education=res["education"],
            income_range=income_range,
            location=f"{res['street']}, {res['district']}, {res['city']}, {res['state']}"
        )
        res["name"] = add_info["name"]
        res["birthday"] = add_info["birthday"]
        res["zipcode"] = add_info["zipcode"]
        res["language"] = add_info["language"]
        res["building"] = add_info["building"]
        res["home_longitude"] = add_info["home_longitude"]
        res["home_latitude"] = add_info["home_latitude"]

        
        ## For Evidence-Based
        if self.user_info['disease']=="healthy controll":
            res["age"] = int(np.random.normal(loc=70.55, scale=7.5, size=None))
            res["weight"] = "{:.2f} lbs".format(int(np.random.normal(loc=179.95, scale=42.2, size=None)))
            res["BMI"] = "{:.2f}".format(np.random.normal(loc=30.15, scale=7.0, size=None))
            res["disease"] = ""
            res["disease"] += random.choices(["Use assisted device; ", ""], weights=[0.545, 0.455])[0]
            res["disease"] += random.choices(["has uncontrolled heart, ", ""], weights=[0.364, 0.636])[0]
            res["disease"] += random.choices(["stroke, ", ""], weights=[0.091, 0.909])[0]
            res["disease"] += random.choices(["high blood pressure, ", ""], weights=[0.545, 0.455])[0]
            res["disease"] += random.choices(["diabetes, ", ""], weights=[0.273, 0.727])[0]
            res["disease"] += random.choices(["osteoporosis, ", ""], weights=[0.545, 0.455])[0]
            res["disease"] += random.choices(["take more than four medications.", "Healthy"], weights=[0.273, 0.727])[0]
        elif self.user_info['disease']=="subjects":
            res["age"] = int(np.random.normal(loc=69.31, scale=7.3, size=None))
            res["weight"] = "{:.2f} lbs".format(int(np.random.normal(loc=183.11, scale=39.8, size=None)) )
            res["BMI"] = "{:.2f}".format(np.random.normal(loc=31.4, scale=7.4, size=None))
            res["disease"] = ""
            res["disease"] += random.choices(["Use assisted device; ", ""], weights=[0.308, 0.692])[0]
            res["disease"] += random.choices(["has uncontrolled heart, ", ""], weights=[0.269, 0.731])[0]
            res["disease"] += random.choices(["stroke, ", ""], weights=[0.231, 0.769])[0]
            res["disease"] += random.choices(["high blood pressure, ", ""], weights=[0.769, 0.231])[0]
            res["disease"] += random.choices(["diabetes, ", ""], weights=[0.423, 0.577])[0]
            res["disease"] += random.choices(["osteoporosis, ", ""], weights=[0.538, 0.462])[0]
            res["disease"] += random.choices(["take more than four medications.", "Healthy"], weights=[0.462, 0.538])[0]
        else:
            res["age"] = int(np.random.normal(loc=70.0, scale=7.5, size=None))
            res["weight"] = "{:.2f} lbs".format(int(np.random.normal(loc=181, scale=41.0, size=None)))
            res["BMI"] = "{:.2f}".format(np.random.normal(loc=31.0, scale=7.0, size=None))
            res["disease"] = ""
            res["disease"] += random.choices(["Use assisted device; ", ""], weights=[0.389, 0.611])[0]
            res["disease"] += random.choices(["has uncontrolled heart, ", ""], weights=[0.3, 0.7])[0]
            res["disease"] += random.choices(["stroke, ", ""], weights=[0.2, 0.8])[0]
            res["disease"] += random.choices(["high blood pressure, ", ""], weights=[0.72, 0.28])[0]
            res["disease"] += random.choices(["diabetes, ", ""], weights=[0.38, 0.62])[0]
            res["disease"] += random.choices(["osteoporosis, ", ""], weights=[0.55, 0.45])[0]
            res["disease"] += random.choices(["take more than four medications.", "Healthy"], weights=[0.41, 0.59])[0]
        #####################


        job_info = self._infer_occupation(
            name=res["name"],
            income_range=income_range,
            education=res["education"],
            location=f"{res['street']}, {res['district']}, {res['city']}, {res['state']}",
            industry=res["industry"],
            disease=res["disease"]
        )
        res["income"] = job_info["income"]
        res["occupation"] = job_info["job"]
        res["retirement"] = job_info["retirement"]
        res["company"] = job_info["company"]
        res["work_addr"] = job_info["work_addr"]
        res["work_longitude"] = job_info["work_longitude"]
        res["work_latitude"] = job_info["work_latitude"]

        return res


    def get_status(self):
        return self.status


