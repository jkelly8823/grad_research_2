import json
import re

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

f = open(r'D:\grad_research_2\datasets\filtered_primevul_test_paired.jsonl', 'r')
f2 = open(r'D:\grad_research_2\datasets\finetunes_primevul.jsonl', 'w+')
samples = f.readlines()
samples = [json.loads(sample) for sample in samples]
for sample in samples:
    try:
        code = sample['func'] #format_cleaner(sample['func'])
    except Exception as e:
        print(sample['func'])
        print(e)


    if sample['target'] == 1:
        status = 'VULNERABLE'
    else:
        status = 'SAFE'
    cwe = sample['cwe']
    cve_desc = sample['cve_desc']

    line = {"messages":
            [
                {"role": "system", "content": "You are an expert in the fields of cybersecurity and code analysis."},
                {"role": "user", "content": f"Please determine the true vulnerability status of the following code sample:\n{code}"},
                {"role": "assistant", "content": (
                    f"This code contains vulnerabilities associated with the following CWEs {cwe}."
                    f"The vulnerabilityy has been described as follows: {cve_desc}"
                    f"FINAL VERDICT: {status}"
                )}
            ]
           }
    f2.write(json.dumps(line) + "\n")

f.close()
f2.close()