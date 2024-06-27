""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-03-12
""" 

from pydantic import BaseModel, Field


class ScheduleEntryLocation(BaseModel):
    start_time: str = Field(description='Start time of an scheduel event in the format of MM-DD-YYYY HH:MM')
    end_time: str = Field(description='End time of an scheduel event in the format of MM-DD-YYYY HH:MM')
    event: str = Field(description='An event (noun word or phrase)')
    location: str = Field(description='The place where the event happen, must including two parts: building, street')
    latitude: float = Field(description='The corresponding latitude of the location')
    longitude: float = Field(description='The corresponding longitude of the location')

    def dump_dict(self):
        return {
            "start_time" : self.start_time,
            "end_time" : self.end_time,
            "event" : self.event,
            "location" : self.location,
            "longitude" : self.longitude,
            "latitude" : self.latitude
        }

class ScheduleLocation(BaseModel):
    schedule: list[ScheduleEntryLocation]

    def dump_dict(self):
        return {idx : entry.dump_dict() for idx, entry in enumerate(self.schedule)}


class ScheduleEntry(BaseModel):
    start_time: str = Field(description='Start time of an scheduel event in the format of MM-DD-YYYY HH:MM')
    end_time: str = Field(description='End time of an scheduel event in the format of MM-DD-YYYY HH:MM')
    event: str = Field(description='An event (noun word or phrase)')

    def dump_dict(self):
        return {
            "start_time" : self.start_time,
            "end_time" : self.end_time,
            "event" : self.event
        }
    
class Schedule(BaseModel):
    schedule: list[ScheduleEntry]
    thoughts: str = Field(description='Multiple thoughts that support your reasoning, format as:\nThought 1: your thought about this question\n...\nThought n: your thought about this question')

    def fetch_thoughts(self):
        return self.thoughts

    def dump_dict(self):
        return {idx : entry.dump_dict() for idx, entry in enumerate(self.schedule)}


class DecomposeEntry(BaseModel):
    activity: str = Field(description='An activity (verb word or phrase)')
    start_time: str = Field(description='Start time of this activity in the format of MM-DD-YYYY HH:MM')
    duration: str = Field(description='Duration time of this activity (in minutes)')
    end_time: str = Field(description='After the duration time, the end time of this activity in the format of MM-DD-YYYY HH:MM')

    def dump_dict(self):
        res = {
            'activity' : self.activity,
            'start_time' : self.start_time, 
            'end_time' : self.end_time
        }
        return res


class Decompose(BaseModel):
    decompose: list[DecomposeEntry]
    thoughts: str = Field(description='Multiple thoughts that support your reasoning, format as:\nThought 1: your thought about this question\n...\nThought n: your thought about this question')

    def fetch_thoughts(self):
        return self.thoughts

    def dump_list(self):
        return [i.dump_dict() for i in self.decompose]


class LocationEntry(BaseModel):
    start_time : str = Field(description='Start time of this activity in the format of MM-DD-YYYY HH:MM')
    end_time : str = Field(description='End time of this activity in the format of MM-DD-YYYY HH:MM')
    location: str = Field(description='The place where the activity happen, including two or three parts: room(optional), building, street')
    latitude: float = Field(description='The corresponding latitude of the location')
    longitude: float = Field(description='The corresponding longitude of the location')

    def dump_dict(self):
        res = {
            'location' : self.location,
            'longitude' : self.longitude,
            'latitude' : self.latitude,
            'start_time' : self.start_time, 
            'end_time' : self.end_time
        }
        return res


class Location(BaseModel):
    location: list[LocationEntry]
    thoughts: str = Field(description='Multiple thoughts that support your reasoning, format as:\nThought 1: your thought about this question\n...\nThought n: your thought about this question')

    def fetch_thoughts(self):
        return self.thoughts

    def dump_list(self):
        return [i.dump_dict() for i in self.location]
    

class StepsEntry(BaseModel):
    start_time : str = Field(description='Start time of this activity in the format of MM-DD-YYYY HH:MM.')
    end_time : str = Field(description='End time of this activity in the format of MM-DD-YYYY HH:MM.')
    activity: str = Field(description='The activity taking during this time period.')
    steps: int = Field(description='Average steps per one minute when doing the given activity.')

    def dump_dict(self):
        res = {
            'activity' : self.activity,
            'steps' : self.steps,
            'start_time' : self.start_time, 
            'end_time' : self.end_time
        }
        return res


class Steps(BaseModel):
    step: list[StepsEntry]
    thoughts: str = Field(description='Multiple thoughts that support your reasoning, format as:\nThought 1: your thought about this question\n...\nThought n: your thought about this question')

    def fetch_thoughts(self):
        return self.thoughts

    def dump_dict(self):
        _temp = {}
        for _s in self.step:
            _s_d = _s.dump_dict()
            _temp[_s_d["activity"]] = _s_d["steps"]
        return _temp


class ChatBotEntry(BaseModel):
    time : str = Field(description='time when use Chatbot in the format of MM-DD-YYYY HH:MM')
    conv : str = Field(description='Conversation between Chatbot and Human. Start Chatbot utterence with \"Chatbot:\", start user utterence with \"User\"')

    def dump_dict(self):
        res = {
            'time' : self.time,
            'conv' : self.conv
        }
        return res

class Chatbot(BaseModel):
    chatbot: list[ChatBotEntry]
    thoughts: str = Field(description='Multiple thoughts that support your reasoning, format as:\nThought 1: your thought about this question\n...\nThought n: your thought about this question')

    def fetch_thoughts(self):
        return self.thoughts

    def dump_dict(self):
        res = {}
        for item in self.chatbot:
            _item = item.dump_dict()
            res[_item["time"]] = _item["conv"]
        return res


class HeartRateEntry(BaseModel):
    start_time : str = Field(description='Start time of this heart rate range in the format of MM-DD-YYYY HH:MM')
    end_time : str = Field(description='Start time of this heart rate range in the format of MM-DD-YYYY HH:MM')
    mean: float = Field(description='The mean value of this heart rate range')
    std: float = Field(description='The standard deviation value of heart rate range')

    def dump_dict(self):
        res = {
            'mean' : self.mean,
            'std' : self.std,
            'start_time' : self.start_time, 
            'end_time' : self.end_time
        }
        return res

class HeartRate(BaseModel):
    heartrate: list[HeartRateEntry]
    thoughts: str = Field(description='Multiple thoughts that support your reasoning, format as:\nThought 1: your thought about this question\n...\nThought n: your thought about this question')

    def fetch_thoughts(self):
        return self.thoughts

    def dump_list(self):
        return [i.dump_dict() for i in self.heartrate]

    

class CatelogueMapEntry(BaseModel):
    activity: str = Field(description='The activity in the given activity list.')
    catelogue: str = Field(description='The catelogue to which the activity belongs.')

class CatelogueMap(BaseModel):
    maps: list[CatelogueMapEntry]

    def dump_dict(self):
        res = {}
        for item in self.maps:
            res[item.activity] = item.catelogue
        return res


class ActivitySet(BaseModel):
    activity: list[str] = Field(description='A list of activities (a present continuous verb phrase)')



