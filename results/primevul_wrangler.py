import os
import dotenv
import json
from collections import defaultdict
import pandas as pd

dotenv.load_dotenv()

def get_primevul_pairs(idxs):
    with open(os.getenv('PRIMEVUL'), "r") as f:
        samples = f.readlines()
    samples = [json.loads(sample) for sample in samples]

    # Step 1: Group relevant idx values by commit_url
    alpha_groups = defaultdict(list)
    for sample in samples:
        sample_idx = sample.get("idx")
        if sample_idx in idxs:  # Only consider idxs in the provided list
            alpha_groups[sample.get("commit_url", None)].append(sample_idx)

    # Step 2: Identify pairs of idx values
    pairs = []
    for group in alpha_groups.values():
        if len(group) > 1:  # Only consider groups with more than one idx
            pairs.extend([(group[i], group[j]) for i in range(len(group)) for j in range(i + 1, len(group))])

    for p in pairs:
        if len(p) > 2:
            print('MORE THAN A PAIR:', p)
    # print("Pairs of idx values sharing the same alpha (filtered by idxs):")
    # print(pairs)
    return pairs

def calculate_pairwise_outcomes(df):
    """
    Calculate pairwise outcomes (P-C, P-V, P-B, P-R) for each pair of idx values.

    Args:
        df (pandas.DataFrame): DataFrame containing the CSV data.
        pairs (list of tuples): List of idx pairs.

    Returns:
        pandas.DataFrame: DataFrame with the pairwise outcomes.
    """

    # Get pairs:
    idxs = df['idx'].astype(int).tolist()
    pairs = get_primevul_pairs(idxs)

    # Create a mapping from idx to its true_vuln and predicted_vuln for fast lookup
    idx_map = df.set_index('idx')[['true_vuln', 'predicted_vuln', 'cwe']]

    # Initialize a list to store the results
    outcomes = []

    # Loop through each pair
    for idx1, idx2 in pairs:
        # Get the true and predicted values for both idxs
        true_vuln_1 = idx_map.loc[idx1, 'true_vuln']
        pred_vuln_1 = idx_map.loc[idx1, 'predicted_vuln']
        true_vuln_2 = idx_map.loc[idx2, 'true_vuln']
        pred_vuln_2 = idx_map.loc[idx2, 'predicted_vuln']
        cwe = idx_map.loc[idx1, 'cwe']
        # Determine the outcome for the pair
        if true_vuln_1 == pred_vuln_1 and true_vuln_2 == pred_vuln_2:
            outcome = 'P-C'  # Pair-wise Correct Prediction
        elif true_vuln_1 != pred_vuln_1 and true_vuln_2 != pred_vuln_2:
            if true_vuln_1 == true_vuln_2:
                outcome = 'P-B'  # Pair-wise Benign Prediction
            else:
                outcome = 'P-V'  # Pair-wise Vulnerable Prediction
        elif (true_vuln_1 == pred_vuln_2) and (true_vuln_2 == pred_vuln_1):
            outcome = 'P-R'  # Pair-wise Reversed Prediction
        else:
            continue  # If no match, skip (although shouldn't happen with proper pairs)

        # Append the result
        outcomes.append({
            'idx1': idx1,
            'idx2': idx2,
            'true_vuln_1': true_vuln_1,
            'pred_vuln_1': pred_vuln_1,
            'true_vuln_2': true_vuln_2,
            'pred_vuln_2': pred_vuln_2,
            'outcome': outcome,
            'cwe': cwe
        })

    # Create a DataFrame from the outcomes
    return pd.DataFrame(outcomes)


# # Load CSV into DataFrame, skipping the first row and stripping whitespace from headers
# file_path = 'outputs/verdicts.csv'  # Replace with your file path
# df = pd.read_csv(file_path, header=0)
# df.columns = df.columns.str.strip()  # Remove any leading/trailing whitespace
# pairwise_df = calculate_pairwise_outcomes(df)
# print(pairwise_df)