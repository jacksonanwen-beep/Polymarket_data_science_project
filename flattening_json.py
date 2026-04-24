import pandas as pd
import json

def flatten_polymarket_data(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)

    flat_rows = []

    print("Flattening data...")

    for event_id, event_info in data.items():
        event_title = event_info.get("event_title")
        
        markets = event_info.get("markets", {})
        
        for question, outcomes in markets.items():
            for outcome_name, price_data in outcomes.items():
                
                history = price_data.get("history", [])
                
                for point in history:
                    
                    row = {
                        "Event_ID": event_id,
                        "Event_Title": event_title,
                        "Question": question,
                        "Outcome_Name": outcome_name,
                        "Timestamp": point.get("t"),
                        "Price": point.get("p")
                    }
                    
                    flat_rows.append(row)

    print(f"Extracted {len(flat_rows)} individual price points. Converting to DataFrame...")
    
    df = pd.DataFrame(flat_rows)
    
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Timestamp'], unit='s')
    else:
        print("WARNING: The DataFrame is empty. No price history was found in the JSON.")
    
    return df


df = flatten_polymarket_data('./all-data.json')

print(df.head())

df.to_csv('polymarket_election_data.csv', index=False)

print("Saved successfully to CSV!")