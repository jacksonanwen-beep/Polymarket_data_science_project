import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def load_and_prepare_data(filepath):
    print("Loading data...")
    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'])

    final_prices = df.sort_values('Date').groupby(['Event_ID', 'Outcome_Name'])['Price'].last().reset_index()
    final_prices['Actual_Outcome'] = (final_prices['Price'] >= 0.99).astype(int)

    df = df.merge(final_prices[['Event_ID', 'Outcome_Name', 'Actual_Outcome']], on=['Event_ID', 'Outcome_Name'], how='left')
    
    print(f"Loaded {len(df)} rows ready for analysis.")
    return df


def calibration_curve(df):
    print("Generating Calibration Curve...")
    
    df['Price_Bucket'] = df['Price'].round(1)
    calibration_data = df.groupby('Price_Bucket')['Actual_Outcome'].mean().reset_index()

    plt.figure(figsize=(8, 8))
    sns.set_theme(style="whitegrid")


    sns.lineplot(
        data=calibration_data, 
        x='Price_Bucket', 
        y='Actual_Outcome', 
        marker='o', 
        linewidth=2, 
        color='blue',
        label='Polymarket Accuracy'
    )

    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfectly Calibrated')

    plt.title('Polymarket Calibration Curve: Predicted vs. Actual Outcomes', fontsize=14, fontweight='bold')
    plt.xlabel('Polymarket Implied Probability (Price)', fontsize=12)
    plt.ylabel('Actual Real-World Win Rate', fontsize=12)
    plt.legend()
    plt.xlim(0, 1)
    plt.ylim(0, 1)

    plt.savefig('calibration_curve.png', bbox_inches='tight', dpi=300)
    plt.show() 



def main():
    df = load_and_prepare_data('polymarket_election_data.csv')
    
    calibration_curve(df)
    
 
main()