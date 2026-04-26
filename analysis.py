import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from econml.dml import CausalForestDML
from sklearn.ensemble import RandomForestRegressor,RandomForestClassifier
    

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


def ols_regression_1(df):
    print("Generating First OLS Regression Table...")
    
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
    print("FIRST OLS REGRESSION RESULTS")
    print("="*60)
    print(model.summary())
    
    with open('first_regression_results.txt', 'w') as f:
        f.write(model.summary().as_text())
        
    print("\nSuccessfully saved regression table to 'first_regression_results.txt'")


def ols_regression_2(df):
    print("Generating Second OLS Regression Table...")
    
    df['Brier_Score'] = (df['Price'] - df['Actual_Outcome'])**2
    
    df = df.sort_values(by=['Event_ID', 'Outcome_Name', 'Date'])
    
    df['14_Day_Volatility'] = df.groupby(['Event_ID', 'Outcome_Name'])['Price'].transform(lambda x: x.rolling(14).std())
    
    gop_heavyweights = [
        'Donald Trump', 'Nikki Haley', 'Ron DeSantis', 
        'Vivek Ramaswamy', 'Tim Scott', 'Chris Christie', 
        'Mike Pence', 'Doug Burgum', 'Republican'
    ]
    df['Is_Republican'] = df['Outcome_Name'].isin(gop_heavyweights).astype(int)
    
    features = ['14_Day_Volatility', 'Is_Republican']
    analysis_df = df[['Brier_Score'] + features].dropna()
    
    X = analysis_df[features]
    y = analysis_df['Brier_Score']
    
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X).fit()
    
    print("\n" + "="*60)
    print("SECOND OLS REGRESSION RESULTS")
    print("="*60)
    print(model.summary())
    

    with open('second_regression_results.txt', 'w') as f:
        f.write(model.summary().as_text())
    
    print("\nSuccessfully saved regression table to 'second_regression_results.txt'")


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


def causal_forest(df):
    print("Generating Causal Forest (HTE)...")
    
    df['Brier_Score'] = (df['Price'] - df['Actual_Outcome'])**2
    max_dates = df.groupby(['Event_ID', 'Outcome_Name'])['Date'].transform('max')
    df['Days_to_Resolution'] = (max_dates - df['Date']).dt.days
    
    df['Is_Underdog'] = (df['Price'] < 0.5).astype(int)
    
    analysis_df = df[['Brier_Score', 'Is_Underdog', 'Days_to_Resolution']].dropna()
    sample_df = analysis_df.sample(n=min(20000, len(analysis_df)), random_state=42)
    
    Y = sample_df['Brier_Score']
    T = sample_df['Is_Underdog']
    X = sample_df[['Days_to_Resolution']]
    
    print("Training Causal Forest...")
    est = CausalForestDML(
        model_y=RandomForestRegressor(n_estimators=50, max_depth=5),
        model_t=RandomForestClassifier(n_estimators=50, max_depth=5),
        discrete_treatment=True,
        n_estimators=100,
        random_state=42
    )
    est.fit(Y, T, X=X)
    
    treatment_effects = est.effect(X)
    
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")
    
    sns.scatterplot(x=X['Days_to_Resolution'], y=treatment_effects, alpha=0.3, color='teal')
    
    plt.axhline(0, color='red', linestyle='--', linewidth=2, label='No Difference (Underdog Error = Favorite Error)')
    
    plt.title('Causal Forest: How Time Changes the "Underdog Penalty"', fontsize=14, fontweight='bold')
    plt.xlabel('Days to Election', fontsize=12)
    plt.ylabel('Treatment Effect on Error\n(> 0: Underdogs are WORSE | < 0: Underdogs are BETTER)', fontsize=12)
    plt.legend()
    
    plt.savefig('causal_forest.png', bbox_inches='tight', dpi=300)
    plt.show()


def main():
    df = load_and_prepare_data('polymarket_election_data.csv')
    
    calibration_curve(df)

    brier_score_distribution(df)

    ols_regression_1(df)

    ols_regression_2(df)

    coefficient_plot(df)

    causal_forest(df)
    
 
main()