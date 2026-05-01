from dataclasses import dataclass


@dataclass(frozen=True)
class EventData:
    id : int
    title : str
    start_date : str
    end_date : str
    volume : str

    
    def to_dict(self):
        return {
            "id" : self.id,
            "title" : self.title,
            "startDate" : self.start_date,
            "endDate" : self.end_date,
            "volume" : self.volume
        }

    @staticmethod
    def from_dict(dict):
        event_id_str = dict.get("id")        
        event_id = int(event_id_str)
        event_title = dict.get("title")
        start_date = dict.get("startDate")
        end_date = dict.get("endDate")
        volume = dict.get("volume")
        return EventData(event_id,event_title,start_date,end_date,volume)

