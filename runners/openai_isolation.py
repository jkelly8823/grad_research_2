import os
import argparse
from dotenv import load_dotenv
from openai import OpenAI
from dataset_parsers import *
load_dotenv()

from get_isolation_results import *

parser = argparse.ArgumentParser()
parser.add_argument(
    '-c',
    '--create',
    action='store_true',
    help="Run the batch job"
)
parser.add_argument(
    '-r',
    '--run',
    action='store_true',
    help="Run the batch job"
)
parser.add_argument(
    '-s',
    '--status',           # Optional flag
    metavar='STATUS',     # Name of the required argument in usage message
    type=str,             # The argument must be a string
    help="Retrieve status for a given batch."
)
parser.add_argument(
    '-v',
    '--verdicts',
    action='store_true',
    help="Collect results into verdicts file"
)
parser.add_argument(
    '-a',
    '--analyze',
    action='store_true',
    help="Collect results into verdicts file"
)


args = parser.parse_args()

client = OpenAI()

ANALYZE_SYSTEM_PROMPT = (" You are an expert in the fields of cybersecurity and code analysis."
                        " You should use the provided information to detect all potential vulnerabilties in the originally presented code sample."
                        #  " You may request additional information."
                        " You should avoid false positives and false negatives."
                        )

HUMAN_SUMMARIZER_ANALYZER = ("Please utilize the output of the summary to inform your analysis of the original code sample."
                    " Evaluate it for any vulnerabilities you can find while avoiding false positives."
                    " Intensively review all detections, reasoning through to ensure they are accurate."
                    # " Utilize the tool summaries to assist your analysis, but do not solely rely upon them."
                    " Perform a step-by-step intense evaluation of the code using your capabilities."
                    " If no true positive vulnerabilities are found respond NONE in your analysis description."
                    # " You have access to a peer RAG agent. If you would like more basic information on a vulnerability,"
                    # " then at the end of your response, respond with 'QNA:', then your list of questions. Your questions"
                    # " should be at the very end of your message. Keep your questions as simple as possible, as you are"
                    # " querying the Common Weakness Enumeration database. An example request would be to provide a" 
                    # " description or example of a specific type of vulnerability. If you have no questions,"
                    # " end your response with 'END' instead. Please engage in at least one round of QNA. "
                    " When you have exhaustively reasoned through all existing vulnerabilities, and excluded all false postives,"
                    " output your final revised analysis prepended by: 'FINAL ANALYSIS:'."
                    " Include a line stating 'VERDICT:', then 'VULNERABLE' or 'SAFE' based upon your results."
                    " Include a line stating 'CWES:', then a list of any present CWEs based upon your vulnerability results."
                    " Include a line stating 'CONFIDENCE:', then a score from 0-100 indicating how certain you are of your answer."
                    " Analyze the following code:\n"
                    "```\n{func}\n```"
                    )

def write_bulk():
    fine_bulk = open("datasets/fine_bulk.jsonl", "w+")

    samples = get_primevul_data(os.getenv('PRIMEVUL'))
    ids = []
    line = {}
    for sample in samples:
        if sample['idx'] in ids:
            continue
        else:
            ids.append(sample['idx'])

        line = {
            "custom_id": f"bulk_{sample['idx']}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": os.getenv("OPENAI_ISOLATION_MODEL"),
                "messages": [
                    {"role": "system", "content": ANALYZE_SYSTEM_PROMPT.strip()},
                    {"role": "user", "content": HUMAN_SUMMARIZER_ANALYZER.format(func=sample['func']).strip()}
                ],
            }
        }
        fine_bulk.write(json.dumps(line) + "\n")

        # print(sample['source'], sample['idx'], sample['vuln'], sample['cwe'])
    return line

def single_completion(line):
    completion = client.chat.completions.create(
        model=line['body']['model'],
        messages=line['body']['messages']
    )
    print(completion.choices[0].message)

