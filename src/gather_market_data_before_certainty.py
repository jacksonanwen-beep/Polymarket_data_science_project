import csv
from dataclasses import asdict, dataclass
import statistics
import json
from typing import Any, Dict, Iterable, List

from tqdm import tqdm
from my_lib.api import date_string_to_unix_timestamp, get_price_data
from my_lib.consts import REPOSITORY_ROOT

@dataclass
class CsvRow:
    event_id: int
    question: str
    outcome: bool
    avg_price: float
    volume: float #added this for kernel curve
    price_std_dev: float # added this for feature importance
    time_before_certainty: int
    offset_before_certainty: int
    collection_period: int
    time_of_event_close: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # normalize bool for CSV (optional but recommended)
        d["outcome"] = int(self.outcome)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CsvRow":
        return cls(
            event_id=int(d["event_id"]),
            question=d["question"],
            outcome=bool(int(d["outcome"])),
            avg_price=float(d["avg_price"]),
            time_before_certainty=int(d["time_before_certainty"]),
            offset_before_certainty=int(d["offset_before_certainty"]),
            collection_period=int(d["collection_period"]),
            time_of_event_close=int(d["time_of_event_close"]),
        )

# renamed from gather_calibration_curve_data.py to gather_market_data_before_certainty.py as the results from this will not only be used for calibration curves, but for a feature importance graph.
def write_csv(path: str, rows: List[CsvRow]) -> None:
    if (len(rows) == 0):
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].to_dict().keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_dict())



def main1():
    with open(f"{REPOSITORY_ROOT}/data/events_with_markets_and_certainty.json", 'r') as f:
        events_with_markets = json.load(f)

    six_months_data = []
    for event in tqdm(events_with_markets):        
        six_months = get_price_data_six_months_before(event)
        if six_months is not None:
            six_months_data += six_months

    write_csv(f"{REPOSITORY_ROOT}/data/market_data_six_months_before_certainty.csv",six_months_data)


def main2():
    with open(f"{REPOSITORY_ROOT}/data/events_with_markets_and_certainty.json", 'r') as f:
        events_with_markets = json.load(f)

    one_months_data = []
    for event in tqdm(events_with_markets):        
        one_month = get_price_data_one_month_before(event)
        if one_month is not None:
            one_months_data += one_month

    write_csv(f"{REPOSITORY_ROOT}/data/market_data_one_month_before_certainty.csv",one_months_data)

def main3():
    with open(f"{REPOSITORY_ROOT}/data/events_with_markets_and_certainty.json", 'r') as f:
        events_with_markets = json.load(f)
    one_weeks_data = []
    for event in tqdm(events_with_markets):        
        one_week = get_price_data_one_week_before(event)
        if one_week is not None:
            one_weeks_data += one_week

    write_csv(f"{REPOSITORY_ROOT}/data/market_data_one_week_before_certainty.csv",one_weeks_data)

def main4():
    with open(f"{REPOSITORY_ROOT}/data/events_with_markets_and_certainty.json", 'r') as f:
        events_with_markets = json.load(f)
    one_days_data = []
    for event in tqdm(events_with_markets):        
        one_day = get_price_data_one_day_before(event)
        if one_day is not None:
            one_days_data += one_day
    
    write_csv(f"{REPOSITORY_ROOT}/data/market_data_one_day_before_certainty.csv",one_days_data)



def get_price_data_before(event:dict, offset_before:int, collection_period:int, fidelity:int):
    event_certainty_date = event["time_of_certainty"]
    event_end_date = date_string_to_unix_timestamp(event['endDate'])
    event_start_data = date_string_to_unix_timestamp(event['startDate'])
    event_volume = float(event.get('volume', 0)) #added this for kernel curve
    six_months_before_certainty = event_certainty_date - offset_before 
    if six_months_before_certainty < event_start_data:
        return None
    
    out = []

    for question, market_data in event["markets"].items():
        clob_token_id = market_data.get('Yes')
        data = get_price_data(
            clob_token_id,
            six_months_before_certainty-collection_period,
            six_months_before_certainty+collection_period,
            fidelity=fidelity)
        price_over_48_hours = list(map(lambda x: float(x.get("p")), data))
        if (len(price_over_48_hours) == 0):
            return
        avg_price = statistics.mean(price_over_48_hours)

        if len(price_over_48_hours) > 1:
            price_std_dev = statistics.stdev(price_over_48_hours)
        else:
            price_std_dev = 0.0

        outcome = int(market_data.get('final_Yes',0))
        
        
        # calculate standard deviation (requires at least two points)
        if len(price_over_48_hours) > 1:
            price_std_dev = statistics.stdev(price_over_48_hours)
        else:
            price_std_dev = 0.0
            
        outcome = int(market_data.get('final_Yes', 0))

        row = CsvRow(
                     event['id'], 
                     question, 
                     outcome,
                     avg_price, 
                     event_volume, # added this for kernel curve
                     price_std_dev, #added this for feature importance
                     offset_before,
                     event_certainty_date,
                     collection_period,
                     event_end_date)
        out.append(row)

    return out


def get_price_data_six_months_before(event: dict):
    SIX_MONTHS = 60*60*24*30*6
    ONE_DAY = 24*60*60 
    return get_price_data_before(event,SIX_MONTHS,ONE_DAY,60)

def get_price_data_one_month_before(event: dict):
    ONE_MONTH = 60*60*24*30
    SIX_HOURS = 60*60*6
    return get_price_data_before(event,ONE_MONTH,SIX_HOURS,30)

def get_price_data_one_week_before(event: dict):
    ONE_WEEK = 60*60*24*7
    ONE_HOUR = 60*60
    return get_price_data_before(event,ONE_WEEK,ONE_HOUR,15)

def get_price_data_one_day_before(event: dict):
    ONE_DAY = 60*60*24
    FIFTEEN_MINUTES = 60*15
    return get_price_data_before(event,ONE_DAY,FIFTEEN_MINUTES,5)

if __name__ == "__main__":
    main1()
    main2()
    main3()
    main4()
