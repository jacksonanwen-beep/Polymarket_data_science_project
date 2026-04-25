import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm


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


def brier_score_distribution(df):
    print("Generating Brier Score Distribution...")
    
    df['Brier_Score'] = (df['Price'] - df['Actual_Outcome'])**2
    
    plt.figure(figsize=(8, 8))
    sns.set_theme(style="whitegrid")
    

    sns.histplot(data=df, x='Brier_Score', bins=30, kde=True, color='purple', edgecolor='black')
    
    mean_brier = df['Brier_Score'].mean()
    plt.axvline(mean_brier, color='red', linestyle='dashed', linewidth=2, 
                label=f'Average Market Error: {mean_brier:.3f}')
    
    plt.title('Distribution of Brier Scores', fontsize=14, fontweight='bold')
    plt.xlabel('Brier Score (0 = Perfect Prediction, 1 = Completely Wrong)', fontsize=12)
    plt.ylabel('Number of Predictions (Frequency)', fontsize=12)
    plt.legend()
    
    plt.savefig('brier_score.png', bbox_inches='tight', dpi=300)
    plt.show()



def ols_regression(df):
    print("Generating OLS Regression Table...")
    
    df['Brier_Score'] = (df['Price'] - df['Actual_Outcome'])**2
    
    max_dates = df.groupby(['Event_ID', 'Outcome_Name'])['Date'].transform('max')
    df['Days_to_Resolution'] = (max_dates - df['Date']).dt.days
    
    df['Market_Certainty'] = abs(df['Price'] - 0.5)
    
    analysis_df = df[['Brier_Score', 'Days_to_Resolution', 'Market_Certainty']].dropna()
    
    X = analysis_df[['Days_to_Resolution', 'Market_Certainty']]
    y = analysis_df['Brier_Score']
    
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X).fit()
    
    print("\n" + "="*60)
    print("OLS REGRESSION RESULTS")
    print("="*60)
    print(model.summary())
    
    with open('regression_results.txt', 'w') as f:
        f.write(model.summary().as_text())
        
    print("\nSuccessfully saved regression table to 'regression_results.txt'")


def coefficient_plot(df):
    print("Generating Coefficient Plot...")
    

    df['Brier_Score'] = (df['Price'] - df['Actual_Outcome'])**2
    max_dates = df.groupby(['Event_ID', 'Outcome_Name'])['Date'].transform('max')
    df['Days_to_Resolution_per_100'] = (max_dates - df['Date']).dt.days / 100
    df['Market_Certainty'] = abs(df['Price'] - 0.5)
    
    analysis_df = df[['Brier_Score', 'Days_to_Resolution_per_100', 'Market_Certainty']].dropna()
    X = analysis_df[['Days_to_Resolution_per_100', 'Market_Certainty']]
    y = analysis_df['Brier_Score']
    
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X).fit()

    coefs = model.params.drop('const')
    conf_ints = model.conf_int().drop('const')
    
    error_margins = coefs - conf_ints[0]
    
    plt.figure(figsize=(10, 5))
    sns.set_theme(style="whitegrid")
    
    plt.errorbar(
        x=coefs, 
        y=coefs.index, 
        xerr=error_margins, 
        fmt='o', 
        color='darkblue', 
        markersize=10, 
        linewidth=2, 
        capsize=6
    )
    
    plt.axvline(0, color='red', linestyle='--', linewidth=2, label='No Effect (Zero Line)')
    
    plt.title('Variables Impacting Polymarket Error (Brier Score)', fontsize=14, fontweight='bold')
    plt.xlabel('Coefficient Effect Size\n(< 0: Improves Accuracy | > 0: Worsens Accuracy)', fontsize=12)
    plt.ylabel('Variables', fontsize=12)
    plt.yticks(fontsize=12, fontweight='bold')
    plt.legend()
    
    plt.savefig('coefficient_plot.png', bbox_inches='tight', dpi=300)
    plt.show()


def main():
    df = load_and_prepare_data('polymarket_election_data.csv')
    
    # calibration_curve(df)

    # brier_score_distribution(df)

    # ols_regression(df)

    coefficient_plot(df)
    
 
main()