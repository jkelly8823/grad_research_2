import pandas as pd
import os

# Define the directory path to start the search
directory_path = r"D:\grad_research_2\results\prev"

# Loop through the directory and its subdirectories
for root, dirs, files in os.walk(directory_path):
    for file in files:
        # Check if the file contains 'cwe' and ends with '.csv'
        if 'counts_by_cwe' in file.lower() and file.endswith('.csv') and 'outcome' not in file.lower() and 'old' not in root:
        # if 'rates_by_cwe' in file.lower() and file.endswith('.csv') and 'outcome' not in file.lower() and 'old' not in root:
        # if 'metrics_by_cwe' in file.lower() and file.endswith('.csv') and 'outcome' not in file.lower() and 'old' not in root:
            # Get the full file path
            pth = os.path.join(root, file)
            # Print or process the file path
            print(pth)

            # pth = r"D:\grad_research_2\results\prev\bulk_run\classification_counts_by_cwe.csv"
            folder = pth[:pth.rfind("\\")].replace("results\prev", "misc\cwe")
            nm = pth[pth.rfind("\\"):]
            print(nm)
            print(folder)
            os.makedirs(folder, exist_ok=True)

            df = pd.read_csv(pth, header=0)
            df = df.fillna(0)

            # Pivot the table to reshape it
            try:
                reshaped_data = df.pivot_table(index='cwe', columns='Metric', values='Count', aggfunc='sum')
                # reshaped_data = df.pivot_table(index='cwe', columns='Metric', values='Rate', aggfunc='first')
                # reshaped_data = df.pivot_table(index='cwe', columns='Metric', values='Score', aggfunc='first')
            except Exception as e:
                reshaped_data = df.pivot_table(index='true_cwe', columns='Metric', values='Count', aggfunc='sum')
                # reshaped_data = df.pivot_table(index='true_cwe', columns='Metric', values='Rate', aggfunc='first')
                # reshaped_data = df.pivot_table(index='true_cwe', columns='Metric', values='Score', aggfunc='first')
            
            # Fill any missing values with 0 (e.g., for missing 'FP' or 'FN' entries)
            reshaped_data = reshaped_data.fillna(0)

            reshaped_data = reshaped_data[['TP', 'TN', 'FP', 'FN']]
            reshaped_data.columns = ['TruePositive', 'TrueNegative', 'FalsePositive', 'FalseNegative']
            # reshaped_data = reshaped_data[['True Positive Rate', 'True Negative Rate', 'False Positive Rate', 'False Negative Rate']]
            # reshaped_data.columns = ['TruePositiveRate', 'TrueNegativeRate', 'FalsePositiveRate', 'FalseNegativeRate']
            # reshaped_data = reshaped_data[['Accuracy', 'Precision', 'Recall', 'F1 Score', 'AUC', 'Avg Confidence']]
            # reshaped_data.columns = ['Accuracy', 'Precision', 'Recall', 'F1Score', 'AUC', 'AvgConfidence']

            # Reset the index to make 'cwe' a regular column
            reshaped_data.reset_index(inplace=True)

            # Print the reshaped DataFrame
            print(reshaped_data)

            reshaped_data.to_csv(folder + nm, index=False)