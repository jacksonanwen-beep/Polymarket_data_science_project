import seaborn as sns
from matplotlib import pyplot as plt
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
import numpy as np
from my_lib.consts import REPOSITORY_ROOT


def generate_one_day_calibration_with_kde():
    # Load the data
    df = pd.read_csv("data/market_data_one_day_before_certainty.csv")
    df = df.dropna(subset=['avg_price', 'outcome'])
    
    y_true = df['outcome'].astype(int)
    y_prob = df['avg_price']

    # Calculate calibration curve
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10, strategy='uniform')

    # Setup the plot
    fig, ax1 = plt.subplots(figsize=(10, 7), facecolor='white')
    
    # Plot Calibration Curve on primary Y-axis
    ax1.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfectly Calibrated')
    ax1.plot(prob_pred, prob_true, marker='s', linewidth=2, label='Market Performance')
    ax1.set_xlabel('Market Price (Predicted probability)')
    ax1.set_ylabel('Actual Proportion of "Yes" Outcomes')
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.legend(loc='upper left')

    # Create secondary Y-axis for KDE
    ax2 = ax1.twinx()
    ax2.set_yticks([])
    ax2.set_label("")
    
    # PLOT THE KDE
    sns.kdeplot(
        data=df, 
        x='avg_price',
        ax=ax2, 
        fill=True, 
        color='blue', 
        alpha=0.1, 
        bw_adjust=0.8, 
        label='Price Density'
    )
    
    plt.title(f'Calibration & Data Distribution 1 Day from Market Certainty')
    plt.tight_layout()
    plt.savefig(f"{REPOSITORY_ROOT}/writeup/calibration_and_kde_1_day.png")
    plt.show()

generate_one_day_calibration_with_kde()