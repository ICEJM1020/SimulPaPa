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

from openai import OpenAI

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
    # prompt += "This year is 2023. "
    # prompt += "The income should be in dollars. "
    # prompt += "The birthday should be in the MM-DD-YYYY format. "
    # prompt += "The demographic of this person should represent the US population sample. "
    prompt += "The generated profile should match the following guidance: <"
    prompt += "{Name} is a {age} {race} {gender} living in {street}, {city}, {district}, {state}, {zipcode}. "
    prompt += "The physical status of {Pronoun} is {diesease}. "
    prompt += "{Pronoun} is a {occupation} with annual income {income}, working at {company}, {company_address}. "
    prompt += "{Pronoun} speaks {language}. Pronoun's education background is {education}. "
    prompt += "{Pronoun}'s date of birth is {birthday}.> "
    prompt += "\n And summarize the key information in your generation, and return your answer in JSON format: "
    prompt += "{\"description\":\"profile_description\"}"

    return prompt


def gpt_description(name, birthday, retry=5,  **kwargs):
    for try_idx in range(retry):
        try:
            description = _gpt_description(name, birthday, **kwargs)
            assert "description" in description.keys()
        except:
            if try_idx + 1 == retry:
                raise {"error":"Error generating description."}
            else:
                continue
        else:
            return description
 
def _gpt_description(name, birthday, **kwargs) -> dict:
    open_ai_client = OpenAI( 
        api_key=CONFIG["openai"]["api_key"],
        organization=CONFIG["openai"]["organization"],
    )

    age = int(date.today().year) - int(birthday.split("-")[-1])
    
    prompt = description_prompt(name=name, birthday=birthday, age=age, **kwargs)
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
                raise {"error":"Error generating information."}
            else:
                continue
        else:
            return infos


