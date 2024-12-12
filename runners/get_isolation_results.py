import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import f1_score, roc_curve, auc, accuracy_score, precision_score, recall_score, precision_recall_curve, confusion_matrix
import ast
from dotenv import load_dotenv

# Custom
from primevul_isolation_results_wrangler import *

dotenv.load_dotenv()

def getResults(out_pth=os.getenv('OUTPUT_PTH'), res_pth=os.getenv('RESULT_PTH'), updater=False):

    # Show Plots
    SHOW = int(os.getenv('SHOW'))
    ROOT_PTH = res_pth
    os.makedirs(ROOT_PTH,exist_ok=True)

    # Load CSV into DataFrame, skipping the first row and stripping whitespace from headers
    file_path = out_pth+'/verdicts.csv'  # Replace with your file path
    df = pd.read_csv(file_path, header=0)
    df.columns = df.columns.str.strip()  # Remove any leading/trailing whitespace
    df = df.dropna(subset=["predicted_confidence"])

    # Define conditions for TP, TN, FP, FN
    df['TP'] = ((df['true_vuln'] == 1) & (df['predicted_vuln'] == 1)).astype(int)
    df['TN'] = ((df['true_vuln'] == 0) & (df['predicted_vuln'] == 0)).astype(int)
    df['FP'] = ((df['true_vuln'] == 0) & (df['predicted_vuln'] == 1)).astype(int)
    df['FN'] = ((df['true_vuln'] == 1) & (df['predicted_vuln'] == 0)).astype(int)

    # Aggregate counts for TP, TN, FP, FN
    counts = df[['TP', 'TN', 'FP', 'FN']].sum().reset_index()
    counts.columns = ['Metric', 'Count']
    counts.to_csv(ROOT_PTH + '/classification_counts.csv', index=False)

    # Calculate accuracy, precision, recall, F1 Score, and AUC
    accuracy = accuracy_score(df['true_vuln'], df['predicted_vuln'])
    precision = precision_score(df['true_vuln'], df['predicted_vuln'])
    recall = recall_score(df['true_vuln'], df['predicted_vuln'])
    f1 = f1_score(df['true_vuln'], df['predicted_vuln'])

    # Normalize predicted_confidence to a 0-1 range for ROC/AUC
    # df['predicted_confidence_normalized'] = df['predicted_confidence'] / 100
    # df['predicted_pos_confidence_normalized'] = df.apply(
    #     lambda row: row['predicted_confidence_normalized'] 
    #     if row['predicted_vuln'] == 1 
    #     else 1 - row['predicted_confidence_normalized'], axis=1
    # )
    df['predicted_confidence_normalized'] = df['predicted_confidence'] / 100
    df['predicted_pos_confidence_normalized'] = df.apply(
        lambda row: 0.5 + row['predicted_confidence_normalized']/2
        if row['predicted_vuln'] == 1 
        else 0.5 - row['predicted_confidence_normalized']/2, axis=1
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
    metrics_df.to_csv(ROOT_PTH + '/classification_metrics.csv', index=False)

    # Plot and save the classification counts and rates
    plt.figure(figsize=(14, 8))
    sns.barplot(x='Metric', y='Count', hue='Metric', data=counts, palette='viridis')
    plt.title('True Positive, True Negative, False Positive, False Negative Counts')
    plt.savefig(ROOT_PTH + '/classification_counts.png')
    plt.show() if SHOW else None

    # Save the rates as a separate table
    # Extract counts for each metric
    counts_idx = counts.set_index('Metric')['Count']

    # Define rates and their formulas
    rates = {
        'True Positive Rate': counts_idx['TP'] / max((counts_idx['TP'] + counts_idx['FN']),1),
        'True Negative Rate': counts_idx['TN'] / max((counts_idx['TN'] + counts_idx['FP']),1),
        'False Positive Rate': counts_idx['FP'] / max((counts_idx['FP'] + counts_idx['TN']),1),
        'False Negative Rate': counts_idx['FN'] / max((counts_idx['FN'] + counts_idx['TP']),1)
    }
    rates_df = pd.DataFrame(rates.items(), columns=['Metric', 'Rate'])
    rates_df.to_csv(ROOT_PTH + '/classification_rates.csv', index=False)

    # TP/TN/FP/FN Rates Graph
    plt.figure(figsize=(14, 8))
    sns.barplot(x='Metric', y='Rate', hue='Metric', data=rates_df, palette='viridis')
    plt.title('True Positive, True Negative, False Positive, False Negative Rates')
    plt.savefig(ROOT_PTH + '/classification_rates.png')
    plt.show() if SHOW else None

    # Accuracy, Precision, Recall, F1 Graph
    plt.figure(figsize=(14, 8))
    sns.barplot(x='Metric', y='Score', hue='Metric', data=metrics_df, palette='coolwarm')
    plt.title('Classification Metrics')
    plt.savefig(ROOT_PTH + '/classification_metrics.png')
    plt.show() if SHOW else None

    # ROC/AUC Graph
    plt.figure(figsize=(14, 8))
    plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.legend(loc="lower right")
    plt.savefig(ROOT_PTH + '/roc_curve.png')
    plt.show() if SHOW else None

    if os.getenv('DATA_SRC').upper() in ['DEVIGN', 'MINH']:
        return

    # ------------------------
    # Grouped by CWE
    # ------------------------

    # Convert string representation of list into an actual list
    df['true_cwe'] = df['true_cwe'].apply(ast.literal_eval)
    # Explode the 'true_cwe' column so that each CWE is in its own row
    df_exploded = df.explode('true_cwe')
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
    cwe_grouped = df_exploded.groupby('true_cwe').apply(lambda x: {
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
    }, include_groups=False).apply(pd.Series)

    # Reset the index to make 'cwe' a column and separate counts and scores
    cwe_grouped_reset = cwe_grouped.reset_index()

    # Separate the counts (TP, TN, FP, FN) into a new DataFrame
    counts_df = cwe_grouped_reset[['true_cwe', 'TP', 'TN', 'FP', 'FN']].melt(id_vars=['true_cwe'], var_name='Metric', value_name='Count')

    # Separate the other metrics (Accuracy, Precision, Recall, etc.) into another DataFrame
    metrics_df = cwe_grouped_reset[['true_cwe', 'Accuracy', 'Precision', 'Recall', 'F1 Score', 'AUC', 'Avg Confidence']].melt(id_vars=['true_cwe'], var_name='Metric', value_name='Score')

    # Save tables table to the results directory
    counts_df.to_csv(ROOT_PTH + '/classification_counts_by_cwe.csv', index=False)
    metrics_df.to_csv(ROOT_PTH + '/classification_metrics_by_cwe.csv', index=False)

    # Plot and save the classification counts (TP, TN, FP, FN)
    # Create the seaborn barplot
    plt.figure(figsize=(14, 8))  # Increase figure size for readability
    sns.barplot(x='Metric', y='Count', hue='true_cwe', data=counts_df, palette='tab20')
    plt.title('True Positive, True Negative, False Positive, False Negative Counts by CWE')
    plt.xlabel('Metrics')
    plt.ylabel('Count')
    plt.xticks(rotation=0)
    plt.legend(title='CWE', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(ROOT_PTH + '/classification_counts_by_cwe.png')
    plt.show() if SHOW else None

    # Calculate rates for each CWE group using the sum of TP, TN, FP, FN as the denominator
    cwe_grouped_reset['True Positive Rate'] = cwe_grouped_reset['TP'] / (cwe_grouped_reset[['TP', 'FN']].sum(axis=1).replace(0, 1))
    cwe_grouped_reset['True Negative Rate'] = cwe_grouped_reset['TN'] / (cwe_grouped_reset[['TN', 'FP']].sum(axis=1).replace(0, 1))
    cwe_grouped_reset['False Positive Rate'] = cwe_grouped_reset['FP'] / (cwe_grouped_reset[['FP', 'TN']].sum(axis=1).replace(0, 1))
    cwe_grouped_reset['False Negative Rate'] = cwe_grouped_reset['FN'] / (cwe_grouped_reset[['FN', 'TP']].sum(axis=1).replace(0, 1))

    # Melt the rates into a long format
    rates_df_grouped = cwe_grouped_reset.melt(id_vars=['true_cwe'], 
                                    value_vars=['True Positive Rate', 'True Negative Rate', 
                                                'False Positive Rate', 'False Negative Rate'],
                                    var_name='Metric', value_name='Rate')

    # Save the rates per CWE to the results directory
    rates_df_grouped.to_csv(ROOT_PTH + '/classification_rates_by_cwe.csv', index=False)

    # TP/TN/FP/FN Rates Graph grouped by CWE
    plt.figure(figsize=(14, 8))  # Increase figure size for readability
    sns.barplot(x='Metric', y='Rate', hue='true_cwe', data=rates_df_grouped, palette='tab20', errorbar=None)
    plt.title('True Positive, True Negative, False Positive, False Negative Rates by CWE')
    plt.xlabel('Metrics')
    plt.ylabel('Rate')
    plt.xticks(rotation=0)
    plt.legend(title='CWE', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(ROOT_PTH + '/classification_rates_by_cwe.png', bbox_inches='tight')  # Ensure legend fits
    plt.show() if SHOW else None

    plt.figure(figsize=(14, 8))  # Increase figure size for readability
    sns.barplot(x='Metric', y='Score', hue='true_cwe', data=metrics_df, palette='tab20', errorbar=None)
    plt.title('Classification Metrics by CWE')
    plt.xlabel('Metrics')
    plt.ylabel('Metric Value')
    plt.xticks(rotation=0)
    plt.legend(title='CWE', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(ROOT_PTH + '/classification_metrics_by_cwe.png', bbox_inches='tight')  # Ensure legend fits
    plt.show() if SHOW else None

    # ROC Curve for grouped metrics (optional based on user needs)
    plt.figure(figsize=(14, 8))
    plt.plot(fpr, tpr, label=f'Overall ROC (AUC = {roc_auc:.2f})')

    # Loop through each unique CWE and plot its corresponding ROC curve using pre-calculated AUC
    for cwe, metrics in cwe_grouped.iterrows():
        group = df_exploded[df_exploded['true_cwe'] == cwe]
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
    plt.savefig(ROOT_PTH + '/roc_curve_by_cwe.png')
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
        if not updater or any(x in ROOT_PTH for x in ['bulk_run_1', 'filtered_bulk_run', 'isolated_std', 'isolated_finetune']):
            generate_outcome_graphs(df, SHOW, ROOT_PTH)
    
    return

if __name__ == '__main__':
    getResults()