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

    def dump_list(self):
        return [i.dump_dict() for i in self.decompose]


class LocationEntry(BaseModel):
    start_time : str = Field(description='Start time of this activity in the format of MM-DD-YYYY HH:MM')
    end_time : str = Field(description='Start time of this activity in the format of MM-DD-YYYY HH:MM')
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

    def dump_list(self):
        return [i.dump_dict() for i in self.location]


class ChatBotEntry(BaseModel):
    time : str = Field(description='time when use Chatbot in the format of MM-DD-YYYY HH:MM')
    conv : str = Field(description='Chatbot conversation with human')

    def dump_dict(self):
        res = {
            'time' : self.location,
            'conv' : self.longitude
        }
        return res

class Chatbot(BaseModel):
    chatbot: list[ChatBotEntry]

    def dump_dict(self):
        res = {}
        for item in self.chatbot:
            res[item["time"]] = item["conv"]
        return res


class ActivitySet(BaseModel):
    activity: list[str] = Field(description='A list of activities (a present continuous verb phrase)')



