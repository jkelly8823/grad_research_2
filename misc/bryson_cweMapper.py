import pandas as pd
import json
import re
import os
import tiktoken
import ast
from dotenv import load_dotenv
load_dotenv()

def over_tokens(sample):
    max_tokens = int(os.getenv('SAMPLE_TOKEN_LIMIT'))
    encoding = tiktoken.get_encoding("cl100k_base")
    encoded_value = encoding.encode(sample)
    num_tokens = len(encoded_value)
    if num_tokens > max_tokens:
        return True
    return False


# Function to clean and parse the JSON data
def get_brysonfixed_data(file_path, limit=-1, start_idx=-1, cherrypick=[], cherryskip=[]):
    with open(file_path, 'r') as file:
        data = json.load(file)
    parsed_data = []
    for item in data:
        idx = len(parsed_data)

        if start_idx != -1 and start_idx != idx:
            continue
        elif start_idx != -1 and start_idx == idx:
            start_idx = -1

        if len(cherrypick) > 0 and idx not in cherrypick:
            continue

        if len(cherryskip) > 0 and idx in cherryskip:
            continue

        try:
            # Decode the escaped string (removes unnecessary escape characters)
            cleaned_code = bytes(item['code'], "utf-8").decode("unicode_escape")
            
            # Further clean up additional escape sequences like backslashes or newlines
            cleaned_code = cleaned_code.replace("\\\\", "\\").replace("\\n", "\n").replace('\\"', '"')
        
            # Update the 'code' field with the cleaned string
            item['code'] = cleaned_code

            dat = {
                "source": 'bryson_dataset',
                "idx": idx,
                "func": item['code'],
                "vuln": item['vulnerable'],
                "cwe": item['category']
            }

            if over_tokens(dat['func']):
                print('Skipping a sample due to token length...')
                continue

            parsed_data.append(dat)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        
        limit -= 1
        if limit == 0:
            break
    return parsed_data

samples = get_brysonfixed_data(os.getenv('BRYSONFIXED'))
df = pd.DataFrame(samples)
print(df['cwe'].unique())

mapping = {
            'stack-based buffer overflow': ['CWE-121'],
            'heap-based buffer overflow': ['CWE-122'],
            'use after free': ['CWE-416'],
            'integer overflow': ['CWE-190'],
            'race condition': ['CWE-362'],
            'command injection': ['CWE-77'],
            'out-of-bounds access': ['CWE-119'], # ?
            'memory leak': ['CWE-401'],
            'double free': ['CWE-415']
        }