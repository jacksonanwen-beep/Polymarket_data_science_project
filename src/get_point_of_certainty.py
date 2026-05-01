


from typing import Dict, List
from my_lib.api import date_string_to_unix_timestamp, get_price_data, requests_get
from my_lib.consts import REPOSITORY_ROOT
from tqdm import tqdm
import time
import json


def get_market_certainty_timestamp(market: dict):
    pass


def main():
    with open(f"{REPOSITORY_ROOT}/data/events_with_markets.json", 'r') as f:
        events_with_markets = json.load(f)


    events_with_markets_and_point_of_certainty = []
    for event in tqdm(events_with_markets):
        point_of_certainty = get_point_of_certainty_for_event(event)
        event_copy = event.copy()
        event_copy["time_of_certainty"] = point_of_certainty
        events_with_markets_and_point_of_certainty.append(event_copy)

    with open(f"{REPOSITORY_ROOT}/data/events_with_markets_and_certainty.json", 'w') as f:
        json.dump(events_with_markets_and_point_of_certainty,f, indent=2)


def get_point_of_certainty_for_event(event_data: dict):
    end_date_str = event_data.get('endDate')
    # start date and end date of this event converted to unix
    end_ts = date_string_to_unix_timestamp(end_date_str)
    event_start_ts = date_string_to_unix_timestamp(event_data.get('startDate'))
    # Look back 700 days from the end_date)
    start_ts = end_ts - (700 * 24 * 3600) 

    # create dictionary for full price history of event {question: {t: , p:}}
    full_price_history = {}

    # option = question yes_or_no = tokens. looks specifically at the dictionary within markets, within the same single event as before
    for question, yes_or_no in event_data.get('markets').items():
        # gets the clob token for yes (in each market)
        clob_token = yes_or_no.get('Yes')
        full_price_history[question] = {}
        # gets the price history (t and p) for each clob token. doesn't have anywhere to go though
        price_history = get_price_data(clob_token, max(start_ts,event_start_ts), end_ts, fidelity=60)
        if not clob_token or not end_date_str:
            continue
        else:
            full_price_history[question] = price_history # adds price history from each market to the dictionary

    
    # Fetch the history
    
    if not full_price_history:
        return None


    for question in full_price_history:
        price_pair_list = full_price_history[question] # = list of dictionaries. want to go through the list and get the 'p' value from each dictionary
        
        for pair in price_pair_list: # pair is a dictionary of "p" : price and "t" : timestamp
            price = pair.get("p")
            time = pair.get("t")
                    # Check if price goes above 0.95
            
            if price_pair_list is not None and price > 0.98:
                return time
    
    return end_ts
        

    
                
  


if __name__ == "__main__":
    main()


