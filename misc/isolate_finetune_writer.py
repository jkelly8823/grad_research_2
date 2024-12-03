import json
import re
import pandas as pd
import math
import random
import os
import tiktoken
from collections import defaultdict
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
    cleaned_code = code
    try:
        # Decode the escaped string (removes unnecessary escape characters)
        cleaned_code = bytes(code, "utf-8").decode("unicode_escape")
    except Exception as e:
        print(e)
    
    try:
        # Further clean up additional escape sequences like backslashes or newlines
        cleaned_code = cleaned_code.replace("\\\\", "\\").replace("\\n", "\n").replace('\\"', '"')
    except Exception as e:
        print(e)
    
    try:
        # Normalize indentation (convert tabs to 4 spaces)
        cleaned_code = cleaned_code.replace("\t", "    ")
    except Exception as e:
        print(e)

    try:
        # Remove excessive whitespace (more than 2 consecutive blank lines)
        cleaned_code = re.sub(r"\n\s*\n", "\n\n", cleaned_code)
    except Exception as e:
        print(e)

    return cleaned_code

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

def write_files(bias = False):
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
                        " Analyze the following code:\n"
                        "```\n{func}\n```"
                        )

    fine_lines = defaultdict(list)
    output=(
            "FINAL ANALYSIS:\n"
            "VERDICT: {verdict}\n"
            "CWES: {cwes}"
    )
    samples = get_primevul_data(r"D:\grad_research_2\datasets\PrimeVul\primevul_train_paired.jsonl")
    for sample in samples:
            if sample['vuln'] == 1:
                resp = output.format(verdict="VULNERABLE", cwes=sample['cwe'])
            else:
                resp = output.format(verdict="SAFE", cwes="NONE")
            line = {"messages":
                [
                    {"role": "system", "content": ANALYZE_SYSTEM_PROMPT.strip()},
                    {"role": "user", "content": HUMAN_SUMMARIZER_ANALYZER.format(func=sample['func'])},
                    {"role": "assistant", "content": resp}
                ]
            }

            fine_lines[sample['vuln']].append(line)

   
    if bias:
        nm = "_biased"
    else:
        nm = ""
    finetune = open(rf'D:\grad_research_2\datasets\isolate{nm}_finetunes_train_primevul.jsonl', 'w+')
    validation = open(rf'D:\grad_research_2\datasets\isolate{nm}_finetunes_validate_primevul.jsonl', 'w+')
    total_len = len(fine_lines[0]) + len(fine_lines[1])
    split = math.ceil(0.8 * total_len)
    if bias:
        safe_size = min(len(fine_lines[0]), math.ceil(0.6 * split))
        vuln_size = split - safe_size

        random.shuffle(fine_lines[0])
        random.shuffle(fine_lines[1])

        print(total_len, split, safe_size, vuln_size, len(fine_lines[0]), len(fine_lines[1]))

        train_safe = fine_lines[0][:safe_size]
        valid_safe = fine_lines[0][safe_size:]
        train_vuln = fine_lines[1][:vuln_size]
        valid_vuln = fine_lines[1][vuln_size:]
        
        train = [json.dumps(line) + "\n" for line in train_safe + train_vuln]
        valid = [json.dumps(line) + "\n" for line in valid_safe + valid_vuln]

        random.shuffle(train)
        random.shuffle(valid)

        finetune.writelines(train)
        validation.writelines(valid)

    else:
        fine_lines = fine_lines[0] + fine_lines[1]
        random.shuffle(fine_lines)

        for idx, line in enumerate(fine_lines):
            if idx <= split:
                finetune.write(json.dumps(line) + "\n")
            else:
                validation.write(json.dumps(line) + "\n")
    finetune.close()
    validation.close()

if __name__ == "__main__":
    write_files(False)