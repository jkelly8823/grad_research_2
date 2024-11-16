import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import f1_score, roc_curve, auc, accuracy_score, precision_score, recall_score
import ast

# Custom
from primevul_wrangler import *

# Show Plots
SHOW = False

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
df['predicted_pos_confidence_normalized'] = df.apply(
    lambda row: row['predicted_confidence_normalized'] 
    if row['predicted_vuln'] == 1 
    else 1 - row['predicted_confidence_normalized'], axis=1
)

# Calculate ROC curve and AUC
fpr, tpr, thresholds = roc_curve(df['true_vuln'], df['predicted_pos_confidence_normalized'])
roc_auc = auc(fpr, tpr)

# Append these metrics to the summary table
metrics = {
    'Accuracy': accuracy,
    'Precision': precision,
    'Recall': recall,
    'F1 Score': f1,
    'AUC': roc_auc,
    'Avg Confidence': df['predicted_confidence_normalized'].mean()
}
metrics_df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Score'])
summary = pd.concat([summary, metrics_df], ignore_index=True)

# Save summary table to the results directory
summary.to_csv('results/classification_summary.csv', index=False)

# Plot and save the classification counts and rates
plt.figure(figsize=(8, 6))
sns.barplot(x='Metric', y='Count', data=summary.iloc[:4], palette='viridis')
plt.title('True Positive, True Negative, False Positive, False Negative Counts')
plt.savefig('results/classification_counts.png')
plt.show() if SHOW else None

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

# TP/TN/FP/FN Rates Graph
plt.figure(figsize=(8, 6))
sns.barplot(x='Metric', y='Rate', data=rates_df, palette='viridis')
plt.title('True Positive, True Negative, False Positive, False Negative Rates')
plt.savefig('results/classification_rates.png')
plt.show() if SHOW else None

# Accuracy, Precision, Recall, F1 Graph
plt.figure(figsize=(8, 6))
sns.barplot(x=list(metrics.keys()), y=list(metrics.values()), palette='coolwarm')
plt.title('Classification Metrics')
plt.savefig('results/classification_metrics.png')
plt.show() if SHOW else None

# ROC/AUC Graph
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic (ROC) Curve')
plt.legend(loc="lower right")
plt.savefig('results/roc_curve.png')
plt.show() if SHOW else None

# ------------------------
# Grouped by CWE
# ------------------------

# Convert string representation of list into an actual list
df['cwe'] = df['cwe'].apply(ast.literal_eval)
# Explode the 'cwe' column so that each CWE is in its own row
df_exploded = df.explode('cwe')
# Create new column for predicted positive confidence normalized
df_exploded['predicted_pos_confidence_normalized'] = df_exploded.apply(
    lambda row: row['predicted_confidence_normalized'] 
    if row['predicted_vuln'] == 1 
    else 1 - row['predicted_confidence_normalized'], axis=1)

# Define conditions for TP, TN, FP, FN for each row
df_exploded['TP'] = ((df_exploded['true_vuln'] == 1) & (df_exploded['predicted_vuln'] == 1)).astype(int)
df_exploded['TN'] = ((df_exploded['true_vuln'] == 0) & (df_exploded['predicted_vuln'] == 0)).astype(int)
df_exploded['FP'] = ((df_exploded['true_vuln'] == 0) & (df_exploded['predicted_vuln'] == 1)).astype(int)
df_exploded['FN'] = ((df_exploded['true_vuln'] == 1) & (df_exploded['predicted_vuln'] == 0)).astype(int)

# Group by individual CWE and calculate TP, TN, FP, FN, and other metrics
cwe_grouped = df_exploded.groupby('cwe').apply(lambda x: {
    'TP': x['TP'].sum(),
    'TN': x['TN'].sum(),
    'FP': x['FP'].sum(),
    'FN': x['FN'].sum(),
    'Accuracy': accuracy_score(x['true_vuln'], x['predicted_vuln']),
    'Precision': precision_score(x['true_vuln'], x['predicted_vuln'], zero_division=0),
    'Recall': recall_score(x['true_vuln'], x['predicted_vuln'], zero_division=0),
    'F1 Score': f1_score(x['true_vuln'], x['predicted_vuln'], zero_division=0),
    'AUC': auc(*roc_curve(x['true_vuln'], x['predicted_pos_confidence_normalized'])[0:2]),
    'Avg Confidence': x['predicted_confidence_normalized'].mean()
}).apply(pd.Series)

# Reset the index to make 'cwe' a column and separate counts and scores
cwe_grouped_reset = cwe_grouped.reset_index()

# Separate the counts (TP, TN, FP, FN) into a new DataFrame
counts_df = cwe_grouped_reset[['cwe', 'TP', 'TN', 'FP', 'FN']].melt(id_vars=['cwe'], var_name='Metric', value_name='Count')

