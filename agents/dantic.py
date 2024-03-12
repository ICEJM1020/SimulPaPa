""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-03-12
""" 

from pydantic import BaseModel, Field




class ScheduleEntry(BaseModel):
    start_time: str = Field(description='Start time of an scheduel event in the format of MM-DD-YYYY HH:MM')
    end_time: str = Field(description='End time of an scheduel event in the format of MM-DD-YYYY HH:MM')
    event: str = Field(description='An event (noun word or phrase)')
    # address: str = Field(description='The place where the event happen, must including four parts: street, city, state, and zipcode')
    # latitude: float = Field(description='The corresponding latitude of the address')
    # longitude: float = Field(description='The corresponding longitude of the address')

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


class ActivitySet(BaseModel):
    activity: list[str] = Field(description='A list of activities (a present continuous verb phrase)')