def bulk_completion():
    batch_input_file = client.files.create(
        file=open("datasets/fine_bulk.jsonl", "rb"),
        purpose="batch"
    )

    batch_input_file_id = batch_input_file.id

    batch = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={
        "description": "Analyzer Isolation Test"
        }
    )

    print("BATCH INFO:\n",batch)

    with open(f"misc/{batch.id}.jsonl", "w+") as file:
        for item in batch:
            try:
                file.write(json.dumps(item) + "\n")
            except Exception as e:
                print(f"Exception: {e}")
                try:
                    file.write(item + "\n")
                except Exception as e2:
                    print(f"Exception: {e2}")
                    try:
                        file.write(str(item) + "\n")
                    except Exception as e3:
                        print(f"Exception: {e3}")
    
    return batch

def extract_vulnerability_info(text):
    # Regex patterns
    status_pattern = r"VERDICT:\s*(\w+)"  # Matches "VULNERABLE" or "SAFE"
    # confidence_pattern = r"CONFIDENCE:\s*(\d+)"  # Matches the confidence score
    confidence_pattern = r"CONFIDENCE\s*[^0-9]*\s*:\s*[^0-9]*\s*(\d+)[^0-9]*"

    cwe_pattern = r"CWES:\s*\[*([^\]]*)\]*"  # Matches the CWE list
    cwe_pattern_2 = r"(CWE-[0-9]*)\s*[^0-9]*\s*"  # Matches the CWE

    # Extract matches
    status_match = re.search(status_pattern, text)
    confidence_match = re.search(confidence_pattern, text)
    cwe_match = re.search(cwe_pattern, text)

    # Extract status (1 for "VULNERABLE", 0 for "SAFE")
    status = 1 if status_match and 'VULN' in status_match.group(1).upper() else 0

    # Extract confidence score
    confidence_score = int(confidence_match.group(1)) if confidence_match else None

    # Extract CWE list
    if cwe_match:
        cwe_list_raw = cwe_match.group(1).strip()
        if cwe_list_raw.upper() == "NONE":  # Handle "NONE"
            cwe_list = []
        else:
            # cwe_list = [cwe.strip("' ") for cwe in cwe_list_raw.split(",")]
            cwe_list = []
            for cwe in cwe_list_raw.split(","):
                inner_cwe_match = re.search(cwe_pattern_2, cwe)
                if inner_cwe_match:
                    cwe_list.append(inner_cwe_match.group(1).upper().strip("' "))
    else:
        cwe_list = []

    return status, confidence_score, cwe_list


def write_verdicts():
    
    with open("outputs/isolated_batch.jsonl", "r") as f:
        results = [json.loads(line) for line in f]

    samples = get_primevul_data(os.getenv('PRIMEVUL'))
    src_map = {}
    for sample in samples:
        if sample['idx'] in src_map.keys():
            continue
        else:
            src_map[sample['idx']] = sample

    with open("outputs/verdicts.csv", "w+", encoding="utf-8", errors="replace") as f:
        header = "run,source,idx,true_vuln,predicted_vuln,predicted_confidence,true_cwe, predicted_cwe\n"
        f.write(header)
    
        for idx, row in enumerate(results):
            # Extract relevant information
            resp = row['response']['body']['choices'][0]['message']['content']
            id = int(row["custom_id"][5:])
            status, confidence, cwe_list = extract_vulnerability_info(resp)
            
            # Prepare the line
            line = [
                idx,                          # Row index
                "primevul",                   # Source
                id,                           # ID
                src_map[id]['vuln'],          # Vulnerability status
                status,                       # Model-determined status
                confidence,                   # Confidence score
                json.dumps(src_map[id]['cwe']),  # CWE array as JSON string
                json.dumps(cwe_list)          # CWE list as JSON string
            ]
            
            formatted_line = []
            for x in line:
                tmp = str(x).replace('"', "'")
                if '[' in tmp:
                    tmp = '"' + tmp + '"'
                formatted_line.append(tmp)
            
            f.write(",".join(formatted_line) + "\n")



if __name__ == "__main__":
    if args.create:
        last_line = write_bulk()
        test_completion = single_completion(last_line)
    elif args.run:
        batch_info = bulk_completion()
    elif args.status:
        print(client.batches.retrieve(args.status))
    elif args.verdicts:
        write_verdicts()
    elif args.analyze:
        getResults()
