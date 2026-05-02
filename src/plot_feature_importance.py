import os
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import PartialDependenceDisplay
import matplotlib.pyplot as plt

from my_lib.consts import REPOSITORY_ROOT


def plot_feature_importance_with_price_volatility():
    # load data for prices of markets before certainty (p>0.98)
    files = [f'{REPOSITORY_ROOT}/data/market_data_six_months_before_certainty.csv', f'{REPOSITORY_ROOT}/data/market_data_one_month_before_certainty.csv',
         f'{REPOSITORY_ROOT}/data/market_data_one_week_before_certainty.csv', f'{REPOSITORY_ROOT}/data/market_data_one_day_before_certainty.csv']
    dataframes = [pd.read_csv(f) for f in files if os.path.exists(f)]
    df = pd.concat(dataframes)

    # target: absolute error
    df['abs_error'] = (df['outcome'] - df['avg_price']).abs()

    # feature 'num_markets' --> count the number of markets in each event to discover abs_error
    df['num_markets'] = df.groupby('event_id')['question'].transform('count')


    # fit Model (excluding avg_price)
    features = ['volume', 'num_markets', 'price_std_dev', 'time_before_certainty']
    X = df[features]
    y = df['abs_error']

    model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    # plot graph
    importance = pd.Series(model.feature_importances_, index=features).sort_values()

    pd_plot = PartialDependenceDisplay.from_estimator(model, X, ['volume','num_markets', 'price_std_dev', 'time_before_certainty'])
    fig = pd_plot.figure_
    fig.set_size_inches(16, 10)

    # 4. Adjust the spacing between subplots (wspace=width, hspace=height)
    fig.subplots_adjust(wspace=0.3, hspace=0.3)  
    plt.savefig(f"{REPOSITORY_ROOT}/writeup/Effect_of_variables_on_accuracy.png")
    plt.show()

if __name__ == "__main__":
    plot_feature_importance_with_price_volatility()