import csv
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List, Set
from datetime import datetime, timezone
from pathlib import Path
from tqdm import tqdm

from my_lib.api import search_events
from my_lib.data_structures import EventData
from my_lib.consts import REPOSITORY_ROOT

# will later use REPOSITORY_ROOT to access events.csv
def is_event_irrelevant(data: EventData):
    t = str(data.title).lower()
    if 'ethereum' in t or 'mention markets' in t: return True
    if 'pope' in t: return True
    if 'of vote' in t: return True # don't want percentage of votes
    if 'share' in t: return True # don't want share of votes
    if 'turnout' in t: return True # don't want turnout
    if 'odds' in t: return True # don't want secondary bets
    if 'jail' in t: return True
    if 'disqualified' in t: return True
    if 'deputy leadership' in t: return True
    if 'ballots' in t: return True
    if 'ban ' in t: return True
    if 'arrested' in t or 'guilty' in t or 'released from custody' in t or 'impeached' in t: return True
    if 'debate' in t: return True
    if 'endorse' in t: return True
    if 'approval' in t: return True
    if 'drop out' in t or 'resigns' in t or 'resign' in t or ' out ' in t or ' drops out ' in t: return True
    if 'announces' in t or 'announce ' in t: return True
    if 'disqualify' in t: return True
    if t in ["nothing ever happens: france edition", "u.s. withdraws from syria before july?", "progressive cities parlay"]: return True
    return False


def filter_events(events: set[EventData]) -> set[EventData]:
    out = set()
    for event in events:
        if is_event_irrelevant(event):
            continue
        out.add(event)
    return out



def main():

    SLUGS = [
        "elections",
        "global-elections",
        "main-election",
        "world-election",
        "world-elections"
    ]

    combined_events = set()
    for slug in SLUGS:
        for event in search_events(1000,slug):
            combined_events.add(event)

    combined_events = filter_events(combined_events)
    print(f"Found {len(combined_events)} unique election events")

    first_event = combined_events.pop()
    with open(f"{REPOSITORY_ROOT}/data/events.csv",'w') as f:
        writer = csv.DictWriter(f,fieldnames=first_event.to_dict().keys())
        writer.writeheader()
        writer.writerow(first_event.to_dict())
        for event in combined_events:
            writer.writerow(event.to_dict())

    with  open(f"{REPOSITORY_ROOT}/data/events.csv",'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            combined_events.add(EventData.from_dict(row))


if __name__ == "__main__":
    main()