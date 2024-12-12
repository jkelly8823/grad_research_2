import pandas as pd
import os
import shutil

# Define the directory path to start the search
directory_path = r"D:\grad_research_2\results\prev"

# Loop through the directory and its subdirectories
for root, dirs, files in os.walk(directory_path):
    for file in files:
        # Check if the file contains 'cwe' and ends with '.csv'
        if 'old' not in root and 'anthropic' not in root:
            pth = os.path.join(root, file)
            folder = pth[:pth.rfind("\\")].replace("results\prev", "misc\cwe")
            nm = pth[pth.rfind("\\"):]
            print(nm)
            print(folder)
            os.makedirs(folder, exist_ok=True)

            if 'counts_by_cwe.csv' in file.lower() and 'outcome' not in file.lower(): 
                df = pd.read_csv(pth, header=0)
                df = df.fillna(0)
                # Pivot the table to reshape it
                try:
                    reshaped_data = df.pivot_table(index='cwe', columns='Metric', values='Count', aggfunc='sum')
                except Exception as e:
                    reshaped_data = df.pivot_table(index='true_cwe', columns='Metric', values='Count', aggfunc='sum')
                # Fill any missing values with 0 (e.g., for missing 'FP' or 'FN' entries)
                reshaped_data = reshaped_data.fillna(0)
                reshaped_data = reshaped_data[['TP', 'TN', 'FP', 'FN']]
                reshaped_data.columns = ['TruePositive', 'TrueNegative', 'FalsePositive', 'FalseNegative']
                # Reset the index to make 'cwe' a regular column
                reshaped_data.reset_index(inplace=True)
                # Convert all columns that can be numeric to numeric
                reshaped_data = reshaped_data.apply(pd.to_numeric, errors='ignore')
                # Round numeric columns to 3 decimal places
                reshaped_data = reshaped_data.round(3)
                # Print the reshaped DataFrame
                # print(reshaped_data)
                reshaped_data.to_csv(folder + nm, index=False)
            elif 'rates_by_cwe.csv' in file.lower() and 'outcome' not in file.lower(): 
                df = pd.read_csv(pth, header=0)
                df = df.fillna(0)
                # Pivot the table to reshape it
                try:
                    reshaped_data = df.pivot_table(index='cwe', columns='Metric', values='Rate', aggfunc='first')
                except Exception as e:
                    reshaped_data = df.pivot_table(index='true_cwe', columns='Metric', values='Rate', aggfunc='first')                
                # Fill any missing values with 0 (e.g., for missing 'FP' or 'FN' entries)
                reshaped_data = reshaped_data.fillna(0)
                reshaped_data = reshaped_data[['True Positive Rate', 'True Negative Rate', 'False Positive Rate', 'False Negative Rate']]
                reshaped_data.columns = ['TruePositiveRate', 'TrueNegativeRate', 'FalsePositiveRate', 'FalseNegativeRate']
                # Reset the index to make 'cwe' a regular column
                reshaped_data.reset_index(inplace=True)
                # Convert all columns that can be numeric to numeric
                reshaped_data = reshaped_data.apply(pd.to_numeric, errors='ignore')
                # Round numeric columns to 3 decimal places
                reshaped_data = reshaped_data.round(3)
                # Print the reshaped DataFrame
                # print(reshaped_data)
                reshaped_data.to_csv(folder + nm, index=False)
            elif 'metrics_by_cwe.csv' in file.lower() and 'outcome' not in file.lower(): 
                df = pd.read_csv(pth, header=0)
                df = df.fillna(0)
                # Pivot the table to reshape it
                try:
                    reshaped_data = df.pivot_table(index='cwe', columns='Metric', values='Score', aggfunc='first')
                except Exception as e:
                    reshaped_data = df.pivot_table(index='true_cwe', columns='Metric', values='Score', aggfunc='first')
                # Fill any missing values with 0 (e.g., for missing 'FP' or 'FN' entries)
                reshaped_data = reshaped_data.fillna(0)
                reshaped_data = reshaped_data[['Accuracy', 'Precision', 'Recall', 'F1 Score', 'AUC', 'Avg Confidence']]
                reshaped_data.columns = ['Accuracy', 'Precision', 'Recall', 'F1Score', 'AUC', 'AvgConfidence']
                # Reset the index to make 'cwe' a regular column
                reshaped_data.reset_index(inplace=True)
                # Convert all columns that can be numeric to numeric
                reshaped_data = reshaped_data.apply(pd.to_numeric, errors='ignore')
                # Round numeric columns to 3 decimal places
                reshaped_data = reshaped_data.round(3)
                # Print the reshaped DataFrame
                # print(reshaped_data)
                reshaped_data.to_csv(folder + nm, index=False)
            elif file.endswith('.csv'):
                df = pd.read_csv(pth, header = 0)
                df = df.fillna(0)
                df = df.apply(pd.to_numeric, errors='ignore')
                df = df.round(3)
                df.to_csv(folder + nm, index=False)
            else:
                shutil.copy(pth, folder + nm)