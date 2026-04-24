from typing import Dict, List
from datetime import datetime, timezone
import re
import requests
import json
import time

EVENT_ENDPOINT = "https://gamma-api.polymarket.com/events/keyset"

def date_string_to_unix_timestamp(date: str) -> int:
    date = re.sub("\.[0-9]+Z","Z",date)
    dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
    timestamp = int(dt.timestamp())
    
    return timestamp


def get_market_details(event_ID):
    response = requests.get("https://gamma-api.polymarket.com/events/" + str(event_ID))
    
    if response.status_code != 200:
        return {}
    
    data = response.json()
    markets = data.get("markets", [])
    dictionary = {}
    
    for market in markets:
        raw_tokens = market.get("clobTokenIds")
        raw_outcomes = market.get("outcomes")
        
        if isinstance(raw_tokens, str):
            clobTokenIds = json.loads(raw_tokens)
        elif isinstance(raw_tokens, list):
            clobTokenIds = raw_tokens
        else:
            clobTokenIds = []
            
        if isinstance(raw_outcomes, str):
            outcomes = json.loads(raw_outcomes)
        elif isinstance(raw_outcomes, list):
            outcomes = raw_outcomes
        else:
            outcomes = []

        question = market.get("question")

        if question and len(outcomes) > 0 and len(outcomes) == len(clobTokenIds): 
            dictionary[question] = dict(zip(outcomes, clobTokenIds))
    
    return dictionary

import requests
def get_event_IDs():
    event_ids = []
    
    limit = 100
    offset = 0

    
    while True:
        query_params = {
            "limit": limit,
            "offset": offset,
            "closed": "true",
            "title_search": "Election"
            }
        
        response = requests.get("https://gamma-api.polymarket.com/events",  params = query_params)
        
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}")
            return {}
        
        events_page = response.json()
        if len(events_page) == 0:
            break

        for event in events_page:
            if "id" in event:
                event_ids.append(event["id"])
    
        offset += 100

    print(event_ids)
    print(f"Found {len(event_ids)} event IDs with titles containing {query_params['title_search']}.")
    
    return event_ids

get_event_IDs()

def get_events_titles_and_timestamps() -> Dict[int,Dict]:
    limit = 100
    offset = 0

    dictionary = {}

    while True:
        query_params = {
            "limit": limit,
            "offset": offset,
            "closed": "true",
            "title_search": "Election"
            }
   
        response = requests.get("https://gamma-api.polymarket.com/events", params = query_params)
    
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}")
            return {}
        
        events_data = response.json()
    
        if len(events_data) == 0:
            break

        for event in events_data:
            event_id_str = event.get("id")
            if not event_id_str:
                continue
        
            event_id = int(event_id_str)
        
            event_title = event.get("title")
            start_date = event.get("startDate", "")
            end_date = event.get("endDate", "")
        
            dictionary[event_id] = {
                "event_title": event_title,
                "event_start_timestamp": date_string_to_unix_timestamp(start_date) if start_date else 0,
                "event_end_timestamp": date_string_to_unix_timestamp(end_date) if end_date else 0
                }
        
        offset += limit
    
    print(f"Found {len(dictionary)} events with titles containing {query_params['title_search']}")
    return dictionary


def get_price_history(clob_token:str, startTs: int): 
    query_params = {
        "market" : clob_token,
        "startTs" : startTs,
        "interval" : "max",
        "fidelity" : 720
    }
    response = requests.get("https://clob.polymarket.com/prices-history", params=query_params)
    if response.status_code == 200:
        return response.json()
    return{}


def main():
    print("STAGE 1: Fetching Events...")
    events = get_events_titles_and_timestamps()
    with open('./events.json','w') as f:
        json.dump(events, f, indent=4)



    print("STAGE 2: Appending Market Tokens...")
    events_with_market_data = events.copy()
    
    for event_id in events_with_market_data.keys():
        markets = get_market_details(event_id)
        events_with_market_data[event_id]["markets"] = markets
        time.sleep(0.2)

    with open('./events_with_market_data.json', 'w') as f:
        json.dump(events_with_market_data, f, indent=4)



    print("STAGE 3: Fetching Price Histories...")
    events_with_prices = events_with_market_data.copy()
    
    total_events = len(events_with_prices)

    for index, (event_id, event_data) in enumerate(events_with_prices.items()):
        
        start_ts = event_data.get("event_start_timestamp", 0)
        markets = event_data.get("markets") or {} 
        
        for question, outcomes_dict in markets.items():
            for outcome_name, clob_token in outcomes_dict.items():
                
                price_history = get_price_history(clob_token, start_ts)
                outcomes_dict[outcome_name] = price_history
                time.sleep(0.2)

        if (index + 1) % 10 == 0:
            print(f"Downloaded price histories for {index + 1} / {total_events} events...")

    with open("./all-data.json", 'w') as f:
        json.dump(events_with_prices, f, indent=4)
        
    print("Data pipeline complete!")
    return events_with_prices

main()