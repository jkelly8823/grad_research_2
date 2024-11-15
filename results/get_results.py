import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import f1_score, roc_curve, auc, accuracy_score, precision_score, recall_score

# Load CSV into DataFrame, skipping the first row and stripping whitespace from headers
file_path = 'outputs/verdicts.csv'  # Replace with your file path
df = pd.read_csv(file_path, header=0)
df.columns = df.columns.str.strip()  # Remove any leading/trailing whitespace

# Define conditions for TP, TN, FP, FN
df['TP'] = ((df['true_vuln'] == 1) & (df['predicted_vuln'] == 1)).astype(int)
df['TN'] = ((df['true_vuln'] == 0) & (df['predicted_vuln'] == 0)).astype(int)
df['FP'] = ((df['true_vuln'] == 0) & (df['predicted_vuln'] == 1)).astype(int)
df['FN'] = ((df['true_vuln'] == 1) & (df['predicted_vuln'] == 0)).astype(int)

# Aggregate counts for TP, TN, FP, FN
summary = df[['TP', 'TN', 'FP', 'FN']].sum().reset_index()
summary.columns = ['Metric', 'Count']

# Calculate accuracy, precision, recall, F1 Score, and AUC
accuracy = accuracy_score(df['true_vuln'], df['predicted_vuln'])
precision = precision_score(df['true_vuln'], df['predicted_vuln'])
recall = recall_score(df['true_vuln'], df['predicted_vuln'])
f1 = f1_score(df['true_vuln'], df['predicted_vuln'])

# Normalize predicted_confidence to a 0-1 range for ROC/AUC
df['predicted_confidence_normalized'] = df['predicted_confidence'] / 10
fpr, tpr, thresholds = roc_curve(df['true_vuln'], df['predicted_confidence_normalized'])
roc_auc = auc(fpr, tpr)

# Append these metrics to the summary table
metrics = {
    'Accuracy': accuracy,
    'Precision': precision,
    'Recall': recall,
    'F1 Score': f1,
    'AUC': roc_auc
}
metrics_df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Score'])
summary = pd.concat([summary, metrics_df], ignore_index=True)

# Save summary table to the results directory
summary.to_csv('results/classification_summary.csv', index=False)

# Plot and save the classification counts and rates
plt.figure(figsize=(8, 6))
sns.barplot(x='Metric', y='Count', data=summary.iloc[:4], palette='viridis', hue='Metric', legend=False)
plt.title('True Positive, True Negative, False Positive, False Negative Counts')
plt.savefig('results/classification_counts.png')
plt.show()

# Save the rates as a separate table
total = len(df)
rates = {
    'True Positive Rate': summary.loc[summary['Metric'] == 'TP', 'Count'].values[0] / total,
    'True Negative Rate': summary.loc[summary['Metric'] == 'TN', 'Count'].values[0] / total,
    'False Positive Rate': summary.loc[summary['Metric'] == 'FP', 'Count'].values[0] / total,
    'False Negative Rate': summary.loc[summary['Metric'] == 'FN', 'Count'].values[0] / total
}
rates_df = pd.DataFrame(rates.items(), columns=['Metric', 'Rate'])
rates_df.to_csv('results/classification_rates.csv', index=False)

plt.figure(figsize=(8, 6))
sns.barplot(x='Metric', y='Rate', data=rates_df, palette='coolwarm', hue='Metric', legend=False)
plt.title('True Positive, True Negative, False Positive, False Negative Rates')
plt.savefig('results/classification_rates.png')
plt.show()

# Plot and save ROC Curve
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='darkorange', label=f'ROC Curve (AUC = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic (ROC) Curve')
plt.legend(loc="lower right")
plt.savefig('results/roc_curve.png')
plt.show()
