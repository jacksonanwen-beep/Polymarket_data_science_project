from typing import Dict
import json
import datetime
import re
import pandas as pd
from tqdm import tqdm

from my_lib.api import get_market_details
from my_lib.consts import REPOSITORY_ROOT
from my_lib.data_structures import EventData


def save_json_file(events_with_markets: Dict[EventData,Dict]):
    json_contents = []
    for event, market_data in events_with_markets.items():
        event_dict = event.to_dict()
        event_dict["markets"] = market_data
        json_contents.append(event_dict)
    
    with open(f"{REPOSITORY_ROOT}/data/events_with_markets.json", 'w') as f:
        json.dump(json_contents, f, indent=2)

if __name__ == "__main__":
    events_basic = pd.read_csv(f"{REPOSITORY_ROOT}/data/events.csv")
    events_all = {}
    for index, row in tqdm(events_basic.iterrows(),total=events_basic.shape[0], desc="Fetching event markets"):
        event = EventData.from_dict(row)
        details = get_market_details(event.id)
        events_all[event] = details
    
    save_json_file(events_all)