def _random_generate(short_description) -> dict:
    infos = {key:"" for key in CONFIG["info"]}
    infos["description"] = "profile_description"

    prompt = "Generate a realistic profile corresponding to the following short description:\n"
    prompt += short_description
    prompt += "\n\n"
    # prompt += "Example 1:\nJohn Smith is a 75-year-old Caucasian male living in an apartment at 123 Main Street, Downtown, Anytown, California, 90210. The physical status of him is early-stage Parkinson's disease. He is a retired Engineer with an annual income of $50,000, previously working at ABC Engineering located at 456 Industrial Road, Anytown, California, 90210. John speaks English and holds a Bachelor's degree in Engineering. His date of birth is May 12, 1948."
    # prompt += "\n\n"
    prompt += "This year is 2023. "
    prompt += "The income should be in dollars. "
    prompt += "The birthday should be in the MM-DD-YYYY format. "
    prompt += "Every information should be specific and realistic. "
    prompt += "Here is the template of the profile description:\n"
    prompt += "{Name} is a {age} {race} {gender} living in {street}, {city}, {district}, {state}, {zipcode}. "
    prompt += "The physical status of {Pronoun} is {diesease}. "
    prompt += "{Pronoun} is a {occupation} with annual income {income}, working at {company}, {company_address}. "
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
            self._start_building()


    def _start_building(self):
        thread = threading.Thread(target=self._build_tree)
        self.status = "building"
        thread.start()
    

    def _build_tree(self):
        
        try:
            self._search_city_state(city=self.user_info["city"], state=self.user_info["state"])
        except:
            self.status = "error"
        else:
            for idx in self.tree["option"].keys():
                try:
                    res = self._search_district(
                        u_city=self.user_info["city"],
                        u_state=self.user_info["state"],
                        city=self.tree["option"][idx]["city"],
                        state=self.tree["option"][idx]["state"],
                        district=self.user_info["district"]
                    )
                except:
                    self.status = "error"
                else:
                    self.tree["option"][idx]["district"] = res
                    self.status = "ready"
            with open(self.tree_file, "w") as f:
                json.dump(self.tree, f)


    def _search_city_state(self, city, state, size=3):
        industries = {key : "population_percentage_in_decimal" for key in CONFIG["industry"]}
        educations = {key : "population_percentage_in_decimal" for key in CONFIG["education"]}
        races = {key : "population_percentage_in_decimal" for key in CONFIG["race"]}
        incomes = {key : "population_percentage_in_decimal" for key in CONFIG["income"]}

        prompt = f"{city} is a city in {state} state. Based on your understanding, make an evaluation from the dimensions of climate, geographical conditions, and economic development. " 
        prompt += f"Please find me {size} cities with similar conditions in the US. "
        prompt += "Furthermore, tell me about the population statistic in this state. These data need to be based on real data, from resources like census bureau or government report. "
        #### data based on? gpt3.5 2010-2020, gpt4 census?
        prompt += "The data should based on real information during 2010 to 2020. Decimal precision needs to reach 4 decimal places. "
        prompt += "Return your answer in the following JSON format without any other information: "
        prompt += "{\"response\" : [{\"city\" : \"city_1\", \"state\" : \"state/province_1\", \"similarity\" : \"similarity_to_given_city_in_decimal\", "
        prompt += f"\"education\": {json.dumps(educations)}, "
        prompt += f"\"income\": {json.dumps(incomes)}, "
        prompt += f"\"industry\": {json.dumps(industries)}, "
        prompt += f"\"race\": {json.dumps(races)}, "
        prompt += "\"gender\": {\"male\":\"gender_percentage_in_decimal\", \"female\":gender_percentage_in_decimal}}, ...], "
        prompt += "\"infomation\" : \"put_other_infomation_you_want_to_tell_here\"}"

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

        _p = 0.0
        self.tree["option"] = {}
        self.tree["prob"] = []
        for idx, city in enumerate(cities):
            self.tree["option"][str(idx)] = {
                    "city" : city["city"],
                    "state" : city["state"],
                    "education" : {"option":[k for k in city["education"]], "prob":[float(city["education"][k]) for k in city["education"]]},
                    "race" : {"option":[k for k in city["race"]], "prob":[float(city["race"][k]) for k in city["race"]]},
                    "income" : {"option":[k for k in city["income"]], "prob":[float(city["income"][k]) for k in city["income"]]},
                    "industry" : {"option":[k for k in city["industry"]], "prob":[float(city["industry"][k]) for k in city["industry"]]},
                    "gender" : {"option":["male", "female"], "prob":[float(city["gender"]["male"]), float(city["gender"]["female"])]},
                    "district" : {},
                }
            self.tree["prob"].append(float(city["similarity"]))
            _p += float(city["similarity"])
        self.tree["prob"] = [x / _p for x in self.tree["prob"]]
        # print(self.tree)
    

    def _search_district(self, u_city, u_state, city, state, district, size=3):
        prompt = f"{district} is a zone in {u_city}, {u_state}. "
        prompt += "Based on your knowledge, to evaluate the convenience of this district, including the population, the infrastructure, and the medical and educational resources. "
        prompt += f"Please find me {size} districts with similar conditions in {city}, {state}. Besides, give me {size} streets in these districts that suitable for living. "
        prompt += "Return your answer in the following JSON format: "
        prompt += "{\"response\" : [{\"district\" : \"district_1\", \"similarity\" : \"similarity_to_given_district_in_decimal\", \"streets\":[\"street_1\", ..., \"street_N\"], ...], "
        prompt += "\"infomation\" : \"put_other_infomation_you_want_to_tell_here\"}"
        
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
    

    def _infer_addtional(self, gender, race, location, education, income_range, age_range=5):
        age = int(date.today().year) - int(self.user_info["birthday"].split("-")[-1])
        prompt = f"There is a {race} {gender} living in {location} who has {education} degree. "
        prompt += "Based on the gender and race information, firstly figure out a name. Tell me the exact zip code of where he/she lives, and possible spoken language. "
        prompt += f"Secondly, based on income range {income_range}, you need to find a building in the location that is suitable to live as home in {location}. "
        prompt += "The building should be affordable and consistent with income levels, whether rented, financed, or already owned. "
        prompt += f"Next, the range of the age is {age-age_range}-{age+age_range}, please generate a birthday in this range. "
        prompt += "Return your answer in the following JSON format: "
        prompt += "{\"response\" : {\"name\" : \"firstname familyname\", \"birthday\" : \"MM-DD-YYYYY\", "
        prompt += "\"language\" : \"language\", \"zipcode\" : \"zipcode\", \"building\":\"building_name\","
        prompt += "\"home_longitude\":\"home_longitude_format_as_xx.xxxxxx\", \"home_latitude\":\"home_latitude_format_as_xx.xxxxxx\"}, "
        prompt += "\"infomation\" : \"put_other_infomation_you_want_to_tell_here\"}"
        

        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
            
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        return json.loads(completion.choices[0].message.content)["response"]
    

    def _infer_occupation(self, name, income_range, location, education, industry):
        age = int(date.today().year) - int(self.user_info["birthday"].split("-")[-1])
        prompt = f"{name}, {age} years old, lives in {location} who has {education} degree. "
        prompt += f"Based on collected information, we that {name} working in {industry}, with income range {income_range}. "
        prompt += "Based on all of the provided information and your inference, provide a reasonable job for him/her and if he/she is retired. "
        prompt += f"And grant {name} a reasonable and annual salary, a exact number in US dollar in the given income range. "
        prompt += "This job needs to be specific and consistent with the career plan of this industry. "
        prompt += "You also have to consider his educational background and age to determine if the job fits your reasoning. "
        prompt += f"And based on your inference, you need to find a working place in where {name} lives. You need provide a company name and address of this company. "
        prompt += f"It's better to find a real company, but it is also possible to create a fake company. "
        prompt += "However, no matter the company is real or fake, the address need to be exact real, and format as \"{building}, {strteet}, {district}, {city}, {state}\""
        prompt += "Return your answer in the following JSON format: "
        prompt += "{\"response\" : {\"job\" : \"job\", \"company\" : \"company_name\", \"work_addr\":\"company_address\", \"income\":\"annual_salary_format_as\""
        prompt += "\"work_longitude\" : \"work_longitude_format_as_xx.xxxxxx\", \"work_latitude\" : \"work_latitude_format_as_xx.xxxxxx\", \"retirement\":\"retired_or_working\"}, "
        prompt += "\"infomation\" : \"put_other_infomation_you_want_to_tell_here\"}"
        

        completion = self.gpt_client.chat.completions.create(
            model = CONFIG["openai"]["model"], 
            
            messages=[{
                "role": "user", "content": prompt
                }]
        )
        return json.loads(completion.choices[0].message.content)["response"]


    def generate_info_dict(self):
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
        
        return res


    def get_status(self):
        return self.status
    

