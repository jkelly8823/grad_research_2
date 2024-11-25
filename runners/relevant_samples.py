from dataset_parsers import *
from collections import defaultdict

def get_samples():
    prime_pth = r"D:\grad_research_2\datasets\PrimeVul\primevul_valid_paired.jsonl"
    primevul = get_primevul_data(prime_pth)

    # Create a defaultdict to group func values by CWE
    cwe_dict = defaultdict(list)
    # Iterate through the data
    
    for item in primevul:
        for cwe in item.get("cwe", []):  # Loop through the list of CWEs for this item
            cwe_dict[cwe].append(item["func"])

    # Convert defaultdict to a regular dict (optional)
    cwe_dict = dict(cwe_dict)

    # Output the result
    for key, value in cwe_dict.items():
        print(key, '\n', value)
        break

    return cwe_dict

if __name__ == '__main__':
    get_samples()