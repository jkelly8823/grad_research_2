import json
import re
import os
import tiktoken
import ast
import pandas as pd
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

def format_cleaner(code):
    # Decode the escaped string (removes unnecessary escape characters)
    cleaned_code = bytes(code, "utf-8").decode("unicode_escape")
    
    # Further clean up additional escape sequences like backslashes or newlines
    cleaned_code = cleaned_code.replace("\\\\", "\\").replace("\\n", "\n").replace('\\"', '"')

    # Normalize indentation (convert tabs to 4 spaces)
    cleaned_code = cleaned_code.replace("\t", "    ")
    
    # Remove excessive whitespace (more than 2 consecutive blank lines)
    cleaned_code = re.sub(r"\n\s*\n", "\n\n", cleaned_code)
        
    return cleaned_code

def bryson_backlash_fixer(text):
    # Find all standalone '\n' occurrences (not preceded by a backslash)
    matches = list(re.finditer(r'(?<!\\)\n', text))

    # Only replace up to the last two standalone '\n' instances
    while len(matches) > 2:
        # Start replacements for all matches except the last two    
        start, end = matches[1].span()
        text = text[:start] + "\\n" + text[end:]

        matches = list(re.finditer(r'(?<!\\)\n', text))    
    return text

# Function to clean and parse the JSON data
def get_bryson_data(file_path, limit=-1, start_idx=-1, cherrypick=[], cherryskip=[]):
    with open(file_path, 'r') as file:
        data = json.load(file)
    parsed_data = []
    idx = -1
    for item in data:
        idx += 1

        if start_idx != -1 and start_idx != idx:
            continue
        elif start_idx != -1 and start_idx == idx:
            start_idx = -1

        if len(cherrypick) > 0 and idx not in cherrypick:
            continue

        if len(cherryskip) > 0 and idx in cherryskip:
            continue

        try:
            # Clean the string
            cleaned_string = item.split('```json')[1].split('```')[0].strip()
            fixed_string = bryson_backlash_fixer(cleaned_string)
            # Load the cleaned string as a JSON object
            json_object = json.loads(fixed_string)

            
            json_object['code'] = format_cleaner(json_object['code'])

            dat = {
                "source": 'bryson_dataset',
                "idx": idx,
                "func": json_object['code'],
                "vuln": 1,
                "cwe": json_object.get('cwe', [])
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

def get_brysonfixed_data(file_path, limit=-1, start_idx=-1, cherrypick=[], cherryskip=[]):
    cwe_mapping = {
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

    with open(file_path, 'r') as file:
        data = json.load(file)
    parsed_data = []
    idx = -1
    for item in data:
        idx += 1

        if start_idx != -1 and start_idx != idx:
            continue
        elif start_idx != -1 and start_idx == idx:
            start_idx = -1

        if len(cherrypick) > 0 and idx not in cherrypick:
            continue

        if len(cherryskip) > 0 and idx in cherryskip:
            continue

        try:
            # Update the 'code' field with the cleaned string
            item['code'] = format_cleaner(item['code'])

            dat = {
                "source": 'bryson_dataset',
                "idx": idx,
                "func": item['code'],
                "vuln": item['vulnerable'],
                "cwe": cwe_mapping.get(item['category'].lower(),['Unknown CWE'])
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

def get_primevul_data(file_path, limit=-1, start_idx=-1, cherrypick=[], cherryskip=[]):
    parsed_data = []
    with open(file_path, "r") as f:
        samples = f.readlines()
    samples = [json.loads(sample) for sample in samples]
    for sample in samples:
        if start_idx != -1 and start_idx != sample["idx"]:
            continue
        elif start_idx != -1 and start_idx == sample["idx"]:
            start_idx = -1

        if len(cherrypick) > 0 and sample["idx"] not in cherrypick:
            continue
            
        if len(cherryskip) > 0 and sample["idx"] in cherryskip:
            continue

        sample['func'] = format_cleaner(sample['func'])

        src = f'primevul_{sample["project"]}_{sample["commit_id"]}'
        dat = {
            "source": src,
            "idx": sample["idx"],
            "func": sample["func"],
            "vuln": sample["target"],
            "cwe": sample.get('cwe', [])
        }

        if over_tokens(dat['func']):
            print('Skipping a sample due to token length...')
            continue
    
        parsed_data.append(dat)

        limit -= 1
        if limit == 0:
            break
    return parsed_data

def get_devign_data(file_path, limit=-1, start_idx=-1, cherrypick=[], cherryskip=[]):
    parsed_data = []
    with open(file_path, "r") as f:
        samples = json.load(f)
    
    idx = -1
    for sample in samples:
        idx += 1

        if start_idx != -1 and start_idx != idx:
            continue
        elif start_idx != -1 and start_idx == idx:
            start_idx = -1

        if len(cherrypick) > 0 and idx not in cherrypick:
            continue
            
        if len(cherryskip) > 0 and idx in cherryskip:
            continue

        
        sample['func'] = format_cleaner(sample['func'])

        src = f'devign_{sample["project"]}_{sample["commit_id"]}'
        dat = {
            "source": src,
            "idx": idx,
            "func": sample['func'],
            "vuln": sample['target'],
            "cwe": 'Unknown CWE'
        }

        if over_tokens(dat['func']):
            print('Skipping a sample due to token length...')
            continue
    
        parsed_data.append(dat)

        limit -= 1
        if limit == 0:
            break

    return parsed_data

def get_minh_data(file_path, limit=-1, start_idx=-1, cherrypick=[], cherryskip=[]):
    parsed_data = []
    
    df = pd.read_csv(file_path)
    
    for idx, sample in df.iterrows():

        if start_idx != -1 and start_idx != idx:
            continue
        elif start_idx != -1 and start_idx == idx:
            start_idx = -1

        if len(cherrypick) > 0 and idx not in cherrypick:
            continue
            
        if len(cherryskip) > 0 and idx in cherryskip:
            continue

        
        sample['vuln_func'] = format_cleaner(sample['vuln_func'])
        src = f'minh_{sample["repo_name"]}_{sample["commit_id"]}'
        dat = {
            "source": src,
            "idx": idx,
            "func": sample['vuln_func'],
            "vuln": 1,
            "cwe": 'Unknown CWE'
        }

        if over_tokens(dat['func']):
            print('Skipping a sample due to token length...')
            continue
        
        parsed_data.append(dat)

        sample['fix_vuln_func'] = format_cleaner(sample['fix_vuln_func'])
        dat2 = {
            "source": src,
            "idx": idx,
            "func": sample['fix_vuln_func'],
            "vuln": 0,
            "cwe": 'Unknown CWE'
        }

        if over_tokens(dat2['func']):
            print('Skipping a sample due to token length...')
            continue

        parsed_data.append(dat2)

        limit -= 2
        if limit == 0:
            break

    return parsed_data

# Function to clean and parse the JSON data
def get_diversevul_data(file_path, limit=-1, start_idx=-1, cherrypick=[], cherryskip=[]):
    with open(file_path, "r") as f:
        samples = f.readlines()
    samples = [json.loads(sample) for sample in samples]
    parsed_data = []
    idx = -1
    for sample in samples:
        idx += 1

        if start_idx != -1 and start_idx != idx:
            continue
        elif start_idx != -1 and start_idx == idx:
            start_idx = -1

        if len(cherrypick) > 0 and idx not in cherrypick:
            continue

        if len(cherryskip) > 0 and idx in cherryskip:
            continue
        
        if len(sample['cwe']) == 0:
            continue

        try:
            # Update the 'code' field with the cleaned string
            sample['func'] = format_cleaner(sample['func'])

            src = f'diversevul_{sample["project"]}_{sample["commit_id"]}'
            dat = {
                "source": src,
                "idx": idx,
                "func": sample['func'],
                "vuln": sample['target'],
                "cwe": sample['cwe']
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


if __name__ == '__main__':
    if os.getenv('DATA_SRC').upper() == 'BRYSON':
        parsed = get_bryson_data(
            file_path=os.getenv('BRYSON'),
            limit=int(os.getenv('SAMPLE_LIMIT')),
            start_idx=int(os.getenv('START_IDX')),
            cherrypick=ast.literal_eval(os.getenv('CHERRYPICK')),
            cherryskip=ast.literal_eval(os.getenv('CHERRYSKIP'))
        )
    elif os.getenv('DATA_SRC').upper() == 'BRYSONFIXED':
        parsed = get_brysonfixed_data(
            file_path=os.getenv('BRYSONFIXED'),
            limit=int(os.getenv('SAMPLE_LIMIT')),
            start_idx=int(os.getenv('START_IDX')),
            cherrypick=ast.literal_eval(os.getenv('CHERRYPICK')),
            cherryskip=ast.literal_eval(os.getenv('CHERRYSKIP'))
        )
    elif os.getenv('DATA_SRC').upper() == 'PRIMEVUL':
        parsed = get_primevul_data(
            file_path=os.getenv('PRIMEVUL'),
            limit=int(os.getenv('SAMPLE_LIMIT')),
            start_idx=int(os.getenv('START_IDX')),
            cherrypick=ast.literal_eval(os.getenv('CHERRYPICK')),
            cherryskip=ast.literal_eval(os.getenv('CHERRYSKIP'))
        )
    elif os.getenv('DATA_SRC').upper() == 'DEVIGN':
        parsed = get_devign_data(
            file_path=os.getenv('DEVIGN'),
            limit=int(os.getenv('SAMPLE_LIMIT')),
            start_idx=int(os.getenv('START_IDX')),
            cherrypick=ast.literal_eval(os.getenv('CHERRYPICK')),
            cherryskip=ast.literal_eval(os.getenv('CHERRYSKIP'))
        )
    elif os.getenv('DATA_SRC').upper() == 'MINH':
        parsed = get_minh_data(
            file_path=os.getenv('MINH'),
            limit=int(os.getenv('SAMPLE_LIMIT')),
            start_idx=int(os.getenv('START_IDX')),
            cherrypick=ast.literal_eval(os.getenv('CHERRYPICK')),
            cherryskip=ast.literal_eval(os.getenv('CHERRYSKIP'))
        )
    elif os.getenv('DATA_SRC').upper() == 'DIVERSEVUL':
        parsed = get_diversevul_data(
            file_path=os.getenv('DIVERSEVUL'),
            limit=int(os.getenv('SAMPLE_LIMIT')),
            start_idx=int(os.getenv('START_IDX')),
            cherrypick=ast.literal_eval(os.getenv('CHERRYPICK')),
            cherryskip=ast.literal_eval(os.getenv('CHERRYSKIP'))
        )
    for elem in parsed:
        print(elem)