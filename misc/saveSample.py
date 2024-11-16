import json
import re
import os
import tiktoken

def over_tokens(sample):
    max_tokens = int(os.getenv('SAMPLE_TOKEN_LIMIT'))
    encoding = tiktoken.get_encoding("cl100k_base")
    encoded_value = encoding.encode(sample)
    num_tokens = len(encoded_value)
    if num_tokens > max_tokens:
        return True
    return False

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
def get_bryson_data(file_path, limit, start_idx, cherrypick):
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

        try:
            # Clean the string
            cleaned_string = item.split('```json')[1].split('```')[0].strip()
            fixed_string = bryson_backlash_fixer(cleaned_string)
            # Load the cleaned string as a JSON object
            json_object = json.loads(fixed_string)

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


def get_primevul_data(file_path, limit, start_idx, cherrypick):
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

# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------

import dotenv
dotenv.load_dotenv()

prime_ids = [195801]
primes = get_primevul_data(os.getenv('PRIMEVUL'), limit=-1, start_idx=-1, cherrypick=prime_ids)

for dat in primes:
    sample = dat['func']
    id = dat['idx']
    with open(f'misc/primevul_{id}.c', mode='w+', encoding='utf-8', errors='replace') as file:
        file.write(sample)