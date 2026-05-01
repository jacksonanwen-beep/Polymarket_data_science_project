
from datetime import datetime
import hashlib
import json
import os
import re
from typing import Dict, List, Optional, Set
import requests
import time

from tqdm import tqdm
from my_lib.consts import REPOSITORY_ROOT
from my_lib.data_structures import EventData

CACHE_DIR = f"{REPOSITORY_ROOT}/data/http_cache"

def rate_limited(n_per_sec):
    min_interval = 1.0 / n_per_sec

    def decorator(func):
        next_allowed_time = [time.perf_counter()]

        def wrapper(*args, **kwargs):
            now = time.perf_counter()

            if now < next_allowed_time[0]:
                time.sleep(next_allowed_time[0] - now)

            result = func(*args, **kwargs)

            next_allowed_time[0] = max(
                next_allowed_time[0] + min_interval,
                time.perf_counter()
            )

            return result

        return wrapper
    return decorator

def date_string_to_unix_timestamp(date: str) -> int:
    date = re.sub(r"\.[0-9]+Z","Z",date)
    dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
    timestamp = int(dt.timestamp())
    
    return timestamp

def _make_cache_key(url: str, params: dict) -> str:
    # ensure consistent ordering of params
    params_string = json.dumps(params or {}, sort_keys=True)
    raw_key = f"{url}?{params_string}"
    return hashlib.sha256(raw_key.encode()).hexdigest()

def _get_cache_path(cache_key: str) -> str:
    return os.path.join(CACHE_DIR, f"{cache_key}.json")

def requests_get(url: str, params: dict = None) -> Optional[Dict]:
    os.makedirs(CACHE_DIR, exist_ok=True)

    cache_key = _make_cache_key(url, params)
    cache_path = _get_cache_path(cache_key)

    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            return json.load(f)

    response = server_get(url, params=params)

    if response.status_code != 200:
        return None

    data = response.json()

    # 💾 save to cache
    with open(cache_path, "w") as f:
        json.dump(data, f)

    return data

@rate_limited(100)
def server_get(*args, **kwargs):
    return requests.get(*args, **kwargs)


def get_market_details(event_ID):
    response = requests_get("https://gamma-api.polymarket.com/events/" + str(event_ID))
    markets = response["markets"]
    dictionary = {}
    
    for market in markets:
        if not "clobTokenIds" in market.keys() or not "outcomes" in market.keys() or not "outcomePrices" in market.keys():
            continue

        clobTokenIds = json.loads(market.get("clobTokenIds")) 
        outcomes = json.loads(market.get("outcomes"))
        question = market.get("question")
        outcome_final = json.loads(market.get("outcomePrices"))

        dictionary[question] = {
            outcomes[0] : clobTokenIds[0],
            outcomes[1] : clobTokenIds[1],
            f"final_{outcomes[0]}" : outcome_final[0],
            f"final_{outcomes[1]}" : outcome_final[1]
        }
        
    return dictionary

MAX_INTERVAL = 10 * 24 * 60 * 60  # 10 days

def get_price_data(
    clob_token: str,
    start_timestamp: int,
    end_timestamp: int,
    fidelity=60
    ) -> Optional[List[Dict[str, int]]]:

    all_data = []
    current_start = start_timestamp

    while current_start < end_timestamp:
        current_end = min(current_start + MAX_INTERVAL, end_timestamp)

        query_params = {
            "market" : clob_token,
            "startTs": current_start,
            "endTs": current_end,
            "fidelity": fidelity
        }

        data = requests_get(
            "https://clob.polymarket.com/prices-history",
            params=query_params
        )

        if data:
            all_data.extend(data.get('history'))

        # move to next window
        current_start = current_end

    # sort data
    all_data = sorted(all_data, key=lambda x: x["t"])

    # deduplicate data
    deduped = []
    seen = set()

    for d in all_data:
        t = d["t"]
        if t not in seen:
            seen.add(t)
            deduped.append(d)

    return deduped


def search_events(max_number: int, slug: str, closed=True, prog_bar=True) -> Set[EventData]:
    accumulating_events = set()
    after_cursor = ""

    prog_bar = tqdm(total=max_number) if prog_bar else None 
    while True:
        query_params = {
            "limit":  min(500,max_number - len(accumulating_events)),
            "closed": str(closed),
            "after_cursor" : after_cursor,
            "tag_slug" : slug
            }
        
   
        response = requests_get("https://gamma-api.polymarket.com/events/keyset", params = query_params)
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}")
            return {}
        
        events_data = response.json()
    
        if len(events_data) == 0:
            break

        
        data_to_fetch = [
            "id",  
            "title",
            "startDate",
            "endDate",
            "volume"    
        ]

        for event in events_data.get("events"):
            if False in [x in event.keys() for x in data_to_fetch]:
                continue
            event_id_str = event.get("id")        
            event_id = int(event_id_str)
            event_title = event.get("title")
            start_date = event.get("startDate")
            end_date = event.get("endDate")
            volume = event.get("volume")

            if(int(float(volume)) < 0):
                print(volume)
            

            accumulating_events.add(EventData(event_id,event_title,start_date,end_date,volume))

        prog_bar.update(len(accumulating_events)) if prog_bar else None

        after_cursor = events_data.get("next_cursor")

        if len(accumulating_events) >= max_number or after_cursor is None:
            break

    prog_bar.close() if prog_bar else None
    return accumulating_events