# Separate the other metrics (Accuracy, Precision, Recall, etc.) into another DataFrame
metrics_df = cwe_grouped_reset[['cwe', 'Accuracy', 'Precision', 'Recall', 'F1 Score', 'AUC', 'Avg Confidence']].melt(id_vars=['cwe'], var_name='Metric', value_name='Score')

# Concatenate the counts and metrics DataFrames
summary_grouped_metrics = pd.concat([counts_df, metrics_df], ignore_index=True)

# Save summary table to the results directory
summary_grouped_metrics.to_csv('results/classification_summary_by_cwe.csv', index=False)

# Plot and save the classification counts (TP, TN, FP, FN)
# plt.figure(figsize=(8, 6))
# sns.barplot(x='Metric', y='Count', data=cwe_grouped[['TP', 'TN']], palette='viridis')
cwe_grouped[['TP', 'TN', 'FP', 'FN']].plot(kind='bar', figsize=(8, 6))
plt.title('True Positive, True Negative, False Positive, False Negative Counts by CWE')
plt.savefig('results/classification_counts_by_cwe.png')
plt.show() if SHOW else None

# Calculate the total number of samples in each CWE group
cwe_grouped_reset['Total Samples'] = df_exploded.groupby('cwe').size().values

# Calculate rates for each CWE group using the total number of samples in the denominator
cwe_grouped_reset['True Positive Rate'] = cwe_grouped_reset['TP'] / cwe_grouped_reset['Total Samples']
cwe_grouped_reset['True Negative Rate'] = cwe_grouped_reset['TN'] / cwe_grouped_reset['Total Samples']
cwe_grouped_reset['False Positive Rate'] = cwe_grouped_reset['FP'] / cwe_grouped_reset['Total Samples']
cwe_grouped_reset['False Negative Rate'] = cwe_grouped_reset['FN'] / cwe_grouped_reset['Total Samples']

# Melt the rates into a long format
rates_df_grouped = cwe_grouped_reset.melt(id_vars=['cwe'], 
                                  value_vars=['True Positive Rate', 'True Negative Rate', 
                                              'False Positive Rate', 'False Negative Rate'],
                                  var_name='Metric', value_name='Rate')

# Save the rates per CWE to the results directory
rates_df_grouped.to_csv('results/classification_rates_by_cwe.csv', index=False)

# TP/TN/FP/FN Rates Graph grouped by CWE
plt.figure(figsize=(8, 6))  # Increase figure size for readability
sns.barplot(x='cwe', y='Rate', hue='Metric', data=rates_df_grouped, palette='viridis', ci=None)
plt.title('True Positive, True Negative, False Positive, False Negative Rates by CWE')
plt.xlabel('CWE')
plt.ylabel('Rate')
plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
plt.legend(title='Metric', bbox_to_anchor=(1.05, 1), loc='upper left')  # Adjust legend position
plt.tight_layout()  # Adjust layout to prevent overlap
plt.savefig('results/classification_rates_by_cwe.png')
plt.show() if SHOW else None

# Plot the results for grouped by CWE
cwe_grouped[['Accuracy', 'Precision', 'Recall', 'F1 Score', 'AUC', 'Avg Confidence']].plot(kind='bar', figsize=(8, 6))
plt.title('Classification Metrics by CWE')
plt.ylabel('Metric Value')
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig('results/classification_metrics_by_cwe.png')
plt.show() if SHOW else None

# ROC Curve for grouped metrics (optional based on user needs)
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, label=f'Overall ROC (AUC = {roc_auc:.2f})')

# Loop through each unique CWE and plot its corresponding ROC curve using pre-calculated AUC
for cwe, metrics in cwe_grouped.iterrows():
    group = df_exploded[df_exploded['cwe'] == cwe]
    fpr_group, tpr_group, thresholds_group = roc_curve(group['true_vuln'], group['predicted_pos_confidence_normalized'])
    roc_auc_group = auc(fpr_group, tpr_group)
    plt.plot(fpr_group, tpr_group, label=f'{cwe} (AUC = {roc_auc_group:.2f})')


# Add the baseline diagonal
plt.plot([0, 1], [0, 1], color='navy', linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic (ROC) Curve by CWE')
plt.legend(loc="lower right")
plt.savefig('results/roc_curve_by_cwe.png')
plt.show() if SHOW else None

# ------------------------
# PrimeVul Pairings
# ------------------------
# Direct from PrimeVul-
# We define four outcomes of the pair-wise prediction:
# • Pair-wise Correct Prediction (P-C): The model correctly
# predicts the ground-truth labels for both elements of a pair.
# • Pair-wise Vulnerable Prediction (P-V): The model incorrectly predicts both elements of the pair as vulnerable.
# • Pair-wise Benign Prediction (P-B): The model incorrectly
# predicts both elements of the pair as benign.
# • Pair-wise Reversed Prediction (P-R): The model incorrectly
# and inversely predicts the labels for the pair.

if os.getenv('DATA_SRC').upper() == 'PRIMEVUL':
    pairwise_df = generate_outcome_graphs(df, SHOW)

