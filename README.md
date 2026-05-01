# **The Illusion of the Safe Bet in Polymarket Election Events**

See the writeup in https://jacksonanwen-beep.github.io/Polymarket_data_science_project/

## **Project Overview**

This project analyses the price history of election events (from 6 months out to 1 day out from market certainty), using calibration curves to assess the accuracy of market predictions in relation to time, and a feature importance plot to consider the individual effect of variables (volatility, volume, event complexity).


## Setup

In order to run the code you must have python3 installed, then setup the virtual environment and install the dependencies with the following commands:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r ./requirements.txt
```


## **How to Reproduce graphs**

Run scripts in following order:
1. `gather_events.py`
2. `gather_event_data.py`
3. `get_point_of_certainty.py`
4. `gather_market_data_before_certainty.py`
5. `generate_one_day_calibration_with_kde.py`,`generate_one_week_calibration_with_kde.py`,`generate_one_month_calibration_with_kde.py`,`generate_six_months_calibration_with_kde.py`,`plot_feature_importance.py`
