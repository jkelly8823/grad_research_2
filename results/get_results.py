import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load CSV into DataFrame
file_path = r'outputs\verdicts.csv'  # Replace with your file path
df = pd.read_csv(file_path, header=0)

# Define conditions for TP, TN, FP, FN
df['TP'] = ((df['true_vuln'] == 1) & (df['predicted_vuln'] == 1)).astype(int)
df['TN'] = ((df['true_vuln'] == 0) & (df['predicted_vuln'] == 0)).astype(int)
df['FP'] = ((df['true_vuln'] == 0) & (df['predicted_vuln'] == 1)).astype(int)
df['FN'] = ((df['true_vuln'] == 1) & (df['predicted_vuln'] == 0)).astype(int)

# Aggregate counts
summary = df[['TP', 'TN', 'FP', 'FN']].sum().reset_index()
summary.columns = ['Metric', 'Count']

# Display and save summary table
print("Summary Table:")
print(summary)
summary.to_csv('results/classification_summary.csv', index=False)
print("Summary table saved to 'classification_summary.csv'.")

# Generate and save bar plot for TP, TN, FP, FN counts
plt.figure(figsize=(8, 6))
sns.barplot(x='Metric', y='Count', data=summary, palette='viridis')
plt.title('True Positive, True Negative, False Positive, False Negative Counts')
plt.savefig('results/classification_counts.png')
print("Classification counts plot saved as 'classification_counts.png'.")
plt.show()

# Calculate rates
total = len(df)
rates = {
    'True Positive Rate': summary.loc[summary['Metric'] == 'TP', 'Count'].values[0] / total,
    'True Negative Rate': summary.loc[summary['Metric'] == 'TN', 'Count'].values[0] / total,
    'False Positive Rate': summary.loc[summary['Metric'] == 'FP', 'Count'].values[0] / total,
    'False Negative Rate': summary.loc[summary['Metric'] == 'FN', 'Count'].values[0] / total
}

# Display and save rates table
rates_df = pd.DataFrame(rates.items(), columns=['Metric', 'Rate'])
print("\nRates Table:")
print(rates_df)
rates_df.to_csv('results/classification_rates.csv', index=False)
print("Rates table saved to 'classification_rates.csv'.")

# Generate and save bar plot for rates
plt.figure(figsize=(8, 6))
sns.barplot(x='Metric', y='Rate', data=rates_df, palette='coolwarm')
plt.title('True Positive, True Negative, False Positive, False Negative Rates')
plt.savefig('results/classification_rates.png')
print("Classification rates plot saved as 'classification_rates.png'.")
plt.show()
