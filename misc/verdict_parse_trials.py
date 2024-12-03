import pandas as pd
import ast

# Load the CSV
file_path = r"D:\grad_research_2\outputs\verdicts.csv"
df = pd.read_csv(file_path, header=0)
df.columns = df.columns.str.strip()

# Parse array-like columns
columns_to_parse = ["true_cwe", "predicted_cwe"]  # Replace with actual column names
for column in columns_to_parse:
    df[column] = df[column].apply(ast.literal_eval)  # Safely parse strings into lists

# Check the DataFrame
print(df.head())
