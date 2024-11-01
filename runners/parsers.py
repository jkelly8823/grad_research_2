import json
import re

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
def get_bryson_data(file_path, limit):
    with open(file_path, 'r') as file:
        data = json.load(file)
    parsed_data = []
    for item in data:
        try:
            # Clean the string
            cleaned_string = item.split('```json')[1].split('```')[0].strip()
            fixed_string = bryson_backlash_fixer(cleaned_string)
            # Load the cleaned string as a JSON object
            json_object = json.loads(fixed_string)

            dat = {
                "source": f'bryson_dataset_{len(parsed_data)+1}',
                "func": json_object['code'],
                "vuln": 1
            }
            parsed_data.append(dat)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        
        limit -= 1
        if limit == 0:
            break
    return parsed_data


def get_primevul_data(file_path, limit):
    parsed_data = []
    
    with open(file_path, "r") as f:
        samples = f.readlines()
    samples = [json.loads(sample) for sample in samples]
    for sample in samples:
        src = f'primevul_{sample["project"]}_{sample["commit_id"]}'
        dat = {
            "source": src,
            "func": sample["func"],
            "vuln": sample["target"]
        }
        parsed_data.append(dat)

        limit -= 1
        if limit == 0:
            break
    return parsed_data